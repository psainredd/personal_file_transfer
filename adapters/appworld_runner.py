"""AppWorld runner: drives a CodeWorldAgent through AppWorld tasks.

Verified (README): AppWorld(task_id=..., experiment_name=...) context manager,
world.task.instruction, world.execute(code), load_task_ids(dataset), and
`appworld evaluate <experiment> <dataset>`. The agent must finish by running
`apis.supervisor.complete_task(...)` itself. Read the README's
"Agent Development Restrictions" section before running.

  REGISTRY_AGENT_ENTRYPOINT=my_pkg.agent:make python adapters/appworld_runner.py \
      --experiment registry-v1 --dataset dev
  appworld evaluate registry-v1 dev
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from appworld import AppWorld, load_task_ids

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from contracts import load_agent  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--experiment", required=True)
    ap.add_argument("--dataset", default="dev")  # train | dev | test_normal | test_challenge
    ap.add_argument("--max-steps", type=int, default=40)
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args()

    agent = load_agent()
    for task_id in load_task_ids(args.dataset)[: args.limit]:
        with AppWorld(task_id=task_id, experiment_name=args.experiment) as world:
            agent.reset(world.task.instruction)
            output = None
            for _ in range(args.max_steps):
                code = agent.next_code(output)
                if code is None:
                    break
                output = world.execute(code)


if __name__ == "__main__":
    main()
