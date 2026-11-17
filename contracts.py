"""Plug-in contracts: the four small shapes a registry agent can implement.

A harness template declares which contract it needs (`plug_in.contract`).
The registry only offers a template when the agent implements that contract.
Adapters in adapters/ translate between a contract and a benchmark's own interface.
"""
from __future__ import annotations

import importlib
import json
import os
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass
class ToolSpec:
    name: str
    description: str
    parameters: dict[str, Any]  # JSON schema of the arguments


@dataclass
class ToolCall:
    id: str
    name: str
    arguments: dict[str, Any]


@dataclass
class Message:
    role: str  # "system" | "user" | "assistant" | "tool"
    content: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)
    tool_call_id: str | None = None


@dataclass
class AgentReply:
    content: str | None = None
    tool_calls: list[ToolCall] = field(default_factory=list)


class ChatToolAgent(Protocol):
    """Conversational agent that calls tools the HARNESS provides (tau-bench, AgentDojo)."""

    def reset(self, system_prompt: str, tools: list[ToolSpec]) -> None: ...
    def respond(self, messages: list[Message]) -> AgentReply: ...


class ObservationActionAgent(Protocol):
    """UI/computer-use agent (OSWorld, AndroidWorld, WebArena, WASP).

    `act` returns actions as strings in the benchmark's own action space.
    """

    def reset(self, instruction: str) -> None: ...
    def act(self, observation: dict[str, Any]) -> list[str]: ...


class CodeWorldAgent(Protocol):
    """Agent that writes code run inside a simulated world (AppWorld).

    `next_code` returns the next code cell, or None when finished.
    """

    def reset(self, instruction: str) -> None: ...
    def next_code(self, last_output: str | None) -> str | None: ...


class TextAgent(Protocol):
    """Single-turn text in, text out (InjecAgent model slot, promptfoo, garak, PyRIT)."""

    def respond(self, prompt: str) -> str: ...


def load_agent(entrypoint: str | None = None) -> Any:
    """Resolve 'package.module:factory' (or $REGISTRY_AGENT_ENTRYPOINT) and call the factory."""
    entrypoint = entrypoint or os.environ["REGISTRY_AGENT_ENTRYPOINT"]
    module, _, attr = entrypoint.partition(":")
    if not attr:
        raise ValueError("entrypoint must look like 'package.module:factory'")
    return getattr(importlib.import_module(module), attr)()


class HttpTextAgent:
    """TextAgent over HTTP. Wire format: POST {"prompt": str} -> {"reply": str}."""

    def __init__(self, url: str, headers: dict[str, str] | None = None, timeout: float = 120.0):
        self.url, self.headers, self.timeout = url, headers or {}, timeout

    def respond(self, prompt: str) -> str:
        req = urllib.request.Request(
            self.url,
            data=json.dumps({"prompt": prompt}).encode(),
            headers={"Content-Type": "application/json", **self.headers},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            return json.loads(resp.read())["reply"]
