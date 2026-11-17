# Harness templates

Templates that let registry users run external eval harnesses against their own agents.
Each template is a manifest (`templates/<id>.yaml`) plus, where the harness takes code,
an adapter (`adapters/`). Users implement a **contract** once; every template that needs
that contract then works for their agent.

## Contracts (what an agent implements)

| Contract | Shape | Used by |
|---|---|---|
| `chat_tools` | `reset(system_prompt, tools)`, `respond(messages) -> reply with tool calls` | tau2-bench, AgentDojo |
| `observation_action` | `reset(instruction)`, `act(observation) -> [action strings]` | OSWorld, AndroidWorld, WebArena, WASP |
| `code_world` | `reset(instruction)`, `next_code(last_output) -> code or None` | AppWorld |
| `model_text` / `text_endpoint` | text in, text out (HTTP: `POST {"prompt"} -> {"reply"}`) | InjecAgent, promptfoo, garak, PyRIT |
| `sdk_redirect` | agent uses an OpenAI/Anthropic/Google SDK whose base URL or model name can be redirected | Inspect bridge |
| `mcp_config` | the agent's MCP config files | mcp-scan |
| `inherits_host_benchmark` | whatever the host benchmark needs | DoomArena |

Definitions are in `contracts.py`. Point an adapter at your agent with
`REGISTRY_AGENT_ENTRYPOINT=package.module:factory`.

## Status of the 14 templates

Run `python validate_templates.py` for the live table. **None is publishable yet**: each still
needs a pinned upstream version, and DoomArena, WASP and PyRIT also need a smoke test written.

- `docs-verified` (official docs read): inspect-bridge, tau2-bench
- `partially-verified` (README/doc snippets read): webarena, osworld, appworld, androidworld, agentdojo, injecagent, pyrit, garak, mcp-scan, promptfoo
- `paper-only`: doomarena, wasp

Each manifest lists what was verified and what was not, under `verification`.

## What was actually run

- `tests/smoke_inspect_bridge.py`: the Inspect bridge adapter end to end with a stand-in agent on `mockllm` (the model call is captured and scored). The tokenizer download is stubbed because the build environment had no network.
- `tests/smoke_adapters.py`: the HTTP text agent through the promptfoo provider (success and error paths), the OSWorld adapter's shape, and the AppWorld runner loop against a **fake** `appworld` module.
- `validate_templates.py`: schema validation, adapter existence and compilation.

**Not run:** every upstream harness itself (tau2, OSWorld, AndroidWorld, AppWorld, AgentDojo, InjecAgent, garak, promptfoo, PyRIT, mcp-scan, WebArena, WASP, DoomArena), since none could be installed and executed in the build environment. The adapters for tau2, AndroidWorld, AgentDojo and InjecAgent compile but have not been executed against the real package, and lines marked `UNVERIFIED` in them need checking against the pinned version.

## Before publishing a template to users

1. Pin the upstream version in the manifest (`upstream.pin.value`).
2. Install the harness and run `run.smoke_test` for real. Fix anything marked `UNVERIFIED`.
3. Check the license (`license_verified: false` means nobody has confirmed it).
4. Record cost and runtime from a real run in `caveats`.
5. Re-run `python validate_templates.py`.

## Adding a template

Copy a manifest, fill the fields required by `template.schema.json`, add an adapter if the harness takes code, then validate. Prefer `docs-verified` only when you have read the harness's own documentation for the plug-in point.

## What each harness actually grades

Most of these grade the **model, prompt and scaffold** inside the harness's own environment, not your agent's real tools or deployment. Each manifest says so under `plug_in.exercises` and `plug_in.not_exercised`. Show that to users next to every result.
