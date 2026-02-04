"""Multi-database manager for LewtNanny
Separates static game data from dynamic user data for better performance
"""

import json
import logging
import sqlite3
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Optional

import aiosqlite

from src.models.models import (
    Weapon,
)
from src.utils.paths import ensure_user_data_dir

logger = logging.getLogger(__name__)


class MultiDatabaseManager:
    """Manages multiple specialized databases for better performance"""

    def __init__(self, db_dir: Optional[str] = None):
        if db_dir:
            self.db_dir = Path(db_dir)
        else:
            self.db_dir = ensure_user_data_dir()

        # Define database files
        self.databases = {
            "user_data": self.db_dir / "user_data.db",  # Sessions, events, user settings
            "weapons": self.db_dir / "weapons.db",  # Static weapon data
            "attachments": self.db_dir / "attachments.db",  # Scopes, sights, amplifiers
            "resources": self.db_dir / "resources.db",  # Resource pricing
            "crafting": self.db_dir / "crafting.db",  # Blueprints and recipes
        }

        self.db_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"MultiDatabaseManager initialized with db_dir: {self.db_dir}")

    async def initialize_all(self):
        """Initialize all databases and create tables"""
        logger.info("Initializing all databases...")

        for db_name, db_path in self.databases.items():
            await self._initialize_database(db_name, db_path)

        # Migrate data from JSON files
        await self._migrate_all_json_data()

        logger.info("All databases initialized successfully")

    async def _initialize_database(self, db_name: str, db_path: Path):
        """Initialize a specific database with its schema"""
        async with aiosqlite.connect(db_path) as db:
            if db_name == "user_data":
                await self._create_user_data_schema(db)
            elif db_name == "weapons":
                await self._create_weapons_schema(db)
            elif db_name == "attachments":
                await self._create_attachments_schema(db)
            elif db_name == "resources":
                await self._create_resources_schema(db)
            elif db_name == "crafting":
                await self._create_crafting_schema(db)

            await db.commit()
            logger.debug(f"Database {db_name} initialized at {db_path}")

    async def _create_user_data_schema(self, db: aiosqlite.Connection):
        """Create user data tables (sessions, events, etc.)"""
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

        await db.execute("""
            CREATE TABLE IF NOT EXISTS markup_config (
                item_name TEXT PRIMARY KEY,
                markup_value REAL
            )
        """)

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
                ammo INTEGER,
                decay REAL,
                weapon_type TEXT,
                dps REAL,
                eco REAL,
                range_value INTEGER,
                damage REAL,
                reload_time REAL,
                created_at TEXT,
                updated_at TEXT
            )
        """)

        # Indexes for performance
        await db.execute("CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_events_session ON events(session_id)")
        await db.execute(
            "CREATE INDEX IF NOT EXISTS idx_sessions_activity ON sessions(activity_type)"
        )
        await db.execute(
            "CREATE INDEX IF NOT EXISTS idx_session_loot_session ON session_loot_items(session_id)"
        )
        await db.execute("CREATE INDEX IF NOT EXISTS idx_loadouts_name ON loadouts(name)")
        await db.execute(
            "CREATE INDEX IF NOT EXISTS idx_custom_weapons_name ON custom_weapons(name)"
        )

    async def _create_weapons_schema(self, db: aiosqlite.Connection):
        """Create weapons table"""
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
                data_updated TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        await db.execute("CREATE INDEX IF NOT EXISTS idx_weapons_name ON weapons(name)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_weapons_type ON weapons(weapon_type)")

    async def _create_attachments_schema(self, db: aiosqlite.Connection):
        """Create attachments table (scopes, sights, amplifiers)"""
        await db.execute("""
            CREATE TABLE IF NOT EXISTS attachments (
                id TEXT PRIMARY KEY,
                name TEXT,
                attachment_type TEXT,
                ammo INTEGER,
                decay REAL,
                range_bonus INTEGER DEFAULT 0,
                economy_bonus REAL DEFAULT 0,
                data_updated TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        await db.execute("CREATE INDEX IF NOT EXISTS idx_attachments_name ON attachments(name)")
        await db.execute(
            "CREATE INDEX IF NOT EXISTS idx_attachments_type ON attachments(attachment_type)"
        )

    async def _create_resources_schema(self, db: aiosqlite.Connection):
        """Create resources table"""
        await db.execute("""
            CREATE TABLE IF NOT EXISTS resources (
                name TEXT PRIMARY KEY,
                tt_value REAL,
                decay REAL DEFAULT 0,
                data_updated TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        await db.execute("CREATE INDEX IF NOT EXISTS idx_resources_name ON resources(name)")

    async def _create_crafting_schema(self, db: aiosqlite.Connection):
        """Create crafting tables"""
        await db.execute("""
            CREATE TABLE IF NOT EXISTS blueprints (
                id TEXT PRIMARY KEY,
                name TEXT,
                result_item TEXT,
                result_quantity INTEGER DEFAULT 1,
                skill_required TEXT,
                condition_limit INTEGER,
                data_updated TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS blueprint_materials (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                blueprint_id TEXT,
                material_name TEXT,
                quantity INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (blueprint_id) REFERENCES blueprints (id)
            )
        """)

        await db.execute("CREATE INDEX IF NOT EXISTS idx_blueprints_name ON blueprints(name)")
        await db.execute(
            "CREATE INDEX IF NOT EXISTS idx_blueprint_materials_blueprint ON "
            "blueprint_materials(blueprint_id)"
        )
        await db.execute(
            "CREATE INDEX IF NOT EXISTS idx_blueprint_materials_material ON "
            "blueprint_materials(material_name)"
        )

    async def _migrate_all_json_data(self):
        """Migrate all JSON data to appropriate databases"""
        try:
            from src.services.data_migration_service import DataMigrationService

            migrator = DataMigrationService(str(self.db_dir))

            # Check if migration is needed
            counts = await self.get_all_counts()
            total_game_data = sum(
                counts.get(key, 0) for key in ["weapons", "attachments", "resources", "blueprints"]
            )

            if total_game_data == 0:
                logger.info("No game data found, running migration...")
                migration_counts = await migrator.migrate_all(force=False)
                logger.info(f"Migration complete: {migration_counts}")
            else:
                logger.info(f"Game data already exists: {counts}")

        except ImportError:
            logger.warning("Data migration service not available, using legacy migration")

    async def get_all_counts(self) -> dict[str, int]:
        """Get counts from all databases"""
        counts: dict[str, int] = {}

        try:
            # User data counts
            async with aiosqlite.connect(self.databases["user_data"]) as db:
                cursor = await db.execute("SELECT COUNT(*) FROM sessions")
                row = await cursor.fetchone()
                counts["sessions"] = row[0] if row else 0

                cursor = await db.execute("SELECT COUNT(*) FROM events")
                row = await cursor.fetchone()
                counts["events"] = row[0] if row else 0

            # Game data counts
            async with aiosqlite.connect(self.databases["weapons"]) as db:
                cursor = await db.execute("SELECT COUNT(*) FROM weapons")
                row = await cursor.fetchone()
                counts["weapons"] = row[0] if row else 0

            async with aiosqlite.connect(self.databases["attachments"]) as db:
                cursor = await db.execute("SELECT COUNT(*) FROM attachments")
                row = await cursor.fetchone()
                counts["attachments"] = row[0] if row else 0

            async with aiosqlite.connect(self.databases["resources"]) as db:
                cursor = await db.execute("SELECT COUNT(*) FROM resources")
                row = await cursor.fetchone()
                counts["resources"] = row[0] if row else 0

            async with aiosqlite.connect(self.databases["crafting"]) as db:
                cursor = await db.execute("SELECT COUNT(*) FROM blueprints")
                row = await cursor.fetchone()
                counts["blueprints"] = row[0] if row else 0

                cursor = await db.execute("SELECT COUNT(*) FROM blueprint_materials")
                row = await cursor.fetchone()
                counts["blueprint_materials"] = row[0] if row else 0

        except Exception as e:
            logger.error(f"Error getting counts: {e}")

        return counts

    # Additional methods to maintain compatibility with existing code
    async def get_session_count(self) -> int:
        """Get total session count"""
        try:
            async with aiosqlite.connect(self.databases["user_data"]) as db:
                cursor = await db.execute("SELECT COUNT(*) FROM sessions")
                row = await cursor.fetchone()
                return row[0] if row else 0
        except Exception as e:
            logger.error(f"Error getting session count: {e}")
            return 0

    async def get_weapon_count(self) -> int:
        """Get total weapon count"""
        try:
            async with aiosqlite.connect(self.databases["weapons"]) as db:
                cursor = await db.execute("SELECT COUNT(*) FROM weapons")
                row = await cursor.fetchone()
                return row[0] if row else 0
        except Exception as e:
            logger.error(f"Error getting weapon count: {e}")
            return 0

    async def get_all_sessions(self) -> list[dict[str, Any]]:
        """Get all sessions"""
        sessions = []

        try:
            async with aiosqlite.connect(self.databases["user_data"]) as db:
                cursor = await db.execute("""
                    SELECT id, start_time, end_time, activity_type, total_cost, total_return, total_markup
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

    async def get_session_loot_items(self, session_id: str) -> list[dict[str, Any]]:
        """Get all loot items for a session"""
        items = []
        try:
            async with aiosqlite.connect(self.databases["user_data"]) as db:
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

    async def get_session_counts(self, session_id: str) -> dict[str, int]:
        """Get counts of creatures, globals, and HOFs for a session"""
        try:
            async with aiosqlite.connect(self.databases["user_data"]) as db:
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

    async def update_session_totals(
        self,
        session_id: str,
        total_cost: float,
        total_return: float,
        total_markup: float,
    ):
        """Update session totals"""
        try:
            async with aiosqlite.connect(self.databases["user_data"]) as db:
                await db.execute(
                    """
                    UPDATE sessions SET total_cost = ?, total_return = ?, total_markup = ?, end_time = ?
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

    async def update_session_end(self, session_id: str):
        """Update session end time"""
        try:
            async with aiosqlite.connect(self.databases["user_data"]) as db:
                await db.execute(
                    "UPDATE sessions SET end_time = ? WHERE id = ?",
                    (datetime.now(), session_id),
                )
                await db.commit()

            logger.debug(f"Session end time updated: {session_id}")

        except Exception as e:
            logger.error(f"Error updating session end: {e}")

    async def get_session_stats(self, session_id: str) -> dict[str, Any]:
        """Get statistics for a session"""
        try:
            async with aiosqlite.connect(self.databases["user_data"]) as db:
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
            async with aiosqlite.connect(self.databases["user_data"]) as db:
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

    async def delete_session(self, session_id: str) -> bool:
        """Delete a session and its events"""
        try:
            async with aiosqlite.connect(self.databases["user_data"]) as db:
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
            async with aiosqlite.connect(self.databases["user_data"]) as db:
                await db.execute("DELETE FROM events")
                await db.execute("DELETE FROM sessions")
                await db.commit()

            logger.info("All sessions deleted")

        except Exception as e:
            logger.error(f"Error deleting all sessions: {e}")

    async def get_connection(self, db_name: str) -> aiosqlite.Connection:
        """Get connection to specific database"""
        if db_name not in self.databases:
            raise ValueError(f"Unknown database: {db_name}")
        return aiosqlite.connect(self.databases[db_name])

    async def close_all(self):
        """Close all database connections"""
        logger.info("All database connections closed")

    # User data methods (delegated to user_data.db)
    async def create_session(self, session_id: str, activity_type: str) -> bool:
        """Create a new session"""
        try:
            async with aiosqlite.connect(self.databases["user_data"]) as db:
                await db.execute(
                    """
                    INSERT INTO sessions (id, start_time, activity_type, total_cost, total_return, total_markup)
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

    async def add_event(self, event_data: dict[str, Any]) -> bool:
        """Add an event to database"""
        try:
            async with aiosqlite.connect(self.databases["user_data"]) as db:
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

    # Game data query methods
    async def get_all_weapons(self) -> list[Weapon]:
        """Get all weapons from weapons database"""
        weapons = []

        async with aiosqlite.connect(self.databases["weapons"]) as db:
            cursor = await db.execute("""
                SELECT id, name, ammo, decay, weapon_type, dps, eco, range_value,
                       damage, reload_time
                FROM weapons
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

        return weapons

    async def search_weapons(self, query: str, limit: int = 50) -> list[Weapon]:
        """Search weapons by name"""
        weapons = []

        async with aiosqlite.connect(self.databases["weapons"]) as db:
            cursor = await db.execute(
                """
                SELECT id, name, ammo, decay, weapon_type, dps, eco, range_value, damage, reload_time
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

        return weapons

    def create_session_sync(self, session_id: str, activity_type: str) -> bool:
        """Create a new session (synchronous version)"""
        try:
            with sqlite3.connect(self.databases["user_data"]) as db:
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

    def add_event_sync(self, event_data: dict[str, Any]) -> bool:
        """Add an event to database (synchronous version)"""
        try:
            with sqlite3.connect(self.databases["user_data"]) as db:
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

    def save_session_loot_item_sync(
        self,
        session_id: str,
        item_name: str,
        quantity: int,
        total_value: float,
        markup_percent: float,
    ) -> bool:
        """Save or update a loot item for a session (synchronous version)"""
        try:
            with sqlite3.connect(self.databases["user_data"]) as db:
                db.execute(
                    """
                    INSERT OR REPLACE INTO session_loot_items
                    (session_id, item_name, quantity, total_value, markup_percent)
                    VALUES (?, ?, ?, ?, ?)
                """,
                    (session_id, item_name, quantity, total_value, markup_percent),
                )
                db.commit()
            logger.debug(f"Saved loot item (sync): {item_name} for session {session_id}")
            return True
        except Exception as e:
            logger.error(f"Error saving session loot item (sync): {e}")
            return False

    async def get_session_skills(self, session_id: str) -> list[dict[str, Any]]:
        """Get skill gains for a session"""
        skills = []
        try:
            async with aiosqlite.connect(self.databases["user_data"]) as db:
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
            async with aiosqlite.connect(self.databases["user_data"]) as db:
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
