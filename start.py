#!/usr/bin/env python3
"""
LewtNanny Launcher
Quick start script for LewtNanny application
"""

import sys
import os
from pathlib import Path

def main():
    """Launch LewtNanny"""
    print("LewtNanny - Entropia Universe Loot Tracker")
    print("=" * 50)
    
    # Check for chat log
    default_log_path = os.path.join(os.path.expanduser("~"), "Documents", "Entropia Universe", "chat.log")
    if os.path.exists(default_log_path):
        print(f"[OK] Found chat log: {default_log_path}")
    else:
        print(f"[WARN] Chat log not found at: {default_log_path}")
        print("  (This is normal if you haven't run Entropia Universe yet)")
    
    # Check data files
    if Path("weapons.json").exists() and Path("crafting.json").exists():
        weapons_count = len(__import__('json').load(open("weapons.json")).get('data', {}))
        crafting_count = len(__import__('json').load(open("crafting.json")).get('data', {}))
        print(f"[OK] Database loaded: {weapons_count} weapons, {crafting_count} blueprints")
    else:
        print("[WARN] Database files not found")
    
    print("\nStarting application...")
    
    try:
        # Try to import and start the new PyQt6 application
        from main import main as main_app
        main_app()
    except ImportError as e:
        print(f"[WARN] PyQt6 not available: {e}")
        print("Falling back to Tkinter version...")
        try:
            from main_mvp import main as fallback_app
            import asyncio
            asyncio.run(fallback_app())
        except ImportError as e2:
            print(f"[ERROR] Neither PyQt6 nor fallback available: {e2}")
            print("Please install required dependencies:")
            print("  pip install PyQt6 qasync")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n[OK] LewtNanny stopped by user")
    except Exception as e:
        print(f"\n[ERROR] Error starting LewtNanny: {e}")
        print("\nTroubleshooting:")
        print("1. Ensure all dependencies are installed:")
        print("   pip install -r requirements.txt")
        print("2. Try running with specific UI framework:")
        print("   python main.py --ui pyqt6")
        print("   python main.py --ui tkinter")
        sys.exit(1)

if __name__ == "__main__":
    main()