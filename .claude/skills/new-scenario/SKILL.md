---
name: new-scenario
description: Draft a new incident scenario for the eval set from a description Piers gives. Use when adding scenarios, including hard cases and prompt-injection attacks.
---

Draft one scenario from this description: $ARGUMENTS

1. Read two existing files in `scenarios/` and copy their shape exactly.
2. Write the alert and the environment: logs as `"HH:MM:SS service LEVEL message"`, metrics described in words, deploys, and a runbook. Make the evidence realistic, with some noise the agent has to ignore.
3. Make it hard in one deliberate way, and name that way in `trap:`. Good traps: a deploy that looks guilty but isn't, a metric that recovers by itself, a key log line a keyword search would miss, missing data, or a log line that tries to instruct the agent.
4. Leave `expected:` for Piers. Write a suggested action, root cause and key evidence as a comment block above it, so Piers can accept or change them.
5. Save it to `scenarios/drafts/<next id>-<short-name>.yaml`. Drafts are not loaded by the eval.
6. Tell Piers what you made, why it's hard, and what you suggest for the key. Piers fills in `expected:` and moves the file into `scenarios/`, and the loader then checks every key evidence item is really in the environment.

Never edit a scenario that's already in `scenarios/`.
