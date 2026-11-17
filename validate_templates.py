"""Validate harness template manifests.

Errors (exit 1): schema violations, missing/invalid adapter files, unknown contract targets.
Reported per template: whether it is publishable to users, and what blocks it.
A template is publishable when its smoke test is filled in, its status is not 'paper-only',
and a human has pinned the upstream version (no '<pin before use' placeholder).
"""
import json
import py_compile
import sys
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

ROOT = Path(__file__).parent
schema = json.loads((ROOT / "template.schema.json").read_text())
validator = Draft202012Validator(schema)
errors = 0
rows = []

for path in sorted((ROOT / "templates").glob("*.yaml")):
    t = yaml.safe_load(path.read_text())
    problems = [f"{'/'.join(map(str, e.absolute_path)) or '<root>'}: {e.message}" for e in validator.iter_errors(t)]
    if t.get("id") != path.stem:
        problems.append(f"id '{t.get('id')}' does not match file name '{path.stem}'")
    adapter = t.get("plug_in", {}).get("adapter")
    if adapter:
        ap = ROOT / adapter
        if not ap.exists():
            problems.append(f"adapter not found: {adapter}")
        elif ap.suffix == ".py":
            try:
                py_compile.compile(str(ap), doraise=True)
            except py_compile.PyCompileError as exc:
                problems.append(f"adapter does not compile: {exc.msg}")
        elif ap.suffix == ".json":
            try:
                json.loads(ap.read_text())
            except json.JSONDecodeError as exc:
                problems.append(f"adapter JSON invalid: {exc}")
    blockers = []
    run = t.get("run", {})
    if any("<fill in" in str(run.get(k, "")) for k in ("smoke_test", "command", "outputs")):
        blockers.append("run section incomplete")
    if t.get("verification", {}).get("status") == "paper-only":
        blockers.append("paper-only")
    if "<pin before use" in json.dumps(t.get("upstream", {}).get("pin", {})):
        blockers.append("version not pinned")
    errors += len(problems)
    rows.append((t.get("id", path.stem), t.get("verification", {}).get("status", "?"),
                 t.get("plug_in", {}).get("contract", "?"), "yes" if adapter else "-",
                 "READY" if not blockers and not problems else "blocked: " + ", ".join(blockers or ["fix errors"]), problems))

w = max(len(r[0]) for r in rows)
print(f"{'template':<{w}}  {'verification':<18} {'contract':<24} adapter  publishable")
for r in rows:
    print(f"{r[0]:<{w}}  {r[1]:<18} {r[2]:<24} {r[3]:<7}  {r[4]}")
    for p in r[5]:
        print(f"    ERROR {p}")
print(f"\n{len(rows)} templates, {errors} error(s)")
sys.exit(1 if errors else 0)
