#!/usr/bin/env python3
"""Test polling for new loot"""

import sys
from pathlib import Path
import asyncio

sys.path.insert(0, str(Path(__file__).parent))

from src.services.config_manager import ConfigManager
from src.services.chat_reader import ChatReader
from src.core.database import DatabaseManager
from src.models.models import ActivityType

async def test_polling():
    print("=" * 60)
    print("TESTING POLLING FOR NEW LOOT")
    print("=" * 60)

    # Initialize
    db = DatabaseManager()
    await db.initialize()

    config = ConfigManager()
    await config.initialize()

    # Create chat reader
    chat_reader = ChatReader(db, config)
    chat_reader.current_activity = ActivityType.HUNTING

    # Track events
    events = []
    chat_reader.new_event.connect(lambda e: events.append(e))

    # Start monitoring
    chat_path = r"C:\Users\sutto\Documents\Entropia Universe\chat.log"
    print(f"\n1. Starting monitoring...")
    success = await chat_reader.start_monitoring(chat_path)
    print(f"   Success: {success}")
    print(f"   _polling: {chat_reader._polling}")

    # Check file size before
    file_size_before = Path(chat_path).stat().st_size
    print(f"   File size: {file_size_before}")

    # Wait for polling to detect changes
    print(f"\n2. Waiting 2 seconds for polling to detect changes...")
    await asyncio.sleep(2)

    # Check file size after
    file_size_after = Path(chat_path).stat().st_size
    print(f"   File size after: {file_size_after}")
    print(f"   Size changed: {file_size_after > file_size_before}")

    # Check if events were received
    print(f"\n3. Events received: {len(events)}")

    # Stop polling
    print(f"\n4. Stopping monitoring...")
    await chat_reader.stop_monitoring()
    print(f"   _polling: {chat_reader._polling}")

    # Show events
    if events:
        loot_events = [e for e in events if e['event_type'] == 'loot']
        print(f"\n5. Loot events: {len(loot_events)}")
        for e in loot_events[:5]:
            print(f"   - {e.get('parsed_data', {}).get('items', 'Unknown')}")

    print("\n" + "=" * 60)

    await db.close()

asyncio.run(test_polling())
