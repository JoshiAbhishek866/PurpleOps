"""Tests for state.tokens_used increment behavior (Bug #3 regression test)."""
import os
os.environ.setdefault("AWS_ACCESS_KEY_ID", "test")
os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "test")
os.environ.setdefault("AWS_REGION", "us-east-1")

import pytest
from src.agents.coordinator_agent import CoordinatorAgent, CampaignState


@pytest.fixture
def state():
    return CampaignState(
        campaign_id="test-camp-1",
        target="https://example.com",
        token_budget=10000,
    )


@pytest.fixture
def coordinator():
    return CoordinatorAgent()


def test_tokens_used_increments_from_dict_with_total_tokens(coordinator, state):
    """dict response with 'total_tokens' -> tokens_used += total_tokens."""
    response = {"usage_metadata": {"total_tokens": 150}}
    added = coordinator._track_tokens(state, response)
    assert added == 150
    assert state.tokens_used == 150


def test_tokens_used_increments_from_dict_input_output_tokens(coordinator, state):
    """dict response with input_tokens + output_tokens -> tokens_used += sum."""
    response = {"usage_metadata": {"input_tokens": 80, "output_tokens": 40}}
    added = coordinator._track_tokens(state, response)
    assert added == 120
    assert state.tokens_used == 120


def test_tokens_used_increments_from_bedrock_usage_shape(coordinator, state):
    """Bedrock Converse API: {'usage': {'inputTokens': N, 'outputTokens': N}}."""
    response = {"usage": {"inputTokens": 60, "outputTokens": 30}}
    added = coordinator._track_tokens(state, response)
    assert added == 90
    assert state.tokens_used == 90


def test_tokens_used_increments_from_aimessage_usage_metadata(coordinator, state):
    """LangChain AIMessage-like object with .usage_metadata attr."""
    class FakeAIMessage:
        usage_metadata = {"total_tokens": 200}
        response_metadata = {}

    response = FakeAIMessage()
    added = coordinator._track_tokens(state, response)
    assert added == 200
    assert state.tokens_used == 200


def test_tokens_used_increments_from_aimessage_response_metadata(coordinator, state):
    """LangChain AIMessage-like object with .response_metadata.token_usage."""
    class FakeAIMessage:
        usage_metadata = None
        response_metadata = {"usage": {"total_tokens": 75}}

    response = FakeAIMessage()
    added = coordinator._track_tokens(state, response)
    assert added == 75
    assert state.tokens_used == 75


def test_tokens_used_increments_from_int(coordinator, state):
    """Raw int response -> tokens_used += int."""
    added = coordinator._track_tokens(state, 42)
    assert added == 42
    assert state.tokens_used == 42


def test_tokens_used_handles_none_response(coordinator, state):
    """None response -> no increment, no exception."""
    added = coordinator._track_tokens(state, None)
    assert added == 0
    assert state.tokens_used == 0


def test_tokens_used_handles_response_without_usage(coordinator, state):
    """Response dict without usage keys -> no increment, no exception."""
    response = {"result": "some text", "intermediate_steps": []}
    added = coordinator._track_tokens(state, response)
    assert added == 0
    assert state.tokens_used == 0


def test_tokens_used_accumulates_across_multiple_calls(coordinator, state):
    """Multiple LLM calls accumulate into state.tokens_used."""
    coordinator._track_tokens(state, {"usage_metadata": {"total_tokens": 100}})
    coordinator._track_tokens(state, {"usage": {"inputTokens": 50, "outputTokens": 25}})
    coordinator._track_tokens(state, 25)
    assert state.tokens_used == 200  # 100 + 75 + 25


def test_fake_llm_full_loop(coordinator, state):
    """End-to-end: fake LLM with known usage -> state.tokens_used > 0."""
    # Simulate a Red Agent response
    fake_red_response = {
        "output": "Found 3 vulnerabilities",
        "findings": [],
        "usage_metadata": {"total_tokens": 500},
    }
    coordinator._track_tokens(state, fake_red_response)

    # Simulate a Blue Agent response (Bedrock shape)
    fake_blue_response = {
        "output": "Applied 3 remediations",
        "remediations": [],
        "usage": {"inputTokens": 200, "outputTokens": 100},
    }
    coordinator._track_tokens(state, fake_blue_response)

    assert state.tokens_used > 0
    assert state.tokens_used == 500 + 300  # 800
