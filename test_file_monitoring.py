#!/usr/bin/env python3
"""
Test file monitoring - is the watchdog observer actually detecting changes?
"""

import asyncio
import sys
import time
import logging
import tempfile
import os
from pathlib import Path
from threading import Event

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

sys.path.insert(0, str(Path(__file__).parent))

from src.services.chat_reader import ChatReader
from src.core.database import DatabaseManager
from src.services.config_manager import ConfigManager
from src.models.models import ActivityType


async def test_file_monitoring():
    """Test if file monitoring actually detects new lines"""
    logger.info("=" * 60)
    logger.info("TESTING FILE MONITORING")
    logger.info("=" * 60)
    
    db_manager = DatabaseManager()
    await db_manager.initialize()
    
    config_manager = ConfigManager()
    await config_manager.initialize()
    
    chat_reader = ChatReader(db_manager, config_manager)
    
    events_received = []
    
    def on_event(event_data):
        events_received.append(event_data)
        logger.info(f"[EVENT] {event_data['event_type']}: {event_data.get('parsed_data', {})}")
    
    chat_reader.new_event.connect(on_event)
    
    session_id = "test_file_monitoring"
    await db_manager.create_session(session_id, ActivityType.HUNTING.value)
    chat_reader.current_session_id = session_id
    chat_reader.current_activity = ActivityType.HUNTING
    
    # Create a temp file for testing
    with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
        temp_path = f.name
        f.write("# Temp test file\n")
    
    logger.info(f"\nCreated temp file: {temp_path}")
    
    # Start monitoring
    logger.info("Starting monitoring...")
    success = await chat_reader.start_monitoring(temp_path)
    
    if not success:
        logger.error("Failed to start monitoring!")
        os.unlink(temp_path)
        await db_manager.close()
        return False
    
    logger.info("Monitoring started. Waiting 2 seconds...")
    await asyncio.sleep(2)
    
    # Write some test lines
    logger.info("\nWriting test lines to file...")
    test_lines = [
        "2026-01-21 12:53:41 [System] [] You inflicted 11.4 points of damage",
        "2026-01-21 12:53:43 [System] [] You have gained 0.2017 experience in your Aim skill",
        "2026-01-21 12:53:52 [System] [] You received Universal Ammo x (1525) Value: 0.1525 PED",
        "2026-01-21 12:53:58 [Globals] [] Team \"1\" killed a creature (Subject SH-14: Brawler) with a value of 443 PED!",
        "2026-01-21 12:54:58 [System] [] Critical hit - Armor penetration! You took 15.3 points of damage",
    ]
    
    with open(temp_path, 'a', encoding='utf-8') as f:
        for line in test_lines:
            f.write(line + "\n")
            logger.info(f"Wrote: {line[:60]}...")
    
    logger.info(f"Wrote {len(test_lines)} lines. Waiting 3 seconds for detection...")
    await asyncio.sleep(3)
    
    # Stop monitoring
    await chat_reader.stop_monitoring()
    
    # Cleanup
    os.unlink(temp_path)
    
    logger.info("\n" + "=" * 60)
    logger.info("RESULTS")
    logger.info("=" * 60)
    
    logger.info(f"Events received: {len(events_received)}")
    
    if len(events_received) == 0:
        logger.error("FAIL: No events detected!")
        logger.error("The file watcher is NOT working!")
        await db_manager.close()
        return False
    elif len(events_received) < len(test_lines):
        logger.warning(f"PARTIAL: Got {len(events_received)}/{len(test_lines)} events")
    else:
        logger.info(f"SUCCESS: Got {len(events_received)}/{len(test_lines)} events")
    
    # Show what was detected
    event_types = {}
    for event in events_received:
        etype = event['event_type']
        event_types[etype] = event_types.get(etype, 0) + 1
    
    logger.info(f"\nEvent breakdown:")
    for etype, count in sorted(event_types.items()):
        logger.info(f"  {etype}: {count}")
    
    await db_manager.close()
    return len(events_received) > 0


if __name__ == "__main__":
    result = asyncio.run(test_file_monitoring())
    sys.exit(0 if result else 1)
