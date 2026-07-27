"""
Agent State + Pydantic-схемы structured outputs.

State — то, что течёт по графу между узлами.
Pydantic-модели — контракты для structured output LLM (router, repair).
"""

from typing import Annotated, Literal, Optional
from typing_extensions import TypedDict

from pydantic import BaseModel, Field
from langgraph.graph.message import add_messages


# ---------- Structured output: классификация intent ----------

Intent = Literal[
    "product",       # plans, pricing, features, limits, billing, troubleshooting
    "complaint",     # refund demands, angry customer, data loss, legal threats
    "chitchat",      # greetings, thanks, small talk
    "offtopic",      # not about Northwind Cloud at all
]


class IntentClassification(BaseModel):
    """Structured output роутера: агент обязан вернуть ровно эту схему."""

    intent: Intent = Field(description="Customer message intent category")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence 0..1")
    reasoning: str = Field(description="One short sentence why")


# ---------- Structured output: починка ответа после guard_output ----------

class RepairedAnswer(BaseModel):
    """Ответ, переписанный без нарушений политик."""

    answer: str = Field(description="Rewritten answer, policy-compliant, under 150 words")


# ---------- Structured output: groundedness-судья (Self-RAG lite) ----------

class GroundednessVerdict(BaseModel):
    """Вердикт: подкреплён ли ответ контекстом из retrieval."""

    grounded: bool = Field(
        description="True if every factual claim in the answer is supported by the context"
    )
    unsupported_claims: list[str] = Field(
        default_factory=list,
        description="Claims not supported by the context (empty if grounded)",
    )


# ---------- Состояние графа ----------

class AgentState(TypedDict):
    # история сообщений; add_messages корректно мёржит списки
    messages: Annotated[list, add_messages]
    # результат guard_input: ok | injection | pii
    input_guard: Optional[str]
    # intent от роутера
    intent: Optional[str]
    intent_confidence: Optional[float]
    # какие тулы были вызваны (для логов/метрик)
    tools_used: list[str]
    # нарушения, найденные guard_output (до починки)
    output_violations: list[str]
    # groundedness: None = не проверялся, True/False = вердикт судьи
    grounded: Optional[bool]
    # финальный ответ пользователю
    answer: Optional[str]
    # эскалация на человека
    escalated: bool
