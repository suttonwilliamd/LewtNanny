#!/usr/bin/env python3
"""
Comprehensive test script for LewtNanny data flow
Tests chat parsing, event emission, and signal connections
"""

import asyncio
import sys
import logging
from pathlib import Path

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

sys.path.insert(0, str(Path(__file__).parent))

from src.services.chat_reader import ChatReader
from src.core.database import DatabaseManager
from src.services.config_manager import ConfigManager
from src.models.models import ActivityType

class MockOverlay:
    """Mock overlay to capture events"""
    def __init__(self):
        self.events_received = []
        
    def add_event(self, event_data):
        logger.info(f"[MOCK_OVERLAY] Received event: {event_data.get('event_type', 'unknown')}")
        self.events_received.append(event_data)

async def test_chat_parsing_flow():
    """Test the complete chat parsing flow"""
    logger.info("=" * 60)
    logger.info("TESTING CHAT PARSING DATA FLOW")
    logger.info("=" * 60)
    
    # Initialize services
    db_manager = DatabaseManager()
    await db_manager.initialize()
    logger.info("[TEST] Database initialized")
    
    config_manager = ConfigManager()
    await config_manager.initialize()
    logger.info("[TEST] Config manager initialized")
    
    # Create chat reader
    chat_reader = ChatReader(db_manager, config_manager)
    logger.info("[TEST] ChatReader created")
    
    # Create mock overlay
    mock_overlay = MockOverlay()
    
    # Connect signal manually to test
    def on_new_event(event_data):
        logger.info(f"[TEST] >>> SIGNAL RECEIVED: {event_data.get('event_type', 'unknown')} <<<")
        mock_overlay.add_event(event_data)
    
    chat_reader.new_event.connect(on_new_event)
    logger.info("[TEST] Signal connected to mock overlay")
    
    # Create a test session
    session_id = f"test_session_{Path(__file__).stem}"
    await db_manager.create_session(session_id, ActivityType.HUNTING.value)
    chat_reader.current_session_id = session_id
    chat_reader.current_activity = ActivityType.HUNTING
    logger.info(f"[TEST] Created session: {session_id}")
    
    # Test lines from sample_chat.log
    test_lines = [
        "2024-01-18 14:30:15 [System] [You] You inflicted 25.5 points of damage",
        "2024-01-18 14:30:18 [System] [You] Critical hit - Additional damage! You inflicted 45.0 points of damage",
        "2024-01-18 14:30:22 [System] [You] You missed",
        "2024-01-18 14:30:25 [System] [You] You have gained 0.5 experience in your Rifle skill",
        "2024-01-18 14:30:30 [System] [You] You received Animal Oil x (5) Value: 1.25 PED",
        "2024-01-18 14:30:35 [System] [You] You received Shrapnel x (1000) Value: 0.10 PED",
        "2024-01-18 14:31:00 [Globals] [System] PlayerName killed a creature (Atrox Provider) with a value of 500 PED!",
        "2024-01-18 14:31:15 [System] [You] Your Rifle has improved by 0.1",
    ]
    
    logger.info(f"\n[TEST] Processing {len(test_lines)} test lines...")
    logger.info("-" * 60)
    
    for i, line in enumerate(test_lines, 1):
        logger.info(f"\n[TEST] Line {i}: {line}")
        await chat_reader.parse_line(line)
    
    logger.info("\n" + "=" * 60)
    logger.info("TEST RESULTS")
    logger.info("=" * 60)
    
    # Check results
    events_received = mock_overlay.events_received
    logger.info(f"Total events received by mock overlay: {len(events_received)}")
    
    event_types = {}
    for event in events_received:
        event_type = event.get('event_type', 'unknown')
        event_types[event_type] = event_types.get(event_type, 0) + 1
    
    logger.info(f"Event types received: {event_types}")
    
    # Verify critical event types
    expected_types = {
        'combat': 3,  # damage, critical, miss
        'skill_gain': 2,  # skill, skill_improved
        'loot': 2,  # two loot items
        'global': 1,  # global event
    }
    
    success = True
    for expected_type, expected_count in expected_types.items():
        actual_count = event_types.get(expected_type, 0)
        if actual_count >= expected_count:
            logger.info(f"[OK] {expected_type}: {actual_count}/{expected_count}+ expected")
        else:
            logger.error(f"[FAIL] {expected_type}: {actual_count}/{expected_count}+ expected")
            success = False
    
    # Check DB
    events_in_db = await db_manager.get_session_events(session_id)
    logger.info(f"Events in database: {len(events_in_db)}")
    
    if len(events_in_db) >= 8:
        logger.info(f"[OK] Database contains {len(events_in_db)} events")
    else:
        logger.error(f"[FAIL] Database only has {len(events_in_db)} events, expected 8+")
        success = False
    
    logger.info("=" * 60)
    if success:
        logger.info("ALL TESTS PASSED - Data flow is working!")
    else:
        logger.error("SOME TESTS FAILED - Check the output above")
    logger.info("=" * 60)
    
    await db_manager.close()
    return success

if __name__ == "__main__":
    result = asyncio.run(test_chat_parsing_flow())
    sys.exit(0 if result else 1)
