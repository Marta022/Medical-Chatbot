from __future__ import annotations

import logging
import time
import uuid
from typing import Any

from flask import Flask, jsonify, request

from api.dependencies import ApiDependencies, default_dependencies
from config.api_config import API_SETTINGS, ApiSettings
from config.logging_config import new_correlation_id, setup_logging
from config.settings import SETTINGS
from models import QueryRequest

logger = logging.getLogger(__name__)


def _error_payload(message: str) -> dict[str, dict[str, str]]:
    return {"error": {"message": message}}


def _deps(app: Flask) -> ApiDependencies:
    return app.config["API_DEPS"]


def _api_settings(app: Flask) -> ApiSettings:
    return app.config["API_SETTINGS"]


def _model_id() -> str:
    provider = SETTINGS.llm_provider
    if provider == "openai":
        return SETTINGS.openai_model
    if provider == "ollama":
        return SETTINGS.ollama_model
    return "medical-chatbot-default"


def _extract_user_message(messages: list[dict[str, Any]]) -> str:
    for item in reversed(messages):
        if str(item.get("role", "")).lower() == "user":
            content = item.get("content", "")
            if isinstance(content, str):
                return content
    return ""


def _extract_api_key_from_request() -> str | None:
    auth_header = request.headers.get("Authorization", "")
    if auth_header.lower().startswith("bearer "):
        return auth_header[7:].strip()
    return request.headers.get("X-API-Key")


def create_app(
    dependencies: ApiDependencies | None = None,
    api_settings: ApiSettings | None = None,
) -> Flask:
    setup_logging()
    app = Flask(__name__)
    app.config["API_DEPS"] = dependencies or default_dependencies()
    app.config["API_SETTINGS"] = api_settings or API_SETTINGS

    @app.before_request
    def _correlation_context() -> None:
        # Keep API logs correlated per-request.
        new_correlation_id()

        if request.endpoint == "health":
            return

        settings = _api_settings(app)
        if not settings.api_enabled:
            raise RuntimeError("api_disabled")

        if settings.require_api_key:
            expected_key = (settings.api_key or "").strip()
            provided_key = (_extract_api_key_from_request() or "").strip()
            if not expected_key:
                raise RuntimeError("api_key_not_configured")
            if provided_key != expected_key:
                raise PermissionError("unauthorized")

    @app.errorhandler(ValueError)
    def _handle_value_error(exc: ValueError) -> tuple[Any, int]:
        logger.warning("API value error: %s", exc)
        return jsonify(_error_payload(str(exc))), 400

    @app.errorhandler(PermissionError)
    def _handle_permission_error(exc: PermissionError) -> tuple[Any, int]:
        logger.warning("API permission error: %s", exc)
        return jsonify(_error_payload(str(exc))), 401

    @app.errorhandler(RuntimeError)
    def _handle_runtime_error(exc: RuntimeError) -> tuple[Any, int]:
        logger.warning("API runtime error: %s", exc)
        return jsonify(_error_payload(str(exc))), 503

    @app.errorhandler(Exception)
    def _handle_unexpected_error(exc: Exception) -> tuple[Any, int]:
        logger.exception("Unhandled API error: %s", exc)
        return jsonify(_error_payload("internal_error")), 500

    @app.get("/health")
    def health() -> Any:
        return jsonify(
            {
                "status": "ok",
                "service": "medical-chatbot-api",
                "version": "v1-skeleton",
                "api_enabled": _api_settings(app).api_enabled,
                "auth_required": _api_settings(app).require_api_key,
            }
        )

    @app.post("/chat")
    def chat() -> Any:
        payload = request.get_json(silent=True) or {}
        settings = _api_settings(app)
        raw_query = str(payload.get("query", ""))
        if len(raw_query) > settings.max_query_chars:
            raise ValueError("query too long")
        query_request = QueryRequest(
            query=raw_query,
            top_k=int(payload.get("top_k", SETTINGS.default_top_k)),
            language=str(payload.get("language", "ro")),
            filters=payload.get("filters"),
        )
        if query_request.top_k > settings.max_top_k:
            raise ValueError(f"top_k must be <= {settings.max_top_k}")

        orchestrator = _deps(app).orchestrator_factory()
        result = orchestrator.run(query_request)
        return jsonify(_deps(app).to_json_compatible(result))

    @app.post("/ingest")
    def ingest() -> Any:
        payload = request.get_json(silent=True) or {}
        json_path = str(payload.get("json_path", SETTINGS.dataset_json_path))
        csv_path = str(payload.get("csv_path", SETTINGS.dataset_csv_path))
        chunking_strategy = str(payload.get("chunking_strategy", "section"))
        inserted = _deps(app).ingest(json_path, csv_path, chunking_strategy)
        return jsonify(
            {
                "status": "ok",
                "inserted": inserted,
                "json_path": json_path,
                "csv_path": csv_path,
                "chunking_strategy": chunking_strategy,
            }
        )

    @app.post("/eval")
    def eval_smoke() -> Any:
        result = _deps(app).run_eval()
        return jsonify(_deps(app).to_json_compatible(result))

    @app.get("/v1/models")
    def openai_models() -> Any:
        now = int(time.time())
        model_id = _model_id()
        return jsonify(
            {
                "object": "list",
                "data": [
                    {
                        "id": model_id,
                        "object": "model",
                        "created": now,
                        "owned_by": "medical-chatbot",
                    }
                ],
            }
        )

    @app.post("/v1/chat/completions")
    def openai_chat_completions() -> Any:
        payload = request.get_json(silent=True) or {}
        messages = payload.get("messages", [])
        settings = _api_settings(app)
        if not isinstance(messages, list):
            raise ValueError("messages must be a list")
        if len(messages) > settings.max_messages:
            raise ValueError(f"too many messages (max {settings.max_messages})")

        query = _extract_user_message(messages)
        if len(query) > settings.max_query_chars:
            raise ValueError("query too long")
        query_request = QueryRequest(
            query=query,
            top_k=int(payload.get("top_k", SETTINGS.default_top_k)),
            language=str(payload.get("language", "ro")),
            filters=payload.get("filters"),
        )
        if query_request.top_k > settings.max_top_k:
            raise ValueError(f"top_k must be <= {settings.max_top_k}")

        orchestrator = _deps(app).orchestrator_factory()
        result = orchestrator.run(query_request)

        completion_id = f"chatcmpl-{uuid.uuid4().hex[:24]}"
        created = int(time.time())
        model = str(payload.get("model") or result.model or _model_id())
        content = result.response or ""
        return jsonify(
            {
                "id": completion_id,
                "object": "chat.completion",
                "created": created,
                "model": model,
                "choices": [
                    {
                        "index": 0,
                        "message": {"role": "assistant", "content": content},
                        "finish_reason": "stop",
                    }
                ],
                "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            }
        )

    return app


if __name__ == "__main__":
    create_app().run(host="0.0.0.0", port=8000, debug=False)
