"""
Database manager for LewtNanny using SQLite for performance
Uses the new data migration service for loading JSON game data
"""

import sqlite3
import asyncio
import aiosqlite
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any
import json
from decimal import Decimal

from src.models.models import Weapon, CraftingBlueprint

logger = logging.getLogger(__name__)


class DatabaseManager:
    def __init__(self, db_path: str = "data/leotnanny.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(exist_ok=True)
        
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
        
        await db.execute("CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_events_session ON events(session_id)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_sessions_activity ON sessions(activity_type)")
        
        await db.execute("CREATE INDEX IF NOT EXISTS idx_weapons_name ON weapons(name)")
        
        logger.debug("Database tables created")
        
        await self.migrate_schema(db)
    
    async def migrate_schema(self, db: aiosqlite.Connection):
        """Migrate database schema if needed"""
        try:
            cursor = await db.execute("PRAGMA table_info(weapons)")
            columns = {row[1]: row for row in await cursor.fetchall()}
            
            needed_columns = {
                'damage': 'ALTER TABLE weapons ADD COLUMN damage REAL DEFAULT 0',
                'reload_time': 'ALTER TABLE weapons ADD COLUMN reload_time REAL DEFAULT 0',
                'name': 'ALTER TABLE weapons ADD COLUMN name TEXT'
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
            with open(weapons_path, 'r', encoding='utf-8') as f:
                weapons_data = json.load(f)

            weapons_migrated = 0
            for weapon_id, weapon_info in weapons_data.get('data', {}).items():
                try:
                    damage = float(weapon_info.get('damage', 0))
                    ammo = int(weapon_info.get('ammo', 0))
                    decay = float(weapon_info.get('decay', 0))
                    decay_per_hit = decay / max(1, ammo) if ammo > 0 else decay
                    dps = damage / 3.0
                    eco = (damage / decay_per_hit) if decay_per_hit > 0 else 0

                    await db.execute("""
                        INSERT OR IGNORE INTO weapons (id, name, ammo, decay, weapon_type, dps, eco)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        weapon_id,
                        weapon_id,
                        ammo,
                        decay,
                        weapon_info.get('type', 'Unknown'),
                        dps,
                        eco
                    ))
                    weapons_migrated += 1
                except Exception as e:
                    logger.error(f"Error migrating weapon {weapon_id}: {e}")

            logger.info(f"Legacy migrated {weapons_migrated} weapons")

        crafting_path = self.db_path.parent / "crafting.json"
        if crafting_path.exists():
            with open(crafting_path, 'r', encoding='utf-8') as f:
                crafting_data = json.load(f)

            blueprints_migrated = 0
            for blueprint_id, materials in crafting_data.get('data', {}).items():
                try:
                    result_item = blueprint_id.replace(' Blueprint (L)', '').replace(' Blueprint', '')
                    await db.execute("""
                        INSERT OR IGNORE INTO blueprints (id, name, result_item)
                        VALUES (?, ?, ?)
                    """, (blueprint_id, blueprint_id, result_item))

                    if isinstance(materials, list):
                        for material in materials:
                            if isinstance(material, list) and len(material) >= 2:
                                await db.execute("""
                                    INSERT OR IGNORE INTO blueprint_materials (blueprint_id, material_name, quantity)
                                    VALUES (?, ?, ?)
                                """, (blueprint_id, material[0], int(material[1])))

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
    
    async def get_all_weapons(self) -> List[Weapon]:
        """Get all weapons from database"""
        weapons = []
        
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                SELECT id, name, ammo, decay, weapon_type, dps, eco, range_value, damage, reload_time
                FROM weapons
            """)
            
            async for row in cursor:
                weapons.append(Weapon(
                    id=row[0],
                    name=row[1],
                    ammo=row[2],
                    decay=Decimal(str(row[3])),
                    weapon_type=row[4],
                    dps=Decimal(str(row[5])) if row[5] else None,
                    eco=Decimal(str(row[6])) if row[6] else None,
                    range_=row[7]
                ))
        
        logger.debug(f"Retrieved {len(weapons)} weapons from database")
        return weapons
    
    async def get_weapon_by_name(self, name: str) -> Optional[Weapon]:
        """Get weapon by name or ID"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                SELECT id, name, ammo, decay, weapon_type, dps, eco, range_value
                FROM weapons 
                WHERE name = ? OR id = ?
            """, (name, name))
            
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
                    range_=row[7]
                )
        return None
    
    async def search_weapons(self, query: str, limit: int = 50) -> List[Weapon]:
        """Search weapons by name"""
        weapons = []
        
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                SELECT id, name, ammo, decay, weapon_type, dps, eco, range_value
                FROM weapons 
                WHERE name LIKE ? OR id LIKE ?
                ORDER BY name
                LIMIT ?
            """, (f"%{query}%", f"%{query}%", limit))
            
            async for row in cursor:
                weapons.append(Weapon(
                    id=row[0],
                    name=row[1],
                    ammo=row[2],
                    decay=Decimal(str(row[3])),
                    weapon_type=row[4],
                    dps=Decimal(str(row[5])) if row[5] else None,
                    eco=Decimal(str(row[6])) if row[6] else None,
                    range_=row[7]
                ))
        
        logger.debug(f"Search for '{query}' returned {len(weapons)} weapons")
        return weapons
    
    async def get_weapons_by_type(self, weapon_type: str) -> List[Weapon]:
        """Get weapons by type"""
        weapons = []
        
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                SELECT id, name, ammo, decay, weapon_type, dps, eco, range_value
                FROM weapons
                WHERE weapon_type = ?
                ORDER BY name
            """, (weapon_type,))
            
            async for row in cursor:
                weapons.append(Weapon(
                    id=row[0],
                    name=row[1],
                    ammo=row[2],
                    decay=Decimal(str(row[3])),
                    weapon_type=row[4],
                    dps=Decimal(str(row[5])) if row[5] else None,
                    eco=Decimal(str(row[6])) if row[6] else None,
                    range_=row[7]
                ))
        
        return weapons
    
    async def get_blueprint_by_name(self, name: str) -> Optional[CraftingBlueprint]:
        """Get crafting blueprint by name or ID"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                SELECT id, name, materials, result_item, result_quantity, 
                       skill_required, condition_limit
                FROM crafting_blueprints 
                WHERE name = ? OR id = ?
            """, (name, name))
            
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
                    condition_limit=row[6]
                )
        return None
    
    async def create_session(self, session_id: str, activity_type: str) -> bool:
        """Create a new session"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    INSERT INTO sessions (id, start_time, activity_type, total_cost, total_return, total_markup)
                    VALUES (?, ?, ?, 0, 0, 0)
                """, (session_id, datetime.now(), activity_type))
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
                db.execute("""
                    INSERT INTO sessions (id, start_time, activity_type, total_cost, total_return, total_markup)
                    VALUES (?, ?, ?, 0, 0, 0)
                """, (session_id, datetime.now(), activity_type))
                db.commit()

            logger.info(f"Session created (sync): {session_id}")
            return True

        except Exception as e:
            logger.error(f"Error creating session (sync): {e}")
            return False
    
    async def add_event(self, event_data: Dict[str, Any]) -> bool:
        """Add an event to the database"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    INSERT INTO events (timestamp, event_type, activity_type, raw_message, parsed_data, session_id)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    datetime.now(),
                    event_data.get('event_type'),
                    event_data.get('activity_type'),
                    event_data.get('raw_message'),
                    json.dumps(event_data.get('parsed_data', {})),
                    event_data.get('session_id')
                ))
                await db.commit()

            logger.debug(f"Event added: {event_data.get('event_type')}")
            return True

        except Exception as e:
            logger.error(f"Error adding event: {e}")
            return False

    def add_event_sync(self, event_data: Dict[str, Any]) -> bool:
        """Add an event to the database (synchronous version)"""
        try:
            import sqlite3
            with sqlite3.connect(self.db_path) as db:
                db.execute("""
                    INSERT INTO events (timestamp, event_type, activity_type, raw_message, parsed_data, session_id)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    datetime.now(),
                    event_data.get('event_type'),
                    event_data.get('activity_type'),
                    event_data.get('raw_message'),
                    json.dumps(event_data.get('parsed_data', {})),
                    event_data.get('session_id')
                ))
                db.commit()

            logger.debug(f"Event added (sync): {event_data.get('event_type')}")
            return True

        except Exception as e:
            logger.error(f"Error adding event (sync): {e}")
            return False
    
    async def get_session_stats(self, session_id: str) -> Dict[str, Any]:
        """Get statistics for a session"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute("""
                    SELECT COUNT(*) as event_count,
                           SUM(CASE WHEN event_type = 'combat' THEN 1 ELSE 0 END) as combat_count,
                           SUM(CASE WHEN event_type = 'loot' THEN 1 ELSE 0 END) as loot_count
                    FROM events
                    WHERE session_id = ?
                """, (session_id,))
                
                row = await cursor.fetchone()
                
                if row:
                    return {
                        'session_id': session_id,
                        'event_count': row[0] or 0,
                        'combat_count': row[1] or 0,
                        'loot_count': row[2] or 0
                    }
                
                return {
                    'session_id': session_id,
                    'event_count': 0,
                    'combat_count': 0,
                    'loot_count': 0
                }
        
        except Exception as e:
            logger.error(f"Error getting session stats: {e}")
            return {}
    
    async def get_session_events(self, session_id: str) -> List[Dict[str, Any]]:
        """Get all events for a session"""
        events = []
        
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute("""
                    SELECT id, timestamp, event_type, activity_type, raw_message, parsed_data
                    FROM events
                    WHERE session_id = ?
                    ORDER BY timestamp
                """, (session_id,))
                
                async for row in cursor:
                    events.append({
                        'id': row[0],
                        'timestamp': row[1],
                        'event_type': row[2],
                        'activity_type': row[3],
                        'raw_message': row[4],
                        'parsed_data': json.loads(row[5]) if row[5] else {}
                    })
        
        except Exception as e:
            logger.error(f"Error getting session events: {e}")
        
        return events
    
    async def get_all_sessions(self) -> List[Dict[str, Any]]:
        """Get all sessions"""
        sessions = []
        
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute("""
                    SELECT id, start_time, end_time, activity_type, total_cost, total_return, total_markup
                    FROM sessions
                    ORDER BY start_time DESC
                """)
                
                async for row in cursor:
                    sessions.append({
                        'id': row[0],
                        'start_time': row[1],
                        'end_time': row[2],
                        'activity_type': row[3],
                        'total_cost': row[4] or 0,
                        'total_return': row[5] or 0,
                        'total_markup': row[6] or 0
                    })
        
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
                    (datetime.now(), session_id)
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
