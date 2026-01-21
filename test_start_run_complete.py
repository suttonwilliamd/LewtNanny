#!/usr/bin/env python3
"""Test Start Run flow - simulates clicking Start Run button"""

import sys
from pathlib import Path
import asyncio

sys.path.insert(0, str(Path(__file__).parent))

from src.services.config_manager import ConfigManager
from src.services.chat_reader import ChatReader
from src.core.database import DatabaseManager
from src.models.models import ActivityType

async def test_start_run_flow():
    print("=" * 60)
    print("TESTING START RUN FLOW")
    print("=" * 60)

    # Initialize
    db = DatabaseManager()
    await db.initialize()
    config = ConfigManager()
    await config.initialize()

    # Create chat reader
    chat_reader = ChatReader(db, config)

    # Track events
    events = []
    chat_reader.new_event.connect(lambda e: events.append(e))

    # Get chat path (like UI does)
    chat_path = config.get("chat_monitoring.log_file_path", "")
    print(f"\n1. Chat path: {chat_path}")
    print(f"   Path exists: {Path(chat_path).exists()}")

    # Simulate clicking "Start Run"
    print(f"\n2. Starting monitoring (clicking Start Run)...")
    chat_reader.current_activity = ActivityType.HUNTING
    success = await chat_reader.start_monitoring(chat_path)
    print(f"   Success: {success}")
    print(f"   last_position: {chat_reader.last_position}")
    print(f"   _polling: {chat_reader._polling}")

    # Process file (like the polling would)
    print(f"\n3. Processing file changes...")
    await chat_reader.process_file_changes(chat_path)
    print(f"   New last_position: {chat_reader.last_position}")

    # Show results
    print(f"\n4. Events received: {len(events)}")

    loot_events = [e for e in events if e['event_type'] == 'loot']
    print(f"   Loot events: {len(loot_events)}")

    if loot_events:
        print(f"\n5. First 10 loot items:")
        for i, e in enumerate(loot_events[:10], 1):
            parsed = e.get('parsed_data', {})
            print(f"   {i}. {parsed.get('items', 'Unknown')} = {parsed.get('value', 0)} PED")

        # Calculate total
        total = sum(e.get('parsed_data', {}).get('value', 0) for e in loot_events)
        print(f"\n6. Total loot value: {total:.4f} PED")

    # Stop
    await chat_reader.stop_monitoring()

    print("\n" + "=" * 60)

    await db.close()

asyncio.run(test_start_run_flow())
