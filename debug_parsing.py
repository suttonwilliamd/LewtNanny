"""
Debug chat parsing to see what's going wrong
"""

import sys
import os
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent))

def debug_parsing():
    """Debug what's happening with chat parsing"""
    print("DEBUG: Chat Parsing Analysis")
    print("=" * 40)
    
    try:
        from src.services.chat_reader_real import ChatLogReader
        print("[OK] ChatLogReader imported")
    except Exception as e:
        print(f"✗ Import failed: {e}")
        return
    
    # Use sample chat file
    sample_log = Path("sample_chat.log")
    if not sample_log.exists():
        print(f"[ERROR] Sample log not found: {sample_log}")
        return
    
    events_received = []
    
    def debug_callback(event):
        events_received.append(event)
        print(f"\n--- EVENT RECEIVED ---")
        print(f"Type: {event.event_type}")
        print(f"Raw: {event.raw_message}")
        print(f"Timestamp: {event.timestamp}")
        
        if hasattr(event, 'damage'):
            print(f"Damage: {event.damage}, Critical: {getattr(event, 'critical', False)}")
        elif hasattr(event, 'items'):
            print(f"Items: {event.items}")
        elif hasattr(event, 'skill_name'):
            print(f"Skill: {event.skill_name}, Amount: {event.amount}")
        elif hasattr(event, 'value'):
            print(f"Player: {getattr(event, 'player', 'N/A')}, Target: {getattr(event, 'target', 'N/A')}, Value: {event.value} PED")
    
    # Create reader and process
    print(f"\nProcessing file: {sample_log}")
    reader = ChatLogReader(str(sample_log), debug_callback)
    
    try:
        reader._check_file_changes()
        print(f"\n✓ Total events processed: {len(events_received)}")
        
        # Debug line-by-line
        print(f"\n--- LINE BY LINE DEBUG ---")
        with open(sample_log, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            for i, line in enumerate(lines):
                line = line.strip()
                if line:
                    log_line = reader._parse_log_line(line)
                    if log_line:
                        print(f"Line {i+1}: Channel={log_line.channel}, Msg={log_line.msg[:50]}...")
                        
    except Exception as e:
        print(f"[ERROR] Processing failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_parsing()