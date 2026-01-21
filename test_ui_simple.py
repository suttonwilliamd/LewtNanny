#!/usr/bin/env python3
"""Test UI event handling"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.ui.main_window_tabbed import TabbedMainWindow
from src.core.database import DatabaseManager
from src.services.config_manager import ConfigManager
from src.services.chat_reader import ChatReader
import asyncio

async def test_ui_event():
    print("=" * 60)
    print("TESTING UI EVENT HANDLING")
    print("=" * 60)

    # Initialize managers
    db = DatabaseManager()
    await db.initialize()

    config = ConfigManager()
    await config.initialize()

    # Create chat reader
    chat_reader = ChatReader(db, config)

    # Create a mock UI (we'll just test the event handler directly)
    print("\n1. Creating event data for loot")

    event_data = {
        'event_type': 'loot',
        'activity_type': 'hunting',
        'raw_message': '2026-01-21 14:43:19 [System] [] You received Shrapnel x (1377) Value: 0.1377 PED',
        'parsed_data': {
            'item_name': 'Shrapnel',
            'quantity': 1377,
            'value': 0.1377,
            'timestamp': '2026-01-21T14:43:19.000'
        },
        'session_id': 'test_session'
    }

    print(f"   Event type: {event_data['event_type']}")
    print(f"   Item: {event_data['parsed_data']['item_name']} x ({event_data['parsed_data']['quantity']})")
    print(f"   Value: {event_data['parsed_data']['value']} PED")

    print("\n2. Testing parse_line directly")

    # Test the chat reader's parse_line method
    line = "2026-01-21 14:43:19 [System] [] You received Shrapnel x (1377) Value: 0.1377 PED"
    chat_reader.current_session_id = 'test_session'
    chat_reader.current_activity.type = 'hunting'

    result = await chat_reader.parse_line(line)

    print(f"   Parse result: {result}")

    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)

    await db.close()

if __name__ == "__main__":
    asyncio.run(test_ui_event())
