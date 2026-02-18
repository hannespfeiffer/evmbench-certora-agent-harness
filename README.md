# EVMBench Certora Agent Harness

Configurable agent harness for iterative smart-contract spec generation/refinement using:
- EVMBench-style tasks (`openai/frontier-evals` -> `project/evmbench`)
- Certora Prover (`Certora/CertoraProver`)
- LLM backend: OpenAI API, local Ollama, or mock mode

## What this does
The harness loops over a challenge:
1. Reads contract/context files.
2. Asks an LLM for Certora CVL spec text (strict JSON output).
3. Runs Certora.
4. Feeds verifier output back to the LLM.
5. Repeats until success or max iterations.

Run artifacts are persisted for every iteration.

## Project layout
- `src/evmbench_certora_harness/` core implementation
- `configs/harness.example.yaml` sample config
- `scripts/fetch_evmbench.sh` helper to pull benchmark tasks
- `examples/sample_challenge/` minimal local scaffold
- `00_..05_*.md` experiment notes (Obsidian-friendly)

## Prerequisites
- Python 3.9+
- Certora Prover installed and runnable (`certoraRun` or `certoraRun.py`)
- Solver/toolchain dependencies required by Certora (Z3/CVC5/JDK/etc.)
- One LLM backend:
  - OpenAI: `OPENAI_API_KEY`
  - Ollama: local server on `http://localhost:11434`

Certora upstream:
- https://github.com/Certora/CertoraProver

EVMBench upstream:
- https://github.com/openai/frontier-evals/tree/main/project/evmbench

## Install
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Configure
Copy and edit config:
```bash
cp configs/harness.example.yaml configs/harness.yaml
```

## Run
Single challenge:
```bash
python -m evmbench_certora_harness.cli run \
  --config configs/harness.yaml \
  --challenge datasets/evmbench/audits/2023-07-pooltogether \
  --max-iterations 4
```

First challenge from glob in config:
```bash
python -m evmbench_certora_harness.cli run --config configs/harness.yaml --limit 1
```

Dry run (no Certora execution):
```bash
python -m evmbench_certora_harness.cli run --config configs/harness.yaml --dry-run
```

## Notes
- Certora command syntax varies by project. Keep `certora.command_template` challenge-aware.
- The harness stores full logs under `runs/` for post-mortem analysis.
