# EVMBENCH-CERTORA Thought Log

## 2026-02-18 implementation notes
- Confirmed EVMBench assets are available in `openai/frontier-evals` under `project/evmbench`.
- Confirmed open-source Certora prover repo: `Certora/CertoraProver`.
- Implemented a configurable Python harness with:
  - OpenAI and Ollama LLM backends.
  - Iterative spec-refinement loop.
  - Certora command execution + feedback-driven retries.
  - Run artifact logging per challenge and iteration.

## Decisions
- Keep Certora invocation command configurable in YAML per challenge corpus.
- Default to strict JSON outputs from the LLM to keep the loop deterministic.
- Store full run artifacts (`prompt`, `llm-response`, `certora.log`) for replay/debug.

## Risks / Unknowns
- Certora local build/install is heavyweight; this repo ships harness glue, not Certora binaries.
- EVMBench challenge-specific Certora configs may need per-task tuning.
- Large contracts may exceed context windows; truncation heuristics may hide critical details.

## Next actions
1. Run against one real EVMBench audit folder with a working local Certora installation.
2. Add task-specific prompt templates for exploit, findings, and patch modes.
3. Add parser improvements for Certora counterexamples and rule-level outcomes.
