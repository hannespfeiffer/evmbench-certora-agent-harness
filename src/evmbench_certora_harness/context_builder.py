from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class ContextFile:
    path: Path
    content: str


def _read_text(path: Path, max_bytes: int) -> str:
    data = path.read_bytes()[:max_bytes]
    return data.decode("utf-8", errors="ignore")


def collect_context(
    challenge_dir: Path,
    globs: list[str],
    max_files: int,
    max_total_bytes: int,
) -> list[ContextFile]:
    seen: set[Path] = set()
    files: list[Path] = []

    for pattern in globs:
        for candidate in challenge_dir.glob(pattern):
            if not candidate.is_file():
                continue
            resolved = candidate.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            files.append(candidate)

    files = sorted(files)

    out: list[ContextFile] = []
    consumed = 0

    for file_path in files:
        if len(out) >= max_files:
            break

        remaining = max_total_bytes - consumed
        if remaining <= 0:
            break

        content = _read_text(file_path, max_bytes=remaining)
        if not content.strip():
            continue

        out.append(ContextFile(path=file_path, content=content))
        consumed += len(content.encode("utf-8", errors="ignore"))

    return out


def render_context(files: list[ContextFile]) -> str:
    chunks: list[str] = []
    for item in files:
        chunks.append(f"### FILE: {item.path}\n{item.content}\n")
    return "\n".join(chunks)
