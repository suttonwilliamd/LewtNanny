#!/usr/bin/env python3
"""Test the loot regex with the specific messages from the user"""

import re

LOOT_PATTERN = re.compile(r'You\s+received\s+(.+?)\s+x\s*\((\d+)\)\s+Value:\s*([\d.]+)\s+PED')

TEST_MESSAGES = [
    "2026-01-21 14:35:07 [System] [] You received Shrapnel x (566) Value: 0.0566 PED",
    "2026-01-21 14:35:07 [System] [] You received Animal Muscle Oil x (11) Value: 0.3300 PED",
    "2026-01-21 14:35:07 [System] [] You received Nova Fragment x (11) Value: 0.0001 PED",
]

print("Testing loot regex pattern...")
print(f"Pattern: {LOOT_PATTERN.pattern}")
print()

for msg in TEST_MESSAGES:
    match = LOOT_PATTERN.search(msg)
    if match:
        item_name, quantity, value = match.groups()
        print(f"MATCHED: {msg[:60]}...")
        print(f"   Item: {item_name}, Qty: {quantity}, Value: {value}")
    else:
        print(f"NO MATCH: {msg}")
print()

print("Testing against original sample_chat.log format...")
SAMPLE_LOOT = "2024-01-18 14:30:30 [System] [You] You received Animal Oil x (5) Value: 1.25 PED"
match = LOOT_PATTERN.search(SAMPLE_LOOT)
if match:
    item_name, quantity, value = match.groups()
    print(f"MATCHED: {SAMPLE_LOOT}")
    print(f"   Item: {item_name}, Qty: {quantity}, Value: {value}")
else:
    print(f"NO MATCH: {SAMPLE_LOOT}")
