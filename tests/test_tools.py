from triage import tools
from triage.scenario import load_scenarios

BAD_DEPLOY = next(s for s in load_scenarios() if s.id == "001").environment
NO_DEPLOYS = next(s for s in load_scenarios() if s.id == "003").environment


def test_log_search_ignores_case_and_says_when_nothing_matches():
    assert "applyDiscount" in tools.search_logs(BAD_DEPLOY, "typeerror")
    assert tools.search_logs(BAD_DEPLOY, "kafka").startswith("No log lines contain 'kafka'.")


def test_a_search_that_matches_nothing_says_what_does_exist():
    """Scenario 004: the agent searched three times, matched nothing, and concluded there were no logs."""
    env = next(s for s in load_scenarios() if s.id == "004").environment
    reply = tools.search_logs(env, "trip history")
    assert f"There are {len(env.logs)} log lines" in reply and "trips-api" in reply


def test_an_unknown_metric_lists_the_real_ones():
    reply = tools.get_metric(BAD_DEPLOY, "checkout-api.errors")
    assert "No metric called" in reply and "checkout-api.5xx_rate" in reply


def test_no_deploys_is_said_plainly_not_returned_as_nothing():
    assert tools.list_deploys(NO_DEPLOYS) == "No deploys in the last 7 days."
    assert "v2.41.0" in tools.list_deploys(BAD_DEPLOY)


def test_everything_a_tool_returns_can_be_quoted():
    """A line the agent copies from a tool result must pass the quote check, in every scenario."""
    for scenario in load_scenarios():
        env = scenario.environment
        shown = [tools.search_logs(env), tools.list_deploys(env), tools.read_runbook(env)]
        shown += [tools.get_metric(env, name) for name in env.metrics]
        for line in "\n".join(shown).splitlines():
            assert line in env.text(), line  # includes "No deploys in the last 7 days."
