"""Multi-database manager for LewtNanny
Separates game data into dedicated database files for better organization
"""

import asyncio
import logging
from pathlib import Path

import aiosqlite

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages multiple database files for different data categories"""

    def __init__(self, db_dir: Path | None = None):
        from src.utils.paths import ensure_user_data_dir

        if db_dir:
            self.db_dir = db_dir
        else:
            self.db_dir = ensure_user_data_dir()

        self.db_dir.mkdir(parents=True, exist_ok=True)

        self.databases: dict[str, aiosqlite.Connection] = {}

        self.weapons_db = self.db_dir / "weapons.db"
        self.attachments_db = self.db_dir / "attachments.db"
        self.resources_db = self.db_dir / "resources.db"
        self.crafting_db = self.db_dir / "crafting.db"
        self.main_db = self.db_dir / "user_data.db"

        logger.info(f"DatabaseManager initialized with directory: {self.db_dir}")

    async def initialize_all(self):
        """Initialize all databases"""
        logger.info("Initializing all databases...")

        await self._init_weapons_db()
        await self._init_attachments_db()
        await self._init_resources_db()
        await self._init_crafting_db()
        await self._init_main_db()

        logger.info("All databases initialized")

    async def _init_weapons_db(self):
        """Initialize weapons database"""
        async with aiosqlite.connect(self.weapons_db) as db:
            await db.executescript("""
                CREATE TABLE IF NOT EXISTS weapons (
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

                CREATE INDEX IF NOT EXISTS idx_weapons_name ON weapons(name);
                CREATE INDEX IF NOT EXISTS idx_weapons_type ON weapons(weapon_type);
                CREATE INDEX IF NOT EXISTS idx_weapons_dps ON weapons(dps DESC);
                CREATE INDEX IF NOT EXISTS idx_weapons_eco ON weapons(eco DESC);
            """)
            await db.commit()
        logger.debug("Weapons database initialized")

    async def _init_attachments_db(self):
        """Initialize attachments database (includes scopes and sights)"""
        async with aiosqlite.connect(self.attachments_db) as db:
            await db.executescript("""
                CREATE TABLE IF NOT EXISTS attachments (
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

                CREATE INDEX IF NOT EXISTS idx_attachments_name ON attachments(name);
                CREATE INDEX IF NOT EXISTS idx_attachments_type ON attachments(attachment_type);
            """)
            await db.commit()
        logger.debug("Attachments database initialized")

    async def _init_resources_db(self):
        """Initialize resources database"""
        async with aiosqlite.connect(self.resources_db) as db:
            await db.executescript("""
                CREATE TABLE IF NOT EXISTS resources (
                    name TEXT PRIMARY KEY,
                    tt_value REAL DEFAULT 0,
                    decay REAL DEFAULT 0,
                    data_updated TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE INDEX IF NOT EXISTS idx_resources_name ON resources(name);
                CREATE INDEX IF NOT EXISTS idx_resources_tt_value ON resources(tt_value DESC);
            """)
            await db.commit()
        logger.debug("Resources database initialized")

    async def _init_crafting_db(self):
        """Initialize crafting database (blueprints and materials)"""
        async with aiosqlite.connect(self.crafting_db) as db:
            await db.executescript("""
                CREATE TABLE IF NOT EXISTS blueprints (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    result_item TEXT,
                    result_quantity INTEGER DEFAULT 1,
                    skill_required TEXT,
                    condition_limit INTEGER,
                    data_updated TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS blueprint_materials (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    blueprint_id TEXT NOT NULL,
                    material_name TEXT NOT NULL,
                    quantity INTEGER NOT NULL,
                    FOREIGN KEY (blueprint_id) REFERENCES blueprints(id) ON DELETE CASCADE,
                    UNIQUE(blueprint_id, material_name)
                );

                CREATE INDEX IF NOT EXISTS idx_blueprints_name ON blueprints(name);
                CREATE INDEX IF NOT EXISTS idx_blueprint_materials_bp ON blueprint_materials(
                    blueprint_id);
                CREATE INDEX IF NOT EXISTS idx_blueprint_materials_mat ON blueprint_materials(
                    material_name);
            """)
            await db.commit()
        logger.debug("Crafting database initialized")

    async def _init_main_db(self):
        """Initialize main database (user session data only)"""
        async with aiosqlite.connect(self.main_db) as db:
            await db.executescript("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    start_time TIMESTAMP,
                    end_time TIMESTAMP,
                    activity_type TEXT,
                    total_cost REAL,
                    total_return REAL,
                    total_markup REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

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
                );

                CREATE TABLE IF NOT EXISTS markup_config (
                    item_name TEXT PRIMARY KEY,
                    markup_value REAL
                );

                CREATE TABLE IF NOT EXISTS session_loot_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    item_name TEXT,
                    quantity INTEGER,
                    total_value REAL,
                    markup_percent REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES sessions (id)
                );

                CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp);
                CREATE INDEX IF NOT EXISTS idx_events_session ON events(session_id);
                CREATE INDEX IF NOT EXISTS idx_sessions_activity ON sessions(activity_type);
                CREATE INDEX IF NOT EXISTS idx_session_loot_session ON session_loot_items(
                    session_id);
            """)
            await db.commit()
        logger.debug("Main database initialized")

    async def get_weapon_count(self) -> int:
        """Get total weapon count"""
        async with aiosqlite.connect(self.weapons_db) as db:
            cursor = await db.execute("SELECT COUNT(*) FROM weapons")
            row = await cursor.fetchone()
            return row[0] if row else 0

    async def get_attachment_count(self) -> int:
        """Get total attachment count"""
        async with aiosqlite.connect(self.attachments_db) as db:
            cursor = await db.execute("SELECT COUNT(*) FROM attachments")
            row = await cursor.fetchone()
            return row[0] if row else 0

    async def get_resource_count(self) -> int:
        """Get total resource count"""
        async with aiosqlite.connect(self.resources_db) as db:
            cursor = await db.execute("SELECT COUNT(*) FROM resources")
            row = await cursor.fetchone()
            return row[0] if row else 0

    async def get_blueprint_count(self) -> int:
        """Get total blueprint count"""
        async with aiosqlite.connect(self.crafting_db) as db:
            cursor = await db.execute("SELECT COUNT(*) FROM blueprints")
            row = await cursor.fetchone()
            return row[0] if row else 0

    async def get_counts(self) -> dict[str, int]:
        """Get counts of all data tables"""
        return {
            "weapons": await self.get_weapon_count(),
            "attachments": await self.get_attachment_count(),
            "resources": await self.get_resource_count(),
            "blueprints": await self.get_blueprint_count(),
        }

    async def close_all(self):
        """Close all database connections"""
        for name, db in self.databases.items():
            try:
                await db.close()
            except Exception as e:
                logger.error(f"Error closing database {name}: {e}")
        self.databases.clear()
        logger.info("All database connections closed")


class WeaponsDatabase:
    """Database operations for weapons"""

    def __init__(self, db_path: Path | None = None):
        from src.utils.paths import ensure_user_data_dir

        if db_path:
            self.db_path = db_path
        else:
            self.db_path = ensure_user_data_dir() / "weapons.db"

    async def get_all_weapons(self) -> list:
        """Get all weapons"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM weapons ORDER BY name")
            weapons = []
            async for row in cursor:
                weapons.append(dict(row))
            return weapons

    async def get_weapon_by_name(self, name: str) -> dict | None:
        """Get weapon by name"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM weapons WHERE name = ? LIMIT 1", (name,))
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def search_weapons(self, query: str, limit: int = 50) -> list:
        """Search weapons by name"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                """
                SELECT * FROM weapons
                WHERE name LIKE ?
                ORDER BY name
                LIMIT ?
            """,
                (f"%{query}%", limit),
            )
            weapons = []
            async for row in cursor:
                weapons.append(dict(row))
            return weapons

    async def get_weapons_by_type(self, weapon_type: str) -> list:
        """Get weapons by type"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                """
                SELECT * FROM weapons
                WHERE weapon_type = ?
                ORDER BY dps DESC
            """,
                (weapon_type,),
            )
            weapons = []
            async for row in cursor:
                weapons.append(dict(row))
            return weapons

    async def get_best_weapons_by_dps(self, limit: int = 10) -> list:
        """Get top weapons by DPS"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                """
                SELECT * FROM weapons
                WHERE dps > 0
                ORDER BY dps DESC
                LIMIT ?
            """,
                (limit,),
            )
            weapons = []
            async for row in cursor:
                weapons.append(dict(row))
            return weapons

    async def clear_all(self):
        """Clear all weapons"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM weapons")
            await db.commit()

    async def insert_weapon(self, weapon_data: dict):
        """Insert a single weapon"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT OR REPLACE INTO weapons
                (id, name, ammo, decay, weapon_type, dps, eco, range_value,
                 damage, reload_time, hits, data_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    weapon_data.get("id"),
                    weapon_data.get("name"),
                    weapon_data.get("ammo", 0),
                    weapon_data.get("decay", 0),
                    weapon_data.get("weapon_type"),
                    weapon_data.get("dps"),
                    weapon_data.get("eco"),
                    weapon_data.get("range_value", 0),
                    weapon_data.get("damage", 0),
                    weapon_data.get("reload_time", 0),
                    weapon_data.get("hits", 0),
                    weapon_data.get("data_updated"),
                ),
            )
            await db.commit()


class AttachmentsDatabase:
    """Database operations for attachments"""

    def __init__(self, db_path: Path | None = None):
        from src.utils.paths import ensure_user_data_dir

        if db_path:
            self.db_path = db_path
        else:
            self.db_path = ensure_user_data_dir() / "attachments.db"

    async def get_all_attachments(self) -> list:
        """Get all attachments"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM attachments ORDER BY name")
            attachments = []
            async for row in cursor:
                attachments.append(dict(row))
            return attachments

    async def get_attachments_by_type(self, attachment_type: str) -> list:
        """Get attachments by type"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                """
                SELECT * FROM attachments
                WHERE attachment_type = ?
                ORDER BY name
            """,
                (attachment_type,),
            )
            attachments = []
            async for row in cursor:
                attachments.append(dict(row))
            return attachments

    async def search_attachments(self, query: str) -> list:
        """Search attachments by name"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                """
                SELECT * FROM attachments
                WHERE name LIKE ?
                ORDER BY name
            """,
                (f"%{query}%",),
            )
            attachments = []
            async for row in cursor:
                attachments.append(dict(row))
            return attachments

    async def get_attachment_by_name(self, name: str) -> dict | None:
        """Get attachment by name"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM attachments WHERE name = ? LIMIT 1", (name,))
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def clear_all(self):
        """Clear all attachments"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM attachments")
            await db.commit()

    async def insert_attachment(self, attachment_data: dict):
        """Insert a single attachment"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT OR REPLACE INTO attachments
                (id, name, attachment_type, ammo, decay, damage_bonus, ammo_bonus,
                 decay_modifier, economy_bonus, range_bonus, data_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    attachment_data.get("id"),
                    attachment_data.get("name"),
                    attachment_data.get("attachment_type"),
                    attachment_data.get("ammo", 0),
                    attachment_data.get("decay", 0),
                    attachment_data.get("damage_bonus", 0),
                    attachment_data.get("ammo_bonus", 0),
                    attachment_data.get("decay_modifier", 0),
                    attachment_data.get("economy_bonus", 0),
                    attachment_data.get("range_bonus", 0),
                    attachment_data.get("data_updated"),
                ),
            )
            await db.commit()


class ResourcesDatabase:
    """Database operations for resources"""

    def __init__(self, db_path: Path | None = None):
        from src.utils.paths import ensure_user_data_dir

        if db_path:
            self.db_path = db_path
        else:
            self.db_path = ensure_user_data_dir() / "resources.db"

    async def get_all_resources(self) -> list:
        """Get all resources"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM resources ORDER BY name")
            resources = []
            async for row in cursor:
                resources.append(dict(row))
            return resources

    async def get_resource_by_name(self, name: str) -> dict | None:
        """Get resource by name"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM resources WHERE name = ? LIMIT 1", (name,))
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def search_resources(self, query: str, limit: int = 50) -> list:
        """Search resources by name"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                """
                SELECT * FROM resources
                WHERE name LIKE ?
                ORDER BY name
                LIMIT ?
            """,
                (f"%{query}%", limit),
            )
            resources = []
            async for row in cursor:
                resources.append(dict(row))
            return resources

    async def get_resources_by_tt_value(self, min_tt: float = 0, max_tt: float = 1000) -> list:
        """Get resources within TT value range"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                """
                SELECT * FROM resources
                WHERE tt_value BETWEEN ? AND ?
                ORDER BY tt_value DESC
            """,
                (min_tt, max_tt),
            )
            resources = []
            async for row in cursor:
                resources.append(dict(row))
            return resources

    async def clear_all(self):
        """Clear all resources"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM resources")
            await db.commit()

    async def insert_resource(self, resource_data: dict):
        """Insert a single resource"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT OR REPLACE INTO resources
                (name, tt_value, decay, data_updated)
                VALUES (?, ?, ?, ?)
            """,
                (
                    resource_data.get("name"),
                    resource_data.get("tt_value", 0),
                    resource_data.get("decay", 0),
                    resource_data.get("data_updated"),
                ),
            )
            await db.commit()


class CraftingDatabase:
    """Database operations for crafting blueprints"""

    def __init__(self, db_path: Path | None = None):
        from src.utils.paths import ensure_user_data_dir

        if db_path:
            self.db_path = db_path
        else:
            self.db_path = ensure_user_data_dir() / "crafting.db"

    async def get_all_blueprints(self) -> list:
        """Get all blueprints with materials"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM blueprints ORDER BY name")
            blueprints = []
            async for row in cursor:
                bp = dict(row)
                bp["materials"] = await self._get_blueprint_materials(db, row["id"])
                blueprints.append(bp)
            return blueprints

    async def get_blueprint_by_name(self, name: str) -> dict | None:
        """Get blueprint by name with materials"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM blueprints WHERE name = ? LIMIT 1", (name,))
            row = await cursor.fetchone()
            if not row:
                return None
            bp = dict(row)
            bp["materials"] = await self._get_blueprint_materials(db, row["id"])
            return bp

    async def search_blueprints(self, query: str) -> list:
        """Search blueprints by name"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                """
                SELECT * FROM blueprints
                WHERE name LIKE ?
                ORDER BY name
            """,
                (f"%{query}%",),
            )
            blueprints = []
            async for row in cursor:
                bp = dict(row)
                bp["materials"] = await self._get_blueprint_materials(db, row["id"])
                blueprints.append(bp)
            return blueprints

    async def get_blueprints_by_material(self, material_name: str) -> list:
        """Find blueprints that use a specific material"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                """
                SELECT DISTINCT bp.* FROM blueprints bp
                JOIN blueprint_materials bm ON bp.id = bm.blueprint_id
                WHERE bm.material_name LIKE ?
                ORDER BY bp.name
            """,
                (f"%{material_name}%",),
            )
            blueprints = []
            async for row in cursor:
                bp = dict(row)
                bp["materials"] = await self._get_blueprint_materials(db, row["id"])
                blueprints.append(bp)
            return blueprints

    async def _get_blueprint_materials(self, db: aiosqlite.Connection, blueprint_id: str) -> list:
        """Get materials for a blueprint"""
        cursor = await db.execute(
            """
            SELECT * FROM blueprint_materials WHERE blueprint_id = ?
        """,
            (blueprint_id,),
        )
        materials = []
        async for row in cursor:
            materials.append(dict(row))
        return materials

    async def clear_all(self):
        """Clear all blueprints and materials"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM blueprint_materials")
            await db.execute("DELETE FROM blueprints")
            await db.commit()

    async def insert_blueprint(self, blueprint_data: dict):
        """Insert a single blueprint"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT OR REPLACE INTO blueprints
                (id, name, result_item, result_quantity, skill_required,
                 condition_limit, data_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    blueprint_data.get("id"),
                    blueprint_data.get("name"),
                    blueprint_data.get("result_item"),
                    blueprint_data.get("result_quantity", 1),
                    blueprint_data.get("skill_required"),
                    blueprint_data.get("condition_limit"),
                    blueprint_data.get("data_updated"),
                ),
            )
            await db.commit()

    async def insert_blueprint_material(self, blueprint_id: str, material_name: str, quantity: int):
        """Insert a blueprint material"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT OR IGNORE INTO blueprint_materials
                (blueprint_id, material_name, quantity)
                VALUES (?, ?, ?)
            """,
                (blueprint_id, material_name, quantity),
            )
            await db.commit()


async def initialize_separate_databases():
    """Initialize all separate databases"""
    manager = DatabaseManager()
    await manager.initialize_all()
    return manager


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    print("Initializing separate databases...")
    manager = asyncio.run(initialize_separate_databases())

    counts = asyncio.run(manager.get_counts())
    print("\nDatabase counts:")
    for db_name, count in counts.items():
        print(f"  {db_name}: {count}")

    print("\nSeparate databases initialized successfully!")
