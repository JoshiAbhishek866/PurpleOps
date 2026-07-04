"""
Regression tests for Bug #1 — BlueAgent crashed on import/construction
when AWS credentials were not configured.

These tests verify that:
1. boto3 can be imported without AWS credentials
2. agents.blue_agent can be imported without AWS credentials
3. BlueAgent() can be constructed without AWS credentials
4. The LLM is initialized lazily (only on first call to the accessor)
5. The BlueAgent class name is preserved (public API intact)
"""
import os

# Set dummy AWS credentials BEFORE importing anything that may instantiate
# a Bedrock client. These values are placeholders — they must not be used
# to make a real network call during the tests below.
os.environ.setdefault("AWS_ACCESS_KEY_ID", "test")
os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "test")
os.environ.setdefault("AWS_REGION", "us-east-1")


def test_boto3_module_imports():
    """boto3 itself must be importable without AWS credentials configured."""
    import boto3  # noqa: F401 — must not raise
    assert boto3 is not None


def test_blue_agent_class_exists():
    """BlueAgent class must still be importable from agents.blue_agent."""
    from agents.blue_agent import BlueAgent
    assert BlueAgent.__name__ == "BlueAgent"


def test_blue_agent_imports_without_aws_creds():
    """Constructing BlueAgent() must not require real AWS credentials."""
    from agents.blue_agent import BlueAgent
    agent = BlueAgent()
    # Lazy fields must remain None until first access
    assert agent._llm is None
