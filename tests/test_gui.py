"""
Quick test of the GUI with real chat parsing
"""

import sys
import os
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent))

def test_gui():
    """Test the GUI with real chat parsing"""
    try:
        from main_mvp import SimpleDB, SimpleConfig, SimpleMainWindow
        import tkinter as tk
        
        print("[OK] GUI imports successful")
        
        # Initialize database
        db = SimpleDB()
        # Note: This would be async in real usage, but for quick test...
        import json
        if Path("weapons.json").exists():
            with open("weapons.json", 'r', encoding='utf-8') as f:
                weapons_data = json.load(f)
                for weapon_id, info in weapons_data.get('data', {}).items():
                    db.weapons[weapon_id] = info
        
        if Path("crafting.json").exists():
            with open("crafting.json", 'r', encoding='utf-8') as f:
                crafting_data = json.load(f)
                for blueprint_id, materials in crafting_data.get('data', {}).items():
                    db.blueprints[blueprint_id] = materials
        
        print(f"[OK] Loaded {len(db.weapons)} weapons and {len(db.blueprints)} blueprints")
        
        # Initialize config
        config = SimpleConfig()
        
        # Create GUI
        app = SimpleMainWindow(db, config)
        
        # Set up sample chat file for testing
        sample_chat = Path("sample_chat.log")
        if sample_chat.exists():
            app.log_file_var.set(str(sample_chat))
            print(f"[OK] Set sample chat file: {sample_chat}")
        
        print("[OK] GUI created successfully")
        print("\nTo test:")
        print("1. Click 'Start Session'")
        print("2. The GUI should parse events from sample_chat.log")
        print("3. Watch the event feed and analysis tabs")
        print("\nClose the window to exit test.")
        
        # Run GUI (this will block until window is closed)
        app.run()
        
        return True
        
    except Exception as e:
        print(f"[ERROR] GUI test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_gui()
    print(f"\nTest result: {'PASSED' if success else 'FAILED'}")