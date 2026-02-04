"""Database manager for LewtNanny using SQLite for performance
Uses the new data migration service for loading JSON game data
"""

import json
import logging
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import aiosqlite

from src.models.models import CraftingBlueprint, Weapon
from src.utils.paths import ensure_user_data_dir

logger = logging.getLogger(__name__)


class DatabaseManager:
    def __init__(self, db_path: str | None = None):
        if db_path:
            self.db_path = Path(db_path)
        else:
            user_data_dir = ensure_user_data_dir()
            self.db_path = user_data_dir / "user_data.db"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        logger.info(f"DatabaseManager initialized with path: {self.db_path}")

    async def initialize(self):
        """Initialize database and create tables"""
        logger.info("Initializing database...")

        async with aiosqlite.connect(self.db_path) as db:
            await self.create_tables(db)
            await self.migrate_json_data(db)
            await db.commit()

        logger.info("Database initialization complete")

    async def create_tables(self, db: aiosqlite.Connection):
        """Create all necessary database tables"""
        logger.debug("Creating database tables...")

        await db.execute("""
            CREATE TABLE IF NOT EXISTS weapons (
                id TEXT PRIMARY KEY,
                name TEXT,
                ammo INTEGER,
                decay REAL,
                weapon_type TEXT,
                dps REAL,
                eco REAL,
                range_value INTEGER,
                damage REAL,
                reload_time REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS crafting_blueprints (
                id TEXT PRIMARY KEY,
                name TEXT,
                materials TEXT,
                result_item TEXT,
                result_quantity INTEGER,
                skill_required TEXT,
                condition_limit INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                start_time TIMESTAMP,
                end_time TIMESTAMP,
                activity_type TEXT,
                total_cost REAL,
                total_return REAL,
                total_markup REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP,
                event_type TEXT,
                activity_type TEXT,
                raw_message TEXT,
                parsed_data TEXT,
                session_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessions (id)
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS markup_config (
                item_name TEXT PRIMARY KEY,
                markup_value REAL
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS session_loot_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                item_name TEXT,
                quantity INTEGER,
                total_value REAL,
                markup_percent REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessions (id)
            )
        """)

        await db.execute("CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_events_session ON events(session_id)")
        await db.execute(
            "CREATE INDEX IF NOT EXISTS idx_sessions_activity ON sessions(activity_type)"
        )
        await db.execute(
            "CREATE INDEX IF NOT EXISTS idx_session_loot_session ON session_loot_items(session_id)"
        )

        await db.execute("CREATE INDEX IF NOT EXISTS idx_weapons_name ON weapons(name)")

        logger.debug("Database tables created")

        await self.migrate_schema(db)

    async def migrate_schema(self, db: aiosqlite.Connection):
        """Migrate database schema if needed"""
        try:
            cursor = await db.execute("PRAGMA table_info(weapons)")
            columns = {row[1]: row for row in await cursor.fetchall()}

            needed_columns = {
                "damage": "ALTER TABLE weapons ADD COLUMN damage REAL DEFAULT 0",
                "reload_time": "ALTER TABLE weapons ADD COLUMN reload_time REAL DEFAULT 0",
                "name": "ALTER TABLE weapons ADD COLUMN name TEXT",
            }

            for col_name, alter_stmt in needed_columns.items():
                if col_name not in columns:
                    try:
                        await db.execute(alter_stmt)
                        logger.info(f"Added column: {col_name}")
                    except Exception as e:
                        logger.debug(f"Column {col_name} may already exist: {e}")

            logger.debug("Schema migration complete")

        except Exception as e:
            logger.error(f"Schema migration error: {e}")

    async def _legacy_migrate_json_data(self, db: aiosqlite.Connection):
        """Legacy migration method - kept for fallback"""
        logger.info("Starting legacy JSON data migration...")

        weapons_path = self.db_path.parent / "weapons.json"
        if weapons_path.exists():
            with open(weapons_path, encoding="utf-8") as f:
                weapons_data = json.load(f)

            weapons_migrated = 0
            for weapon_id, weapon_info in weapons_data.get("data", {}).items():
                try:
                    damage = float(weapon_info.get("damage", 0))
                    ammo = int(weapon_info.get("ammo", 0))
                    decay = float(weapon_info.get("decay", 0))
                    decay_per_hit = decay / max(1, ammo) if ammo > 0 else decay
                    dps = damage / 3.0
                    eco = (damage / decay_per_hit) if decay_per_hit > 0 else 0

                    await db.execute(
                        """
                        INSERT OR IGNORE INTO weapons (id, name, ammo, decay, weapon_type, dps, eco)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            weapon_id,
                            weapon_id,
                            ammo,
                            decay,
                            weapon_info.get("type", "Unknown"),
                            dps,
                            eco,
                        ),
                    )
                    weapons_migrated += 1
                except Exception as e:
                    logger.error(f"Error migrating weapon {weapon_id}: {e}")

            logger.info(f"Legacy migrated {weapons_migrated} weapons")

        crafting_path = self.db_path.parent / "crafting.json"
        if crafting_path.exists():
            with open(crafting_path, encoding="utf-8") as f:
                crafting_data = json.load(f)

            blueprints_migrated = 0
            for blueprint_id, materials in crafting_data.get("data", {}).items():
                try:
                    result_item = blueprint_id.replace(" Blueprint (L)", "").replace(
                        " Blueprint", ""
                    )
                    # Store materials as JSON in crafting_blueprints table
                    materials_json = json.dumps(materials) if isinstance(materials, list) else "[]"

                    await db.execute(
                        """
                        INSERT OR IGNORE INTO crafting_blueprints
                        (id, name, materials, result_item, result_quantity)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (blueprint_id, blueprint_id, materials_json, result_item, 1),
                    )

                    # Also populate the old tables for backward compatibility
                    await db.execute(
                        """
                        INSERT OR IGNORE INTO crafting_blueprints
                        (id, name, materials, result_item, result_quantity)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (blueprint_id, blueprint_id, materials_json, result_item, 1),
                    )

                    if isinstance(materials, list):
                        for material in materials:
                            if isinstance(material, list) and len(material) >= 2:
                                await db.execute(
                                    """
                                        INSERT OR IGNORE INTO blueprint_materials
                                        (blueprint_id, material_name, quantity)
                                        VALUES (?, ?, ?)
                                        """,
                                    (blueprint_id, material[0], int(material[1])),
                                )

                    blueprints_migrated += 1
                except Exception as e:
                    logger.error(f"Error migrating blueprint {blueprint_id}: {e}")

            logger.info(f"Legacy migrated {blueprints_migrated} blueprints")

        logger.info("Legacy JSON data migration complete")

    async def migrate_json_data(self, db: aiosqlite.Connection):
        """Migrate data from JSON files to SQLite using the new migration service"""
        logger.info("Checking JSON data migration status...")

        try:
            from src.services.data_migration_service import DataMigrationService

            cursor = await db.execute("SELECT COUNT(*) FROM weapons")
            result = await cursor.fetchone()
            weapon_count = result[0] if result and result[0] else 0

            if weapon_count > 0:
                logger.info(f"Weapons already exist ({weapon_count}), checking other tables...")

                cursor = await db.execute("SELECT COUNT(*) FROM attachments")
                result = await cursor.fetchone()
                attachment_count = result[0] if result and result[0] else 0

                cursor = await db.execute("SELECT COUNT(*) FROM resources")
                result = await cursor.fetchone()
                resource_count = result[0] if result and result[0] else 0

                cursor = await db.execute("SELECT COUNT(*) FROM blueprints")
                result = await cursor.fetchone()
                blueprint_count = result[0] if result and result[0] else 0

                if attachment_count == 0 or resource_count == 0 or blueprint_count == 0:
                    logger.info("Missing data detected, running full migration...")
                    migrator = DataMigrationService(str(self.db_path))
                    counts = await migrator.migrate_all(force=False)
                    logger.info(f"Migration complete: {counts}")
                else:
                    logger.info("All game data already migrated. Skipping.")
            else:
                logger.info("No weapons found, running full migration...")
                migrator = DataMigrationService(str(self.db_path))
                counts = await migrator.migrate_all(force=False)
                logger.info(f"Migration complete: {counts}")

        except ImportError as e:
            logger.warning(f"Could not import migration service, using legacy migration: {e}")
            await self._legacy_migrate_json_data(db)
        except Exception as e:
            logger.error(f"Migration error: {e}")
            await self._legacy_migrate_json_data(db)

    async def get_all_weapons(self) -> list[Weapon]:
        """Get all weapons from database"""
        weapons = []

        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                SELECT id, name, ammo, decay, weapon_type, dps, eco,
                range_value, damage, reload_time FROM weapons
            """)

            async for row in cursor:
                weapons.append(
                    Weapon(
                        id=row[0],
                        name=row[1],
                        ammo=row[2],
                        decay=Decimal(str(row[3])),
                        weapon_type=row[4],
                        dps=Decimal(str(row[5])) if row[5] else None,
                        eco=Decimal(str(row[6])) if row[6] else None,
                        range_=row[7],
                    )
                )

        logger.debug(f"Retrieved {len(weapons)} weapons from database")
        return weapons

    async def get_weapon_by_name(self, name: str) -> Weapon | None:
        """Get weapon by name or ID"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """
                SELECT id, name, ammo, decay, weapon_type, dps, eco, range_value
                FROM weapons
                WHERE name = ? OR id = ?
            """,
                (name, name),
            )

            row = await cursor.fetchone()
            if row:
                return Weapon(
                    id=row[0],
                    name=row[1],
                    ammo=row[2],
                    decay=Decimal(str(row[3])),
                    weapon_type=row[4],
                    dps=Decimal(str(row[5])) if row[5] else None,
                    eco=Decimal(str(row[6])) if row[6] else None,
                    range_=row[7],
                )
        return None

    async def search_weapons(self, query: str, limit: int = 50) -> list[Weapon]:
        """Search weapons by name"""
        weapons = []

        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """
                SELECT id, name, ammo, decay, weapon_type, dps, eco, range_value
                FROM weapons
                WHERE name LIKE ? OR id LIKE ?
                ORDER BY name
                LIMIT ?
            """,
                (f"%{query}%", f"%{query}%", limit),
            )

            async for row in cursor:
                weapons.append(
                    Weapon(
                        id=row[0],
                        name=row[1],
                        ammo=row[2],
                        decay=Decimal(str(row[3])),
                        weapon_type=row[4],
                        dps=Decimal(str(row[5])) if row[5] else None,
                        eco=Decimal(str(row[6])) if row[6] else None,
                        range_=row[7],
                    )
                )

        logger.debug(f"Search for '{query}' returned {len(weapons)} weapons")
        return weapons

    async def get_weapons_by_type(self, weapon_type: str) -> list[Weapon]:
        """Get weapons by type"""
        weapons = []

        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """
                SELECT id, name, ammo, decay, weapon_type, dps, eco, range_value
                FROM weapons
                WHERE weapon_type = ?
                ORDER BY name
            """,
                (weapon_type,),
            )

            async for row in cursor:
                weapons.append(
                    Weapon(
                        id=row[0],
                        name=row[1],
                        ammo=row[2],
                        decay=Decimal(str(row[3])),
                        weapon_type=row[4],
                        dps=Decimal(str(row[5])) if row[5] else None,
                        eco=Decimal(str(row[6])) if row[6] else None,
                        range_=row[7],
                    )
                )

        return weapons

    async def get_blueprint_by_name(self, name: str) -> CraftingBlueprint | None:
        """Get crafting blueprint by name or ID"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """
                SELECT id, name, materials, result_item, result_quantity,
                       skill_required, condition_limit
                FROM crafting_blueprints
                WHERE name = ? OR id = ?
            """,
                (name, name),
            )

            row = await cursor.fetchone()
            if row:
                materials = json.loads(row[2]) if row[2] else []
                return CraftingBlueprint(
                    id=row[0],
                    name=row[1],
                    materials=materials,
                    result_item=row[3],
                    result_quantity=row[4],
                    skill_required=row[5],
                    condition_limit=row[6],
                )
        return None

    async def create_session(self, session_id: str, activity_type: str) -> bool:
        """Create a new session"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    """
                    INSERT INTO sessions (id, start_time, activity_type, total_cost,
                    total_return, total_markup)
                    VALUES (?, ?, ?, 0, 0, 0)
                    """,
                    (session_id, datetime.now(), activity_type),
                )
                await db.commit()

            logger.info(f"Session created: {session_id}")
            return True

        except Exception as e:
            logger.error(f"Error creating session: {e}")
            return False

    def create_session_sync(self, session_id: str, activity_type: str) -> bool:
        """Create a new session (synchronous version for use with Qt event loop)"""
        try:
            import sqlite3

            with sqlite3.connect(self.db_path) as db:
                db.execute(
                    """
                    INSERT INTO sessions (id, start_time, activity_type,
                    total_cost, total_return, total_markup)
                    VALUES (?, ?, ?, 0, 0, 0)
                    """,
                    (session_id, datetime.now(), activity_type),
                )
                db.commit()

            logger.info(f"Session created (sync): {session_id}")
            return True

        except Exception as e:
            logger.error(f"Error creating session (sync): {e}")
            return False

    async def add_event(self, event_data: dict[str, Any]) -> bool:
        """Add an event to the database"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    """
                    INSERT INTO events (timestamp, event_type, activity_type,
                    raw_message, parsed_data, session_id)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        datetime.now(),
                        event_data.get("event_type"),
                        event_data.get("activity_type"),
                        event_data.get("raw_message"),
                        json.dumps(event_data.get("parsed_data", {})),
                        event_data.get("session_id"),
                    ),
                )
                await db.commit()

            logger.debug(f"Event added: {event_data.get('event_type')}")
            return True

        except Exception as e:
            logger.error(f"Error adding event: {e}")
            return False

    def add_event_sync(self, event_data: dict[str, Any]) -> bool:
        """Add an event to the database (synchronous version)"""
        try:
            import sqlite3

            with sqlite3.connect(self.db_path) as db:
                db.execute(
                    """
                    INSERT INTO events (timestamp, event_type, activity_type,
                    raw_message, parsed_data, session_id)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        datetime.now(),
                        event_data.get("event_type"),
                        event_data.get("activity_type"),
                        event_data.get("raw_message"),
                        json.dumps(event_data.get("parsed_data", {})),
                        event_data.get("session_id"),
                    ),
                )
                db.commit()

            logger.debug(f"Event added (sync): {event_data.get('event_type')}")
            return True

        except Exception as e:
            logger.error(f"Error adding event (sync): {e}")
            return False

    async def get_session_stats(self, session_id: str) -> dict[str, Any]:
        """Get statistics for a session"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    """
                    SELECT COUNT(*) as event_count,
                           SUM(CASE WHEN event_type = 'combat' THEN 1 ELSE 0 END) as combat_count,
                           SUM(CASE WHEN event_type = 'loot' THEN 1 ELSE 0 END) as loot_count
                    FROM events
                    WHERE session_id = ?
                """,
                    (session_id,),
                )

                row = await cursor.fetchone()

                if row:
                    return {
                        "session_id": session_id,
                        "event_count": row[0] or 0,
                        "combat_count": row[1] or 0,
                        "loot_count": row[2] or 0,
                    }

                return {
                    "session_id": session_id,
                    "event_count": 0,
                    "combat_count": 0,
                    "loot_count": 0,
                }

        except Exception as e:
            logger.error(f"Error getting session stats: {e}")
            return {}

    async def get_session_events(self, session_id: str) -> list[dict[str, Any]]:
        """Get all events for a session"""
        events = []

        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    """
                    SELECT id, timestamp, event_type, activity_type, raw_message, parsed_data
                    FROM events
                    WHERE session_id = ?
                    ORDER BY timestamp
                """,
                    (session_id,),
                )

                async for row in cursor:
                    events.append(
                        {
                            "id": row[0],
                            "timestamp": row[1],
                            "event_type": row[2],
                            "activity_type": row[3],
                            "raw_message": row[4],
                            "parsed_data": json.loads(row[5]) if row[5] else {},
                        }
                    )

        except Exception as e:
            logger.error(f"Error getting session events: {e}")

        return events

    async def get_all_sessions(self) -> list[dict[str, Any]]:
        """Get all sessions"""
        sessions = []

        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute("""
                    SELECT id, start_time, end_time, activity_type,
                    total_cost, total_return, total_markup
                    FROM sessions
                    ORDER BY start_time DESC
                """)

                async for row in cursor:
                    sessions.append(
                        {
                            "id": row[0],
                            "start_time": row[1],
                            "end_time": row[2],
                            "activity_type": row[3],
                            "total_cost": row[4] or 0,
                            "total_return": row[5] or 0,
                            "total_markup": row[6] or 0,
                        }
                    )

        except Exception as e:
            logger.error(f"Error getting all sessions: {e}")

        return sessions

    async def delete_session(self, session_id: str) -> bool:
        """Delete a session and its events"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("DELETE FROM events WHERE session_id = ?", (session_id,))
                await db.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
                await db.commit()

            logger.info(f"Session deleted: {session_id}")
            return True

        except Exception as e:
            logger.error(f"Error deleting session: {e}")
            return False

    async def delete_all_sessions(self):
        """Delete all sessions and events"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("DELETE FROM events")
                await db.execute("DELETE FROM sessions")
                await db.commit()

            logger.info("All sessions deleted")

        except Exception as e:
            logger.error(f"Error deleting all sessions: {e}")

    async def update_session_end(self, session_id: str):
        """Update session end time"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    "UPDATE sessions SET end_time = ? WHERE id = ?",
                    (datetime.now(), session_id),
                )
                await db.commit()

            logger.debug(f"Session end time updated: {session_id}")

        except Exception as e:
            logger.error(f"Error updating session end: {e}")

    async def get_session_count(self) -> int:
        """Get total session count"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute("SELECT COUNT(*) FROM sessions")
                row = await cursor.fetchone()
                return row[0] if row else 0
        except Exception as e:
            logger.error(f"Error getting session count: {e}")
            return 0

    async def get_weapon_count(self) -> int:
        """Get total weapon count"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute("SELECT COUNT(*) FROM weapons")
                row = await cursor.fetchone()
                return row[0] if row else 0
        except Exception as e:
            logger.error(f"Error getting weapon count: {e}")
            return 0

    async def close(self):
        """Close database connection (placeholder for future connection pooling)"""
        logger.info("Database connection closed")

    async def save_session_loot_item(
        self,
        session_id: str,
        item_name: str,
        quantity: int,
        total_value: float,
        markup_percent: float,
    ):
        """Save or update a loot item for a session"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    """
                    INSERT OR REPLACE INTO session_loot_items
                    (session_id, item_name, quantity, total_value, markup_percent)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (session_id, item_name, quantity, total_value, markup_percent),
                )
                await db.commit()
            logger.debug(f"Saved loot item: {item_name} for session {session_id}")
        except Exception as e:
            logger.error(f"Error saving session loot item: {e}")

    async def get_session_loot_items(self, session_id: str) -> list[dict[str, Any]]:
        """Get all loot items for a session"""
        items = []
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    """
                    SELECT id, item_name, quantity, total_value, markup_percent
                    FROM session_loot_items
                    WHERE session_id = ?
                    ORDER BY total_value DESC
                """,
                    (session_id,),
                )

                async for row in cursor:
                    items.append(
                        {
                            "id": row[0],
                            "item_name": row[1],
                            "quantity": row[2],
                            "total_value": row[3],
                            "markup_percent": row[4],
                        }
                    )
        except Exception as e:
            logger.error(f"Error getting session loot items: {e}")
        return items

    async def delete_session_loot_items(self, session_id: str):
        """Delete all loot items for a session"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    "DELETE FROM session_loot_items WHERE session_id = ?", (session_id,)
                )
                await db.commit()
        except Exception as e:
            logger.error(f"Error deleting session loot items: {e}")

    async def update_session_totals(
        self,
        session_id: str,
        total_cost: float,
        total_return: float,
        total_markup: float,
    ):
        """Update session totals"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    """
                    UPDATE sessions SET total_cost = ?, total_return = ?,
                    total_markup = ?, end_time = ?
                    WHERE id = ?
                    """,
                    (
                        total_cost,
                        total_return,
                        total_markup,
                        datetime.now(),
                        session_id,
                    ),
                )
                await db.commit()
            logger.debug(f"Session totals updated: {session_id}")
        except Exception as e:
            logger.error(f"Error updating session totals: {e}")

    async def get_session_counts(self, session_id: str) -> dict[str, int]:
        """Get counts of creatures, globals, and HOFs for a session"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    """
                    SELECT raw_message
                    FROM events
                    WHERE session_id = ?
                """,
                    (session_id,),
                )

                creatures = 0
                globals_count = 0
                hofs = 0

                async for row in cursor:
                    raw_message = row[0] or ""
                    if "Hall of Fame" in raw_message or "HOF" in raw_message:
                        hofs += 1
                    elif "killed a creature" in raw_message:
                        globals_count += 1
                        creatures += 1

                return {"creatures": creatures, "globals": globals_count, "hofs": hofs}

        except Exception as e:
            logger.error(f"Error getting session counts: {e}")
            return {"creatures": 0, "globals": 0, "hofs": 0}

    async def get_session_skills(self, session_id: str) -> list[dict[str, Any]]:
        """Get skill gains for a session"""
        skills = []
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    """
                    SELECT parsed_data
                    FROM events
                    WHERE session_id = ? AND event_type IN ('skill_gain', 'skill')
                    ORDER BY timestamp
                """,
                    (session_id,),
                )

                async for row in cursor:
                    parsed_data = row[0]
                    if parsed_data:
                        try:
                            data = (
                                json.loads(parsed_data)
                                if isinstance(parsed_data, str)
                                else parsed_data
                            )
                            skills.append(data)
                        except json.JSONDecodeError:
                            logger.warning(f"Failed to parse skill data: {parsed_data}")

        except Exception as e:
            logger.error(f"Error getting session skills: {e}")

        return skills

    async def get_session_combat_events(self, session_id: str) -> list[dict[str, Any]]:
        """Get combat events for a session"""
        combat_events = []
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    """
                    SELECT parsed_data
                    FROM events
                    WHERE session_id = ? AND event_type = 'combat'
                    ORDER BY timestamp
                """,
                    (session_id,),
                )

                async for row in cursor:
                    parsed_data = row[0]
                    if parsed_data:
                        try:
                            data = (
                                json.loads(parsed_data)
                                if isinstance(parsed_data, str)
                                else parsed_data
                            )
                            combat_events.append(data)
                        except json.JSONDecodeError:
                            logger.warning(f"Failed to parse combat data: {parsed_data}")

        except Exception as e:
            logger.error(f"Error getting session combat events: {e}")

        return combat_events
