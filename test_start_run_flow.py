#!/usr/bin/env python3
"""Test the full Start Run flow"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.services.config_manager import ConfigManager
from src.services.chat_reader import ChatReader
from src.core.database import DatabaseManager
from src.models.models import ActivityType
import asyncio

async def test_start_run():
    print("=" * 60)
    print("TESTING START RUN FLOW")
    print("=" * 60)

    # Initialize managers (like the app does)
    print("\n1. Initializing managers...")
    db = DatabaseManager()
    await db.initialize()
    print("   Database initialized")

    config = ConfigManager()
    await config.initialize()
    print("   Config manager initialized")

    # Check config (like ConfigTab does)
    chat_path = config.get("chat_monitoring.log_file_path", "")
    print(f"\n2. Chat path from config: {chat_path}")
    print(f"   Path exists: {Path(chat_path).exists()}")

    # Create chat reader (like main.py does)
    print("\n3. Creating chat reader...")
    chat_reader = ChatReader(db, config)
    print("   Chat reader created")

    # Test the regex directly
    print("\n4. Testing regex on latest loot lines...")
    import re
    loot_pattern = re.compile(r'You\s+received\s+(.+?)\s+x\s*\((\d+)\)\s+Value:\s*([\d.]+)\s+PED')

    test_lines = [
        "2026-01-21 15:00:55 [System] [] You received Animal Hide x (7) Value: 0.0700 PED",
        "2026-01-21 14:59:50 [System] [] You received Shrapnel x (927) Value: 0.0927 PED",
    ]

    for line in test_lines:
        match = loot_pattern.search(line)
        if match:
            item, qty, value = match.groups()
            print(f"   MATCH: {item} x ({qty}) = {value} PED")
        else:
            print(f"   NO MATCH: {line}")

    # Start monitoring (like Start Run does)
    print(f"\n5. Starting monitoring...")
    chat_reader.current_activity = ActivityType.HUNTING
    success = await chat_reader.start_monitoring(chat_path)
    print(f"   Success: {success}")
    print(f"   last_position: {chat_reader.last_position}")
    print(f"   _polling: {chat_reader._polling}")

    # Process file changes (read new loot)
    print(f"\n6. Processing file changes...")
    await chat_reader.process_file_changes(chat_path)
    print(f"   New last_position: {chat_reader.last_position}")

    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)

    await db.close()

asyncio.run(test_start_run())
