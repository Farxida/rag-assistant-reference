"""
Guardrails — детерминированные проверки входа и выхода.

Чистые функции без LLM: дёшево, мгновенно, тестируемо pytest'ом.
LLM-репеар подключается в графе только если guard_output нашёл нарушения.

Вход:  prompt injection, PII, мусор/спам.
Выход: скидки/промокоды, обещание конкретного клинера/времени,
       внутренняя кухня, утечка системного промпта, длина.
"""

import re

# ---------- INPUT GUARDS ----------

# Паттерны prompt injection (классика: смена роли, слив промпта, override)
_INJECTION_PATTERNS = [
    r"ignore (all |your |previous |prior )*(instructions|rules|prompts?)",
    r"disregard (all |your |previous )*(instructions|rules)",
    r"system prompt",
    r"you are now",
    r"pretend (to be|you are)",
    r"act as (?!a customer)",
    r"jailbreak",
    r"developer mode",
    r"\bDAN\b",
    r"repeat (everything|your instructions|the text) above",
    r"what (is|are) your (instructions|rules|system)",
    r"новые инструкции",
    r"забудь (все|свои) (инструкции|правила)",
]
_INJECTION_RX = re.compile("|".join(_INJECTION_PATTERNS), re.IGNORECASE)

# PII, которое клиенту незачем слать в чат (карты, пароли)
_PII_PATTERNS = [
    r"\b(?:\d[ -]?){13,19}\b",              # номер карты
    r"\bcvv\b|\bcvc\b",
    r"\bmy password\b|\bпароль\b",
]
_PII_RX = re.compile("|".join(_PII_PATTERNS), re.IGNORECASE)


def guard_input(text: str) -> str:
    """Возвращает 'ok' | 'injection' | 'pii' | 'empty'."""
    if not text or not text.strip():
        return "empty"
    if _INJECTION_RX.search(text):
        return "injection"
    if _PII_RX.search(text):
        return "pii"
    return "ok"


# ---------- OUTPUT GUARDS ----------

# Ловим ПРЕДЛОЖЕНИЕ скидки, а не упоминание: «we don't offer discounts» — легитимный ответ
_DISCOUNT_RX = re.compile(
    r"(?:can|will|happy to|glad to|let me|i'?ll)\s+(?:give|offer|apply|arrange)\s+(?:you\s+)?(?:a\s+|an\s+)?\S{0,12}\s?discount"
    r"|here'?s\s+(?:a\s+)?\d{1,2}%"
    r"|\b\d{1,2}%\s+off\b"
    r"|\bpromo ?code|\bcoupon code"
    r"|\bfree (?:month|year|upgrade|credits)"
    r"|дам скидк|сделаем скидк|предоставим скидк",
    re.IGNORECASE,
)
# необоснованные обещания SLA/uptime, которых нет в базе знаний
_PROMISE_CLEANER_RX = re.compile(
    r"(guarantee[ds]? (you )?100% uptime|promise[ds]? (you )?(zero|no) downtime|guarantee[ds]? .*refund)",
    re.IGNORECASE,
)
# слив системного промпта / внутренностей
_LEAK_RX = re.compile(
    r"(system prompt|my instructions (are|say)|as an ai (language )?model|according to my rules)",
    re.IGNORECASE,
)
# протёкшая разметка tool-вызовов (llama иногда «проговаривает» вызовы текстом)
_TOOLCALL_LEAK_RX = re.compile(
    r"<function[^>]*>[^<{]*(?:</function>)?\s*(?:\{[^}]*\})?|"
    r"<tool_call>(?:.*?</tool_call>)?|"
    r"^\s*\{\"(?:city_or_area|service_type|query|city)\":[^}]*\}\s*$",
    re.IGNORECASE | re.DOTALL | re.MULTILINE,
)


def strip_toolcall_markup(text: str) -> str:
    """Детерминированно вырезает протёкшую tool-разметку из ответа."""
    cleaned = _TOOLCALL_LEAK_RX.sub("", text or "")
    # схлопываем оставшиеся пустые строки
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()
    return cleaned

MAX_ANSWER_WORDS = 220  # правило «under 150 words» + запас на форматирование


def guard_output(text: str) -> list[str]:
    """Возвращает список нарушений (пустой = всё чисто)."""
    violations = []
    if not text or not text.strip():
        violations.append("empty_answer")
        return violations
    if _DISCOUNT_RX.search(text):
        violations.append("discount_offer")
    if _PROMISE_CLEANER_RX.search(text):
        violations.append("unbacked_promise")
    if _LEAK_RX.search(text):
        violations.append("prompt_leak")
    if len(text.split()) > MAX_ANSWER_WORDS:
        violations.append("too_long")
    return violations


# ---------- Шаблонные ответы (детерминированные ветки графа) ----------

REFUSAL_INJECTION = (
    "I can only help with questions about Northwind Cloud. "
    "How can I help you with Northwind Cloud?"
)

REFUSAL_PII = (
    "For your security, please don't share card details or passwords in this chat. "
    "Payments are handled safely in the billing portal. "
    "How else can I help you with Northwind Cloud?"
)

REFUSAL_EMPTY = "I didn't catch that — how can I help you with Northwind Cloud?"

CHITCHAT_REPLY = (
    "Hello! I'm the Northwind Cloud assistant. I can help with plans and pricing, "
    "features, limits, integrations and troubleshooting. What would you like to know?"
)

OFFTOPIC_REPLY = (
    "That's outside what I can help with — I only cover Northwind Cloud products "
    "and services. If you have a question about the platform, I'm here!"
)

ESCALATION_REPLY = (
    "I'm sorry to hear that — this needs a human touch. I've flagged your case "
    "for our support team. They'll get back to you shortly. You can also reach us "
    "directly at support@northwind.cloud."
)
