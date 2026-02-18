# Run Plan

## Stage 1: Environment
1. Install Python deps (`pip install -e .`).
2. Install/build Certora Prover or ensure `certoraRun.py`/`certoraRun` is on `PATH`.
3. Configure one LLM backend:
   - API: set `OPENAI_API_KEY`
   - Local: run Ollama and pull model.

## Stage 2: Data
1. Fetch EVMBench subset with `scripts/fetch_evmbench.sh`.
2. Validate challenge path and command template in `configs/harness.example.yaml`.

## Stage 3: Mini validation
1. Run one challenge for 2-3 iterations.
2. Confirm artifacts under `runs/<challenge>/<timestamp>/`.
3. Verify loop adapts based on Certora feedback.

## Stage 4: Wider sweep
1. Increase challenge count and max iterations.
2. Track solve/violation/syntax-error rates.
3. Compare OpenAI vs Ollama backends.
