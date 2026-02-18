from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class LLMConfig:
    provider: str = "openai"
    model: str = "gpt-5-mini"
    temperature: float = 0.2
    max_output_tokens: int = 1600
    timeout_sec: int = 120
    api_key_env: str = "OPENAI_API_KEY"
    base_url: str | None = None


@dataclass
class CertoraConfig:
    spec_path: str = "specs/AutoSpec.cvl"
    command_template: str = "certoraRun certora.conf --verify Vault:{spec_path}"
    timeout_sec: int = 900
    success_markers: list[str] = field(
        default_factory=lambda: ["VERIFICATION SUCCESSFUL", "No errors found"]
    )
    failure_markers: list[str] = field(
        default_factory=lambda: ["VIOLATION", "FAILED", "ERROR", "Exception", "Syntax"]
    )


@dataclass
class HarnessConfig:
    name: str = "evmbench-certora-agent-harness"
    challenge_root: Path = Path("datasets/evmbench/audits")
    challenge_glob: str = "*"
    context_globs: list[str] = field(
        default_factory=lambda: ["**/*.sol", "**/*.md", "**/*.yaml", "**/*.yml"]
    )
    max_context_files: int = 100
    max_context_bytes: int = 180000
    max_iterations: int = 6
    output_dir: Path = Path("runs")
    objective: str = (
        "Generate Certora specs that expose true security-relevant violations. "
        "If syntax or type errors occur, repair and retry."
    )
    system_prompt_path: Path | None = Path("prompts/system_prompt.md")
    llm: LLMConfig = field(default_factory=LLMConfig)
    certora: CertoraConfig = field(default_factory=CertoraConfig)


def _as_path(value: str | Path) -> Path:
    return Path(value).expanduser()


def _resolve_relative(path: Path, base_dir: Path) -> Path:
    if path.is_absolute():
        return path
    return (base_dir / path).resolve()


def _coerce_llm(data: dict[str, Any]) -> LLMConfig:
    return LLMConfig(
        provider=str(data.get("provider", "openai")),
        model=str(data.get("model", "gpt-5-mini")),
        temperature=float(data.get("temperature", 0.2)),
        max_output_tokens=int(data.get("max_output_tokens", 1600)),
        timeout_sec=int(data.get("timeout_sec", 120)),
        api_key_env=str(data.get("api_key_env", "OPENAI_API_KEY")),
        base_url=data.get("base_url"),
    )


def _coerce_certora(data: dict[str, Any]) -> CertoraConfig:
    return CertoraConfig(
        spec_path=str(data.get("spec_path", "specs/AutoSpec.cvl")),
        command_template=str(
            data.get(
                "command_template",
                "certoraRun certora.conf --verify Vault:{spec_path}",
            )
        ),
        timeout_sec=int(data.get("timeout_sec", 900)),
        success_markers=list(
            data.get("success_markers", ["VERIFICATION SUCCESSFUL", "No errors found"])
        ),
        failure_markers=list(
            data.get(
                "failure_markers", ["VIOLATION", "FAILED", "ERROR", "Exception", "Syntax"]
            )
        ),
    )


def load_config(path: str | Path) -> HarnessConfig:
    config_path = _as_path(path).resolve()
    with config_path.open("r", encoding="utf-8") as handle:
        raw: dict[str, Any] = yaml.safe_load(handle) or {}

    base_dir = config_path.parent

    llm_cfg = _coerce_llm(dict(raw.get("llm", {})))
    certora_cfg = _coerce_certora(dict(raw.get("certora", {})))

    cfg = HarnessConfig(
        name=str(raw.get("name", "evmbench-certora-agent-harness")),
        challenge_root=_as_path(raw.get("challenge_root", "datasets/evmbench/audits")),
        challenge_glob=str(raw.get("challenge_glob", "*")),
        context_globs=list(raw.get("context_globs", ["**/*.sol", "**/*.md", "**/*.yaml", "**/*.yml"])),
        max_context_files=int(raw.get("max_context_files", 100)),
        max_context_bytes=int(raw.get("max_context_bytes", 180000)),
        max_iterations=int(raw.get("max_iterations", 6)),
        output_dir=_as_path(raw.get("output_dir", "runs")),
        objective=str(
            raw.get(
                "objective",
                "Generate Certora specs that expose true security-relevant violations. "
                "If syntax or type errors occur, repair and retry.",
            )
        ),
        system_prompt_path=_as_path(raw.get("system_prompt_path", "prompts/system_prompt.md")),
        llm=llm_cfg,
        certora=certora_cfg,
    )

    cfg.challenge_root = _resolve_relative(cfg.challenge_root, base_dir)
    cfg.output_dir = _resolve_relative(cfg.output_dir, base_dir)

    if cfg.system_prompt_path is not None:
        cfg.system_prompt_path = _resolve_relative(cfg.system_prompt_path, base_dir)

    return cfg
