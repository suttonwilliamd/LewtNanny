#!/usr/bin/env python3
"""Test loot detection with the actual chat.log"""

import sys
sys.path.insert(0, '.')

from src.services.chat_reader import ChatReader
from src.core.database import DatabaseManager
from src.services.config_manager import ConfigManager
from src.models.models import ActivityType
import asyncio

async def main():
    print("=" * 60)
    print("TESTING LOOT DETECTION")
    print("=" * 60)

    db = DatabaseManager()
    await db.initialize()

    config = ConfigManager()
    await config.initialize()

    reader = ChatReader(db, config)
    reader.current_activity = ActivityType.HUNTING

    events = []
    reader.new_event.connect(lambda e: events.append(e))

    # Read from chat.log
    chat_path = r"C:\Users\sutto\Documents\Entropia Universe\chat.log"

    print(f"\n1. Starting monitoring (resets last_position to 0)")
    success = await reader.start_monitoring(chat_path)
    print(f"   Success: {success}")
    print(f"   last_position: {reader.last_position}")

    print(f"\n2. Processing file changes")
    await reader.process_file_changes(chat_path)
    print(f"   New last_position: {reader.last_position}")

    print(f"\n3. Events received: {len(events)}")

    # Count loot events
    loot_events = [e for e in events if e['event_type'] == 'loot']
    print(f"   Loot events: {len(loot_events)}")

    # Show loot events
    if loot_events:
        print("\n4. Loot items detected:")
        for i, event in enumerate(loot_events[:10], 1):  # Show first 10
            parsed = event.get('parsed_data', {})
            print(f"   {i}. {parsed.get('items', 'Unknown')} = {parsed.get('value', 0)} PED")

    # Show total value
    total_loot = sum(e.get('parsed_data', {}).get('value', 0) for e in loot_events)
    print(f"\n5. Total loot value: {total_loot:.4f} PED")

    await db.close()

    print("\n" + "=" * 60)
    if len(loot_events) > 0:
        print("SUCCESS: Loot detection is working!")
    else:
        print("FAILURE: No loot events detected!")
    print("=" * 60)

asyncio.run(main())
