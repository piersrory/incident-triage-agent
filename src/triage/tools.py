"""What the agent can do to investigate. Each tool reads one part of the scenario's simulated
environment and returns text, the way a real log search or metrics query would.

The agent is given only the alert. Everything else it has to ask for, so a run shows what it
chose to look at, and what it never checked.
"""

from triage.scenario import Environment

MAX_LOG_LINES = 20


def search_logs(env: Environment, query: str = "") -> str:
    """Log lines containing the query (any case). An empty query returns the most recent lines."""
    lines = [line for line in env.logs if query.lower() in line.lower()]
    if not lines:
        return f"No log lines contain '{query}'."
    return "\n".join(lines[-MAX_LOG_LINES:])


def list_metrics(env: Environment) -> str:
    """The names of the metrics that exist. The agent has to pick which ones to read."""
    return "\n".join(env.metrics) or "No metrics are available."


def get_metric(env: Environment, name: str) -> str:
    """What one metric's graph shows, in words."""
    if name not in env.metrics:
        return f"No metric called '{name}'. Available: {', '.join(env.metrics) or 'none'}."
    return env.metrics[name]


def list_deploys(env: Environment) -> str:
    """Recent releases and flag changes, oldest first."""
    if not env.deploys:
        return "No deploys in the last 7 days."
    return "\n".join(f"{d.at} {d.service} {d.version}: {d.change}" for d in env.deploys)


def read_runbook(env: Environment) -> str:
    """The team's written instructions for this alert."""
    return env.runbook or "There is no runbook for this alert."
