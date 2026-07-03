"""
LangGraph Multi-Step Reasoning Agent for PurpleOps

Provides an optional upgrade from AgentExecutor to LangGraph state machines.
Enables Plan → Execute → Observe → Reflect → Adjust loops.

IMPORTANT: This is OPT-IN. Existing AgentExecutor remains the default.
Set AGENT_MODE=langgraph in .env to enable.

Fail-graceful: falls back to basic execution if langgraph is not installed.
"""

import os
import logging
from typing import Dict, List, Optional, Any, TypedDict, Annotated
from datetime import datetime

logger = logging.getLogger(__name__)


def is_langgraph_available() -> bool:
    """Check if langgraph is installed."""
    try:
        import langgraph
        return True
    except ImportError:
        return False


def is_langgraph_enabled() -> bool:
    """Check if langgraph mode is enabled via env var."""
    return os.getenv("AGENT_MODE", "default").lower() == "langgraph"


# ==================== State Definition ====================

class AgentState(TypedDict):
    """State shared across all nodes in the agent graph."""
    target: str
    plan: List[str]
    current_step: int
    observations: List[Dict]
    reflections: List[str]
    final_result: Optional[Dict]
    iteration: int
    max_iterations: int


# ==================== Graph Builder ====================

class LangGraphSecurityAgent:
    """
    Multi-step reasoning agent using LangGraph.

    Execution flow:
    1. PLAN: Analyze target and create an attack/defense plan
    2. EXECUTE: Run the current step's tool
    3. OBSERVE: Analyze the tool output
    4. REFLECT: Decide whether to adjust the plan or proceed
    5. FINALIZE: Compile all observations into a final report
    """

    def __init__(self, agent_type: str = "red", llm_provider=None):
        self.agent_type = agent_type
        self.llm = llm_provider
        self._graph = None

    def _build_graph(self):
        """Build the LangGraph state machine."""
        if not is_langgraph_available():
            logger.warning("LangGraph not installed — using basic execution")
            return None

        try:
            from langgraph.graph import StateGraph, END

            graph = StateGraph(AgentState)

            # Add nodes
            graph.add_node("plan", self._plan_node)
            graph.add_node("execute", self._execute_node)
            graph.add_node("observe", self._observe_node)
            graph.add_node("reflect", self._reflect_node)
            graph.add_node("finalize", self._finalize_node)

            # Add edges
            graph.set_entry_point("plan")
            graph.add_edge("plan", "execute")
            graph.add_edge("execute", "observe")
            graph.add_edge("observe", "reflect")
            graph.add_conditional_edges(
                "reflect",
                self._should_continue,
                {"continue": "execute", "finalize": "finalize"},
            )
            graph.add_edge("finalize", END)

            self._graph = graph.compile()
            return self._graph
        except Exception as e:
            logger.error(f"Failed to build LangGraph: {e}")
            return None

    # ==================== Node Functions ====================

    async def _plan_node(self, state: AgentState) -> AgentState:
        """Create an attack/defense plan based on the target."""
        target = state["target"]

        if self.agent_type == "red":
            plan = [
                f"Reconnaissance scan of {target}",
                f"Test SQL injection on {target} endpoints",
                f"Test XSS vulnerabilities on {target} input fields",
                f"Check authentication and authorization weaknesses",
                f"Test for privilege escalation vectors",
            ]
        else:
            plan = [
                f"Analyze threat indicators for {target}",
                f"Review and update WAF rules for {target}",
                f"Check security group configurations",
                f"Generate compliance assessment",
                f"Create mitigation recommendations",
            ]

        state["plan"] = plan
        state["current_step"] = 0
        logger.info(f"[{self.agent_type.upper()}] Plan created: {len(plan)} steps")
        return state

    async def _execute_node(self, state: AgentState) -> AgentState:
        """Execute the current step of the plan."""
        step_idx = state["current_step"]
        if step_idx >= len(state["plan"]):
            return state

        current_step = state["plan"][step_idx]
        logger.info(f"[{self.agent_type.upper()}] Executing step {step_idx + 1}: {current_step}")

        # Simulate tool execution (in production, this calls real tools)
        observation = {
            "step": step_idx + 1,
            "action": current_step,
            "result": f"Completed: {current_step}",
            "timestamp": datetime.utcnow().isoformat(),
            "status": "success",
        }

        state["observations"].append(observation)
        state["current_step"] = step_idx + 1
        return state

    async def _observe_node(self, state: AgentState) -> AgentState:
        """Analyze the latest observation."""
        if not state["observations"]:
            return state

        latest = state["observations"][-1]
        logger.info(f"[{self.agent_type.upper()}] Observing: {latest['result'][:100]}")
        return state

    async def _reflect_node(self, state: AgentState) -> AgentState:
        """Reflect on progress and decide next action."""
        completed = state["current_step"]
        total = len(state["plan"])
        state["iteration"] = state.get("iteration", 0) + 1

        reflection = f"Step {completed}/{total} complete. Iteration {state['iteration']}."

        if completed < total:
            reflection += " Proceeding to next step."
        else:
            reflection += " All steps complete — finalizing."

        state["reflections"].append(reflection)
        logger.info(f"[{self.agent_type.upper()}] Reflection: {reflection}")
        return state

    async def _finalize_node(self, state: AgentState) -> AgentState:
        """Compile all observations into a final report."""
        state["final_result"] = {
            "agent_type": self.agent_type,
            "target": state["target"],
            "steps_completed": state["current_step"],
            "total_steps": len(state["plan"]),
            "observations": state["observations"],
            "reflections": state["reflections"],
            "iterations": state["iteration"],
            "timestamp": datetime.utcnow().isoformat(),
        }
        logger.info(f"[{self.agent_type.upper()}] Finalized: {state['current_step']} steps completed")
        return state

    def _should_continue(self, state: AgentState) -> str:
        """Decide whether to continue executing or finalize."""
        if state["current_step"] >= len(state["plan"]):
            return "finalize"
        if state.get("iteration", 0) >= state.get("max_iterations", 10):
            return "finalize"
        return "continue"

    # ==================== Public API ====================

    async def run(self, target: str, max_iterations: int = 10) -> Dict:
        """
        Run the multi-step agent against a target.

        Falls back to basic execution if LangGraph is not available.
        """
        if not is_langgraph_available() or not is_langgraph_enabled():
            return self._basic_execution(target)

        graph = self._build_graph()
        if not graph:
            return self._basic_execution(target)

        initial_state: AgentState = {
            "target": target,
            "plan": [],
            "current_step": 0,
            "observations": [],
            "reflections": [],
            "final_result": None,
            "iteration": 0,
            "max_iterations": max_iterations,
        }

        try:
            final_state = await graph.ainvoke(initial_state)
            return final_state.get("final_result", {})
        except Exception as e:
            logger.error(f"LangGraph execution failed: {e}")
            return self._basic_execution(target)

    def _basic_execution(self, target: str) -> Dict:
        """Fallback: basic single-pass execution without LangGraph."""
        return {
            "agent_type": self.agent_type,
            "target": target,
            "mode": "basic (LangGraph disabled or unavailable)",
            "steps_completed": 0,
            "timestamp": datetime.utcnow().isoformat(),
        }
