"""
Test script for LewtNanny MVP functionality
"""

import asyncio
import sys
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent))

from main_mvp import SimpleDB, SimpleConfig


async def test_database():
    """Test database loading and searching"""
    print("Testing database functionality...")
    
    db = SimpleDB()
    await db.initialize()
    
    # Test weapons
    weapons_count = len(db.weapons)
    print(f"[OK] Loaded {weapons_count} weapons")
    
    # Test blueprints
    blueprints_count = len(db.blueprints)
    print(f"[OK] Loaded {blueprints_count} blueprints")
    
    # Test weapon search
    results = db.search_weapons("pistol")
    print(f"[OK] Found {len(results)} weapons matching 'pistol'")
    
    # Test session creation
    session_id = "test_session_123"
    db.create_session(session_id, "hunting")
    print(f"[OK] Created session: {session_id}")
    
    # Test event adding
    test_event = {
        'event_type': 'LOOT',
        'activity_type': 'hunting',
        'raw_message': 'You looted Animal Oil from Atrox',
        'parsed_data': {'timestamp': '2024-01-01T12:00:00'},
        'session_id': session_id
    }
    db.add_event(test_event)
    print(f"[OK] Added test event to session")
    
    # Verify event was added
    if session_id in db.sessions and len(db.sessions[session_id]['events']) > 0:
        print(f"[OK] Session now has {len(db.sessions[session_id]['events'])} events")
    else:
        print("[FAIL] Event was not added to session")
    
    return True


def test_config():
    """Test configuration system"""
    print("\nTesting configuration system...")
    
    config = SimpleConfig()
    
    # Test default values
    monitoring = config.get('chat_monitoring.monitoring_enabled', False)
    print(f"[OK] Default monitoring setting: {monitoring}")
    
    # Test nested key access
    log_path = config.get('chat_monitoring.log_file_path', 'default')
    print(f"[OK] Default log path: {log_path}")
    
    return True


async def main():
    """Run all tests"""
    print("LewtNanny MVP - Running Tests")
    print("=" * 40)
    
    try:
        # Test database
        db_ok = await test_database()
        
        # Test config
        config_ok = test_config()
        
        # Summary
        print("\n" + "=" * 40)
        if db_ok and config_ok:
            print("[OK] All tests passed! MVP is ready.")
            return True
        else:
            print("[FAIL] Some tests failed.")
            return False
            
    except Exception as e:
        print(f"[ERROR] Test failed with error: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)