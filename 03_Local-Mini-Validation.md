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
