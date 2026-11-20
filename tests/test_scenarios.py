import pytest
from pydantic import ValidationError

from triage.scenario import Scenario, load_scenarios


def test_every_scenario_file_loads():
    scenarios = load_scenarios()
    assert scenarios, "there should be at least one scenario"
    ids = [s.id for s in scenarios]
    assert len(ids) == len(set(ids)), "scenario ids must be unique"


def test_key_evidence_must_be_in_the_environment():
    good = load_scenarios()[0].model_dump(mode="json")
    good["expected"]["key_evidence"] = ["a line that appears nowhere"]
    with pytest.raises(ValidationError):
        Scenario.model_validate(good)


def test_a_misspelt_key_is_an_error():
    bad = load_scenarios()[0].model_dump(mode="json")
    bad["expected"]["root_cuase"] = "bad_deploy"
    with pytest.raises(ValidationError):
        Scenario.model_validate(bad)
