#!/usr/bin/env python3
"""Test the actual UI code path"""

import sys
from pathlib import Path
import asyncio

sys.path.insert(0, str(Path(__file__).parent))

from src.services.config_manager import ConfigManager
from src.services.chat_reader import ChatReader
from src.core.database import DatabaseManager
from src.models.models import ActivityType

async def test_actual_ui_path():
    print("=" * 60)
    print("TESTING ACTUAL UI CODE PATH")
    print("=" * 60)

    # Initialize (like app does)
    db = DatabaseManager()
    await db.initialize()

    config = ConfigManager()
    await config.initialize()

    # Create chat reader (like main.py does)
    chat_reader = ChatReader(db, config)
    print(f"\n1. Chat reader created")

    # Get chat path (like ConfigTab does)
    chat_path = config.get("chat_monitoring.log_file_path", "")
    print(f"2. Chat path: {chat_path}")

    # Set activity (like UI does when starting session)
    chat_reader.current_activity = ActivityType.HUNTING

    # Track events
    events = []
    def on_event(e):
        events.append(e)
        print(f"   *** SIGNAL RECEIVED: {e['event_type']} - {e.get('parsed_data', {}).get('items', 'N/A')}")
    chat_reader.new_event.connect(on_event)

    # Start monitoring (like start_session does)
    print(f"\n3. Starting monitoring...")
    success = await chat_reader.start_monitoring(chat_path)
    print(f"   Success: {success}")
    print(f"   last_position: {chat_reader.last_position}")

    # Process any new lines (like polling does)
    print(f"\n4. Processing file changes...")
    await chat_reader.process_file_changes(chat_path)

    # Check events
    print(f"\n5. Events received: {len(events)}")

    if events:
        loot_events = [e for e in events if e['event_type'] == 'loot']
        print(f"   Loot events: {len(loot_events)}")
        for e in loot_events[:5]:
            print(f"   - {e.get('parsed_data', {}).get('items', 'Unknown')}")
    else:
        print("   NO EVENTS!")

    # Stop
    await chat_reader.stop_monitoring()

    print("\n" + "=" * 60)
    if events:
        print("SUCCESS: Chat reader emits signals correctly!")
    else:
        print("FAILURE: No events received!")
    print("=" * 60)

    await db.close()

asyncio.run(test_actual_ui_path())
