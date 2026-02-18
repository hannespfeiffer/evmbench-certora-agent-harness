from __future__ import annotations

import subprocess
import time
from dataclasses import dataclass
from pathlib import Path


@dataclass
class CertoraResult:
    command: str
    exit_code: int
    elapsed_sec: float
    stdout: str
    stderr: str
    status: str
    reason: str


class CertoraTimeoutError(RuntimeError):
    pass


def _contains_any(haystack: str, needles: list[str]) -> bool:
    lowered = haystack.lower()
    return any(marker.lower() in lowered for marker in needles)


def run_certora(
    command: str,
    cwd: Path,
    timeout_sec: int,
    success_markers: list[str],
    failure_markers: list[str],
    dry_run: bool = False,
) -> CertoraResult:
    start = time.time()

    if dry_run:
        elapsed = time.time() - start
        return CertoraResult(
            command=command,
            exit_code=0,
            elapsed_sec=elapsed,
            stdout="DRY RUN: certora execution skipped",
            stderr="",
            status="dry-run",
            reason="Execution skipped by --dry-run",
        )

    try:
        proc = subprocess.run(
            command,
            cwd=str(cwd),
            shell=True,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout_sec,
        )
    except subprocess.TimeoutExpired as exc:
        elapsed = time.time() - start
        stdout = exc.stdout or ""
        stderr = exc.stderr or ""
        return CertoraResult(
            command=command,
            exit_code=124,
            elapsed_sec=elapsed,
            stdout=stdout,
            stderr=stderr,
            status="timeout",
            reason=f"Timeout after {timeout_sec}s",
        )

    elapsed = time.time() - start
    combined = f"{proc.stdout}\n{proc.stderr}"

    if proc.returncode == 0 and _contains_any(combined, success_markers):
        status = "success"
        reason = "Found success marker"
    elif proc.returncode == 0 and not _contains_any(combined, failure_markers):
        status = "success"
        reason = "Zero exit code and no failure marker"
    else:
        status = "failure"
        reason = "Non-zero exit code or failure marker"

    return CertoraResult(
        command=command,
        exit_code=proc.returncode,
        elapsed_sec=elapsed,
        stdout=proc.stdout,
        stderr=proc.stderr,
        status=status,
        reason=reason,
    )


def summarize_feedback(result: CertoraResult, max_chars: int = 10000) -> str:
    combined = (
        f"status={result.status}; reason={result.reason}; exit_code={result.exit_code}; "
        f"elapsed={result.elapsed_sec:.2f}s\n"
        "--- STDOUT ---\n"
        f"{result.stdout}\n"
        "--- STDERR ---\n"
        f"{result.stderr}"
    )
    if len(combined) <= max_chars:
        return combined
    return combined[-max_chars:]
