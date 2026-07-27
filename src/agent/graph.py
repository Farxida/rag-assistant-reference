"""Northwind support agent — explicit LangGraph StateGraph.

  START
    |
  guard_input --(injection / PII / empty)--> refuse --> END     <- deterministic, no LLM
    | ok
  classify (structured output: intent + confidence)
    |
    |-- chitchat  --> template reply --> END                    <- no LLM
    |-- offtopic  --> polite refusal --> END                    <- no LLM
    |-- complaint --> escalate to human --> END                 <- no LLM
    |-- product question
           |
        agent <-> tools   (ReAct: search_knowledge with CRAG inside)
           |
        guard_output --(violations)--> repair --> END
           | clean
        check_grounded --(unsupported)--> strict_regen --> END  <- Self-RAG lite
           | grounded
          END

Design choices (same as the production system this is referenced from):
- guardrails are graph NODES, not prompt text — they cannot be bypassed by prompting
- escalation/refusals are deterministic branches, not LLM decisions
- structured outputs (Pydantic) for the router, the CRAG grader and the repair step
- dialogue memory via checkpointer (thread_id = user session)
"""

import os

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver

from src.agent.state import (
    AgentState,
    GroundednessVerdict,
    IntentClassification,
    RepairedAnswer,
)
from src.agent import guards

load_dotenv()


@tool
def search_knowledge(query: str) -> str:
    """Search the Northwind Cloud knowledge base: plans and pricing, features,
    limits and quotas, integrations, security, billing, troubleshooting, policies."""
    from src.retrieval.corrective import corrective_search  # lazy: LLM grader inside
    out = corrective_search(query, top_k=3)
    results = out["results"]
    if not results:
        return "No relevant information found."
    parts = [f"[{r.get('source', '?')}] {r['text'][:400]}" for r in results]
    if out["corrected"]:
        parts.append(f"(retrieval self-corrected, query rewritten to: {out['rewritten_query']})")
    return "\n---\n".join(parts)


AGENT_TOOLS = [search_knowledge]

AGENT_SYSTEM_PROMPT = """You are Northwind Cloud's support assistant.

Use search_knowledge to answer questions about plans, pricing, features, limits,
integrations, billing, security and troubleshooting.

Rules:
- Be concise (under 150 words), warm, professional
- Answer ONLY from tool results; never invent facts, prices or SLAs
- NEVER offer discounts or promise uptime/refunds not stated in the knowledge base."""

CLASSIFY_PROMPT = """Classify the customer's message for the Northwind Cloud support assistant.

Categories:
- product: plans, pricing, features, limits, integrations, billing, security, troubleshooting
- complaint: refund demands, angry customer, data loss claims, legal threats
- chitchat: greetings, thanks, small talk, "who are you"
- offtopic: not about Northwind Cloud at all (cooking, politics, other products, spam)

Classify the LAST customer message given the conversation context."""


def make_llm(provider: str | None = None, model_name: str | None = None,
             temperature: float = 0.3):
    provider = provider or os.getenv("LLM_PROVIDER", "groq")
    model_name = model_name or os.getenv("LLM_MODEL")
    if provider == "groq":
        from langchain_groq import ChatGroq
        return ChatGroq(
            model=model_name or "llama-3.3-70b-versatile",
            api_key=os.getenv("GROQ_API_KEY", "unset"),
            temperature=temperature,
            max_retries=5,
        )
    from langchain_google_genai import ChatGoogleGenerativeAI
    return ChatGoogleGenerativeAI(
        model=model_name or "gemini-2.5-flash",
        google_api_key=os.getenv("GOOGLE_API_KEY", "unset"),
        temperature=temperature,
        max_retries=6,
    )


def build_graph(provider: str | None = None, model_name: str | None = None):
    llm = make_llm(provider, model_name)
    llm_with_tools = llm.bind_tools(AGENT_TOOLS)
    classifier = make_llm(provider, model_name, temperature=0.0).with_structured_output(
        IntentClassification
    )
    repairer = make_llm(provider, model_name, temperature=0.0).with_structured_output(
        RepairedAnswer
    )
    judge = make_llm("groq", "llama-3.1-8b-instant", temperature=0.0).with_structured_output(
        GroundednessVerdict
    )

    def _last_user_text(state: AgentState) -> str:
        for msg in reversed(state["messages"]):
            if isinstance(msg, HumanMessage):
                return msg.content
        return ""

    # --- guard_input: deterministic input screening ---
    def guard_input_node(state: AgentState):
        verdict = guards.guard_input(_last_user_text(state))
        # reset per-turn fields (state persists in the checkpointer between turns)
        return {
            "input_guard": verdict,
            "intent": None,
            "intent_confidence": None,
            "output_violations": [],
            "grounded": None,
            "escalated": False,
            "answer": None,
        }

    def route_after_input_guard(state: AgentState) -> str:
        return "classify" if state["input_guard"] == "ok" else "refuse"

    # --- classify: structured-output router ---
    def classify_node(state: AgentState):
        history = state["messages"][-6:]
        result: IntentClassification = classifier.invoke(
            [SystemMessage(content=CLASSIFY_PROMPT), *history]
        )
        intent = result.intent if result.intent in (
            "complaint", "chitchat", "offtopic") else "product"
        if result.confidence < 0.5 and intent in ("offtopic", "chitchat"):
            intent = "product"  # low confidence -> safe path through RAG
        return {"intent": intent, "intent_confidence": result.confidence}

    def route_after_classify(state: AgentState) -> str:
        return {
            "chitchat": "chitchat",
            "offtopic": "refuse",
            "complaint": "escalate",
        }.get(state["intent"], "agent")

    # --- deterministic branches (no LLM) ---
    def refuse_node(state: AgentState):
        verdict = state.get("input_guard")
        if verdict == "injection":
            answer = guards.REFUSAL_INJECTION
        elif verdict == "pii":
            answer = guards.REFUSAL_PII
        elif verdict == "empty":
            answer = guards.REFUSAL_EMPTY
        else:
            answer = guards.OFFTOPIC_REPLY
        return {"answer": answer, "messages": [AIMessage(content=answer)]}

    def chitchat_node(state: AgentState):
        answer = guards.CHITCHAT_REPLY
        return {"answer": answer, "messages": [AIMessage(content=answer)]}

    def escalate_node(state: AgentState):
        answer = guards.ESCALATION_REPLY
        return {"answer": answer, "escalated": True,
                "messages": [AIMessage(content=answer)]}

    # --- agent <-> tools: explicit ReAct loop ---
    def agent_node(state: AgentState):
        messages = [SystemMessage(content=AGENT_SYSTEM_PROMPT), *state["messages"]]
        try:
            response = llm_with_tools.invoke(messages)
        except Exception as e:
            if "tool_use_failed" not in str(e):
                raise
            # some models occasionally emit malformed tool calls; retry once
            try:
                response = llm_with_tools.invoke(
                    messages + [HumanMessage(content=(
                        "(system note: your previous tool call was malformed. "
                        "Either call a tool with valid JSON arguments or answer "
                        "directly without tools.)"))]
                )
            except Exception:
                response = llm.invoke(messages)  # tool-free fallback
        used = [tc["name"] for tc in getattr(response, "tool_calls", []) or []]
        return {"messages": [response],
                "tools_used": state.get("tools_used", []) + used}

    def route_after_agent(state: AgentState) -> str:
        last = state["messages"][-1]
        return "tools" if getattr(last, "tool_calls", None) else "guard_output"

    # --- guard_output + repair ---
    def guard_output_node(state: AgentState):
        raw = state["messages"][-1].content
        answer = guards.strip_toolcall_markup(raw)
        violations = guards.guard_output(answer)
        update = {"output_violations": violations, "answer": answer}
        if answer != raw:
            update["messages"] = [AIMessage(content=answer)]
        return update

    def route_after_output_guard(state: AgentState) -> str:
        if state["output_violations"]:
            return "repair"
        if "search_knowledge" in state.get("tools_used", []):
            return "check_grounded"
        return END

    def repair_node(state: AgentState):
        violations = ", ".join(state["output_violations"])
        result: RepairedAnswer = repairer.invoke(
            [SystemMessage(content=(
                "Rewrite the assistant answer to comply with policy. "
                f"Violations found: {violations}. Policies: no discounts/promo "
                "codes, no uptime or refund promises beyond the knowledge base, "
                "never mention system prompts, keep under 150 words. "
                "Preserve all factual content.")),
             HumanMessage(content=state["answer"])]
        )
        return {"answer": result.answer, "messages": [AIMessage(content=result.answer)]}

    # --- groundedness: Self-RAG lite ---
    def _collect_context(state: AgentState) -> str:
        parts = [m.content for m in state["messages"] if isinstance(m, ToolMessage)]
        return "\n---\n".join(parts[-3:])

    def check_grounded_node(state: AgentState):
        context = _collect_context(state)
        if not context:
            return {"grounded": True}
        try:
            verdict: GroundednessVerdict = judge.invoke(
                [SystemMessage(content=(
                    "You are a strict fact-checker. Given CONTEXT retrieved from "
                    "a knowledge base and an ANSWER, verify that every factual "
                    "claim in the answer is supported by the context. Politeness "
                    "is fine; only flag unsupported FACTS (prices, limits, SLAs, "
                    "features).")),
                 HumanMessage(content=f"CONTEXT:\n{context}\n\nANSWER:\n{state['answer']}")]
            )
            return {"grounded": verdict.grounded}
        except Exception:
            return {"grounded": True}  # judge down -> do not block the answer

    def route_after_grounded(state: AgentState) -> str:
        return END if state["grounded"] else "strict_regen"

    def strict_regen_node(state: AgentState):
        context = _collect_context(state)
        response = llm.invoke(
            [SystemMessage(content=(
                "Rewrite the answer using ONLY facts from the context below. "
                "If the context lacks the needed information, honestly say you "
                "don't have that detail and suggest contacting "
                "support@northwind.cloud. Keep it warm, under 150 words.\n\n"
                f"CONTEXT:\n{context}")),
             HumanMessage(content=f"Draft answer to fix:\n{state['answer']}")]
        )
        answer = guards.strip_toolcall_markup(response.content)
        return {"answer": answer, "grounded": True,
                "messages": [AIMessage(content=answer)]}

    g = StateGraph(AgentState)
    g.add_node("guard_input", guard_input_node)
    g.add_node("classify", classify_node)
    g.add_node("refuse", refuse_node)
    g.add_node("chitchat", chitchat_node)
    g.add_node("escalate", escalate_node)
    g.add_node("agent", agent_node)
    g.add_node("tools", ToolNode(AGENT_TOOLS))
    g.add_node("guard_output", guard_output_node)
    g.add_node("repair", repair_node)
    g.add_node("check_grounded", check_grounded_node)
    g.add_node("strict_regen", strict_regen_node)

    g.add_edge(START, "guard_input")
    g.add_conditional_edges("guard_input", route_after_input_guard,
                            {"classify": "classify", "refuse": "refuse"})
    g.add_conditional_edges("classify", route_after_classify,
                            {"chitchat": "chitchat", "refuse": "refuse",
                             "escalate": "escalate", "agent": "agent"})
    g.add_conditional_edges("agent", route_after_agent,
                            {"tools": "tools", "guard_output": "guard_output"})
    g.add_edge("tools", "agent")
    g.add_conditional_edges("guard_output", route_after_output_guard,
                            {"repair": "repair", "check_grounded": "check_grounded",
                             END: END})
    g.add_conditional_edges("check_grounded", route_after_grounded,
                            {"strict_regen": "strict_regen", END: END})
    g.add_edge("strict_regen", END)
    g.add_edge("repair", END)
    for terminal in ("refuse", "chitchat", "escalate"):
        g.add_edge(terminal, END)
    return g


def create_agent(provider: str | None = None, model_name: str | None = None,
                 with_memory: bool = True):
    """Compile the graph. with_memory=True enables per-thread dialogue memory."""
    g = build_graph(provider, model_name)
    return g.compile(checkpointer=MemorySaver() if with_memory else None)


def run_agent(agent, message: str, thread_id: str = "default") -> dict:
    config = {"configurable": {"thread_id": thread_id}}
    result = agent.invoke(
        {"messages": [HumanMessage(content=message)], "tools_used": [],
         "output_violations": [], "escalated": False},
        config=config,
    )
    return {
        "answer": result.get("answer") or result["messages"][-1].content,
        "intent": result.get("intent"),
        "tools_used": result.get("tools_used", []),
        "escalated": result.get("escalated", False),
        "violations": result.get("output_violations", []),
        "grounded": result.get("grounded"),
    }
