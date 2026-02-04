"""Data migration service
Loads all JSON data from data/ directory into separate SQLite database files
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

import aiosqlite

logger = logging.getLogger(__name__)


class DataMigrationService:
    """Handles all data migration from JSON to separate SQLite databases"""

    def __init__(self, db_dir: str = None):
        from src.utils.paths import ensure_user_data_dir
        if db_dir:
            self.db_dir = Path(db_dir)
        else:
            self.db_dir = ensure_user_data_dir()

        self.data_path = Path(__file__).parent.parent.parent / "data"
        self.json_files = {
            'weapons': self.data_path / 'weapons.json',
            'attachments': self.data_path / 'attachments.json',
            'scopes': self.data_path / 'scopes.json',
            'sights': self.data_path / 'sights.json',
            'resources': self.data_path / 'resources.json',
            'crafting': self.data_path / 'crafting.json'
        }

    async def migrate_all(self, force: bool = False) -> dict[str, int]:
        """Migrate all JSON data to separate SQLite databases

        Args:
            force: If True, clear existing data and re-migrate

        Returns:
            Dict with counts of migrated items per category
        """
        from src.core.database_manager import DatabaseManager

        manager = DatabaseManager(self.db_dir)
        await manager.initialize_all()

        counts = {
            'weapons': await self._migrate_weapons_to_db(manager.weapons_db, force),
            'attachments': await self._migrate_attachments_to_db(manager.attachments_db, force),
            'scopes': await self._migrate_scopes_to_db(manager.attachments_db, force),
            'sights': await self._migrate_sights_to_db(manager.attachments_db, force),
            'resources': await self._migrate_resources_to_db(manager.resources_db, force),
            'blueprints': await self._migrate_blueprints_to_db(manager.crafting_db, force),
            'blueprint_materials': await self._migrate_blueprint_materials_to_db(manager.crafting_db, force)
        }

        await manager.close_all()
        return counts

    async def verify_data(self) -> dict[str, Any]:
        """Verify migration results and return counts"""
        from src.core.database_manager import DatabaseManager

        manager = DatabaseManager(self.db_dir)
        counts = await manager.get_counts()
        await manager.close_all()
        return counts

    async def _migrate_weapons_to_db(self, db_path: Path, force: bool = False) -> int:
        """Migrate weapons from JSON to separate weapons database"""
        weapons_path = self.json_files['weapons']
        if not weapons_path.exists():
            logger.warning("weapons.json not found")
            return 0

        with open(weapons_path, encoding='utf-8') as f:
            data = json.load(f)

        updated = data.get('updated', '')
        updated_dt = datetime.strptime(updated, '%Y%m%dT%H%M%S') if updated else None

        async with aiosqlite.connect(db_path) as db:
            if force:
                await db.execute("DELETE FROM weapons")

            count = 0
            for weapon_id, weapon_info in data.get('data', {}).items():
                try:
                    decay = float(weapon_info.get('decay', 0))
                    ammo = int(weapon_info.get('ammo', 0))

                    decay_per_hit = decay / max(1, ammo) if ammo > 0 else decay
                    base_damage = self._estimate_damage(weapon_info.get('type', ''))
                    dps = base_damage / 3.0 if base_damage > 0 else 0
                    eco = (base_damage / decay_per_hit) if decay_per_hit > 0 else 0

                    await db.execute("""
                        INSERT INTO weapons
                        (id, name, ammo, decay, weapon_type, dps, eco, data_updated)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        weapon_id,
                        weapon_id,
                        ammo,
                        decay,
                        weapon_info.get('type', 'Unknown'),
                        dps,
                        eco,
                        updated_dt
                    ))
                    count += 1
                except Exception as e:
                    logger.error(f"Error migrating weapon {weapon_id}: {e}")

            await db.commit()

        logger.info(f"Migrated {count} weapons to {db_path.name}")
        return count

    async def _migrate_attachments_to_db(self, db_path: Path, force: bool = False) -> int:
        """Migrate attachments from JSON to separate attachments database"""
        attachments_path = self.json_files['attachments']
        if not attachments_path.exists():
            logger.warning("attachments.json not found")
            return 0

        with open(attachments_path, encoding='utf-8') as f:
            data = json.load(f)

        updated = data.get('updated', '')
        updated_dt = datetime.strptime(updated, '%Y%m%dT%H%M%S') if updated else None

        async with aiosqlite.connect(db_path) as db:
            if force:
                await db.execute("DELETE FROM attachments")

            count = 0
            for attachment_id, attach_info in data.get('data', {}).items():
                try:
                    await db.execute("""
                        INSERT INTO attachments
                        (id, name, attachment_type, ammo, decay, data_updated)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        attachment_id,
                        attachment_id,
                        attach_info.get('type', 'Unknown'),
                        int(attach_info.get('ammo', 0)),
                        float(attach_info.get('decay', 0)),
                        updated_dt
                    ))
                    count += 1
                except Exception as e:
                    logger.error(f"Error migrating attachment {attachment_id}: {e}")

            await db.commit()

        logger.info(f"Migrated {count} attachments to {db_path.name}")
        return count

    async def _migrate_scopes_to_db(self, db_path: Path, force: bool = False) -> int:
        """Migrate scopes from JSON to attachments database"""
        scopes_path = self.json_files['scopes']
        if not scopes_path.exists():
            logger.warning("scopes.json not found")
            return 0

        with open(scopes_path, encoding='utf-8') as f:
            data = json.load(f)

        updated = data.get('updated', '')
        updated_dt = datetime.strptime(updated, '%Y%m%dT%H%M%S') if updated else None

        async with aiosqlite.connect(db_path) as db:
            count = 0
            for scope_id, scope_info in data.get('data', {}).items():
                try:
                    await db.execute("""
                        INSERT OR IGNORE INTO attachments
                        (id, name, attachment_type, ammo, decay, range_bonus, data_updated)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        scope_id,
                        scope_id,
                        'Scope',
                        int(scope_info.get('ammo', 0)),
                        float(scope_info.get('decay', 0)),
                        20,
                        updated_dt
                    ))
                    count += 1
                except Exception as e:
                    logger.error(f"Error migrating scope {scope_id}: {e}")

            await db.commit()

        logger.info(f"Migrated {count} scopes to {db_path.name}")
        return count

    async def _migrate_sights_to_db(self, db_path: Path, force: bool = False) -> int:
        """Migrate sights from JSON to attachments database"""
        sights_path = self.json_files['sights']
        if not sights_path.exists():
            logger.warning("sights.json not found")
            return 0

        with open(sights_path, encoding='utf-8') as f:
            data = json.load(f)

        updated = data.get('updated', '')
        updated_dt = datetime.strptime(updated, '%Y%m%dT%H%M%S') if updated else None

        async with aiosqlite.connect(db_path) as db:
            count = 0
            for sight_id, sight_info in data.get('data', {}).items():
                try:
                    await db.execute("""
                        INSERT OR IGNORE INTO attachments
                        (id, name, attachment_type, ammo, decay, economy_bonus, data_updated)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        sight_id,
                        sight_id,
                        'Sight',
                        int(sight_info.get('ammo', 0)),
                        float(sight_info.get('decay', 0)),
                        0.05,
                        updated_dt
                    ))
                    count += 1
                except Exception as e:
                    logger.error(f"Error migrating sight {sight_id}: {e}")

            await db.commit()

        logger.info(f"Migrated {count} sights to {db_path.name}")
        return count

    async def _migrate_resources_to_db(self, db_path: Path, force: bool = False) -> int:
        """Migrate resources from JSON to separate resources database"""
        resources_path = self.json_files['resources']
        if not resources_path.exists():
            logger.warning("resources.json not found")
            return 0

        with open(resources_path, encoding='utf-8') as f:
            data = json.load(f)

        updated = data.get('updated', '')
        updated_dt = datetime.strptime(updated, '%Y%m%dT%H%M%S') if updated else None

        async with aiosqlite.connect(db_path) as db:
            if force:
                await db.execute("DELETE FROM resources")

            count = 0
            for resource_name, resource_info in data.get('data', {}).items():
                try:
                    if isinstance(resource_info, (int, float, str)):
                        tt_value = float(resource_info)
                        decay = 0.0
                    else:
                        tt_value = float(resource_info.get('tt_value', 0))
                        decay = float(resource_info.get('decay', 0))

                    await db.execute("""
                        INSERT OR REPLACE INTO resources
                        (name, tt_value, decay, data_updated)
                        VALUES (?, ?, ?, ?)
                    """, (
                        resource_name,
                        tt_value,
                        decay,
                        updated_dt
                    ))
                    count += 1
                except Exception as e:
                    logger.error(f"Error migrating resource {resource_name}: {e}")

            await db.commit()

        logger.info(f"Migrated {count} resources to {db_path.name}")
        return count

    async def _migrate_blueprints_to_db(self, db_path: Path, force: bool = False) -> int:
        """Migrate blueprints from JSON to separate crafting database"""
        crafting_path = self.json_files['crafting']
        if not crafting_path.exists():
            logger.warning("crafting.json not found")
            return 0

        with open(crafting_path, encoding='utf-8') as f:
            data = json.load(f)

        updated = data.get('updated', '')
        updated_dt = datetime.strptime(updated, '%Y%m%dT%H%M%S') if updated else None

        async with aiosqlite.connect(db_path) as db:
            if force:
                await db.execute("DELETE FROM blueprints")

            count = 0
            for blueprint_id, _materials in data.get('data', {}).items():
                try:
                    name = blueprint_id
                    result_item = name.replace(' Blueprint (L)', '').replace(' Blueprint', '')

                    await db.execute("""
                        INSERT INTO blueprints
                        (id, name, result_item, data_updated)
                        VALUES (?, ?, ?, ?)
                    """, (
                        blueprint_id,
                        name,
                        result_item,
                        updated_dt
                    ))
                    count += 1
                except Exception as e:
                    logger.error(f"Error migrating blueprint {blueprint_id}: {e}")

            await db.commit()

        logger.info(f"Migrated {count} blueprints to {db_path.name}")
        return count

    async def _migrate_blueprint_materials_to_db(self, db_path: Path, force: bool = False) -> int:
        """Migrate blueprint materials from JSON to crafting database"""
        crafting_path = self.json_files['crafting']
        if not crafting_path.exists():
            return 0

        with open(crafting_path, encoding='utf-8') as f:
            data = json.load(f)

        async with aiosqlite.connect(db_path) as db:
            if force:
                await db.execute("DELETE FROM blueprint_materials")

            count = 0
            for blueprint_id, materials in data.get('data', {}).items():
                if not isinstance(materials, list):
                    continue

                for material in materials:
                    if not isinstance(material, list) or len(material) < 2:
                        continue

                    try:
                        material_name = material[0]
                        quantity = material[1]

                        await db.execute("""
                            INSERT OR IGNORE INTO blueprint_materials
                            (blueprint_id, material_name, quantity)
                            VALUES (?, ?, ?)
                        """, (
                            blueprint_id,
                            material_name,
                            int(quantity)
                        ))
                        count += 1
                    except Exception as e:
                        logger.error(f"Error migrating material {material_name} for {blueprint_id}: {e}")

            await db.commit()

        logger.info(f"Migrated {count} blueprint materials to {db_path.name}")
        return count

    def _estimate_damage(self, weapon_type: str) -> float:
        """Estimate base damage based on weapon type"""
        damage_estimates = {
            'Pistol': 15,
            'Rifle': 25,
            'Carbine': 20,
            'Shotgun': 35,
            'Flamethrower': 10,
            'Melee': 40,
            'Shortblades': 12,
            'Longblades': 25,
            'Axis': 30,
            'Bow': 20,
            'Crossbow': 22,
            'Mindforce': 50,
            'Support': 5,
            'RifleS': 25,
            'PistolS': 15,
            'Laser Rifle': 28,
            'Laser Pistol': 12,
            'Assault Rifle': 22,
            'Sniper Rifle': 40
        }
        return damage_estimates.get(weapon_type, 15)


async def run_migration(force: bool = False) -> dict[str, int]:
    """Standalone migration runner using separate databases"""
    service = DataMigrationService()
    return await service.migrate_all(force=force)


if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO)

    force = '--force' in sys.argv or '-f' in sys.argv

    print("Starting data migration...")
    counts = asyncio.run(run_migration(force))

    print("\nMigration complete!")
    print(f"  Weapons: {counts['weapons']}")
    print(f"  Attachments: {counts['attachments']}")
    print(f"  Scopes: {counts.get('scopes', 0)}")
    print(f"  Sights: {counts.get('sights', 0)}")
    print(f"  Resources: {counts['resources']}")
    print(f"  Blueprints: {counts['blueprints']}")
    print(f"  Blueprint Materials: {counts['blueprint_materials']}")
