"""The loop, tested with a scripted stand-in for the model: no API key, no cost."""

from langchain_core.messages import AIMessage

from triage.agent import MAX_MODEL_CALLS, SUBMIT, investigate
from triage.scenario import Action, RootCause, load_scenarios

BAD_DEPLOY = next(s for s in load_scenarios() if s.id == "001")
GOOD_DECISION = {
    "action": "page",
    "root_cause": "bad_deploy",
    "summary": "Checkout is failing since v2.41.0.",
    "evidence": ["v2.41.0"],
    "confidence": 90,
}


def asks(*calls: tuple[str, dict]) -> AIMessage:
    return AIMessage(
        content="",
        tool_calls=[{"name": name, "args": args, "id": f"call-{i}"} for i, (name, args) in enumerate(calls)],
    )


class Scripted:
    """Replies with a fixed list of messages, then repeats the last one. Records what it was sent."""

    def __init__(self, *replies: AIMessage):
        self.replies = list(replies)
        self.seen: list[list] = []

    def bind_tools(self, specs):
        return self

    def invoke(self, messages):
        self.seen.append(messages)
        reply = self.replies.pop(0) if len(self.replies) > 1 else self.replies[0]
        return reply.model_copy(update={"id": None})  # a real model sends a new message every turn


def test_it_investigates_then_returns_the_decision():
    model = Scripted(asks(("list_deploys", {}), ("search_logs", {"query": "error"})), asks((SUBMIT, GOOD_DECISION)))
    run = investigate(BAD_DEPLOY, model)
    assert run.finished and run.decision.action == Action.PAGE
    assert [c.name for c in run.tool_calls] == ["list_deploys", "search_logs", SUBMIT]
    assert run.model_calls == 2
    # the second request carried the tool results back to the model
    assert any("v2.41.0" in str(m.content) for m in model.seen[1])


def test_an_invalid_decision_is_sent_back_to_be_fixed():
    model = Scripted(asks((SUBMIT, GOOD_DECISION | {"action": "escalate"})), asks((SUBMIT, GOOD_DECISION)))
    run = investigate(BAD_DEPLOY, model)
    assert run.finished and run.model_calls == 2
    assert any("not valid" in str(m.content) for m in model.seen[1])


def test_running_out_of_turns_notifies_and_never_dismisses():
    model = Scripted(asks(("list_metrics", {})))
    run = investigate(BAD_DEPLOY, model)
    assert not run.finished and run.model_calls == MAX_MODEL_CALLS
    assert run.decision.action == Action.NOTIFY and run.decision.root_cause == RootCause.UNKNOWN


def test_a_reply_with_no_tool_call_gets_a_reminder():
    model = Scripted(AIMessage(content="It looks like a bad deploy."), asks((SUBMIT, GOOD_DECISION)))
    run = investigate(BAD_DEPLOY, model)
    assert run.finished
    assert SUBMIT in str(model.seen[1][-1].content)


def test_the_model_never_sees_the_answer_key():
    model = Scripted(asks((SUBMIT, GOOD_DECISION)))
    investigate(BAD_DEPLOY, model)
    sent = " ".join(str(m.content) for m in model.seen[0])
    assert BAD_DEPLOY.alert.summary in sent
    assert BAD_DEPLOY.expected.why not in sent and BAD_DEPLOY.title not in sent
