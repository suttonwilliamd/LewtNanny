"""Loadout Service
Handles saving, loading, and managing weapon loadouts
"""

import asyncio
import json
import logging
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any

import aiosqlite

logger = logging.getLogger(__name__)


@dataclass
class WeaponLoadout:
    """Complete weapon loadout configuration"""

    id: int | None = None
    name: str = ""
    weapon: str = ""
    amplifier: str | None = None
    scope: str | None = None
    sight_1: str | None = None
    sight_2: str | None = None
    damage_enh: int = 0
    accuracy_enh: int = 0
    economy_enh: int = 0
    created_at: str | None = None
    updated_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "weapon": self.weapon,
            "amplifier": self.amplifier,
            "scope": self.scope,
            "sight_1": self.sight_1,
            "sight_2": self.sight_2,
            "damage_enh": self.damage_enh,
            "accuracy_enh": self.accuracy_enh,
            "economy_enh": self.economy_enh,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WeaponLoadout":
        """Create from dictionary"""
        return cls(
            id=data.get("id"),
            name=data.get("name", ""),
            weapon=data.get("weapon", ""),
            amplifier=data.get("amplifier"),
            scope=data.get("scope"),
            sight_1=data.get("sight_1"),
            sight_2=data.get("sight_2"),
            damage_enh=data.get("damage_enh", 0),
            accuracy_enh=data.get("accuracy_enh", 0),
            economy_enh=data.get("economy_enh", 0),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )


@dataclass
class CustomWeapon:
    """Custom user-defined weapon"""

    id: int | None = None
    name: str = ""
    decay: Decimal = Decimal("0")
    ammo_burn: int = 0
    dps: Decimal = Decimal("0")
    created_at: str | None = None
    updated_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "decay": str(self.decay),
            "ammo_burn": self.ammo_burn,
            "dps": str(self.dps),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CustomWeapon":
        """Create from dictionary"""
        return cls(
            id=data.get("id"),
            name=data.get("name", ""),
            decay=Decimal(str(data.get("decay", "0"))),
            ammo_burn=int(data.get("ammo_burn", 0)),
            dps=Decimal(str(data.get("dps", "0"))),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )


class LoadoutService:
    """Service for managing weapon loadouts"""

    def __init__(self, db_manager=None):
        if db_manager:
            self.db_manager = db_manager
        else:
            from src.core.multi_database_manager import MultiDatabaseManager

            self.db_manager = MultiDatabaseManager()
        self._initialized = False

    async def initialize(self):
        """Initialize the loadout and custom_weapon tables"""
        if self._initialized:
            return

        async with aiosqlite.connect(self.db_manager.databases["user_data"]) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS loadouts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    weapon TEXT NOT NULL,
                    amplifier TEXT,
                    scope TEXT,
                    sight_1 TEXT,
                    sight_2 TEXT,
                    damage_enh INTEGER DEFAULT 0,
                    accuracy_enh INTEGER DEFAULT 0,
                    economy_enh INTEGER DEFAULT 0,
                    created_at TEXT,
                    updated_at TEXT
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS custom_weapons (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    decay TEXT NOT NULL,
                    ammo_burn INTEGER DEFAULT 0,
                    dps TEXT DEFAULT '0',
                    created_at TEXT,
                    updated_at TEXT
                )
            """)
            await db.commit()
            self._initialized = True
            logger.info("Loadout service initialized")

    async def create_loadout(self, loadout: WeaponLoadout) -> int:
        """Create a new loadout, returns the new ID"""
        await self.initialize()

        now = datetime.now().isoformat()
        loadout.created_at = now
        loadout.updated_at = now

        async with aiosqlite.connect(self.db_manager.databases["user_data"]) as db:
            cursor = await db.execute(
                """
                INSERT INTO loadouts
                (name, weapon, amplifier, scope, sight_1, sight_2,
                 damage_enh, accuracy_enh, economy_enh, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    loadout.name,
                    loadout.weapon,
                    loadout.amplifier,
                    loadout.scope,
                    loadout.sight_1,
                    loadout.sight_2,
                    loadout.damage_enh,
                    loadout.accuracy_enh,
                    loadout.economy_enh,
                    loadout.created_at,
                    loadout.updated_at,
                ),
            )
            await db.commit()
            rowid = cursor.lastrowid
            loadout.id = int(rowid) if rowid is not None else 0
            logger.info(f"Created loadout: {loadout.name} (ID: {loadout.id})")
            return loadout.id

    async def get_loadout(self, loadout_id: int) -> WeaponLoadout | None:
        """Get a loadout by ID"""
        await self.initialize()

        async with aiosqlite.connect(self.db_manager.databases["user_data"]) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM loadouts WHERE id = ?", (loadout_id,)
            )
            row = await cursor.fetchone()
            return WeaponLoadout.from_dict(dict(row)) if row else None

    async def get_loadout_by_name(self, name: str) -> WeaponLoadout | None:
        """Get a loadout by name"""
        await self.initialize()

        async with aiosqlite.connect(self.db_manager.databases["user_data"]) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM loadouts WHERE name = ?", (name,))
            row = await cursor.fetchone()
            return WeaponLoadout.from_dict(dict(row)) if row else None

    async def get_all_loadouts(self) -> list[WeaponLoadout]:
        """Get all loadouts"""
        await self.initialize()

        async with aiosqlite.connect(self.db_manager.databases["user_data"]) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM loadouts ORDER BY name")
            loadouts = []
            async for row in cursor:
                loadouts.append(WeaponLoadout.from_dict(dict(row)))
            return loadouts

    async def update_loadout(self, loadout: WeaponLoadout) -> bool:
        """Update an existing loadout"""
        await self.initialize()

        if not loadout.id:
            logger.warning("Cannot update loadout without ID")
            return False

        loadout.updated_at = datetime.now().isoformat()

        async with aiosqlite.connect(self.db_manager.databases["user_data"]) as db:
            await db.execute(
                """
                UPDATE loadouts SET
                    name = ?,
                    weapon = ?,
                    amplifier = ?,
                    scope = ?,
                    sight_1 = ?,
                    sight_2 = ?,
                    damage_enh = ?,
                    accuracy_enh = ?,
                    economy_enh = ?,
                    updated_at = ?
                WHERE id = ?
            """,
                (
                    loadout.name,
                    loadout.weapon,
                    loadout.amplifier,
                    loadout.scope,
                    loadout.sight_1,
                    loadout.sight_2,
                    loadout.damage_enh,
                    loadout.accuracy_enh,
                    loadout.economy_enh,
                    loadout.updated_at,
                    loadout.id,
                ),
            )
            await db.commit()
            logger.info(f"Updated loadout: {loadout.name} (ID: {loadout.id})")
            return True

    async def delete_loadout(self, loadout_id: int) -> bool:
        """Delete a loadout"""
        await self.initialize()

        async with aiosqlite.connect(self.db_manager.databases["user_data"]) as db:
            cursor = await db.execute(
                "DELETE FROM loadouts WHERE id = ?", (loadout_id,)
            )
            await db.commit()
            deleted = cursor.rowcount > 0
            if deleted:
                logger.info(f"Deleted loadout ID: {loadout_id}")
            return deleted

    async def delete_loadout_by_name(self, name: str) -> bool:
        """Delete a loadout by name"""
        await self.initialize()

        async with aiosqlite.connect(self.db_manager.databases["user_data"]) as db:
            cursor = await db.execute("DELETE FROM loadouts WHERE name = ?", (name,))
            await db.commit()
            deleted = cursor.rowcount > 0
            if deleted:
                logger.info(f"Deleted loadout: {name}")
            return deleted

    async def get_loadout_count(self) -> int:
        """Get total number of loadouts"""
        await self.initialize()

        async with aiosqlite.connect(self.db_manager.databases["user_data"]) as db:
            cursor = await db.execute("SELECT COUNT(*) FROM loadouts")
            row = await cursor.fetchone()
            return row[0] if row else 0

    async def export_loadouts(self) -> str:
        """Export all loadouts as JSON"""
        loadouts = await self.get_all_loadouts()
        return json.dumps([l.to_dict() for l in loadouts], indent=2)

    async def import_loadouts(self, json_data: str, replace: bool = False) -> int:
        """Import loadouts from JSON"""
        try:
            data = json.loads(json_data)
            loadouts = [WeaponLoadout.from_dict(d) for d in data]
            imported = 0

            for loadout in loadouts:
                existing = await self.get_loadout_by_name(loadout.name)
                if existing and not replace:
                    logger.info(f"Skipping existing loadout: {loadout.name}")
                    continue
                elif existing and replace:
                    loadout.id = existing.id
                    await self.update_loadout(loadout)
                else:
                    await self.create_loadout(loadout)
                imported += 1

            logger.info(f"Imported {imported} loadouts")
            return imported
        except Exception as e:
            logger.error(f"Error importing loadouts: {e}")
            raise

    async def search_loadouts(self, query: str) -> list[WeaponLoadout]:
        """Search loadouts by name"""
        await self.initialize()

        async with aiosqlite.connect(self.db_manager.databases["user_data"]) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM loadouts WHERE name LIKE ? ORDER BY name",
                (f"%{query}%",),
            )
            loadouts = []
            async for row in cursor:
                loadouts.append(WeaponLoadout.from_dict(dict(row)))
            return loadouts

    async def create_custom_weapon(self, weapon: CustomWeapon) -> int:
        """Create a new custom weapon, returns the new ID"""
        await self.initialize()

        now = datetime.now().isoformat()
        weapon.created_at = now
        weapon.updated_at = now

        async with aiosqlite.connect(self.db_manager.databases["user_data"]) as db:
            cursor = await db.execute(
                """
                INSERT INTO custom_weapons
                (name, decay, ammo, dps, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    weapon.name,
                    str(weapon.decay),
                    weapon.ammo_burn,
                    str(weapon.dps),
                    weapon.created_at,
                    weapon.updated_at,
                ),
            )
            await db.commit()
            rowid = cursor.lastrowid
            new_id = int(rowid) if rowid is not None else 0
            weapon.id = new_id
            logger.info(f"Created custom weapon: {weapon.name} (ID: {weapon.id})")
            return new_id

    async def get_all_custom_weapons(self) -> list[CustomWeapon]:
        """Get all custom weapons"""
        await self.initialize()

        async with aiosqlite.connect(self.db_manager.databases["user_data"]) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM custom_weapons ORDER BY name")
            weapons = []
            async for row in cursor:
                weapons.append(CustomWeapon.from_dict(dict(row)))
            return weapons

    async def get_custom_weapon(self, weapon_id: int) -> CustomWeapon | None:
        """Get a custom weapon by ID"""
        await self.initialize()

        async with aiosqlite.connect(self.db_manager.databases["user_data"]) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM custom_weapons WHERE id = ?", (weapon_id,)
            )
            row = await cursor.fetchone()
            return CustomWeapon.from_dict(dict(row)) if row else None

    async def get_custom_weapon_by_name(self, name: str) -> CustomWeapon | None:
        """Get a custom weapon by name"""
        await self.initialize()

        async with aiosqlite.connect(self.db_manager.databases["user_data"]) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM custom_weapons WHERE name = ?", (name,)
            )
            row = await cursor.fetchone()
            return CustomWeapon.from_dict(dict(row)) if row else None

    async def update_custom_weapon(self, weapon: CustomWeapon) -> bool:
        """Update an existing custom weapon"""
        await self.initialize()

        if not weapon.id:
            logger.warning("Cannot update custom weapon without ID")
            return False

        weapon.updated_at = datetime.now().isoformat()

        async with aiosqlite.connect(self.db_manager.databases["user_data"]) as db:
            await db.execute(
                """
                UPDATE custom_weapons SET
                    name = ?,
                    decay = ?,
                    ammo_burn = ?,
                    dps = ?,
                    updated_at = ?
                WHERE id = ?
            """,
                (
                    weapon.name,
                    str(weapon.decay),
                    weapon.ammo_burn,
                    str(weapon.dps),
                    weapon.updated_at,
                    weapon.id,
                ),
            )
            await db.commit()
            logger.info(f"Updated custom weapon: {weapon.name} (ID: {weapon.id})")
            return True

    async def delete_custom_weapon(self, weapon_id: int) -> bool:
        """Delete a custom weapon"""
        await self.initialize()

        async with aiosqlite.connect(self.db_manager.databases["user_data"]) as db:
            cursor = await db.execute(
                "DELETE FROM custom_weapons WHERE id = ?", (weapon_id,)
            )
            await db.commit()
            deleted = cursor.rowcount > 0
            if deleted:
                logger.info(f"Deleted custom weapon ID: {weapon_id}")
            return deleted


# Convenience functions
async def save_loadout(
    name: str,
    weapon: str,
    amplifier: str | None = None,
    scope: str | None = None,
    sight_1: str | None = None,
    sight_2: str | None = None,
    damage_enh: int = 0,
    accuracy_enh: int = 0,
    economy_enh: int = 0,
) -> int:
    """Save a new loadout"""
    service = LoadoutService()
    loadout = WeaponLoadout(
        name=name,
        weapon=weapon,
        amplifier=amplifier,
        scope=scope,
        sight_1=sight_1,
        sight_2=sight_2,
        damage_enh=damage_enh,
        accuracy_enh=accuracy_enh,
        economy_enh=economy_enh,
    )
    return await service.create_loadout(loadout)


async def load_loadouts() -> list[WeaponLoadout]:
    """Load all loadouts"""
    service = LoadoutService()
    return await service.get_all_loadouts()


async def delete_loadout(name: str) -> bool:
    """Delete a loadout by name"""
    service = LoadoutService()
    return await service.delete_loadout_by_name(name)


if __name__ == "__main__":

    logging.basicConfig(level=logging.INFO)

    async def test():
        service = LoadoutService()

        # Create test loadout
        loadout = WeaponLoadout(
            name="My Combat Loadout",
            weapon="ArMatrix BC-100 (L)",
            amplifier="ArMatrix B-Amplifier 10P (L)",
            scope="Alekz Precision Scope",
            sight_1="Bullseye 1-8 Sight",
            damage_enh=10,
            accuracy_enh=5,
            economy_enh=5,
        )

        id = await service.create_loadout(loadout)
        print(f"Created loadout with ID: {id}")

        # Get all loadouts
        loadouts = await service.get_all_loadouts()
        print(f"Total loadouts: {len(loadouts)}")
        for l in loadouts:
            print(f"  - {l.name}: {l.weapon}")

        # Export
        await service.export_loadouts()
        print(f"\nExported {len(loadouts)} loadouts to JSON")

        # Clean up test
        await service.delete_loadout_by_name("My Combat Loadout")
        print("Cleaned up test loadout")

    asyncio.run(test())
