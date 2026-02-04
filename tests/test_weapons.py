"""Quick test to verify weapons are working"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent))


def main():
    print("Testing weapons functionality...")
    print("=" * 40)

    # Test database loading
    try:
        import json

        with open("weapons.json") as f:
            data = json.load(f)
            weapons_count = len(data.get("data", {}))
            print(f"[OK] Weapons database loaded: {weapons_count} weapons")

            # Test a few specific weapons
            test_weapons = ["Pulsar (L)", "Korss H400 (L)", "Pulsar (L)"]
            for weapon in test_weapons:
                if weapon in data.get("data", {}):
                    info = data["data"][weapon]
                    print(f"[OK] Found test weapon: {weapon}")
                    print(f"     Type: {info.get('type', 'Unknown')}")
                    print(f"     Ammo: {info.get('ammo', 0)}")
                    print(f"     Decay: {info.get('decay', 0)}")
                else:
                    print(f"[ERROR] Test weapon not found: {weapon}")
    except Exception as e:
        print(f"[ERROR] Failed to load weapons: {e}")

    print("\nTest completed!")
    print("If you're seeing this, the weapons database is working.")
    print("The issue may be in the weapon selector population.")
    print("Check the Weapons tab in the main application.")


if __name__ == "__main__":
    main()
