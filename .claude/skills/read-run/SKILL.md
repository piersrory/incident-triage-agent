---
name: read-run
description: Diagnose a triage run that scored badly. Use after a run when key evidence is below 100%, a quote was not found, the action or cause was wrong, or the agent ran out of turns.
---

Diagnose the saved run for scenario $ARGUMENTS. Read `runs/<id>.json` and the matching file in `scenarios/`.

Work in this order, and stop at the first step that explains the miss:

1. **State the miss with numbers.** Which score lines are wrong, and by how much. No cause yet.
2. **Check the scorer.** For each quote not found, is the text something a tool really returns? Compare it with `Environment.text()` and with what `src/triage/tools.py` would return for the agent's actual tool calls.
3. **Check the answer key.** Does each missed key evidence item have to be in a correct answer, or did the agent cite equally good evidence? If the key looks too narrow or wrong, say why. Never edit `expected:` or `trap:`: Piers decides.
4. **Check the agent.** List its tool calls in order. For each missed key evidence item, say which call would have surfaced it, and why the agent didn't make it. Read what the tools returned, not only what the agent asked for. Check its unknowns for claims that something doesn't exist.

Then propose exactly one change, in this form:
"If we change X because of Y, then Z should improve, without harming W."

Do not call the model. Do not edit any file. Finish by giving Piers the command to test the change, for example `uv run python -m triage.run <id>`.
