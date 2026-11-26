# Incident triage agent

An agent investigates a production alert with tools and decides page, notify or dismiss.
It is measured on scripted incidents in `scenarios/`, each with a hand-written answer key.

## Commands

- `uv run pytest -q` runs the tests. They use a scripted stand-in for the model, so they are free. Run them before saying a change works.
- `uv run python -m triage.run [id ...]` calls the real model and costs money. Never run it yourself. Give Piers the command and wait for the output.
- `TRIAGE_MODEL=<model id>` in front of the run command tries another model.

## Rules

- Piers owns the answer keys. Never edit `expected:` or `trap:` in a scenario file. If a key looks wrong, say why and let Piers decide.
- Nothing from `expected`, `trap` or `title` may reach the model. `tests/test_agent.py` checks this; keep that test passing.
- When a run scores badly, check the scorer and the answer key before blaming the agent. `/read-run <id>` does this.
- Change one thing at a time (prompt, tool, or model), state the expected effect first, then compare runs. One run is not proof; say so.
- There is no prompt injection defence yet. That is deliberate: it will be measured undefended first. Don't add one unasked.
- Whatever a tool returns must be quotable. If you add tool output, add it to `Environment.text()` too, or correct quotes get marked as invented.
- Commit only when asked. No AI attribution lines in commits. `.env` and `runs/` stay out of git.

## Quality bar

This project is public, so every claim must be checkable.
- Every number in the README comes from a saved run and a command anyone can repeat.
- Each change to the agent is recorded in `docs/findings.md` as: what we saw, what we changed and why, what we predicted, what happened.

## Style

- Plain English in docstrings and commit messages: say why, not what. Commit subjects are a full sentence about the change.
- Small functions, no new dependencies without asking.
- Shell commands must have no `#` comments (zsh pastes them as errors).
