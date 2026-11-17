"""promptfoo custom Python provider that calls a registry TextAgent over HTTP.

Verified: Python providers are referenced as `file://provider.py` (or `file://provider.py:fn`)
and the function takes (prompt, options, context). UNVERIFIED in this session: the exact return
shape; `{"output": ...}` is promptfoo's documented convention, so confirm on your version.

promptfooconfig.yaml:
  targets:
    - id: file://adapters/promptfoo_provider.py
      label: registry-agent
      config:
        url: https://agents.example.com/my-agent   # POST {"prompt"} -> {"reply"}
        headers: {Authorization: "Bearer {{env.AGENT_TOKEN}}"}
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from contracts import HttpTextAgent  # noqa: E402


def call_api(prompt, options, context):
    cfg = (options or {}).get("config", {})
    try:
        agent = HttpTextAgent(cfg["url"], cfg.get("headers"), float(cfg.get("timeout", 120)))
        return {"output": agent.respond(prompt)}
    except Exception as exc:  # surface as a provider error, not a crash
        return {"error": f"{type(exc).__name__}: {exc}"}
