"""
Quick test to see what's in the main window
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent))

def main():
    print("Testing main window components...")
    
    try:
        from main_mvp import SimpleDB, SimpleConfig
        print("[OK] Basic imports successful")
    except Exception as e:
        print(f"✗ Basic import failed: {e}")
        return
    
    try:
        from src.services.chat_reader_real import ChatLogReader
        from overlay import SessionOverlay
        print(f"[OK] Real parsing components available: {ChatLogReader is not None and SessionOverlay is not None}")
    except Exception as e:
        print(f"✗ Real parsing import failed: {e}")
        return
    
    # Check weapons database
    try:
        import json
        with open("weapons.json", 'r') as f:
            data = json.load(f)
            weapons_count = len(data.get('data', {}))
            print(f"[OK] Weapons database: {weapons_count} weapons")
    except Exception as e:
        print(f"✗ Weapons database error: {e}")
    
    # Test creating the main components
    db = SimpleDB()
    config = SimpleConfig()
    
    print("\nTesting main window creation...")
    
    try:
        # Import the main window class directly
        import main_mvp
        main_mvp.Real_PARSING_AVAILABLE = True
        
        # Create main window
        window = main_mvp.SimpleMainWindow(db, config)
        print("[OK] Main window created")
        
        # Check if weapon selector exists
        if hasattr(window, 'weapon_selector'):
            print(f"[OK] Weapon selector exists: {window.weapon_selector}")
        else:
            print("[ERROR] Weapon selector does NOT exist")
            
        # Check if weapons are populated
        if hasattr(window, 'db'):
            print(f"[OK] DB reference exists: {len(window.db.weapons)} weapons")
        else:
            print("[ERROR] DB reference does NOT exist")
            
    except Exception as e:
        print(f"✗ Main window creation failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()