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

## 2026-02-18 certora local prover + harness execution notes
- Fetched EVMBench corpus into `datasets/evmbench` via `scripts/fetch_evmbench.sh`.
- Installed local proving prerequisites on macmini:
  - JDK 21 (Temurin)
  - Rust toolchain (`cargo`, `rustc`) and `rustfilt`
  - Solvers `z3` and `cvc5`
  - `solc` 0.8.7 via `solc-select`
- Built `Certora/CertoraProver` from source with `./gradlew assemble`.
  - Local prover artifacts available under `/Users/hpagent/tools/certora-local`.
- Verified local prover executes without `CERTORAKEY` when `CERTORA` and PATH include `tac_optimizer`.
- Added challenge-specific harness config:
  - `configs/harness.curves-security.local.yaml`
  - Targets `datasets/evmbench/audits/2024-01-curves` + `patch/Security.sol`.
- Added OpenRouter support as a first-class provider in `llm.py`.
  - New provider value: `openrouter`
  - API key env supported: `OPENROUTER_API_KEY` (or explicit `api_key_env`).
- Fixed harness command execution behavior to pin to configured `certora.command_template`.
  - Prevents LLM command drift from bypassing local prover env wiring.

## Open issues
- Python 3.9 + LibreSSL emits `urllib3` warnings (non-fatal).
- Real OpenRouter run requires `OPENROUTER_API_KEY` on macmini.
