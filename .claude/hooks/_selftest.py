#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""guard 的自我測試:直接呼叫 guard.evaluate(),不經 shell,避免危險字串觸發本機 hook。"""
import importlib.util
import pathlib

_p = pathlib.Path(__file__).parent / "guard-dangerous-commands.py"
_spec = importlib.util.spec_from_file_location("guard", _p)
guard = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(guard)

CASES = [
    # (command, expected_decision)
    ("git push --force", "deny"),
    ("git push -f origin main", "deny"),
    ("git push --force-with-lease", "deny"),
    ("git push origin --delete feat/x", "deny"),
    ("git push origin :main", "deny"),
    ("sudo rm file", "deny"),
    ("rm -rf /", "deny"),
    ("rm -fr ~", "deny"),
    ("rm    -rf    *", "deny"),
    ("echo hi && rm -rf /", "deny"),
    ("rm -rf build/", "ask"),
    ("rm -r node_modules", "ask"),
    ("find . -name '*.tmp' -delete", "ask"),
    ("git reset --hard HEAD~1", "ask"),
    ("git clean -fdx", "ask"),
    ("docker volume prune", "ask"),
    ("psql -c 'DROP DATABASE prod'", "ask"),
    ("mysql -e 'TRUNCATE TABLE users'", "ask"),
    ("ls -la", "allow"),
    ("git push origin main", "allow"),
    ("rm file.txt", "allow"),
]

fails = 0
for cmd, expect in CASES:
    decision, _, _ = guard.evaluate(guard.split_commands(cmd))
    got = decision or "allow"
    mark = "OK " if got == expect else "FAIL"
    if got != expect:
        fails += 1
    print(f"[{mark}] expect={expect:5s} got={got:5s} | {cmd}")

print(f"\n{'ALL PASSED' if fails == 0 else str(fails) + ' FAILED'} ({len(CASES)} cases)")
