"""OSWorld adapter: wraps an ObservationActionAgent in OSWorld's agent shape.

Verified (OSWorld guide + lib_run_single.py): the runner calls agent.reset() then, per step,
`response, actions = agent.predict(instruction, obs)` and executes each action via env.step.
Place this file in OSWorld/mm_agents/ and import it in run.py or scripts/python/run_multienv.py.
UNVERIFIED: whether the pinned version passes extra kwargs to reset()/predict().
Actions are strings in OSWorld's action space (e.g. pyautogui code, or DONE / FAIL).
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from contracts import load_agent  # noqa: E402


class RegistryOSWorldAgent:
    def __init__(self, platform: str = "ubuntu", action_space: str = "pyautogui",
                 observation_type: str = "screenshot", max_trajectory_length: int = 3, **kwargs):
        self.inner = load_agent()
        self.instruction = ""

    def reset(self, *args, **kwargs):
        self.instruction = ""

    def predict(self, instruction: str, obs: dict, **kwargs):
        if instruction != self.instruction:
            self.instruction = instruction
            self.inner.reset(instruction)
        actions = self.inner.act(obs)
        return "registry agent step", actions
