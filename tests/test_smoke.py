from pathlib import Path

from evmbench_certora_harness.config import load_config


def test_load_example_config() -> None:
    cfg = load_config(Path("configs/harness.example.yaml"))
    assert cfg.llm.provider in {"openai", "ollama"}
    assert cfg.max_iterations > 0
    assert cfg.challenge_root.name == "audits"
