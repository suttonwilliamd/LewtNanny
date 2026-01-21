#!/usr/bin/env python3
"""Test the UI event handling with a mock UI"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.services.chat_reader import ChatReader
from src.core.database import DatabaseManager
from src.services.config_manager import ConfigManager
from src.models.models import ActivityType, EventType
import asyncio

# Create a mock event like the chat reader would emit
LOOT_EVENT = {
    'event_type': EventType.LOOT.value,
    'activity_type': ActivityType.HUNTING.value,
    'raw_message': '2026-01-21 15:00:55 [System] [] You received Animal Hide x (7) Value: 0.0700 PED',
    'parsed_data': {
        'item_name': 'Animal Hide',
        'quantity': 7,
        'value': 0.07,
        'timestamp': '2026-01-21T15:00:55.000'
    },
    'session_id': 'test_session'
}

async def test_ui_event_handling():
    print("=" * 60)
    print("TESTING UI EVENT HANDLING")
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

    # Track if signal is emitted
    signal_received = False

    def on_signal(event_data):
        nonlocal signal_received
        signal_received = True
        print(f"\n SIGNAL RECEIVED!")
        print(f" Event type: {event_data.get('event_type')}")
        print(f" Parsed data: {event_data.get('parsed_data')}")

    # Connect signal
    chat_reader.new_event.connect(on_signal)

    # Emit a loot event by parsing a line
    test_line = "2026-01-21 15:00:55 [System] [] You received Animal Hide x (7) Value: 0.0700 PED"
    print(f"\n1. Parsing line: {test_line}")
    await chat_reader.parse_line(test_line)

    print(f"\n2. Signal received: {signal_received}")

    # Now test what the UI would do with this event
    print(f"\n3. Testing UI processing...")

    event_type = LOOT_EVENT.get('event_type')
    parsed_data = LOOT_EVENT.get('parsed_data', {})

    print(f"   Event type: {event_type}")
    print(f"   Item name: {parsed_data.get('item_name', '')}")
    print(f"   Quantity: {parsed_data.get('quantity', 0)}")
    print(f"   Value: {parsed_data.get('value', 0)}")

    # Check if the new format is correct
    item_name = parsed_data.get('item_name', '')
    quantity = parsed_data.get('quantity', 0)
    if item_name and quantity > 0:
        print(f"   New format looks correct!")
    else:
        print(f"   ERROR: Format is wrong!")

    print("\n" + "=" * 60)

    await db.close()

asyncio.run(test_ui_event_handling())
