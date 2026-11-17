"""AgentDojo adapter: wraps a ChatToolAgent as a pipeline element.

Verified: AgentDojo composes pipelines from BasePipelineElement inside AgentPipeline
(`python -m agentdojo.scripts.benchmark` is the CLI). The package says its API is still
under development.
UNVERIFIED (copy the exact signature from the pinned agentdojo.agent_pipeline.base_pipeline_element
and agentdojo.functions_runtime): query() arguments, message dict shape, how tool calls are
executed. The usual pattern is [system prompt, init query, this element, ToolsExecutionLoop].
"""
from __future__ import annotations

import sys
from pathlib import Path

from agentdojo.agent_pipeline.base_pipeline_element import BasePipelineElement

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from contracts import AgentReply, Message, ToolCall, ToolSpec, load_agent  # noqa: E402


class RegistryLLM(BasePipelineElement):
    name = "registry-agent"

    def __init__(self):
        self.inner = load_agent()

    def query(self, query, runtime, env=None, messages=(), extra_args=None):  # UNVERIFIED signature
        specs = [ToolSpec(f.name, f.description, f.parameters.model_json_schema())
                 for f in runtime.functions.values()]
        self.inner.reset("", specs)
        reply: AgentReply = self.inner.respond([_to_contract(m) for m in messages])
        out = {
            "role": "assistant",
            "content": reply.content,
            "tool_calls": [{"id": c.id, "function": c.name, "args": c.arguments} for c in reply.tool_calls] or None,
        }
        return query, runtime, env, [*messages, out], extra_args or {}


def _to_contract(m: dict) -> Message:
    content = m.get("content") or ""
    if isinstance(content, list):  # content blocks
        content = " ".join(b.get("content", "") for b in content if isinstance(b, dict))
    calls = [ToolCall(c.get("id", ""), c["function"], c.get("args", {})) for c in (m.get("tool_calls") or [])]
    return Message(role=m["role"], content=content, tool_calls=calls)
