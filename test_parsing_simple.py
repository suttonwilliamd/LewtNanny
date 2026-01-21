#!/usr/bin/env python3
"""Test the loot parsing without polling"""

import sys
from pathlib import Path
import re

sys.path.insert(0, str(Path(__file__).parent))

from src.services.config_manager import ConfigManager
from src.services.chat_reader import ChatReader
from src.core.database import DatabaseManager
from src.models.models import ActivityType
import asyncio

async def test_parsing():
    print("=" * 60)
    print("TESTING LOOT PARSING")
    print("=" * 60)

    # Initialize
    db = DatabaseManager()
    await db.initialize()

    config = ConfigManager()
    await config.initialize()

    # Create chat reader
    chat_reader = ChatReader(db, config)
    chat_reader.current_activity = ActivityType.HUNTING
    chat_reader.current_session_id = "test_session"

    # Track events
    events = []
    chat_reader.new_event.connect(lambda e: events.append(e))

    # Read last 100 lines from chat.log
    chat_path = r"C:\Users\sutto\Documents\Entropia Universe\chat.log"
    print(f"\nReading from: {chat_path}")

    with open(chat_path, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()

    # Get last 100 lines
    recent_lines = lines[-100:]
    print(f"Processing last {len(recent_lines)} lines...")

    # Parse each line
    loot_count = 0
    for line in recent_lines:
        line = line.strip()
        if line:
            await chat_reader.parse_line(line)
            if any(e['event_type'] == 'loot' for e in events):
                loot_count += 1

    print(f"\nTotal events received: {len(events)}")
    print(f"Loot events: {loot_count}")

    # Show loot events
    loot_events = [e for e in events if e['event_type'] == 'loot']
    if loot_events:
        print(f"\nLoot items detected:")
        for e in loot_events[:10]:
            parsed = e.get('parsed_data', {})
            print(f"  - {parsed.get('items', 'Unknown')} = {parsed.get('value', 0)} PED")

    print("\n" + "=" * 60)

    await db.close()

asyncio.run(test_parsing())
