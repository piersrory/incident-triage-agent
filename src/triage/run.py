"""Run the agent on scenarios and score each against the answer key. This calls the model, so it costs money.

    uv run python -m triage.run 001        one scenario
    uv run python -m triage.run            all of them

Each run is saved to runs/<scenario id>.json. Set TRIAGE_MODEL to try another model.
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic

from triage.agent import SUBMIT, Run, investigate
from triage.decision import score
from triage.scenario import load_scenarios

RUNS_DIR = Path(__file__).parents[2] / "runs"
DEFAULT_MODEL = "claude-opus-5-5"
# US dollars per million tokens (input, output), for the cost estimate only
PRICES = {
    "claude-opus-5-5": (4.00, 20.00),
    "claude-sonnet-5-5": (2.00, 10.00),
    "claude-haiku-5-5": (0.10, 0.50),
    "claude-fable-5-2": (8.00, 40.00),
}


def cost(run: Run, model: str) -> float | None:
    if model not in PRICES:
        return None
    per_input, per_output = PRICES[model]
    return (run.input_tokens * per_input + run.output_tokens * per_output) / 1_000_000


def main(ids: list[str]) -> None:
    load_dotenv()
    model = os.environ.get("TRIAGE_MODEL", DEFAULT_MODEL)
    llm = ChatAnthropic(model=model, max_tokens=8000, output_config={"effort": "medium"})
    scenarios = [s for s in load_scenarios() if not ids or s.id in ids]
    if not scenarios:
        sys.exit(f"No scenario matches {ids}.")
    RUNS_DIR.mkdir(exist_ok=True)

    print(f"model: {model}\n")
    for scenario in scenarios:
        run = investigate(scenario, llm)
        result = score(scenario, run.decision)
        (RUNS_DIR / f"{scenario.id}.json").write_text(run.model_dump_json(indent=2))

        d, expected = run.decision, scenario.expected
        print(f"{scenario.id}  {scenario.title}")
        for call in run.tool_calls:
            if call.name != SUBMIT:
                print(f"     looked at  {call.name} {call.args or ''}")
        print(f"     decided    {d.action.value}, {d.root_cause.value}, confidence {d.confidence}")
        print(f"     expected   {expected.action.value}, {expected.root_cause.value}")
        print(f"     summary    {d.summary}")
        marks = [
            "action right" if result.action_correct else "UNDER-ESCALATED" if result.under_escalated else "over-escalated",
            "cause right" if result.cause_correct else "cause wrong",
            f"key evidence cited {result.key_evidence_cited:.0%}",
            f"{len(result.quotes_not_found)} quotes not found",
        ]
        if not run.finished:
            marks.append("RAN OUT OF TURNS")
        print(f"     score      {'; '.join(marks)}")
        dollars = cost(run, model)
        spent = f"${dollars:.3f}" if dollars is not None else "cost unknown"
        print(f"     cost       {run.model_calls} model calls, {run.seconds}s, {spent}\n")


if __name__ == "__main__":
    main(sys.argv[1:])
