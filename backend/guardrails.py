import re
from typing import List

from chat_models import GuardrailResult


DOMAIN_KEYWORDS = {
    "sales order",
    "sales orders",
    "delivery",
    "deliveries",
    "billing",
    "billing document",
    "billing documents",
    "invoice",
    "invoicing",
    "payment",
    "customer",
    "product",
    "plant",
    "order to cash",
    "o2c",
    "trace",
    "flow",
    "sap",
}


BLOCKLIST_PATTERNS = [
    r"\bpoem\b",
    r"\bjoke\b",
    r"\bstory\b",
    r"\brecipe\b",
    r"\bmovie\b",
    r"\bweather\b",
    r"\bstock price\b",
    r"\bpolitics\b",
]


def run_guardrails(question: str) -> GuardrailResult:
    text = question.lower().strip()

    if not text:
        return GuardrailResult(allowed=False, reason="Empty question")

    for pat in BLOCKLIST_PATTERNS:
        if re.search(pat, text):
            return GuardrailResult(allowed=False, reason="Prompt appears off-topic for this domain")

    matched: List[str] = [kw for kw in DOMAIN_KEYWORDS if kw in text]
    has_id_like_token = bool(re.search(r"\b(\d{5,}|so[_\-\s]?\d+|del[_\-\s]?\d+|bill[_\-\s]?\d+)\b", text))

    if not matched and not has_id_like_token:
        return GuardrailResult(
            allowed=False,
            reason="Question is not related to SAP O2C entities or lifecycle flows",
            matched_keywords=[],
        )

    return GuardrailResult(allowed=True, reason="Accepted", matched_keywords=sorted(matched))
