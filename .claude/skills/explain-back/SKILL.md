---
name: explain-back
description: Walk Piers through one file of this repo until every design decision in it can be explained without notes. Use when Piers asks for the walkthrough, or names a file to understand before publishing.
---

Teach one file per turn: $ARGUMENTS. If no file is given, take the next one in data-flow order:
a scenario file with `src/triage/scenario.py`, then `tools.py`, `decision.py`, `agent.py`, `run.py`, then the tests.

For the file:
1. Say what question the file answers, in one sentence.
2. Explain the three or four design decisions in it that a careful reviewer would question, each with a clickable line reference. Say why each exists, and what would go wrong without it.
3. Ask Piers three questions: two about what the code does, one about a design choice ("why not...?").
4. Stop and wait for the answers.

Then say what's right, correct what's wrong in a sentence or two, and only then offer the next file. Don't move on until the answers are right.

Use plain English. If an analogy helps, use a restaurant kitchen.
