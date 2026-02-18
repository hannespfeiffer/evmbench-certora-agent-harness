from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .agent import HarnessRunner
from .config import load_config
from .llm import LLMError, create_llm_client


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="EVMBench + Certora iterative harness")
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list", help="List challenges from config")
    list_parser.add_argument("--config", required=True, help="Path to harness YAML config")
    list_parser.add_argument("--limit", type=int, default=20, help="Max number of challenges")

    run_parser = subparsers.add_parser("run", help="Run harness against one or more challenges")
    run_parser.add_argument("--config", required=True, help="Path to harness YAML config")
    run_parser.add_argument(
        "--challenge",
        help=(
            "Optional challenge path. Can be absolute, relative to CWD, "
            "or relative to challenge_root in config."
        ),
    )
    run_parser.add_argument("--limit", type=int, default=1, help="Number of challenges when auto-discovering")
    run_parser.add_argument("--max-iterations", type=int, help="Override iteration budget")
    run_parser.add_argument("--dry-run", action="store_true", help="Skip Certora execution")

    return parser


def _cmd_list(config_path: Path, limit: int) -> int:
    config = load_config(config_path)

    # List mode does not require LLM initialization.
    runner = HarnessRunner(config=config, llm_client=_NoopLLMClient(), dry_run=True)
    challenges = runner.discover_challenges(limit=limit)

    if not challenges:
        print("No challenges found.")
        return 1

    for challenge in challenges:
        print(challenge)
    return 0


def _cmd_run(
    config_path: Path,
    challenge: str | None,
    limit: int,
    dry_run: bool,
    max_iterations: int | None,
) -> int:
    config = load_config(config_path)

    try:
        llm_client = create_llm_client(config.llm)
    except LLMError as exc:
        print(f"Failed to initialize LLM client: {exc}", file=sys.stderr)
        return 2

    runner = HarnessRunner(
        config=config,
        llm_client=llm_client,
        dry_run=dry_run,
        max_iterations_override=max_iterations,
    )

    specific = Path(challenge) if challenge else None
    results = runner.run(specific_challenge=specific, limit=limit)

    if not results:
        print("No matching challenges found.")
        return 1

    for item in results:
        print(json.dumps(item, indent=2))

    any_success = any(item.get("status") == "success" for item in results)
    if dry_run:
        return 0
    return 0 if any_success else 3


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    config_path = Path(args.config)

    if args.command == "list":
        return _cmd_list(config_path=config_path, limit=args.limit)

    if args.command == "run":
        return _cmd_run(
            config_path=config_path,
            challenge=args.challenge,
            limit=args.limit,
            dry_run=args.dry_run,
            max_iterations=args.max_iterations,
        )

    parser.error(f"Unknown command: {args.command}")
    return 2


class _NoopLLMClient:
    def complete_json(self, system_prompt: str, user_prompt: str):
        raise RuntimeError("Noop LLM client should not be used in list mode")


if __name__ == "__main__":
    raise SystemExit(main())
