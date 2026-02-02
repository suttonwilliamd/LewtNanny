#!/usr/bin/env python3
"""Debug script - run this while the app is running"""

import sys
from pathlib import Path
import asyncio
import time

sys.path.insert(0, str(Path(__file__).parent))

from src.services.config_manager import ConfigManager
from src.services.chat_reader import ChatReader
from src.core.multi_database_manager import MultiDatabaseManager
from src.models.models import ActivityType


async def debug_monitoring():
    print("=" * 60)
    print("DEBUGGING CHAT MONITORING")
    print("=" * 60)

    # Initialize
    db = MultiDatabaseManager()
    await db.initialize_all()
    config = ConfigManager()
    await config.initialize()

    # Create chat reader
    chat_reader = ChatReader(db, config)
    chat_reader.current_activity = ActivityType.HUNTING

    # Track events
    events = []

    def on_event(e):
        events.append(e)
        print(
            f"*** SIGNAL RECEIVED: {e['event_type']} - {e.get('parsed_data', {}).get('items', 'N/A')}"
        )

    chat_reader.new_event.connect(on_event)

    # Get chat path
    chat_path = config.get("chat_monitoring.log_file_path", "")
    print(f"\nChat path: {chat_path}")
    print(f"Path exists: {Path(chat_path).exists()}")

    # Start monitoring (now synchronous)
    print(f"\nStarting monitoring...")
    success = chat_reader.start_monitoring(chat_path)
    print(f"Success: {success}")
    print(f"last_position: {chat_reader.last_position}")
    print(f"_polling: {chat_reader._polling}")

    # Get current file size
    file_size = Path(chat_path).stat().st_size
    print(f"File size: {file_size}")

    # Simulate getting loot - append a fake loot line to the chat.log
    print(f"\n--- Simulating new loot by appending to chat.log ---")
    fake_loot = "2026-01-21 15:30:00 [System] [] You received Shrapnel x (999) Value: 0.0999 PED\n"
    with open(chat_path, "a", encoding="utf-8") as f:
        f.write(fake_loot)
    print(f"Wrote fake loot line: {fake_loot.strip()}")

    # Wait for polling to detect
    print(f"\nWaiting 2 seconds for polling to detect changes...")
    await asyncio.sleep(1)

    # Check if timer is active
    print(
        f"Poll timer active: {chat_reader._poll_timer.isActive() if chat_reader._poll_timer else 'No timer'}"
    )

    await asyncio.sleep(1)

    # Check events
    print(f"\nEvents received: {len(events)}")

    if events:
        for e in events:
            print(f"  {e['event_type']}: {e.get('parsed_data', {})}")
    else:
        print("NO EVENTS RECEIVED!")

    # Check if polling task is running
    if chat_reader._poll_timer and chat_reader._poll_timer.isActive():
        print(f"\nPoll timer active: {chat_reader._poll_timer.isActive()}")

    # Stop
    chat_reader.stop_monitoring()

    print("\n" + "=" * 60)

    await db.close()


asyncio.run(debug_monitoring())
