#!/usr/bin/env python3
"""Test parse_line directly"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.services.chat_reader import ChatReader
from src.core.database import DatabaseManager
from src.services.config_manager import ConfigManager
from src.models.models import ActivityType
import asyncio

async def test_parse_line():
    print("=" * 60)
    print("TESTING parse_line METHOD")
    print("=" * 60)

    # Initialize
    db = DatabaseManager()
    await db.initialize()

    config = ConfigManager()
    await config.initialize()

    reader = ChatReader(db, config)
    reader.current_session_id = 'test_session'
    reader.current_activity = ActivityType.HUNTING

    events_received = []
    reader.new_event.connect(lambda e: events_received.append(e))

    # Test loot line
    test_line = "2026-01-21 14:43:19 [System] [] You received Shrapnel x (1377) Value: 0.1377 PED"

    print(f"\nTesting line: {test_line}")
    print(f"reader.current_session_id: {reader.current_session_id}")

    # Parse the line
    await reader.parse_line(test_line)

    print(f"\nEvents received: {len(events_received)}")

    if events_received:
        event = events_received[0]
        print(f"Event type: {event['event_type']}")
        print(f"Parsed data: {event['parsed_data']}")
        print(f"Session ID: {event['session_id']}")
    else:
        print("ERROR: No events received!")

    print("\n" + "=" * 60)
    if events_received and events_received[0]['event_type'] == 'loot':
        print("SUCCESS: Loot event was detected and emitted!")
    else:
        print("FAILURE: Loot event was NOT detected!")
    print("=" * 60)

    await db.close()

asyncio.run(test_parse_line())
