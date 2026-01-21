#!/usr/bin/env python3
"""
Simple test for data flow verification without GUI
Tests: ChatReader parsing → Signal emission → Mock Overlay reception
"""

import asyncio
import sys
import logging
from pathlib import Path

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


class MockOverlay:
    """Mock overlay that tracks received events"""

    def __init__(self):
        self.events = []
        self.stats = {
            'globals': 0,
            'hofs': 0,
            'items': 0,
            'total_cost': 0,
            'total_return': 0,
        }

    def add_event(self, event_data):
        event_type = event_data.get('event_type', 'unknown')
        parsed_data = event_data.get('parsed_data', {})

        logger.info(f"[MOCK_OVERLAY] Received: {event_type}")

        if event_type == 'loot':
            value = parsed_data.get('value', 0)
            self.stats['items'] += 1
            self.stats['total_return'] += value
            logger.info(f"[MOCK_OVERLAY] Updated stats: {self.stats}")

        elif event_type == 'global':
            self.stats['globals'] += 1
            logger.info(f"[MOCK_OVERLAY] Updated stats: {self.stats}")

        elif event_type == 'hof':
            self.stats['hofs'] += 1
            logger.info(f"[MOCK_OVERLAY] Updated stats: {self.stats}")

        self.events.append(event_data)


async def test_data_flow():
    """Test the complete data flow"""
    logger.info("=" * 60)
    logger.info("DATA FLOW VERIFICATION TEST")
    logger.info("=" * 60)

    db_manager = DatabaseManager()
    await db_manager.initialize()

    config_manager = ConfigManager()
    await config_manager.initialize()

    chat_reader = ChatReader(db_manager, config_manager)

    mock_overlay = MockOverlay()

    chat_reader.new_event.connect(mock_overlay.add_event)
    logger.info("[OK] Signal connected")

    session_id = f"test_session_flow"
    await db_manager.create_session(session_id, ActivityType.HUNTING.value)
    chat_reader.current_session_id = session_id
    chat_reader.current_activity = ActivityType.HUNTING

    test_cases = [
        ("You received Animal Oil x (5) Value: 1.25 PED", "loot"),
        ("You received Shrapnel x (1000) Value: 0.10 PED", "loot"),
        ("You inflicted 25.5 points of damage", "combat"),
        ("Critical hit - Additional damage! You inflicted 45.0 points of damage", "combat"),
        ("You missed", "combat"),
        ("PlayerName killed a creature (Atrox Provider) with a value of 500 PED!", "global"),
        ("HOF! PlayerName looted 100 PED", "hof"),
        ("You have gained 0.5 experience in your Rifle skill", "skill_gain"),
    ]

    logger.info(f"\nProcessing {len(test_cases)} test cases...")
    expected_counts = {'loot': 2, 'combat': 3, 'global': 1, 'hof': 1, 'skill_gain': 1}
    actual_counts = {}

    for line, expected_type in test_cases:
        logger.info(f"\n> {line[:60]}...")
        await chat_reader.parse_line(line)

    logger.info("\n" + "=" * 60)
    logger.info("RESULTS")
    logger.info("=" * 60)

    for event in mock_overlay.events:
        et = event.get('event_type', 'unknown')
        actual_counts[et] = actual_counts.get(et, 0) + 1

    logger.info(f"Expected: {expected_counts}")
    logger.info(f"Actual:   {actual_counts}")

    success = True
    for et, expected in expected_counts.items():
        actual = actual_counts.get(et, 0)
        if actual >= expected:
            logger.info(f"[OK] {et}: {actual}/{expected}")
        else:
            logger.error(f"[FAIL] {et}: {actual}/{expected}")
            success = False

    logger.info(f"\nMock overlay stats: {mock_overlay.stats}")
    logger.info(f"Total events received: {len(mock_overlay.events)}")

    if mock_overlay.stats['items'] >= 2:
        logger.info("[OK] Loot items counted correctly")
    else:
        logger.error("[FAIL] Loot items NOT counted")
        success = False

    if mock_overlay.stats['globals'] >= 1:
        logger.info("[OK] Global counted correctly")
    else:
        logger.error("[FAIL] Global NOT counted")
        success = False

    logger.info("=" * 60)
    if success:
        logger.info("DATA FLOW VERIFIED - All tests passed!")
    else:
        logger.error("SOME TESTS FAILED")
    logger.info("=" * 60)

    return success


if __name__ == "__main__":
    result = asyncio.run(test_data_flow())
    sys.exit(0 if result else 1)
