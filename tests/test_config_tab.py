"""Test script for the new ConfigTab with weapon loadout system
Run this to test the LootNanny-style weapon selection
"""

import asyncio
import logging
import sys

from PyQt6.QtWidgets import QApplication

from src.services.loadout_service import CustomWeapon, LoadoutService, WeaponLoadout
from src.ui.components.config_tab import ConfigTab

logging.basicConfig(level=logging.INFO)


async def test_services():
    """Test the loadout and custom weapon services"""
    print("\n=== Testing Loadout Service ===")

    service = LoadoutService()

    test_loadout = WeaponLoadout(
        name="Test Combat Loadout",
        weapon="Korss H400 (L)",
        amplifier="A104 BLP Amp",
        scope="SMC Sight",
        sight_1="Bullseye 1-8 Sight",
        sight_2="None",
        damage_enh=10,
        accuracy_enh=5,
        economy_enh=5,
    )

    loadout_id = await service.create_loadout(test_loadout)
    print(f"Created loadout with ID: {loadout_id}")

    loadouts = await service.get_all_loadouts()
    print(f"Total loadouts: {len(loadouts)}")
    for loadout in loadouts:
        print(f"  - {loadout.name}: {loadout.weapon}")

    custom_weapon = CustomWeapon(name="Test Custom Weapon", decay="0.15", ammo_burn=12, dps="20.0")

    cw_id = await service.create_custom_weapon(custom_weapon)
    print(f"\nCreated custom weapon with ID: {cw_id}")

    custom_weapons = await service.get_all_custom_weapons()
    print(f"Total custom weapons: {len(custom_weapons)}")
    for cw in custom_weapons:
        print(f"  - {cw.name}: Decay={cw.decay}, Ammo={cw.ammo_burn}, DPS={cw.dps}")

    await service.delete_loadout_by_name("Test Combat Loadout")
    await service.delete_custom_weapon(cw_id)
    print("\nCleaned up test data")


def test_ui():
    """Test the ConfigTab UI"""
    print("\n=== Testing ConfigTab UI ===")

    app = QApplication(sys.argv)

    window = ConfigTab()
    window.setWindowTitle("ConfigTab Test - Weapon Loadout System")
    window.resize(900, 700)

    window.show()

    print("ConfigTab window opened. Click 'Add Loadout' to create a new loadout.")
    print("Click 'Create Custom Weapon' to add a custom weapon.")
    print("Use the Weapons tab to manage loadouts.")

    sys.exit(app.exec())


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Test the ConfigTab weapon loadout system")
    parser.add_argument("--service", action="store_true", help="Test the loadout service only")
    parser.add_argument("--ui", action="store_true", help="Test the UI only")

    args = parser.parse_args()

    if args.service:
        asyncio.run(test_services())
    elif args.ui:
        test_ui()
    else:
        print("Testing Loadout Service...")
        asyncio.run(test_services())
        print("\nStarting UI Test...")
        test_ui()
