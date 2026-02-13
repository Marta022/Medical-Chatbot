from __future__ import annotations

from config.prompts import build_context_block
from config.settings import BASE_SYSTEM_PROMPT, SETTINGS
from models import GuardrailResult, LLMRequest, QueryRequest

from agent.guardrail.rules_engine import apply_guardrails
from agent.reasoning.llm_router import llm_ask_request
from agent.reasoning.translator import translate_to_english, translate_to_romanian
from rag.retrieval.retriever import retrieve_top_similar


def _safe_translate_to_english(text: str) -> str:
    try:
        return translate_to_english(text)
    except Exception:
        return text


def _safe_translate_to_romanian(items: list[str]) -> list[str]:
    if not items:
        return []
    try:
        return translate_to_romanian(items)
    except Exception:
        return items


def answer_query(request: QueryRequest) -> tuple[str | None, GuardrailResult, list[str]]:
    guardrail_result = apply_guardrails(request.query)
    if not guardrail_result.is_valid:
        return guardrail_result.message, guardrail_result, []

    query_en = _safe_translate_to_english(request.query)
    retrieval_result = retrieve_top_similar(query_en, top_k=request.top_k)
    context_lines = retrieval_result.context_lines(with_score=True)
    context_lines_ro = _safe_translate_to_romanian(context_lines)

    response = llm_ask_request(
        request=LLMRequest(
            system_prompt=BASE_SYSTEM_PROMPT,
            user_message=request.query,
            context_block=build_context_block(context_lines_ro),
        )
    )
    return response.content, guardrail_result, context_lines_ro


def run_chat_loop(top_k: int | None = None) -> None:
    query_top_k = top_k if top_k is not None else SETTINGS.default_top_k
    while True:
        query = input("You: ").strip()
        if not query:
            continue
        if query.lower() in {"exit", "quit", ":q"}:
            print("Bye.")
            break

        request = QueryRequest(query=query, top_k=query_top_k)
        response, guardrail_result, context_used = answer_query(request)

        if not guardrail_result.is_valid:
            print(guardrail_result.message)
            continue

        print("\nContext folosit (in romana):")
        for index, item in enumerate(context_used, start=1):
            print(f"\n{index}. {item}")
        print("\n" + "=" * 80 + "\n")
        print(f"Assistant: {response}\n")
