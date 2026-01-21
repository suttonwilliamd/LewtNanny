#!/usr/bin/env python3
"""
Comprehensive test for UI data flow
Tests that events flow from chat reader through to all UI components
"""

import asyncio
import sys
import logging
from pathlib import Path
from unittest.mock import MagicMock, patch

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


class MockUI:
    """Mock UI to capture events and verify data flow"""
    
    def __init__(self):
        self.events_received = {
            'overlay': [],
            'streamer_tab': [],
            'combat_tab': [],
            'skills_tab': [],
            'loot_summary': [],
            'run_log': []
        }
    
    def overlay_add_event(self, event_data):
        logger.info(f"[MOCK_UI] Overlay received: {event_data.get('event_type', 'unknown')}")
        self.events_received['overlay'].append(event_data)
    
    def streamer_tab_add_event(self, event_data):
        logger.info(f"[MOCK_UI] Streamer tab received: {event_data.get('event_type', 'unknown')}")
        self.events_received['streamer_tab'].append(event_data)
    
    def combat_tab_add_event(self, event_data):
        logger.info(f"[MOCK_UI] Combat tab received: {event_data.get('event_type', 'unknown')}")
        self.events_received['combat_tab'].append(event_data)
    
    def skills_tab_add_event(self, event_data):
        logger.info(f"[MOCK_UI] Skills tab received: {event_data.get('event_type', 'unknown')}")
        self.events_received['skills_tab'].append(event_data)
    
    def loot_summary_update(self, event_type, parsed_data):
        logger.info(f"[MOCK_UI] Loot summary updated: {event_type}")
        self.events_received['loot_summary'].append({'type': event_type, 'data': parsed_data})
    
    def run_log_add(self, event_data):
        logger.info(f"[MOCK_UI] Run log updated: {event_data.get('event_type', 'unknown')}")
        self.events_received['run_log'].append(event_data)


async def test_ui_data_flow():
    """Test the complete UI data flow"""
    logger.info("=" * 60)
    logger.info("TESTING UI DATA FLOW")
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
    
    # Create mock UI
    mock_ui = MockUI()
    
    # Connect signal to mock UI handlers (simulating main_window.handle_new_event)
    def on_new_event(event_data):
        logger.info(f"[TEST] >>> SIGNAL RECEIVED: {event_data.get('event_type', 'unknown')} <<<")
        
        # Simulate handle_new_event logic
        event_type = event_data.get('event_type', 'unknown')
        parsed_data = event_data.get('parsed_data', {})
        
        # Update Overlay
        logger.info(f"[TEST] Updating OVERLAY...")
        mock_ui.overlay_add_event(event_data)
        
        # Update Streamer Tab
        logger.info(f"[TEST] Updating STREAMER TAB...")
        mock_ui.streamer_tab_add_event(event_data)
        
        # Update Combat Tab (only for combat events)
        if event_type == 'combat':
            logger.info(f"[TEST] Updating COMBAT TAB...")
            mock_ui.combat_tab_add_event(event_data)
        
        # Update Skills Tab (only for skill events)
        if event_type in ['skill_gain', 'skill']:
            logger.info(f"[TEST] Updating SKILLS TAB...")
            mock_ui.skills_tab_add_event(event_data)
        
        # Update Loot Summary (only for loot events)
        if event_type == 'loot':
            logger.info(f"[TEST] Updating LOOT SUMMARY...")
            mock_ui.loot_summary_update(event_type, parsed_data)
        
        # Update Run Log (for all events)
        logger.info(f"[TEST] Updating RUN LOG...")
        mock_ui.run_log_add(event_data)
        
        logger.info(f"[TEST] <<< Event handling complete >>>")
    
    chat_reader.new_event.connect(on_new_event)
    logger.info("[TEST] Signal connected to mock UI handlers")
    
    # Create a test session
    session_id = f"test_session_ui_{Path(__file__).stem}"
    await db_manager.create_session(session_id, ActivityType.HUNTING.value)
    chat_reader.current_session_id = session_id
    chat_reader.current_activity = ActivityType.HUNTING
    logger.info(f"[TEST] Created session: {session_id}")
    
    # Test lines from REAL chat.log format
    test_lines = [
        ("2026-01-21 12:53:41 [System] [] You inflicted 11.4 points of damage", "combat"),
        ("2026-01-21 12:53:42 [System] [] Critical hit - Additional damage! You inflicted 45.0 points of damage", "combat"),
        ("2026-01-21 12:53:47 [System] [] The attack missed you", "combat"),
        ("2026-01-21 12:53:53 [System] [] You have gained 0.5 experience in your Rifle skill", "skill_gain"),
        ("2026-01-21 12:53:52 [System] [] You received Animal Oil x (5) Value: 1.25 PED", "loot"),
        ("2026-01-21 12:53:52 [System] [] You received Shrapnel x (1000) Value: 0.10 PED", "loot"),
        ("2026-01-21 12:53:58 [Globals] [] PlayerName killed a creature (Atrox Provider) with a value of 500 PED!", "global"),
        ("2026-01-21 12:54:58 [System] [] Your Rifle has improved by 0.1", "skill_gain"),
    ]
    
    logger.info(f"\n[TEST] Processing {len(test_lines)} test lines...")
    logger.info("-" * 60)
    
    for i, (line, expected_type) in enumerate(test_lines, 1):
        logger.info(f"\n[TEST] Line {i}: {line}")
        await chat_reader.parse_line(line)
    
    logger.info("\n" + "=" * 60)
    logger.info("TEST RESULTS")
    logger.info("=" * 60)
    
    # Verify results
    success = True
    
    # Check overlay received all events
    overlay_events = len(mock_ui.events_received['overlay'])
    logger.info(f"Overlay events: {overlay_events}/8 expected")
    if overlay_events == 8:
        logger.info("[OK] Overlay received all events")
    else:
        logger.error(f"[FAIL] Overlay only received {overlay_events}/8 events")
        success = False
    
    # Check streamer tab received all events
    streamer_events = len(mock_ui.events_received['streamer_tab'])
    logger.info(f"Streamer tab events: {streamer_events}/8 expected")
    if streamer_events == 8:
        logger.info("[OK] Streamer tab received all events")
    else:
        logger.error(f"[FAIL] Streamer tab only received {streamer_events}/8 events")
        success = False
    
    # Check combat tab received combat events
    combat_events = len(mock_ui.events_received['combat_tab'])
    logger.info(f"Combat tab events: {combat_events}/3 expected")
    if combat_events == 3:
        logger.info("[OK] Combat tab received all combat events")
    else:
        logger.error(f"[FAIL] Combat tab only received {combat_events}/3 events")
        success = False
    
    # Check skills tab received skill events
    skills_events = len(mock_ui.events_received['skills_tab'])
    logger.info(f"Skills tab events: {skills_events}/2 expected")
    if skills_events == 2:
        logger.info("[OK] Skills tab received all skill events")
    else:
        logger.error(f"[FAIL] Skills tab only received {skills_events}/2 events")
        success = False
    
    # Check loot summary updated for loot events
    loot_summary_events = len(mock_ui.events_received['loot_summary'])
    logger.info(f"Loot summary updates: {loot_summary_events}/2 expected")
    if loot_summary_events == 2:
        logger.info("[OK] Loot summary updated for all loot events")
    else:
        logger.error(f"[FAIL] Loot summary only updated {loot_summary_events}/2 times")
        success = False
    
    # Check run log updated for all events
    run_log_events = len(mock_ui.events_received['run_log'])
    logger.info(f"Run log updates: {run_log_events}/8 expected")
    if run_log_events == 8:
        logger.info("[OK] Run log updated for all events")
    else:
        logger.error(f"[FAIL] Run log only updated {run_log_events}/8 times")
        success = False
    
    logger.info("=" * 60)
    if success:
        logger.info("ALL UI DATA FLOW TESTS PASSED!")
    else:
        logger.error("SOME UI DATA FLOW TESTS FAILED!")
    logger.info("=" * 60)
    
    await db_manager.close()
    return success


if __name__ == "__main__":
    result = asyncio.run(test_ui_data_flow())
    sys.exit(0 if result else 1)
