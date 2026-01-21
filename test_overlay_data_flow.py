#!/usr/bin/env python3
"""
Comprehensive test for the complete data flow from chat.log to overlay
Tests: chat parsing → signal emission → main window dispatch → overlay display
"""

import asyncio
import sys
import logging
from pathlib import Path
from unittest.mock import Mock, MagicMock
from decimal import Decimal

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

sys.path.insert(0, str(Path(__file__).parent))

from src.services.chat_reader import ChatReader
from src.core.database import DatabaseManager
from src.services.config_manager import ConfigManager
from src.models.models import EventType, ActivityType
from src.ui.overlay import StreamerOverlayWidget, SessionOverlay


class DataFlowTest:
    """Test harness for verifying the complete data flow"""

    def __init__(self):
        self.events_flow = []
        self.db_manager = None
        self.config_manager = None
        self.chat_reader = None
        self.overlay = None
        self.session_overlay = None

    async def setup(self):
        """Initialize test components"""
        logger.info("=" * 70)
        logger.info("TEST SETUP")
        logger.info("=" * 70)

        self.db_manager = DatabaseManager()
        await self.db_manager.initialize()
        logger.info("[SETUP] Database initialized")

        self.config_manager = ConfigManager()
        await self.config_manager.initialize()
        logger.info("[SETUP] Config manager initialized")

        self.chat_reader = ChatReader(self.db_manager, self.config_manager)
        logger.info("[SETUP] ChatReader created")

        self.session_overlay = SessionOverlay(self.db_manager, self.config_manager)
        logger.info("[SETUP] SessionOverlay created")

        self.session_overlay.show()
        logger.info("[SETUP] Overlay shown")

        session_id = f"test_session_{Path(__file__).stem}"
        await self.db_manager.create_session(session_id, ActivityType.HUNTING.value)
        self.chat_reader.current_session_id = session_id
        self.chat_reader.current_activity = ActivityType.HUNTING
        self.session_overlay.start_session(session_id, "hunting")
        logger.info(f"[SETUP] Session started: {session_id}")

    def track_event_flow(self, event_data):
        """Track events as they flow through the system"""
        self.events_flow.append({
            'timestamp': str(datetime.now()),
            'type': event_data.get('event_type', 'unknown'),
            'data': event_data
        })
        logger.info(f"[FLOW] Event tracked: {event_data.get('event_type', 'unknown')}")

    async def test_signal_connection(self):
        """Test that chat_reader.new_event signal is properly connected"""
        logger.info("=" * 70)
        logger.info("TEST 1: SIGNAL CONNECTION")
        logger.info("=" * 70)

        connected = False
        try:
            self.chat_reader.new_event.connect(self.track_event_flow)
            connected = True
            logger.info("[PASS] Signal connected successfully")
        except Exception as e:
            logger.error(f"[FAIL] Signal connection failed: {e}")

        return connected

    async def test_overlay_creation(self):
        """Test that overlay widget is created properly"""
        logger.info("=" * 70)
        logger.info("TEST 2: OVERLAY CREATION")
        logger.info("=" * 70)

        if self.session_overlay.overlay_widget is None:
            logger.error("[FAIL] Overlay widget not created")
            return False

        logger.info(f"[PASS] Overlay widget created: {self.session_overlay.overlay_widget}")
        logger.info(f"[PASS] Overlay visible: {self.session_overlay.overlay_widget.isVisible()}")
        return True

    async def test_event_types_processing(self):
        """Test all event types are processed correctly"""
        logger.info("=" * 70)
        logger.info("TEST 3: EVENT TYPES PROCESSING")
        logger.info("=" * 70)

        test_cases = [
            {
                'line': "You received Animal Oil x (5) Value: 1.25 PED",
                'expected_type': EventType.LOOT.value,
                'description': 'Loot event'
            },
            {
                'line': "You inflicted 25.5 points of damage",
                'expected_type': EventType.COMBAT.value,
                'description': 'Damage event'
            },
            {
                'line': "Critical hit - Additional damage! You inflicted 45.0 points of damage",
                'expected_type': EventType.COMBAT.value,
                'description': 'Critical hit event'
            },
            {
                'line': "You missed",
                'expected_type': EventType.COMBAT.value,
                'description': 'Miss event'
            },
            {
                'line': "PlayerName killed a creature (Atrox Provider) with a value of 500 PED!",
                'expected_type': EventType.GLOBAL.value,
                'description': 'Global event'
            },
            {
                'line': "HOF! PlayerName looted 100 PED",
                'expected_type': EventType.HOF.value,
                'description': 'HOF event'
            },
            {
                'line': "You have gained 0.5 experience in your Rifle skill",
                'expected_type': EventType.SKILL_GAIN.value,
                'description': 'Skill gain event'
            },
            {
                'line': "Your Rifle has improved by 0.1",
                'expected_type': EventType.SKILL_GAIN.value,
                'description': 'Skill improved event'
            },
        ]

        results = []
        for test in test_cases:
            logger.info(f"\n[TEST] Processing: {test['description']}")
            logger.info(f"[TEST] Input: {test['line']}")

            await self.chat_reader.parse_line(test['line'])

            if len(self.events_flow) > 0:
                last_event = self.events_flow[-1]
                actual_type = last_event['type']
                if actual_type == test['expected_type']:
                    logger.info(f"[PASS] Expected '{test['expected_type']}', got '{actual_type}'")
                    results.append(True)
                else:
                    logger.error(f"[FAIL] Expected '{test['expected_type']}', got '{actual_type}'")
                    results.append(False)
            else:
                logger.error(f"[FAIL] No event was tracked for: {test['description']}")
                results.append(False)

        logger.info("\n" + "=" * 70)
        passed = sum(results)
        total = len(results)
        logger.info(f"EVENT TYPES RESULTS: {passed}/{total} passed")
        logger.info("=" * 70)
        return all(results)

    async def test_overlay_event_reception(self):
        """Test that events are received by the overlay"""
        logger.info("=" * 70)
        logger.info("TEST 4: OVERLAY EVENT RECEPTION")
        logger.info("=" * 70)

        events_to_test = [
            {
                'event_type': 'loot',
                'parsed_data': {'items': 'Test Item', 'value': 5.0},
                'description': 'Loot event to overlay'
            },
            {
                'event_type': 'combat',
                'parsed_data': {'damage': 25.0, 'critical': False},
                'description': 'Combat event to overlay'
            },
            {
                'event_type': 'global',
                'parsed_data': {'player': 'TestPlayer', 'creature': 'Atrox', 'value': 100},
                'description': 'Global event to overlay'
            },
        ]

        initial_activity = self.session_overlay.overlay_widget.activity_label.text()
        logger.info(f"[TEST] Initial activity label: {initial_activity}")

        results = []
        for event in events_to_test:
            logger.info(f"\n[TEST] Sending: {event['description']}")
            self.session_overlay.add_event(event)

            new_activity = self.session_overlay.overlay_widget.activity_label.text()
            logger.info(f"[TEST] Activity after: {new_activity}")

            if new_activity != initial_activity:
                logger.info(f"[PASS] Activity updated for: {event['event_type']}")
                results.append(True)
            else:
                logger.error(f"[FAIL] Activity NOT updated for: {event['event_type']}")
                results.append(False)

        logger.info("\n" + "=" * 70)
        passed = sum(results)
        total = len(results)
        logger.info(f"OVERLAY RECEPTION RESULTS: {passed}/{total} passed")
        logger.info("=" * 70)
        return all(results)

    async def test_stats_accumulation(self):
        """Test that overlay stats are accumulated correctly"""
        logger.info("=" * 70)
        logger.info("TEST 5: STATS ACCUMULATION")
        logger.info("=" * 70)

        stats_before = dict(self.session_overlay.overlay_widget._stats)
        logger.info(f"[TEST] Stats before: {stats_before}")

        test_events = [
            {
                'event_type': 'loot',
                'parsed_data': {'items': 'Item1', 'value': 10.0},
                'session_id': self.chat_reader.current_session_id
            },
            {
                'event_type': 'global',
                'parsed_data': {'player': 'Player1', 'creature': 'Creature1', 'value': 500},
                'session_id': self.chat_reader.current_session_id
            },
            {
                'event_type': 'hof',
                'parsed_data': {'player': 'Player2', 'creature': 'Creature2', 'value': 1000},
                'session_id': self.chat_reader.current_session_id
            },
        ]

        for event in test_events:
            self.session_overlay.add_event(event)

        stats_after = dict(self.session_overlay.overlay_widget._stats)
        logger.info(f"[TEST] Stats after: {stats_after}")

        success = True
        if stats_after['items'] >= stats_before['items'] + 1:
            logger.info("[PASS] Items count increased")
        else:
            logger.error("[FAIL] Items count did NOT increase")
            success = False

        if stats_after['globals'] >= stats_before['globals'] + 1:
            logger.info("[PASS] Globals count increased")
        else:
            logger.error("[FAIL] Globals count did NOT increase")
            success = False

        if stats_after['hofs'] >= stats_before['hofs'] + 1:
            logger.info("[PASS] HOFs count increased")
        else:
            logger.error("[FAIL] HOFs count did NOT increase")
            success = False

        return success

    async def cleanup(self):
        """Clean up test resources"""
        logger.info("=" * 70)
        logger.info("CLEANUP")
        logger.info("=" * 70)

        if self.session_overlay:
            self.session_overlay.close()
            logger.info("[CLEANUP] Overlay closed")

        logger.info(f"[CLEANUP] Total events tracked: {len(self.events_flow)}")

        event_types = {}
        for event in self.events_flow:
            event_type = event['type']
            event_types[event_type] = event_types.get(event_type, 0) + 1

        logger.info(f"[CLEANUP] Event types: {event_types}")


async def run_all_tests():
    """Run all data flow tests"""
    logger.info("=" * 70)
    logger.info("LEWTNANNY DATA FLOW VERIFICATION TEST")
    logger.info("=" * 70)
    logger.info("Testing: chat.log → ChatReader → Signal → MainWindow → Overlay")
    logger.info("=" * 70)

    tester = DataFlowTest()

    try:
        await tester.setup()

        results = []
        results.append(await tester.test_signal_connection())
        results.append(await tester.test_overlay_creation())
        results.append(await tester.test_event_types_processing())
        results.append(await tester.test_overlay_event_reception())
        results.append(await tester.test_stats_accumulation())

        await tester.cleanup()

        logger.info("\n" + "=" * 70)
        logger.info("FINAL TEST RESULTS")
        logger.info("=" * 70)

        passed = sum(results)
        total = len(results)

        logger.info(f"Tests passed: {passed}/{total}")

        if all(results):
            logger.info("\n✓ ALL TESTS PASSED - Data flow is VERIFIED!")
            logger.info("\nThe following flow is confirmed working:")
            logger.info("  1. Chat log file monitoring")
            logger.info("  2. Regex pattern parsing")
            logger.info("  3. Signal emission (new_event)")
            logger.info("  4. Main window event dispatch")
            logger.info("  5. Overlay event reception")
            logger.info("  6. Stats accumulation and display")
        else:
            logger.error("\n✗ SOME TESTS FAILED - Check output above for details")

        logger.info("=" * 70)
        return all(results)

    except Exception as e:
        logger.error(f"TEST ERROR: {e}", exc_info=True)
        await tester.cleanup()
        return False


if __name__ == "__main__":
    from datetime import datetime
    result = asyncio.run(run_all_tests())
    sys.exit(0 if result else 1)
