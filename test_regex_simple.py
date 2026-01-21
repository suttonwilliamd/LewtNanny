#!/usr/bin/env python3
"""Simple test to verify loot regex works"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

LOOT_PATTERN = re.compile(r'You\s+received\s+(.+?)\s+x\s*\((\d+)\)\s+Value:\s*([\d.]+)\s+PED')

TEST_LINES = [
    "2026-01-21 14:43:19 [System] [] You received Shrapnel x (1377) Value: 0.1377 PED",
    "2026-01-21 14:35:07 [System] [] You received Animal Muscle Oil x (11) Value: 0.3300 PED",
    "2024-01-18 14:30:30 [System] [You] You received Animal Oil x (5) Value: 1.25 PED",
]

print("Testing loot regex pattern...")
print(f"Pattern: {LOOT_PATTERN.pattern}")
print()

matched = 0
for line in TEST_LINES:
    match = LOOT_PATTERN.search(line)
    if match:
        item_name, quantity, value = match.groups()
        print(f"MATCH: {line}")
        print(f"      Item: {item_name}, Qty: {quantity}, Value: {value} PED")
        matched += 1
    else:
        print(f"NO MATCH: {line}")

print()
if matched == len(TEST_LINES):
    print(f"SUCCESS: All {matched} lines matched!")
else:
    print(f"FAILURE: Only {matched}/{len(TEST_LINES)} lines matched")
