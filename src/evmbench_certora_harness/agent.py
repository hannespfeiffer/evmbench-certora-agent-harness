from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .certora import run_certora, summarize_feedback
from .config import HarnessConfig
from .context_builder import collect_context, render_context
from .llm import BaseLLMClient, LLMError


@dataclass
class IterationResult:
    index: int
    spec_path: str
    command: str
    certora_status: str
    certora_exit_code: int
    certora_reason: str
    elapsed_sec: float


class HarnessRunner:
    def __init__(
        self,
        config: HarnessConfig,
        llm_client: BaseLLMClient,
        dry_run: bool = False,
        max_iterations_override: int | None = None,
    ):
        self.config = config
        self.llm_client = llm_client
        self.dry_run = dry_run
        self.max_iterations = max_iterations_override or config.max_iterations

    def discover_challenges(
        self,
        specific_challenge: Path | None = None,
        limit: int | None = None,
    ) -> list[Path]:
        if specific_challenge is not None:
            candidate = self._resolve_challenge_path(specific_challenge)
            if not candidate.exists():
                return []
            return [candidate]

        matches = [
            path
            for path in sorted(self.config.challenge_root.glob(self.config.challenge_glob))
            if path.is_dir()
        ]
        if limit is not None:
            matches = matches[:limit]
        return matches

    def run(
        self,
        specific_challenge: Path | None = None,
        limit: int | None = 1,
    ) -> list[dict[str, Any]]:
        challenges = self.discover_challenges(specific_challenge=specific_challenge, limit=limit)
        results: list[dict[str, Any]] = []
        for challenge_dir in challenges:
            results.append(self._run_single(challenge_dir))
        return results

    def _resolve_challenge_path(self, path: Path) -> Path:
        expanded = path.expanduser()
        if expanded.is_absolute() and expanded.exists():
            return expanded.resolve()

        cwd_candidate = (Path.cwd() / expanded).resolve()
        if cwd_candidate.exists():
            return cwd_candidate

        rooted_candidate = (self.config.challenge_root / expanded).resolve()
        if rooted_candidate.exists():
            return rooted_candidate

        return expanded.resolve()

    def _load_system_prompt(self) -> str:
        if self.config.system_prompt_path and self.config.system_prompt_path.exists():
            return self.config.system_prompt_path.read_text(encoding="utf-8")
        return (
            "You are an expert formal-methods engineer for EVM contracts. "
            "Always return strict JSON with keys spec_path, certora_command, summary, spec."
        )

    def _build_user_prompt(
        self,
        challenge_dir: Path,
        context_text: str,
        feedback_history: list[str],
        previous_spec: str,
        iteration: int,
    ) -> str:
        feedback_text = "\n\n".join(feedback_history[-3:]) if feedback_history else "none"
        previous_spec_text = previous_spec if previous_spec else "none"

        schema = (
            "{\n"
            '  "spec_path": "specs/AutoSpec.cvl",\n'
            '  "certora_command": "certoraRun certora.conf --verify Vault:{spec_path}",\n'
            '  "summary": "short explanation",\n'
            '  "spec": "full CVL spec text"\n'
            "}"
        )

        return (
            f"Objective:\n{self.config.objective}\n\n"
            f"Challenge directory: {challenge_dir}\n"
            f"Iteration: {iteration}/{self.max_iterations}\n\n"
            "Return JSON with this exact schema:\n"
            f"{schema}\n\n"
            "Requirements:\n"
            "- Produce a valid CVL spec with explicit rules/invariants.\n"
            "- If previous feedback includes parse/type issues, prioritize fixing them.\n"
            "- Preserve exploit-relevant failing properties if they are legitimate.\n"
            "- Return JSON only (no markdown fences).\n\n"
            f"Previous spec:\n{previous_spec_text}\n\n"
            f"Recent Certora feedback:\n{feedback_text}\n\n"
            f"Context files:\n{context_text}\n"
        )

    def _run_single(self, challenge_dir: Path) -> dict[str, Any]:
        now = datetime.now(tz=timezone.utc)
        timestamp = now.strftime("%Y%m%d_%H%M%S")
        run_dir = self.config.output_dir / challenge_dir.name / timestamp
        run_dir.mkdir(parents=True, exist_ok=True)

        system_prompt = self._load_system_prompt()
        context_files = collect_context(
            challenge_dir=challenge_dir,
            globs=self.config.context_globs,
            max_files=self.config.max_context_files,
            max_total_bytes=self.config.max_context_bytes,
        )
        context_text = render_context(context_files)

        feedback_history: list[str] = []
        previous_spec = ""
        final_status = "max-iterations"
        iteration_results: list[IterationResult] = []

        for idx in range(1, self.max_iterations + 1):
            iter_dir = run_dir / f"iter_{idx:02d}"
            iter_dir.mkdir(parents=True, exist_ok=True)

            workspace_dir = iter_dir / "workspace"
            shutil.copytree(challenge_dir, workspace_dir)

            user_prompt = self._build_user_prompt(
                challenge_dir=challenge_dir,
                context_text=context_text,
                feedback_history=feedback_history,
                previous_spec=previous_spec,
                iteration=idx,
            )

            _write_json(
                iter_dir / "prompt.json",
                {
                    "system_prompt": system_prompt,
                    "user_prompt": user_prompt,
                },
            )

            try:
                llm_response = self.llm_client.complete_json(system_prompt=system_prompt, user_prompt=user_prompt)
            except LLMError as exc:
                final_status = "llm-error"
                _write_text(iter_dir / "llm_error.txt", str(exc))
                break

            _write_text(iter_dir / "llm_raw.txt", llm_response.raw_text)
            _write_json(iter_dir / "llm_parsed.json", llm_response.payload)

            spec_text = str(llm_response.payload.get("spec", "")).strip()
            if not spec_text:
                spec_text = "invariant fallback_noop() true;\n"

            spec_rel = str(llm_response.payload.get("spec_path", self.config.certora.spec_path))
            raw_cmd = str(
                llm_response.payload.get("certora_command", self.config.certora.command_template)
            )
            command = raw_cmd.format(spec_path=spec_rel)

            spec_path = workspace_dir / spec_rel
            spec_path.parent.mkdir(parents=True, exist_ok=True)
            _write_text(spec_path, spec_text)

            certora_result = run_certora(
                command=command,
                cwd=workspace_dir,
                timeout_sec=self.config.certora.timeout_sec,
                success_markers=self.config.certora.success_markers,
                failure_markers=self.config.certora.failure_markers,
                dry_run=self.dry_run,
            )

            _write_text(
                iter_dir / "certora.log",
                "--- STDOUT ---\n"
                f"{certora_result.stdout}\n\n"
                "--- STDERR ---\n"
                f"{certora_result.stderr}\n",
            )
            _write_json(
                iter_dir / "iteration_summary.json",
                {
                    "index": idx,
                    "spec_path": spec_rel,
                    "command": command,
                    "certora_status": certora_result.status,
                    "certora_exit_code": certora_result.exit_code,
                    "certora_reason": certora_result.reason,
                    "elapsed_sec": certora_result.elapsed_sec,
                },
            )

            iteration_results.append(
                IterationResult(
                    index=idx,
                    spec_path=spec_rel,
                    command=command,
                    certora_status=certora_result.status,
                    certora_exit_code=certora_result.exit_code,
                    certora_reason=certora_result.reason,
                    elapsed_sec=certora_result.elapsed_sec,
                )
            )

            if self.dry_run:
                final_status = "dry-run"
                break

            if certora_result.status == "success":
                final_status = "success"
                break

            feedback = summarize_feedback(certora_result)
            feedback_history.append(feedback)
            previous_spec = spec_text

        summary = {
            "challenge": str(challenge_dir),
            "run_dir": str(run_dir),
            "status": final_status,
            "iterations": [item.__dict__ for item in iteration_results],
            "timestamp_utc": now.isoformat(),
        }
        _write_json(run_dir / "summary.json", summary)
        return summary


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
