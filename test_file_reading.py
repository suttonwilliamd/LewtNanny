#!/usr/bin/env python3
"""Test reading the actual chat.log file"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.services.chat_reader import ChatReader
from src.core.database import DatabaseManager
from src.services.config_manager import ConfigManager
from src.models.models import ActivityType

CHAT_LOG_PATH = r"C:\Users\sutto\Documents\Entropia Universe\chat.log"

async def test_file_reading():
    print(f"Testing file reading from: {CHAT_LOG_PATH}")
    print("-" * 60)

    # Check if file exists
    if not Path(CHAT_LOG_PATH).exists():
        print(f"ERROR: File does not exist: {CHAT_LOG_PATH}")
        return

    print(f"File exists, size: {Path(CHAT_LOG_PATH).stat().st_size} bytes")
    print()

    # Initialize managers
    db_manager = DatabaseManager()
    await db_manager.initialize()

    config_manager = ConfigManager()
    await config_manager.initialize()

    # Create chat reader
    chat_reader = ChatReader(db_manager, config_manager)

    events_received = []

    def on_event(event_data):
        events_received.append(event_data)
        print(f"RECEIVED EVENT: {event_data['event_type']} - {event_data.get('parsed_data', {})}")

    chat_reader.new_event.connect(on_event)

    # Set session
    chat_reader.current_session_id = "test_file_reading"
    chat_reader.current_activity = ActivityType.HUNTING

    # Read the file
    print("Processing file changes...")
    await chat_reader.process_file_changes(CHAT_LOG_PATH)

    print()
    print("-" * 60)
    print(f"Total events received: {len(events_received)}")

    # Count loot events
    loot_events = [e for e in events_received if e['event_type'] == 'loot']
    print(f"Loot events: {len(loot_events)}")

    if loot_events:
        print("\nLoot items detected:")
        for event in loot_events:
            parsed = event.get('parsed_data', {})
            print(f"  - {parsed.get('items', 'Unknown')} = {parsed.get('value', 0)} PED")

    await db_manager.close()

if __name__ == "__main__":
    asyncio.run(test_file_reading())
