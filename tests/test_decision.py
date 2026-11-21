from triage.decision import Decision, score
from triage.scenario import Action, RootCause, load_scenarios

SCENARIOS = {s.id: s for s in load_scenarios()}


def decision(action: Action, cause: RootCause, evidence: list[str]) -> Decision:
    return Decision(action=action, root_cause=cause, summary="s", evidence=evidence, confidence=80)


def test_the_answer_key_itself_scores_full_marks():
    for scenario in SCENARIOS.values():
        e = scenario.expected
        result = score(scenario, decision(e.action, e.root_cause, e.key_evidence))
        assert result.action_correct and result.cause_correct
        assert result.quotes_not_found == [] and result.key_evidence_cited == 1.0


def test_dismissing_a_real_incident_is_under_escalation():
    result = score(SCENARIOS["001"], decision(Action.DISMISS, RootCause.EXPECTED, []))
    assert result.under_escalated and not result.over_escalated and not result.action_correct


def test_paging_for_expected_behaviour_is_over_escalation():
    result = score(SCENARIOS["002"], decision(Action.PAGE, RootCause.CAPACITY, []))
    assert result.over_escalated and not result.under_escalated


def test_an_invented_quote_is_caught():
    made_up = "03:12:00 checkout-api ERROR database connection refused"
    result = score(SCENARIOS["001"], decision(Action.PAGE, RootCause.BAD_DEPLOY, [made_up]))
    assert result.quotes_not_found == [made_up]
    assert result.key_evidence_cited == 0.0
