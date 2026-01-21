"""
Test the real chat log parsing functionality
"""

import sys
import os
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from src.services.chat_reader_real import ChatLogReader
    print("[OK] ChatLogReader imported successfully")
except ImportError as e:
    print(f"X Failed to import ChatLogReader: {e}")
    sys.exit(1)


def test_chat_parsing():
    """Test chat log parsing with sample data"""
    print("\nTesting Chat Log Parsing...")
    print("=" * 40)
    
    # Use sample chat file
    sample_log = Path(__file__).parent / "sample_chat.log"
    
    events_received = []
    
    def event_callback(event):
        events_received.append(event)
        print(f"[{event.timestamp.strftime('%H:%M:%S')}] {event.event_type.upper()}: {event.raw_message}")
        
        if hasattr(event, 'damage'):
            print(f"  - Damage: {event.damage}, Critical: {getattr(event, 'critical', False)}")
        elif hasattr(event, 'items'):
            print(f"  - Items: {event.items}")
        elif hasattr(event, 'skill_name'):
            print(f"  - Skill: {event.skill_name}, Amount: {event.amount}")
        elif hasattr(event, 'value'):
            print(f"  - Player: {getattr(event, 'player', 'N/A')}, Target: {getattr(event, 'target', 'N/A')}, Value: {event.value} PED")
    
    # Create chat reader
    reader = ChatLogReader(str(sample_log), event_callback)
    
    print(f"Reading from: {sample_log}")
    print("Processing existing content...\n")
    
    # Process existing content
    try:
        reader._check_file_changes()
        print(f"\n[OK] Processed {len(events_received)} events from sample log")
    except Exception as e:
        print(f"[ERROR] Error processing chat log: {e}")
        return False
    
    # Test specific events
    expected_events = ['damage', 'critical', 'miss', 'skill', 'loot', 'global', 'skill_improved']
    found_events = set(event.event_type for event in events_received)
    
    print(f"\nEvent types found: {found_events}")
    print(f"Expected types: {set(expected_events)}")
    
    if len(events_received) >= 6:  # Should have at least 6 events
        print("[OK] Chat parsing working correctly!")
        return True
    else:
        print(f"[ERROR] Only {len(events_received)} events parsed, expected more")
        return False


if __name__ == "__main__":
    success = test_chat_parsing()
    sys.exit(0 if success else 1)