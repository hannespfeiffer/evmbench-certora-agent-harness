# Local Mini Validation

## Status
- Not executed yet on this machine (requires local Certora installation and solver toolchain).

## Planned command
```bash
python -m evmbench_certora_harness.cli run \
  --config configs/harness.example.yaml \
  --challenge datasets/evmbench/audits/2023-07-pooltogether \
  --max-iterations 3
```

## Expected checks
- `runs/.../iter_XX/spec.cvl` generated.
- `certora.log` and `summary.json` generated per iteration.
- Harness terminates on success marker or iteration budget.

## 2026-02-18 additional validation
- Direct local Certora prover run on `2024-01-curves/patch/Security.sol`: PASS (prover executed locally).
- First failure cause was missing `tac_optimizer` in PATH; fixed by prepending `/Users/hpagent/tools/certora-local`.
- Harness execution with Ollama backend was started and produced iteration artifacts.
- OpenRouter provider wiring validated to credential-check stage:
  - Expected failure without key: `Missing API key in env var OPENAI_API_KEY or OPENROUTER_API_KEY`.
- Post-fix harness run (`max-iterations=2`) executes local Certora command correctly.
- Current failure mode is model-generated CVL syntax errors; infra path is functional.
