"""Offline tests: a scripted FunctionModel plays the LLM, and a fake search replaces OpenAlex."""
import pytest
from pydantic_ai.exceptions import UnexpectedModelBehavior
from pydantic_ai.messages import ModelResponse, TextPart, ToolCallPart
from pydantic_ai.models.function import FunctionModel

from scout import agent as scout_agent
from scout import openalex
from scout.models import Paper

PAPERS = [
    Paper(id="W1", title="Good paper", authors=["Ada"], year=2023, citations=150, url="https://openalex.org/W1"),
    Paper(id="W2", title="Old paper", authors=["Bob"], year=2015, citations=900, url="https://openalex.org/W2"),
]
AFTER_2022 = {"topic": "llm agents", "year_op": "after", "year": 2022}


@pytest.fixture(autouse=True)
def fake_search(monkeypatch):
    """Replace the real API call. W2 breaks 'after 2022' on purpose, to test the validator."""
    monkeypatch.setattr(openalex, "search_papers", lambda c, client=None: PAPERS)


def search(constraints):
    return ModelResponse(parts=[ToolCallPart("search_papers", {"constraints": constraints})])


def answer(found, paper_id=None, explanation="because"):
    return ModelResponse(parts=[ToolCallPart("Pick", {"found": found, "paper_id": paper_id, "explanation": explanation})])


def scripted(*responses):
    """A fake LLM that returns the given responses in order."""
    queue = iter(responses)
    return FunctionModel(lambda messages, info: next(queue))


def test_answer_is_built_from_tool_data():
    result, deps = scout_agent.run("q", model=scripted(search(AFTER_2022), answer(True, "W1")))
    assert result.found and result.title == "Good paper"
    assert result.citations == 150  # comes from the Paper, the LLM never sent a number
    assert result.citation_source == "OpenAlex (cited_by_count)"
    assert deps.searches == 1 and deps.constraints.year == 2022


def test_invented_id_is_retried():
    result = scout_agent.ask("q", model=scripted(search(AFTER_2022), answer(True, "W999"), answer(True, "W1")))
    assert result.title == "Good paper"


def test_pick_that_breaks_constraints_is_retried():
    result = scout_agent.ask("q", model=scripted(search(AFTER_2022), answer(True, "W2"), answer(True, "W1")))
    assert result.title == "Good paper"


def test_graceful_rejection():
    result = scout_agent.ask("q", model=scripted(search(AFTER_2022), answer(False, explanation="nothing fits")))
    assert not result.found and result.citations is None
    assert result.explanation == "nothing fits"


def test_answer_without_search_is_not_accepted():
    model = scripted(answer(False), answer(False), answer(False))
    with pytest.raises(UnexpectedModelBehavior):
        scout_agent.ask("q", model=model)


def test_answer_as_plain_json_text_is_accepted():
    text = ModelResponse(parts=[TextPart('{"found": true, "paper_id": "W1", "explanation": "fits"}')])
    result = scout_agent.ask("q", model=scripted(search(AFTER_2022), text))
    assert result.title == "Good paper"


def test_text_that_is_not_json_is_retried():
    chat = ModelResponse(parts=[TextPart("I think W1 is good.")])
    result = scout_agent.ask("q", model=scripted(search(AFTER_2022), chat, answer(True, "W1")))
    assert result.title == "Good paper"