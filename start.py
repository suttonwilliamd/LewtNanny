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
    
    default_log_path = os.path.join(os.path.expanduser("~"), "Documents", "Entropia Universe", "chat.log")
    if os.path.exists(default_log_path):
        print(f"[OK] Found chat log: {default_log_path}")
    else:
        print(f"[WARN] Chat log not found at: {default_log_path}")
        print("  (This is normal if you haven't run Entropia Universe yet)")
    
    if Path("data/weapons.json").exists() and Path("data/crafting.json").exists():
        import json
        weapons_count = len(json.load(open("data/weapons.json")).get('data', {}))
        crafting_count = len(json.load(open("data/crafting.json")).get('data', {}))
        print(f"[OK] Database loaded: {weapons_count} weapons, {crafting_count} blueprints")
    else:
        print("[WARN] Database files not found in data/")
    
    print("\nStarting application...")
    
    try:
        from main import main as main_app
        main_app()
    except KeyboardInterrupt:
        print("\n\n[OK] LewtNanny stopped by user")
    except Exception as e:
        print(f"\n[ERROR] Error starting LewtNanny: {e}")
        print("\nTroubleshooting:")
        print("1. Ensure all dependencies are installed:")
        print("   pip install -r requirements.txt")
        sys.exit(1)

if __name__ == "__main__":
    main()
