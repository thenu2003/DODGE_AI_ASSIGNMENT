import json
import os
import re
from typing import Any, Dict, Optional

try:
    from google import genai as genai_new
except Exception:
    genai_new = None


INTENT_SCHEMA_HINT = {
    "intent": "aggregation | trace_flow | broken_flow | entity_lookup",
    "entities": {
        "document_id": "optional string",
        "entity_type": "optional sales_order|delivery|billing_document|customer|product",
        "entity_id": "optional string/integer-like",
    },
}


def _normalize_text(question: str) -> str:
    return question.strip().lower()


def classify_intent_rule_based(question: str) -> Dict[str, Any]:
    text = _normalize_text(question)
    entities: Dict[str, Any] = {}

    num_match = re.search(r"\b\d{5,}\b", text)
    if num_match:
        entities["entity_id"] = num_match.group(0)
        entities["document_id"] = num_match.group(0)

    if "sales order" in text:
        entities["entity_type"] = "sales_order"
    elif "delivery" in text:
        entities["entity_type"] = "delivery"
    elif "billing" in text or "invoice" in text:
        entities["entity_type"] = "billing_document"
    elif "customer" in text:
        entities["entity_type"] = "customer"
    elif "product" in text:
        entities["entity_type"] = "product"

    if "trace" in text or "full flow" in text or "end to end" in text:
        return {"intent": "trace_flow", "entities": entities, "source": "rule"}
    if "not billed" in text or "broken" in text or "incomplete" in text or "pending billing" in text:
        return {"intent": "broken_flow", "entities": entities, "source": "rule"}
    if "show details" in text or "details for" in text or "lookup" in text:
        return {"intent": "entity_lookup", "entities": entities, "source": "rule"}
    if "highest number" in text or "most" in text or "count" in text or "associated with" in text:
        return {"intent": "aggregation", "entities": entities, "source": "rule"}

    return {"intent": "entity_lookup", "entities": entities, "source": "rule_default"}


def _extract_json(raw: str) -> Optional[Dict[str, Any]]:
    try:
        return json.loads(raw)
    except Exception:
        pass
    match = re.search(r"\{[\s\S]*\}", raw)
    if not match:
        return None
    try:
        return json.loads(match.group(0))
    except Exception:
        return None


def classify_intent_with_gemini(question: str) -> Optional[Dict[str, Any]]:
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return {"_llm_error": "Missing GEMINI_API_KEY/GOOGLE_API_KEY"}

    last_error: Optional[str] = None
    try:
        prompt = (
            "Classify the user's SAP O2C analytics question into one intent and extract entities.\n"
            "Return strict JSON only, no markdown.\n"
            f"Schema: {json.dumps(INTENT_SCHEMA_HINT)}\n"
            f"Question: {question}"
        )

        # Preferred SDK path.
        if genai_new is not None:
            client = genai_new.Client(api_key=api_key)
            for model_name in ("gemini-2.5-flash", "gemini-2.0-flash", "gemini-flash-latest"):
                try:
                    resp = client.models.generate_content(model=model_name, contents=prompt)
                    text = (getattr(resp, "text", "") or "").strip()
                    parsed = _extract_json(text)
                    if parsed and parsed.get("intent") in {"aggregation", "trace_flow", "broken_flow", "entity_lookup"}:
                        parsed["source"] = f"gemini_new_sdk:{model_name}"
                        parsed.setdefault("entities", {})
                        return parsed
                except Exception as model_error:
                    last_error = f"New SDK {model_name} error: {model_error}"
            if not last_error:
                last_error = "New SDK returned non-JSON or unsupported intent"
    except Exception as e:
        last_error = f"New SDK error: {e}"

    try:
        # Backward compatible fallback.
        import google.generativeai as genai_old

        if genai_old is not None:
            genai_old.configure(api_key=api_key)
            model = genai_old.GenerativeModel("gemini-2.0-flash")
            response = model.generate_content(prompt)
            text = (response.text or "").strip()
            parsed = _extract_json(text)
            if parsed and parsed.get("intent") in {"aggregation", "trace_flow", "broken_flow", "entity_lookup"}:
                parsed["source"] = "gemini_old_sdk:gemini-2.0-flash"
                parsed.setdefault("entities", {})
                return parsed
            if not last_error:
                last_error = "Old SDK returned non-JSON or unsupported intent"
    except Exception as e:
        last_error = f"Old SDK error: {e}"

    return {"_llm_error": last_error or "Unknown Gemini classification failure"}


def classify_intent(question: str, use_llm: bool = True) -> Dict[str, Any]:
    llm_error = None
    if use_llm:
        llm_result = classify_intent_with_gemini(question)
        if llm_result and llm_result.get("intent"):
            return llm_result
        if llm_result and llm_result.get("_llm_error"):
            llm_error = llm_result["_llm_error"]
    result = classify_intent_rule_based(question)
    if llm_error:
        result["llm_error"] = llm_error
    return result
