#!/usr/bin/env python3
"""
Test script using REAL chat.log data from the user
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


# REAL chat.log lines from user
REAL_CHAT_LINES = [
    "2026-01-21 12:26:13 [System] [] You inflicted 7.0 points of damage",
    "2026-01-21 12:26:14 [System] [] You inflicted 6.6 points of damage",
    "2026-01-21 12:26:15 [System] [] Critical hit - Additional damage! You inflicted 23.1 points of damage",
    "2026-01-21 12:26:16 [System] [] You inflicted 10.1 points of damage",
    "2026-01-21 12:26:18 [System] [] You inflicted 8.1 points of damage",
    "2026-01-21 12:26:19 [System] [] You inflicted 8.4 points of damage",
    "2026-01-21 12:26:20 [System] [] You inflicted 6.1 points of damage",
    "2026-01-21 12:26:20 [System] [] The attack missed you",
    "2026-01-21 12:26:23 [System] [] The attack missed you",
    "2026-01-21 12:26:25 [System] [] You Evaded the attack",
    "2026-01-21 12:26:27 [System] [] You received Universal Ammo x (5119) Value: 0.5119 PED",
    "2026-01-21 12:26:27 [System] [] You took 11.7 points of damage",
    "2026-01-21 12:26:28 [System] [] You inflicted 7.0 points of damage",
    "2026-01-21 12:26:29 [System] [] You received Shrapnel x (81) Value: 0.0081 PED",
    "2026-01-21 12:26:29 [System] [] You received Animal Hide x (7) Value: 0.0700 PED",
    "2026-01-21 12:33:35 [System] [] You have gained 0.1812 experience in your Rifle skill",
    "2026-01-21 12:33:35 [System] [] You have gained 0.2036 experience in your Skinning skill",
    "2026-01-21 12:33:35 [System] [] You received Shrapnel x (1107) Value: 0.1107 PED",
    "2026-01-21 12:33:35 [System] [] You received Nova Fragment x (8) Value: 0.0000 PED",
    "2026-01-21 12:23:09 [Globals] [] Team \"(Shared Loot)\" killed a creature (The Sand King) with a value of 3280 PED! A record has been added to the Hall of Fame!",
    "2026-01-21 12:23:13 [Globals] [] Kitana Desto Mudock killed a creature (Rextelum Strong) with a value of 65 PED!",
    "2026-01-21 12:26:04 [Globals] [] Chantra TheProfit Moneymaker constructed an item (Explosive Projectiles) worth 156 PED!",
    "2026-01-21 12:33:52 [Globals] [] Ueidi Storm Souza found a deposit (Energized Crystal) with a value of 126 PED!",
    "2026-01-21 12:39:18 [Globals] [] Team \"(Shared Loot)\" found a deposit (M-type Asteroid XIX) with a value of 2392 PED! A record has been added to the Hall of Fame!",
]


async def test_real_chat_data():
    """Test parsing with real chat.log data"""
    logger.info("=" * 60)
    logger.info("TESTING WITH REAL CHAT.LOG DATA")
    logger.info("=" * 60)
    
    db_manager = DatabaseManager()
    await db_manager.initialize()
    
    config_manager = ConfigManager()
    await config_manager.initialize()
    
    chat_reader = ChatReader(db_manager, config_manager)
    
    events_received = []
    
    def on_event(event_data):
        events_received.append(event_data)
        logger.info(f"[RECEIVED] {event_data['event_type']}: {event_data['parsed_data']}")
    
    chat_reader.new_event.connect(on_event)
    
    session_id = "test_real_chat_data"
    await db_manager.create_session(session_id, ActivityType.HUNTING.value)
    chat_reader.current_session_id = session_id
    chat_reader.current_activity = ActivityType.HUNTING
    
    logger.info(f"\nProcessing {len(REAL_CHAT_LINES)} lines from real chat.log...\n")
    
    for i, line in enumerate(REAL_CHAT_LINES, 1):
        logger.info(f"--- Line {i}: {line[:70]} ---")
        await chat_reader.parse_line(line)
    
    logger.info("\n" + "=" * 60)
    logger.info("RESULTS")
    logger.info("=" * 60)
    
    event_types = {}
    for event in events_received:
        etype = event['event_type']
        event_types[etype] = event_types.get(etype, 0) + 1
    
    logger.info(f"\nTotal events detected: {len(events_received)}")
    logger.info(f"Event breakdown:")
    for etype, count in sorted(event_types.items()):
        logger.info(f"  {etype}: {count}")
    
    logger.info("\n" + "-" * 60)
    logger.info("EXPECTED EVENTS:")
    logger.info("  - combat (damage): 10")
    logger.info("  - combat (critical): 1")
    logger.info("  - combat (miss): 2")
    logger.info("  - combat (evade): 1")
    logger.info("  - combat (damage_taken): 1")
    logger.info("  - loot: 4")
    logger.info("  - skill_gain: 2")
    logger.info("  - global (kill): 2")
    logger.info("  - global (team kill + HOF): 1")
    logger.info("  - global (crafting): 1")
    logger.info("  - global (mining): 1")
    logger.info("  - global (team mining + HOF): 1")
    
    expected_total = 10 + 1 + 2 + 1 + 1 + 4 + 2 + 2 + 1 + 1 + 1 + 1  # = 27
    
    logger.info("-" * 60)
    if len(events_received) == expected_total:
        logger.info(f"SUCCESS: Got {len(events_received)}/{expected_total} expected events!")
    else:
        logger.warning(f"PARTIAL: Got {len(events_received)}/{expected_total} expected events")
        missing = expected_total - len(events_received)
        if missing > 0:
            logger.warning(f"  Missing {missing} events")
    
    await db_manager.close()
    return len(events_received) >= expected_total - 2


if __name__ == "__main__":
    result = asyncio.run(test_real_chat_data())
    sys.exit(0 if result else 1)
