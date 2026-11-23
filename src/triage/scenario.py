"""A scripted incident: the alert, the simulated environment the agent can investigate, and
the correct answer, written by hand before the agent exists.

Strict on purpose: a misspelt key in a scenario file is an error, not a silently ignored field.
"""

from enum import StrEnum
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, model_validator

SCENARIOS_DIR = Path(__file__).parents[2] / "scenarios"


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Action(StrEnum):
    PAGE = "page"  # wake a person now
    NOTIFY = "notify"  # post to the team channel; it can wait, or the agent isn't sure
    DISMISS = "dismiss"  # expected behaviour, with evidence that it's expected


class RootCause(StrEnum):
    BAD_DEPLOY = "bad_deploy"
    DEPENDENCY = "dependency"  # a third party or another team's service
    CAPACITY = "capacity"  # load, disk, memory, connection limits
    CONFIG = "config"  # a flag, a secret, a certificate
    LATENT_BUG = "latent_bug"  # a bug that was always there, exposed by new users or new data
    EXPECTED = "expected"  # scheduled work or known behaviour: not an incident
    UNKNOWN = "unknown"  # the environment doesn't contain enough to say


class Alert(Strict):
    name: str
    service: str
    fired_at: str  # ISO 8601, UTC
    summary: str


class Deploy(Strict):
    service: str
    version: str
    at: str  # ISO 8601, UTC
    change: str

    def line(self) -> str:
        """How a deploy reads to the agent. The quote check uses the same text, so it can be quoted."""
        return f"{self.at} {self.service} {self.version}: {self.change}"


NO_DEPLOYS = "No deploys in the last 7 days."
NO_RUNBOOK = "There is no runbook for this alert."


class Environment(Strict):
    """Everything the agent's tools can return for this scenario, and nothing else."""

    logs: list[str]
    metrics: dict[str, str]  # metric name -> what its graph shows, in words
    deploys: list[Deploy] = []
    runbook: str = ""

    def deploy_lines(self) -> list[str]:
        """What the deploy list shows. "Nothing was released" is evidence too, so it has its own line."""
        return [d.line() for d in self.deploys] or [NO_DEPLOYS]

    def runbook_text(self) -> str:
        return self.runbook or NO_RUNBOOK

    def text(self) -> str:
        """Everything in the environment as one string, for checking that a quote is really there."""
        return "\n".join([*self.logs, *self.metrics.values(), self.runbook_text(), *self.deploy_lines()])


class Expected(Strict):
    """The answer key."""

    action: Action
    root_cause: RootCause
    # Exact text from the environment that a correct answer has to rely on
    key_evidence: list[str]
    why: str  # one or two sentences, for whoever reads a disagreement later


class Scenario(Strict):
    id: str
    title: str
    trap: str = ""  # what makes it hard, if anything; never shown to the agent
    alert: Alert
    environment: Environment
    expected: Expected

    @model_validator(mode="after")
    def evidence_is_really_there(self) -> "Scenario":
        haystack = self.environment.text()
        missing = [e for e in self.expected.key_evidence if e not in haystack]
        if missing:
            raise ValueError(f"{self.id}: key evidence not found in the environment: {missing}")
        return self


def load_scenarios(directory: Path = SCENARIOS_DIR) -> list[Scenario]:
    return [
        Scenario.model_validate(yaml.safe_load(path.read_text()))
        for path in sorted(directory.glob("*.yaml"))
    ]
