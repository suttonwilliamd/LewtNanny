#!/usr/bin/env python3
"""
Test chat parsing functionality
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.services.chat_reader import ChatReader
from src.core.database import DatabaseManager
from src.services.config_manager import ConfigManager

async def test_chat_parsing():
    """Test chat parsing with sample data"""
    
    # Initialize services
    db_manager = DatabaseManager()
    await db_manager.initialize()
    
    config_manager = ConfigManager()
    await config_manager.initialize()
    
    # Create chat reader
    chat_reader = ChatReader(db_manager, config_manager)
    
    # Track events
    events = []
    
    def on_new_event(event_data):
        events.append(event_data)
        print(f"[OK] Event detected: {event_data['event_type']}")
        if event_data['event_type'] == 'loot':
            parsed = event_data['parsed_data']
            print(f"   Item: {parsed.get('item_name', 'N/A')} x({parsed.get('quantity', 'N/A')})")
            print(f"   Value: {parsed.get('value', 'N/A')} PED")
        elif event_data['event_type'] == 'combat':
            parsed = event_data['parsed_data']
            if parsed.get('critical'):
                print(f"   [CRITICAL] Hit: {parsed.get('damage', 0)} damage!")
            elif parsed.get('miss'):
                print(f"   [MISS] Missed!")
            else:
                print(f"   Damage: {parsed.get('damage', 0)}")
        elif event_data['event_type'] == 'skill':
            parsed = event_data['parsed_data']
            print(f"   Skill: {parsed.get('skill', 'N/A')} +{parsed.get('experience', 0)} exp")
        elif event_data['event_type'] == 'global':
            parsed = event_data['parsed_data']
            print(f"   [GLOBAL] {parsed.get('type', 'Global')}: {parsed.get('player', 'N/A')} killed {parsed.get('creature', 'N/A')} for {parsed.get('value', 0)} PED!")
    
    chat_reader.new_event.connect(on_new_event)
    
    # Test with sample chat lines
    sample_lines = [
        "2024-01-18 14:30:15 [System] [You] You inflicted 25.5 points of damage",
        "2024-01-18 14:30:18 [System] [You] Critical hit - Additional damage! You inflicted 45.0 points of damage",
        "2024-01-18 14:30:22 [System] [You] You missed",
        "2024-01-18 14:30:25 [System] [You] You have gained 0.5 experience in your Rifle skill",
        "2024-01-18 14:30:30 [System] [You] You received Animal Oil x (5) Value: 1.25 PED",
        "2024-01-18 14:30:35 [System] [Globals] [System] PlayerName killed a creature (Atrox Provider) with a value of 500 PED!",
    ]
    
    print("Testing Chat Parser")
    print("=" * 50)
    
    for line in sample_lines:
        print(f"\nProcessing: {line}")
        chat_reader.parse_line(line)
    
    print("\n" + "=" * 50)
    print(f"Summary: Found {len(events)} events")
    
    # Cleanup
    await db_manager.close()

if __name__ == "__main__":
    asyncio.run(test_chat_parsing())