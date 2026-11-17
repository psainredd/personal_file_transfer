"""InjecAgent model slot: lets a registry TextAgent answer InjecAgent's ReAct prompts.

Verified (README): subclass BaseModel from src/models.py with prepare_input() and call_model(),
then add an entry to the MODELS dict, e.g. MODELS["Registry"] = RegistryModel, and run
  python3 src/evaluate_prompted_agent.py --model_type Registry --model_name registry \
      --setting base --prompt_type InjecAgent --use_cache
IMPORTANT: InjecAgent sends a ReAct-style prompt and scores the text. The agent's own scaffold
and tools are NOT exercised; this measures the model + prompt behind the agent.
Copy this class into src/models.py (or import it there).
"""
from __future__ import annotations

import sys
from pathlib import Path

from src.models import BaseModel

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from contracts import load_agent  # noqa: E402


class RegistryModel(BaseModel):
    def __init__(self, params):
        super().__init__()
        self.agent = load_agent()

    def prepare_input(self, user_prompt_filled):
        return user_prompt_filled

    def call_model(self, model_input):
        return self.agent.respond(model_input)
