from fastapi import HTTPException

from chat_models import ChatQueryRequest, ChatQueryResponse
from guardrails import run_guardrails
from intent_classifier import classify_intent
from query_executor import QueryExecutor
from query_planner import build_query_plan
from response_formatter import format_answer_text


class ChatQueryController:
    def __init__(self, executor: QueryExecutor):
        self.executor = executor

    def handle_query(self, req: ChatQueryRequest) -> ChatQueryResponse:
        guardrail = run_guardrails(req.question)
        if not guardrail.allowed:
            return ChatQueryResponse(
                answer_text=f"Request rejected by guardrails: {guardrail.reason}",
                detected_intent="rejected",
                query_plan={},
                data_result={},
                highlight_nodes=[],
                guardrail=guardrail.model_dump(),
            )

        intent_info = classify_intent(req.question, use_llm=req.use_llm)
        plan = build_query_plan(req.question, intent_info, top_k=req.top_k)

        # Plan-level structural safety validation before execution.
        if plan.intent not in {"aggregation", "trace_flow", "broken_flow", "entity_lookup"}:
            raise HTTPException(status_code=400, detail="Unsupported query intent")
        if not plan.steps:
            raise HTTPException(status_code=400, detail="Invalid query plan (no steps)")

        exec_result = self.executor.execute_plan(plan)
        exec_result["classifier"] = {
            "source": intent_info.get("source", "unknown"),
            "llm_error": intent_info.get("llm_error"),
        }
        answer_text = format_answer_text(plan, exec_result)

        return ChatQueryResponse(
            answer_text=answer_text,
            detected_intent=plan.intent,
            query_plan=plan.model_dump(),
            data_result=exec_result,
            highlight_nodes=exec_result.get("highlight_nodes", []),
            guardrail=guardrail.model_dump(),
        )
