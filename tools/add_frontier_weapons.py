"""
Add Frontier weapons to the database
Decay values in weapons.json are already in PED (not PEC), so no division is needed.
Example: "decay": "0.018" means 0.018 PED per shot
"""

import asyncio
import aiosqlite
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.paths import get_user_data_dir


async def add_frontier_weapons():
    """Add Frontier weapons to the database"""

    weapons = [
        {
            "id": "frontier_combat_knife_standard",
            "name": "Frontier Combat Knife",
            "ammo": 49,
            "decay": 0.00018,  # 0.018 PEC / 100 = 0.00018 PED
            "weapon_type": "Shortblades",
            "damage": 12.5,
            "dps": 15.0,
            "eco": 6.94,
            "range_value": 2,
            "reload_time": 0.83,
        },
        {
            "id": "frontier_combat_knife_adj",
            "name": "Frontier Combat Knife, Adjusted",
            "ammo": 98,
            "decay": 0.00018,  # 0.018 PEC / 100 = 0.00018 PED
            "weapon_type": "Shortblades",
            "damage": 12.5,
            "dps": 15.0,
            "eco": 6.94,
            "range_value": 2,
            "reload_time": 0.83,
        },
        {
            "id": "frontier_combat_knife_adj",
            "name": "Frontier Combat Knife, Adjusted",
            "ammo": 98,
            "decay": 0.00018,  # 0.018 PEC / 100 = 0.00018 PED
            "weapon_type": "Shortblades",
            "damage": 12.5,
            "dps": 15.0,
            "eco": 6.94,
            "range_value": 2,
            "reload_time": 0.83,
        },
        {
            "id": "frontier_hunting_rifle",
            "name": "Frontier Hunting Rifle",
            "ammo": 100,
            "decay": 0.020,  # 0.020 PEC (already in PED terms, no division needed)
            "weapon_type": "Rifle",
            "damage": 18.0,
            "dps": 12.0,
            "eco": 9.0,
            "range_value": 35,
            "reload_time": 1.5,
        },
        {
            "id": "frontier_hunting_rifle_adj",
            "name": "Frontier Hunting Rifle, Adjusted",
            "ammo": 180,
            "decay": 0.020,  # 0.020 PEC (already in PED terms, no division needed)
            "weapon_type": "Rifle",
            "damage": 18.0,
            "dps": 12.0,
            "eco": 9.0,
            "range_value": 35,
            "reload_time": 1.5,
        },
    ]

    db_path = get_user_data_dir() / "weapons.db"

    async with aiosqlite.connect(db_path) as db:
        for weapon in weapons:
            try:
                await db.execute(
                    """
                    INSERT OR IGNORE INTO weapons 
                    (id, name, ammo, decay, weapon_type, damage, dps, eco, range_value, reload_time)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        weapon["id"],
                        weapon["name"],
                        weapon["ammo"],
                        weapon["decay"],
                        weapon["weapon_type"],
                        weapon["damage"],
                        weapon["dps"],
                        weapon["eco"],
                        weapon["range_value"],
                        weapon["reload_time"],
                    ),
                )
                print(f"Added: {weapon['name']}")
            except Exception as e:
                print(f"Error adding {weapon['name']}: {e}")

        await db.commit()
        print("\nDone adding Frontier weapons!")

        cursor = await db.execute(
            "SELECT name, decay, ammo, weapon_type FROM weapons WHERE name LIKE 'Frontier%'"
        )
        rows = await cursor.fetchall()
        print("\nFrontier weapons in database:")
        for row in rows:
            print(f"  {row[0]}: Decay={row[1]}, Ammo={row[2]}, Type={row[3]}")


if __name__ == "__main__":
    asyncio.run(add_frontier_weapons())
