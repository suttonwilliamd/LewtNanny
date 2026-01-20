"""
Database manager for LewtNanny using SQLite for performance
"""

import sqlite3
import asyncio
import aiosqlite
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any
import json
from decimal import Decimal

from src.models.models import Weapon, CraftingBlueprint


class DatabaseManager:
    def __init__(self, db_path: str = "data/leotnanny.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(exist_ok=True)
        
    async def initialize(self):
        """Initialize database and create tables"""
        async with aiosqlite.connect(self.db_path) as db:
            await self.create_tables(db)
            await self.migrate_json_data(db)
            await db.commit()
    
    async def create_tables(self, db: aiosqlite.Connection):
        """Create all necessary database tables"""
        
        # Weapons table
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
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Crafting blueprints table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS crafting_blueprints (
                id TEXT PRIMARY KEY,
                name TEXT,
                materials TEXT,  -- JSON array of [name, quantity]
                result_item TEXT,
                result_quantity INTEGER,
                skill_required TEXT,
                condition_limit INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Sessions table
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
        
        # Events table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP,
                event_type TEXT,
                activity_type TEXT,
                raw_message TEXT,
                parsed_data TEXT,  -- JSON
                session_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessions (id)
            )
        """)
        
        # Create indexes for performance
        await db.execute("CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_events_session ON events(session_id)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_sessions_activity ON sessions(activity_type)")
        
    async def migrate_json_data(self, db: aiosqlite.Connection):
        """Migrate data from JSON files to SQLite"""
        
        # Check if data already exists
        cursor = await db.execute("SELECT COUNT(*) FROM weapons")
        weapon_count = (await cursor.fetchone())[0]
        
        if weapon_count > 0:
            return  # Data already migrated
        
        # Migrate weapons
        weapons_path = Path("weapons.json")
        if weapons_path.exists():
            with open(weapons_path, 'r', encoding='utf-8') as f:
                weapons_data = json.load(f)
                
            for weapon_id, weapon_info in weapons_data.get('data', {}).items():
                await db.execute("""
                    INSERT INTO weapons (id, name, ammo, decay, weapon_type)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    weapon_id,
                    weapon_id,  # Use ID as name for now
                    weapon_info.get('ammo', 0),
                    float(weapon_info.get('decay', 0)),
                    weapon_info.get('type', 'Unknown')
                ))
        
        # Migrate crafting blueprints
        crafting_path = Path("crafting.json")
        if crafting_path.exists():
            with open(crafting_path, 'r', encoding='utf-8') as f:
                crafting_data = json.load(f)
                
            for blueprint_id, materials in crafting_data.get('data', {}).items():
                await db.execute("""
                    INSERT INTO crafting_blueprints (id, name, materials)
                    VALUES (?, ?, ?)
                """, (
                    blueprint_id,
                    blueprint_id,  # Use ID as name for now
                    json.dumps(materials)
                ))
    
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
    
    async def search_weapons(self, query: str, limit: int = 10) -> List[Weapon]:
        """Search weapons by name"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                SELECT id, name, ammo, decay, weapon_type, dps, eco, range_value
                FROM weapons 
                WHERE name LIKE ? OR id LIKE ?
                ORDER BY name
                LIMIT ?
            """, (f"%{query}%", f"%{query}%", limit))
            
            weapons = []
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
            return True
        except Exception:
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
            return True
        except Exception as e:
            print(f"Error adding event: {e}")
            return False