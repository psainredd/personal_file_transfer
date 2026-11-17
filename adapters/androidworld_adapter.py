"""AndroidWorld adapter: wraps an ObservationActionAgent as an EnvironmentInteractingAgent.

Verified (README): subclass EnvironmentInteractingAgent, implement step(goal) returning an
AgentInteractionResult; import in run.py and map a name in _get_agent.
UNVERIFIED (confirm in android_world/agents/base_agent.py on your pin): the helper used to
read UI state, the AgentInteractionResult constructor, and JSONAction fields.
Actions are JSON strings matching android_world/env/json_action.py.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from android_world.agents import base_agent
from android_world.env import json_action

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from contracts import load_agent  # noqa: E402


class RegistryAndroidAgent(base_agent.EnvironmentInteractingAgent):
    def __init__(self, env, name: str = "registry_agent"):
        super().__init__(env, name)
        self.inner = load_agent()
        self._goal = None

    def reset(self, go_home_on_reset: bool = False):
        super().reset(go_home_on_reset)
        self._goal = None

    def step(self, goal: str) -> base_agent.AgentInteractionResult:
        if goal != self._goal:
            self._goal = goal
            self.inner.reset(goal)
        state = self.get_post_transition_state()  # UNVERIFIED helper name
        observation = {"screenshot": state.pixels, "ui_elements": state.ui_elements}
        done = False
        for raw in self.inner.act(observation):
            action = json_action.JSONAction(**json.loads(raw))
            if action.action_type in ("status", "answer"):
                done = True
            self.env.execute_action(action)
        return base_agent.AgentInteractionResult(done, {})  # UNVERIFIED constructor
