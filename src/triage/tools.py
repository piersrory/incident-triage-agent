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
        return f"No log lines contain '{query}'. {what_exists(env)}"
    return "\n".join(lines[-MAX_LOG_LINES:])


def what_exists(env: Environment) -> str:
    """Said after a search that matched nothing, so "my words weren't there" isn't read as "nothing is there"."""
    if not env.logs:
        return "There are no log lines at all."
    services = sorted({line.split()[1] for line in env.logs})  # a line is "time service LEVEL message"
    return f"There are {len(env.logs)} log lines, from: {', '.join(services)}."


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
    return "\n".join(env.deploy_lines())


def read_runbook(env: Environment) -> str:
    """The team's written instructions for this alert."""
    return env.runbook_text()
