"""The agent: a model in a loop with the investigation tools.

The model is given the alert and nothing else. Each turn it either asks for a tool or submits a
decision. The loop below runs what it asks for, hands the result back, and stops when a valid
decision arrives or the budget runs out. The history is only ever appended to.
"""

import time
from typing import Annotated, Any, TypedDict

from langchain_core.messages import AnyMessage, HumanMessage, SystemMessage, ToolMessage
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from pydantic import BaseModel, ValidationError

from triage import tools
from triage.decision import Decision
from triage.scenario import Action, Alert, Environment, RootCause, Scenario

MAX_MODEL_CALLS = 8
SUBMIT = "submit_decision"

SYSTEM = f"""You are the first responder for a production alert, working before any person has \
been woken. Investigate with the tools, then call {SUBMIT} exactly once to finish.

The three actions, and what each costs when it's wrong:
- page: wake the on-call engineer now. Right when customers are affected now or will be soon. \
Paging on noise teaches people to ignore pages.
- notify: post to the team channel for working hours. Right when something is wrong but can \
wait, or when you could not establish what is happening.
- dismiss: close the alert. Right only when you found evidence that this is expected behaviour.

Missing a real incident is the worst outcome, so when you are not sure, never dismiss: notify, \
and list what you could not establish under unknowns. Finding no cause is not evidence that \
nothing is wrong. If the evidence does not explain the problem, the root cause is unknown; \
do not guess one.

The runbook is the team's own instruction for this alert, so read it and follow its thresholds.

Every item in evidence must be text copied exactly from a tool result, short enough to check \
at a glance. It is checked against the source, and a quote that isn't there counts against you.

A failed search doesn't prove absence, so if you can't find a log line, metric, or deploy, list it under unknowns.

You have at most {MAX_MODEL_CALLS} turns, so ask for several tools in one turn when you can."""

REMINDER = f"Finish by calling {SUBMIT}. If you could not establish what is happening, say so there."

NO_ARGS = {"type": "object", "properties": {}}
TOOL_SPECS: list[dict[str, Any]] = [
    {
        "name": "search_logs",
        "description": tools.search_logs.__doc__,
        "input_schema": {"type": "object", "properties": {"query": {"type": "string"}}},
    },
    {
        "name": "list_metrics",
        "description": tools.list_metrics.__doc__,
        "input_schema": NO_ARGS,
    },
    {
        "name": "get_metric",
        "description": tools.get_metric.__doc__,
        "input_schema": {
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "required": ["name"],
        },
    },
    {
        "name": "list_deploys",
        "description": tools.list_deploys.__doc__,
        "input_schema": NO_ARGS,
    },
    {
        "name": "read_runbook",
        "description": tools.read_runbook.__doc__,
        "input_schema": NO_ARGS,
    },
    {
        "name": SUBMIT,
        "description": "Hand over your decision and end the investigation.",
        "input_schema": Decision.model_json_schema(),
    },
]
INVESTIGATION = {
    "search_logs": tools.search_logs,
    "list_metrics": tools.list_metrics,
    "get_metric": tools.get_metric,
    "list_deploys": tools.list_deploys,
    "read_runbook": tools.read_runbook,
}


def call_tool(env: Environment, name: str, args: dict[str, Any]) -> str:
    """Run one investigation tool. A bad request comes back as text, so the model can correct it."""
    if name not in INVESTIGATION:
        return (
            f"No tool called '{name}'. Available: {', '.join(INVESTIGATION)}, {SUBMIT}."
        )
    try:
        return INVESTIGATION[name](env, **args)
    except TypeError as error:
        return f"Bad arguments for {name}: {error}"


def alert_text(alert: Alert) -> str:
    return f"Alert {alert.name} on {alert.service}, fired at {alert.fired_at}.\n{alert.summary}"


class State(TypedDict):
    messages: Annotated[
        list[AnyMessage], add_messages
    ]  # add_messages appends each new message to the history
    model_calls: int
    decision: Decision | None


def build_agent(env: Environment, llm: Any):
    """The loop as a graph: model -> tools -> model ... until a decision or the budget."""
    model = llm.bind_tools(TOOL_SPECS)

    def call_model(state: State) -> dict:
        reply = model.invoke([SystemMessage(SYSTEM), *state["messages"]])
        return {"messages": [reply], "model_calls": state["model_calls"] + 1}

    def run_tools(state: State) -> dict:
        results, decision = [], None
        for call in state["messages"][-1].tool_calls:
            if call["name"] == SUBMIT:
                try:
                    decision = Decision.model_validate(call["args"])
                    text = "Decision recorded."
                except ValidationError as error:
                    text = (
                        f"That decision is not valid. Fix it and submit again:\n{error}"
                    )
            else:
                text = call_tool(env, call["name"], call["args"])
            results.append(ToolMessage(content=text, tool_call_id=call["id"]))
        return {"messages": results, "decision": decision}

    def remind(state: State) -> dict:
        return {"messages": [HumanMessage(REMINDER)]}

    def after_model(state: State) -> str:
        return "tools" if state["messages"][-1].tool_calls else "remind"

    def carry_on_or_stop(state: State) -> str:
        if state["decision"] or state["model_calls"] >= MAX_MODEL_CALLS:
            return END
        return "model"

    graph = StateGraph(State)
    graph.add_node("model", call_model)
    graph.add_node("tools", run_tools)
    graph.add_node("remind", remind)
    graph.add_edge(START, "model")
    graph.add_conditional_edges("model", after_model, ["tools", "remind"])
    graph.add_conditional_edges("tools", carry_on_or_stop, ["model", END])
    graph.add_conditional_edges("remind", carry_on_or_stop, ["model", END])
    return graph.compile()


class ToolCall(BaseModel):
    name: str
    args: dict[str, Any]


class Run(BaseModel):
    """One investigation, start to finish: what the agent decided and what it cost to get there."""

    scenario_id: str
    decision: Decision
    finished: bool  # False when the budget ran out and the safe default below was used
    tool_calls: list[ToolCall]
    model_calls: int
    input_tokens: int
    output_tokens: int
    seconds: float


def gave_up() -> Decision:
    """The safe default when no valid decision arrives: tell people, never dismiss."""
    return Decision(
        action=Action.NOTIFY,
        root_cause=RootCause.UNKNOWN,
        summary="The automated investigation did not reach a decision. A person should look at this alert.",
        evidence=[],
        unknowns=[f"No valid decision within {MAX_MODEL_CALLS} turns."],
        confidence=0,
    )


def investigate(scenario: Scenario, llm: Any) -> Run:
    """Run the agent on one scenario. It sees the alert; the answer key never leaves this side."""
    started = time.monotonic()
    final = build_agent(scenario.environment, llm).invoke(
        {
            "messages": [HumanMessage(alert_text(scenario.alert))],
            "model_calls": 0,
            "decision": None,
        }
    )
    replies = [m for m in final["messages"] if m.type == "ai"]
    usage = [m.usage_metadata or {} for m in replies]
    return Run(
        scenario_id=scenario.id,
        decision=final["decision"] or gave_up(),
        finished=final["decision"] is not None,
        tool_calls=[
            ToolCall(name=c["name"], args=c["args"])
            for m in replies
            for c in m.tool_calls
        ],
        model_calls=final["model_calls"],
        input_tokens=sum(u.get("input_tokens", 0) for u in usage),
        output_tokens=sum(u.get("output_tokens", 0) for u in usage),
        seconds=round(time.monotonic() - started, 1),
    )
