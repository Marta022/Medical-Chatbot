from __future__ import annotations

import argparse
import json

from config.settings import SETTINGS, ensure_startup_valid
from models.serde import serialize_to_json_compatible

from agent.evaluation.benchmark import run_evaluation_smoke
from agent.orchestrator.chat_loop import run_chat_loop
from knowledge.qdrant.ingest import ingest


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Medical chatbot CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    chat_parser = subparsers.add_parser("chat", help="Run interactive chat loop")
    chat_parser.add_argument("--top-k", type=int, default=SETTINGS.default_top_k, help="Retrieval top_k")

    ingest_parser = subparsers.add_parser("ingest", help="Ingest datasets into Qdrant")
    ingest_parser.add_argument(
        "--json-path",
        default=SETTINGS.dataset_json_path,
        help="Path to JSON medical dataset",
    )
    ingest_parser.add_argument(
        "--csv-path",
        default=SETTINGS.dataset_csv_path,
        help="Path to CSV medical dataset",
    )

    subparsers.add_parser("eval", help="Run evaluation smoke check")
    return parser


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    ensure_startup_valid(command=args.command)

    if args.command == "chat":
        run_chat_loop(top_k=args.top_k)
        return

    if args.command == "ingest":
        inserted = ingest(args.json_path, args.csv_path)
        print(f"Inserted into Qdrant: {inserted}")
        return

    if args.command == "eval":
        result = run_evaluation_smoke()
        payload = serialize_to_json_compatible(result)
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return

    parser.error(f"Unknown command: {args.command}")


if __name__ == "__main__":
    main()

