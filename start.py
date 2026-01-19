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
        # Import and start the main application
        from main_mvp import main as main_app
        import asyncio
        asyncio.run(main_app())
    except KeyboardInterrupt:
        print("\n\n[OK] LewtNanny stopped by user")
    except Exception as e:
        print(f"\n[ERROR] Error starting LewtNanny: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()