# EVMBENCH-CERTORA Charter

- Repo: `exp07-evmbench-certora-agent-harness`
- Seed: `2602`
- Model provider: `openai|ollama` (configurable)
- Default model: `gpt-5-mini` (API) or `qwen2.5-coder:14b` (local)

## Goal
Build an agent harness that iteratively writes and refines Certora CVL specs against EVMBench-style smart contract tasks to surface exploitable violations.

## Hard constraints
- Keep all code and experiment notes under this folder.
- Use Certora Prover as the formal verification backend.
- Keep provider/model selection configurable (local or API).

## Docs
- [[05_Experiment-Design]]
- `README.md`
