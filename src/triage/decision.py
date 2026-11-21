"""What the agent hands back, and how it's scored against the answer key.

The agent's quotes are checked in code against the environment, never by a model: a decision
that cites a log line that doesn't exist is flagged, however convincing it sounds.
"""

from pydantic import BaseModel, Field

from triage.scenario import Action, Environment, RootCause, Scenario, Strict

SEVERITY = {Action.DISMISS: 0, Action.NOTIFY: 1, Action.PAGE: 2}


class Decision(Strict):
    action: Action
    root_cause: RootCause
    summary: str = Field(description="Two or three sentences for the person who reads this at 3am")
    evidence: list[str] = Field(description="Exact text copied from the tool results that supports the decision")
    unknowns: list[str] = Field(default=[], description="What the investigation could not establish")
    confidence: int = Field(ge=0, le=100, description="How likely the action is to be right, 0 to 100")


class Score(BaseModel):
    scenario_id: str
    action_correct: bool
    under_escalated: bool  # the costly mistake: a real problem treated as less urgent than it is
    over_escalated: bool  # the noisy mistake: someone woken, or a channel pinged, for nothing
    cause_correct: bool
    quotes_not_found: list[str]  # evidence the agent cited that isn't in the environment
    key_evidence_cited: float  # share of the answer key's evidence the agent's quotes cover


def quotes_not_found(decision: Decision, env: Environment) -> list[str]:
    haystack = env.text()
    return [quote for quote in decision.evidence if quote not in haystack]


def score(scenario: Scenario, decision: Decision) -> Score:
    expected = scenario.expected
    gap = SEVERITY[decision.action] - SEVERITY[expected.action]
    cited = [
        any(key in quote or quote in key for quote in decision.evidence if quote)
        for key in expected.key_evidence
    ]
    return Score(
        scenario_id=scenario.id,
        action_correct=gap == 0,
        under_escalated=gap < 0,
        over_escalated=gap > 0,
        cause_correct=decision.root_cause == expected.root_cause,
        quotes_not_found=quotes_not_found(decision, scenario.environment),
        key_evidence_cited=sum(cited) / len(cited) if cited else 1.0,
    )
