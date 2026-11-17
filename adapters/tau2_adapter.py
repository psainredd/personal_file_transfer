"""tau2-bench adapter: wraps a ChatToolAgent as a tau2 HalfDuplexAgent.

Verified against the tau2-bench Agent Developer Guide: HalfDuplexAgent, constructor
(tools, domain_policy), get_init_state(), generate_next_message(message, state),
factory registered with registry.register_agent_factory(factory, "name").
UNVERIFIED (confirm on the pinned version): message/ToolCall field names and
Tool schema accessor. Run the `mock` domain smoke test first.

Register (src/tau2/registry.py in your tau2-bench checkout):
    from adapters.tau2_adapter import create_registry_agent
    registry.register_agent_factory(create_registry_agent, "registry_agent")
Run:
    REGISTRY_AGENT_ENTRYPOINT=my_pkg.agent:make tau2 run --domain mock --agent registry_agent \
        --agent-llm <m> --user-llm <m> --num-trials 1 --num-tasks 1
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

from pydantic import BaseModel
from tau2.agent.base_agent import HalfDuplexAgent
from tau2.data_model.message import AssistantMessage, Message, ToolCall as Tau2ToolCall

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from contracts import Message as CMessage, ToolCall, ToolSpec, load_agent  # noqa: E402


class RegistryAgentState(BaseModel):
    messages: list[Message] = []


class RegistryAgent(HalfDuplexAgent[RegistryAgentState]):
    def __init__(self, tools, domain_policy: str):
        super().__init__(tools=tools, domain_policy=domain_policy)
        self.inner = load_agent()
        specs = [
            ToolSpec(t.name, getattr(t, "short_desc", "") or "", getattr(t, "params", {}) or {})  # UNVERIFIED
            for t in tools
        ]
        self.inner.reset(domain_policy, specs)

    def get_init_state(self, message_history: Optional[list[Message]] = None) -> RegistryAgentState:
        return RegistryAgentState(messages=list(message_history or []))

    def generate_next_message(self, message, state: RegistryAgentState):
        state.messages.append(message)
        reply = self.inner.respond([_to_contract(m) for m in state.messages])  # UNVERIFIED conversion
        out = AssistantMessage(
            role="assistant",
            content=reply.content,
            tool_calls=[Tau2ToolCall(id=c.id, name=c.name, arguments=c.arguments) for c in reply.tool_calls] or None,
        )
        state.messages.append(out)
        return out, state


def _to_contract(m) -> CMessage:
    calls = [ToolCall(c.id, c.name, c.arguments) for c in (getattr(m, "tool_calls", None) or [])]
    return CMessage(role=m.role, content=getattr(m, "content", "") or "", tool_calls=calls,
                    tool_call_id=getattr(m, "id", None) if m.role == "tool" else None)


def create_registry_agent(tools, domain_policy, **kwargs):
    return RegistryAgent(tools=tools, domain_policy=domain_policy)
