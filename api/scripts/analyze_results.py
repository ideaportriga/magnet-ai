#!/usr/bin/env python3
"""Analyze JSON output from execute_prompt_templates.py"""

import json
import sys
from collections import Counter

data = json.load(sys.stdin)
statuses = Counter(r["status"] for r in data)
print(f"Total: {len(data)}")
for s, c in statuses.items():
    print(f"  {s}: {c}")
print()

errors = [r for r in data if r["status"] == "error"]
error_types = Counter(r["error_type"] for r in errors)
print("Error types:")
for et, c in sorted(error_types.items(), key=lambda x: -x[1]):
    print(f"\n  {et}: {c}")
    msgs = [r["error_message"][:200] for r in errors if r["error_type"] == et]
    msg_counter = Counter(msgs)
    for msg, mc in msg_counter.most_common(10):
        print(f"    [{mc}x] {msg}")

print("\n\nAffected templates by error type:")
for et in sorted(error_types.keys()):
    affected = [
        f"{r['system_name']}[{r['variant']}]" for r in errors if r["error_type"] == et
    ]
    print(f"\n  {et} ({len(affected)}):")
    for name in affected:
        print(f"    - {name}")
