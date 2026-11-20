# Incident triage agent

An alert fires at 3am for a mobile app or the backend behind it. Before anyone is woken, an
agent investigates: it reads the logs, the metrics and the recent releases, then decides whether to page a person, post to the team
channel, or dismiss the alert, and says why, with the evidence it found.

The hard part isn't responding. It's knowing when to wake a person, and giving them a reason
they can check in seconds.

**Status:** day 1. The scenarios and their answer key come first; the agent comes after.

## The decision it makes

| Action | When | Cost of getting it wrong |
| --- | --- | --- |
| `page` | Customers are affected now, or will be soon | Paging on noise teaches people to ignore pages |
| `notify` | Something is wrong but it can wait for working hours, or the agent isn't sure | A real incident sits in a channel overnight |
| `dismiss` | Expected behaviour, with evidence that it's expected | A real incident is closed without anyone seeing it |

The costliest mistake is dismissing or under-escalating a real incident, so recall on real
incidents comes first and false pages second. When the agent isn't sure, it never dismisses:
it notifies, and says what it couldn't establish.

## How it will be measured

Scripted incidents in [`scenarios/`](scenarios/), each with the alert, a small simulated
environment (logs, metrics, deploys, a runbook) and the correct answer, written by hand before
the agent exists. For each run:

- **Action:** did it choose page, notify or dismiss correctly? Reported as recall on real
  incidents and precision of pages, with confidence intervals.
- **Root cause:** did it name the right cause category?
- **Evidence:** does every claim quote something that is really in the environment? Checked in
  code, not by a model.
- **Cost:** tool calls, tokens and seconds per incident.

## Plan

1. Scenarios and answer key (30, covering real incidents, noise and unclear cases).
2. Tools over the simulated environment: `search_logs`, `get_metrics`, `list_deploys`,
   `read_runbook`.
3. The agent loop, with a step budget and a structured final decision.
4. The eval run and the results table.
5. Attacks: a log line that tells the agent to dismiss the alert.

## Running it

```
uv sync
uv run pytest
```
