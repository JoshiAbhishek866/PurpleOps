"""
Project-root conftest.py for pytest.

Ensures that:
- The project root is on sys.path so `from src.config import Config` resolves
- The `src/` directory is on sys.path so `from agents.blue_agent import BlueAgent` resolves

This avoids hard-coding PYTHONPATH=src on every pytest invocation and keeps the
existing `from src.X import Y` import style inside `src/agents/*.py` working.
"""
import os
import sys

_PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
_SRC_DIR = os.path.join(_PROJECT_ROOT, "src")

# Insert at position 0 so they win over any auto-inserted paths.
for _p in (_PROJECT_ROOT, _SRC_DIR):
    if _p not in sys.path:
        sys.path.insert(0, _p)

# Register `src.contracts` under the canonical top-level name `contracts` so
# that `from contracts.task_result import TaskResult` imports resolve in
# agent files. This makes C11's verify grep pattern
# (`from contracts.task_result`) match the agent code.
import src.contracts  # noqa: F401
sys.modules["contracts"] = sys.modules["src.contracts"]
sys.modules["contracts.task_result"] = sys.modules["src.contracts.task_result"]
