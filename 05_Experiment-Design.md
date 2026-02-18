# Experiment Design: EVMBench + Certora Agent Harness

## Objective
Create an autonomous, configurable loop that:
1. Reads a smart contract challenge folder.
2. Prompts an LLM to produce Certora CVL specs + optional command overrides.
3. Executes Certora prover.
4. Feeds verifier output back to the LLM.
5. Iteratively refines until success or budget exhaustion.

## System components
- `config.py`: YAML schema and validation.
- `llm.py`: provider adapters (`openai`, `ollama`).
- `certora.py`: subprocess runner + heuristic result parser.
- `agent.py`: orchestration loop and artifact management.
- `cli.py`: command-line entrypoint.

## Iteration protocol
1. Build context from Solidity/config/docs files.
2. Ask model for strict JSON output containing `spec` and optional `certora_command`.
3. Write spec to workspace.
4. Run Certora command with timeout.
5. Parse outcome and append feedback.
6. Stop early on verification success marker.

## Artifacts
Each iteration stores:
- Prompt payload
- Raw LLM response
- Generated spec
- Certora stdout/stderr log
- Structured summary

## Extensibility
- Add new providers in `llm.py`.
- Add prompt profiles for exploit/finding/patch tasks.
- Add richer Certora log parsers for rule-level scoring.
