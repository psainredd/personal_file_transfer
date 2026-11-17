"""Inspect AI task that runs a registry agent through the Agent Bridge.

Mode "process": the agent is a Python coroutine `async def run(prompt: str) -> str` that
calls its own OpenAI SDK client with model="inspect" (the bridge redirects it).
Mode "sandbox": the agent is a command run inside the sample sandbox; its OpenAI base
URL is pointed at the bridge proxy.

Run:
  inspect eval adapters/inspect_bridge.py -T dataset_path=samples.jsonl \
      -T entrypoint=my_pkg.agent:run --model <provider/model>
"""
from __future__ import annotations

import importlib

from inspect_ai import Task, task
from inspect_ai.agent import Agent, AgentState, agent, agent_bridge, sandbox_agent_bridge
from inspect_ai.dataset import json_dataset
from inspect_ai.model import user_prompt
from inspect_ai.scorer import includes, model_graded_qa
from inspect_ai.util import sandbox


def _load(entrypoint: str):
    module, _, attr = entrypoint.partition(":")
    return getattr(importlib.import_module(module), attr)


@agent
def process_bridged(entrypoint: str, forward_generation_config: bool = False) -> Agent:
    run = _load(entrypoint)

    async def execute(state: AgentState) -> AgentState:
        async with agent_bridge(state, forward_generation_config=forward_generation_config) as bridge:
            await run(user_prompt(state.messages).text)
            return bridge.state

    return execute


@agent
def sandbox_bridged(cmd: list[str]) -> Agent:
    async def execute(state: AgentState) -> AgentState:
        async with sandbox_agent_bridge(state) as bridge:
            prompt = user_prompt(state.messages).text
            result = await sandbox().exec(
                cmd=[*cmd, prompt],
                env={"OPENAI_BASE_URL": f"http://localhost:{bridge.port}/v1"},
            )
            if not result.success:
                raise RuntimeError(f"agent failed: {result.stderr}")
            return bridge.state

    return execute


@task
def bridge_eval(
    dataset_path: str,
    mode: str = "process",  # "process" | "sandbox"
    entrypoint: str | None = None,  # mode=process: "pkg.module:run"
    cmd: str | None = None,  # mode=sandbox: agent command, e.g. "/opt/my_agent --prompt"
    scorer: str = "includes",  # "includes" | "model_graded_qa"
    sandbox_type: str | None = None,  # mode=sandbox usually "docker"
):
    if mode == "process":
        solver = process_bridged(entrypoint)
    elif mode == "sandbox":
        solver, sandbox_type = sandbox_bridged(cmd.split()), sandbox_type or "docker"
    else:
        raise ValueError(f"unknown mode: {mode}")
    return Task(
        dataset=json_dataset(dataset_path),
        solver=solver,
        scorer=includes() if scorer == "includes" else model_graded_qa(),
        sandbox=sandbox_type,
        message_limit=50,
    )
