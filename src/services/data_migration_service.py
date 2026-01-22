"""
Comprehensive data migration service
Loads all JSON data from data/ directory into SQLite
"""

import json
import asyncio
import aiosqlite
from pathlib import Path
from datetime import datetime
from decimal import Decimal
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class DataMigrationService:
    """Handles all data migration from JSON to SQLite"""

    def __init__(self, db_path: str = None):
        from src.utils.paths import ensure_user_data_dir, get_user_data_dir
        if db_path:
            self.db_path = Path(db_path)
        else:
            self.db_path = ensure_user_data_dir() / "lewtnanny.db"
        self.data_path = Path(__file__).parent.parent.parent / "data"
        self.json_files = {
            'weapons': self.data_path / 'weapons.json',
            'attachments': self.data_path / 'attachments.json',
            'scopes': self.data_path / 'scopes.json',
            'sights': self.data_path / 'sights.json',
            'resources': self.data_path / 'resources.json',
            'crafting': self.data_path / 'crafting.json'
        }

    async def migrate_all(self, force: bool = False) -> Dict[str, int]:
        """
        Migrate all JSON data to SQLite

        Args:
            force: If True, clear existing data and re-migrate

        Returns:
            Dict with counts of migrated items per category
        """
        async with aiosqlite.connect(self.db_path) as db:
            await self._create_tables(db)

            if force:
                await self._clear_data(db)

            counts = {
                'weapons': await self._migrate_weapons(db),
                'attachments': await self._migrate_attachments(db),
                'scopes': await self._migrate_scopes(db),
                'sights': await self._migrate_sights(db),
                'resources': await self._migrate_resources(db),
                'blueprints': await self._migrate_blueprints(db),
                'blueprint_materials': await self._migrate_blueprint_materials(db)
            }

            await db.commit()
            return counts

    async def verify_data(self) -> Dict[str, Any]:
        """Verify migration results and return counts"""
        async with aiosqlite.connect(self.db_path) as db:
            counts = {}
            tables = ['weapons', 'attachments', 'resources', 'blueprints', 'blueprint_materials']

            for table in tables:
                cursor = await db.execute(f"SELECT COUNT(*) FROM {table}")
                result = await cursor.fetchone()
                counts[table] = result[0] if result else 0

            # Check sample data
            cursor = await db.execute("SELECT name FROM weapons LIMIT 5")
            samples = await cursor.fetchall()
            counts['sample_weapons'] = [s[0] for s in samples]

            cursor = await db.execute("SELECT name FROM resources LIMIT 5")
            samples = await cursor.fetchall()
            counts['sample_resources'] = [s[0] for s in samples]

            return counts

    async def _create_tables(self, db: aiosqlite.Connection):
        """Create all database tables with proper schema"""
        await db.executescript("""
            DROP TABLE IF EXISTS blueprint_materials;
            DROP TABLE IF EXISTS blueprints;
            DROP TABLE IF EXISTS resources;
            DROP TABLE IF EXISTS attachments;
            DROP TABLE IF EXISTS weapons;

            CREATE TABLE weapons (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                ammo INTEGER DEFAULT 0,
                decay REAL DEFAULT 0,
                weapon_type TEXT,
                dps REAL,
                eco REAL,
                range_value INTEGER DEFAULT 0,
                damage REAL DEFAULT 0,
                reload_time REAL DEFAULT 0,
                hits INTEGER DEFAULT 0,
                data_updated TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE attachments (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                attachment_type TEXT NOT NULL,
                ammo INTEGER DEFAULT 0,
                decay REAL DEFAULT 0,
                damage_bonus REAL DEFAULT 0,
                ammo_bonus REAL DEFAULT 0,
                decay_modifier REAL DEFAULT 0,
                economy_bonus REAL DEFAULT 0,
                range_bonus INTEGER DEFAULT 0,
                data_updated TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE resources (
                name TEXT PRIMARY KEY,
                tt_value REAL DEFAULT 0,
                decay REAL DEFAULT 0,
                data_updated TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE blueprints (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                result_item TEXT,
                result_quantity INTEGER DEFAULT 1,
                skill_required TEXT,
                condition_limit INTEGER,
                data_updated TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE blueprint_materials (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                blueprint_id TEXT NOT NULL,
                material_name TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                FOREIGN KEY (blueprint_id) REFERENCES blueprints(id) ON DELETE CASCADE,
                UNIQUE(blueprint_id, material_name)
            );

            CREATE INDEX idx_weapons_name ON weapons(name);
            CREATE INDEX idx_weapons_type ON weapons(weapon_type);
            CREATE INDEX idx_weapons_dps ON weapons(dps DESC);
            CREATE INDEX idx_weapons_eco ON weapons(eco DESC);

            CREATE INDEX idx_attachments_name ON attachments(name);
            CREATE INDEX idx_attachments_type ON attachments(attachment_type);

            CREATE INDEX idx_resources_name ON resources(name);
            CREATE INDEX idx_resources_tt_value ON resources(tt_value DESC);

            CREATE INDEX idx_blueprints_name ON blueprints(name);
            CREATE INDEX idx_blueprint_materials_bp ON blueprint_materials(blueprint_id);
            CREATE INDEX idx_blueprint_materials_mat ON blueprint_materials(material_name);
        """)
        logger.info("Database tables created")

    async def _migrate_weapons(self, db: aiosqlite.Connection) -> int:
        """Migrate weapons from JSON"""
        weapons_path = self.json_files['weapons']
        if not weapons_path.exists():
            logger.warning("weapons.json not found")
            return 0

        with open(weapons_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        updated = data.get('updated', '')
        updated_dt = datetime.strptime(updated, '%Y%m%dT%H%M%S') if updated else None

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

        logger.info(f"Migrated {count} weapons")
        return count

    async def _migrate_attachments(self, db: aiosqlite.Connection) -> int:
        """Migrate attachments from JSON"""
        attachments_path = self.json_files['attachments']
        if not attachments_path.exists():
            logger.warning("attachments.json not found")
            return 0

        with open(attachments_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        updated = data.get('updated', '')
        updated_dt = datetime.strptime(updated, '%Y%m%dT%H%M%S') if updated else None

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

        logger.info(f"Migrated {count} attachments")
        return count

    async def _migrate_scopes(self, db: aiosqlite.Connection) -> int:
        """Migrate scopes (treated as attachments) from JSON"""
        scopes_path = self.json_files['scopes']
        if not scopes_path.exists():
            logger.warning("scopes.json not found")
            return 0

        with open(scopes_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        updated = data.get('updated', '')
        updated_dt = datetime.strptime(updated, '%Y%m%dT%H%M%S') if updated else None

        count = 0
        for scope_id, scope_info in data.get('data', {}).items():
            try:
                await db.execute("""
                    INSERT INTO attachments
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

        logger.info(f"Migrated {count} scopes")
        return count

    async def _migrate_sights(self, db: aiosqlite.Connection) -> int:
        """Migrate sights (treated as attachments) from JSON"""
        sights_path = self.json_files['sights']
        if not sights_path.exists():
            logger.warning("sights.json not found")
            return 0

        with open(sights_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        updated = data.get('updated', '')
        updated_dt = datetime.strptime(updated, '%Y%m%dT%H%M%S') if updated else None

        count = 0
        for sight_id, sight_info in data.get('data', {}).items():
            try:
                await db.execute("""
                    INSERT INTO attachments
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

        logger.info(f"Migrated {count} sights")
        return count

    async def _migrate_resources(self, db: aiosqlite.Connection) -> int:
        """Migrate resources from JSON"""
        resources_path = self.json_files['resources']
        if not resources_path.exists():
            logger.warning("resources.json not found")
            return 0

        with open(resources_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        updated = data.get('updated', '')
        updated_dt = datetime.strptime(updated, '%Y%m%dT%H%M%S') if updated else None

        count = 0
        for resource_name, resource_info in data.get('data', {}).items():
            try:
                if isinstance(resource_info, (int, float)):
                    tt_value = float(resource_info)
                    decay = 0.0
                elif isinstance(resource_info, str):
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

        logger.info(f"Migrated {count} resources")
        return count

    async def _migrate_blueprints(self, db: aiosqlite.Connection) -> int:
        """Migrate blueprints from JSON"""
        crafting_path = self.json_files['crafting']
        if not crafting_path.exists():
            logger.warning("crafting.json not found")
            return 0

        with open(crafting_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        updated = data.get('updated', '')
        updated_dt = datetime.strptime(updated, '%Y%m%dT%H%M%S') if updated else None

        count = 0
        for blueprint_id, materials in data.get('data', {}).items():
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

        logger.info(f"Migrated {count} blueprints")
        return count

    async def _migrate_blueprint_materials(self, db: aiosqlite.Connection) -> int:
        """Migrate blueprint materials from JSON (normalized)"""
        crafting_path = self.json_files['crafting']
        if not crafting_path.exists():
            return 0

        with open(crafting_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

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

        logger.info(f"Migrated {count} blueprint materials")
        return count

    async def _clear_data(self, db: aiosqlite.Connection):
        """Clear all data tables for fresh migration"""
        await db.execute("DELETE FROM blueprint_materials")
        await db.execute("DELETE FROM blueprints")
        await db.execute("DELETE FROM resources")
        await db.execute("DELETE FROM attachments")
        await db.execute("DELETE FROM weapons")
        logger.info("Cleared all existing data")

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


async def run_migration(force: bool = False) -> Dict[str, int]:
    """Standalone migration runner"""
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
    print(f"  Scopes: {counts.get('scopes', 'N/A')}")
    print(f"  Sights: {counts.get('sights', 'N/A')}")
    print(f"  Resources: {counts['resources']}")
    print(f"  Blueprints: {counts['blueprints']}")
    print(f"  Blueprint Materials: {counts['blueprint_materials']}")
