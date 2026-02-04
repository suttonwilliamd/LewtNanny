"""High-performance data access layer for game data
Uses separate database files for each data category
"""

import asyncio
import logging
from decimal import Decimal
from pathlib import Path
from typing import Any

import aiosqlite

from src.models.game_data import (
    Attachment,
    AttachmentStats,
    Blueprint,
    BlueprintMaterial,
    EnhancedWeaponStats,
    Resource,
    Weapon,
    WeaponStats,
)
from src.utils.paths import ensure_user_data_dir

logger = logging.getLogger(__name__)


class GameDataService:
    """Async data access service for game data using separate databases"""

    def __init__(self, db_dir: Path = None):
        if db_dir is None:
            db_dir = ensure_user_data_dir()
        self.db_dir = db_dir

        self.weapons_db = db_dir / "weapons.db"
        self.attachments_db = db_dir / "attachments.db"
        self.resources_db = db_dir / "resources.db"
        self.crafting_db = db_dir / "crafting.db"

    async def get_counts(self) -> dict[str, int]:
        """Get counts of all data tables"""
        counts = {}

        for db_path, table_name in [
            (self.weapons_db, 'weapons'),
            (self.attachments_db, 'attachments'),
            (self.resources_db, 'resources'),
            (self.crafting_db, 'blueprints')
        ]:
            if db_path.exists():
                async with aiosqlite.connect(db_path) as db:
                    cursor = await db.execute(f"SELECT COUNT(*) FROM {table_name}")
                    result = await cursor.fetchone()
                    counts[table_name] = result[0] if result else 0

        return counts

    async def get_all_weapons(self) -> list[Weapon]:
        """Get all weapons from weapons database"""
        weapons = []
        async with aiosqlite.connect(self.weapons_db) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM weapons ORDER BY name")

            async for row in cursor:
                weapons.append(self._row_to_weapon(row))
        return weapons

    async def get_weapon_by_name(self, name: str) -> Weapon | None:
        """Get weapon by exact name match from weapons database"""
        async with aiosqlite.connect(self.weapons_db) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM weapons WHERE name = ? LIMIT 1",
                (name,)
            )
            row = await cursor.fetchone()
            return self._row_to_weapon(row) if row else None

    async def search_weapons(self, query: str, limit: int = 50) -> list[Weapon]:
        """Search weapons by name from weapons database"""
        weapons = []
        async with aiosqlite.connect(self.weapons_db) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("""
                SELECT * FROM weapons
                WHERE name LIKE ?
                ORDER BY name
                LIMIT ?
            """, (f"%{query}%", limit))

            async for row in cursor:
                weapons.append(self._row_to_weapon(row))
        return weapons

    async def get_weapons_by_type(self, weapon_type: str) -> list[Weapon]:
        """Get weapons by type from weapons database"""
        weapons = []
        async with aiosqlite.connect(self.weapons_db) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("""
                SELECT * FROM weapons
                WHERE weapon_type = ?
                ORDER BY dps DESC
            """, (weapon_type,))

            async for row in cursor:
                weapons.append(self._row_to_weapon(row))
        return weapons

    async def get_best_weapons_by_dps(self, limit: int = 10) -> list[Weapon]:
        """Get top weapons by DPS from weapons database"""
        weapons = []
        async with aiosqlite.connect(self.weapons_db) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("""
                SELECT * FROM weapons
                WHERE dps > 0
                ORDER BY dps DESC
                LIMIT ?
            """, (limit,))

            async for row in cursor:
                weapons.append(self._row_to_weapon(row))
        return weapons

    async def get_best_weapons_by_eco(self, limit: int = 10) -> list[Weapon]:
        """Get top weapons by economy from weapons database"""
        weapons = []
        async with aiosqlite.connect(self.weapons_db) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("""
                SELECT * FROM weapons
                WHERE eco > 0
                ORDER BY eco DESC
                LIMIT ?
            """, (limit,))

            async for row in cursor:
                weapons.append(self._row_to_weapon(row))
        return weapons

    async def get_weapon_stats(self, weapon_name: str) -> WeaponStats | None:
        """Get detailed weapon stats for calculations"""
        weapon = await self.get_weapon_by_name(weapon_name)
        if not weapon:
            return None

        return WeaponStats(
            id=weapon.id,
            name=weapon.name,
            damage=weapon.damage if weapon.damage else Decimal('15'),
            ammo_burn=Decimal(weapon.ammo / 100) if weapon.ammo > 0 else Decimal('0.1'),
            decay=weapon.decay,
            hits=weapon.hits if weapon.hits > 0 else 30,
            range=weapon.range_value if weapon.range_value > 0 else 50,
            reload_time=weapon.reload_time if weapon.reload_time else Decimal('3.0'),
            weapon_type=weapon.weapon_type
        )

    async def get_all_attachments(self) -> list[Attachment]:
        """Get all attachments from attachments database"""
        attachments = []
        async with aiosqlite.connect(self.attachments_db) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM attachments ORDER BY name")

            async for row in cursor:
                attachments.append(self._row_to_attachment(row))
        return attachments

    async def get_attachments_by_type(self, attachment_type: str) -> list[Attachment]:
        """Get attachments by type from attachments database"""
        attachments = []
        async with aiosqlite.connect(self.attachments_db) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("""
                SELECT * FROM attachments
                WHERE attachment_type = ?
                ORDER BY name
            """, (attachment_type,))

            async for row in cursor:
                attachments.append(self._row_to_attachment(row))
        return attachments

    async def search_attachments(self, query: str) -> list[Attachment]:
        """Search attachments by name from attachments database"""
        attachments = []
        async with aiosqlite.connect(self.attachments_db) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("""
                SELECT * FROM attachments
                WHERE name LIKE ?
                ORDER BY name
            """, (f"%{query}%",))

            async for row in cursor:
                attachments.append(self._row_to_attachment(row))
        return attachments

    async def get_attachment_by_name(self, name: str) -> Attachment | None:
        """Get attachment by exact name match from attachments database"""
        async with aiosqlite.connect(self.attachments_db) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM attachments WHERE name = ? LIMIT 1",
                (name,)
            )
            row = await cursor.fetchone()
            return self._row_to_attachment(row) if row else None

    async def get_attachment_stats(self, attachment_name: str) -> AttachmentStats | None:
        """Get attachment stats for weapon calculations"""
        attachment = await self.get_attachment_by_name(attachment_name)
        if not attachment:
            return None

        return AttachmentStats(
            id=attachment.id,
            name=attachment.name,
            attachment_type=attachment.attachment_type,
            damage_bonus=attachment.damage_bonus,
            ammo_bonus=attachment.ammo_bonus,
            decay_modifier=attachment.decay_modifier,
            economy_bonus=attachment.economy_bonus,
            range_bonus=attachment.range_bonus
        )

    async def get_all_resources(self) -> list[Resource]:
        """Get all resources from resources database"""
        resources = []
        async with aiosqlite.connect(self.resources_db) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM resources ORDER BY name")

            async for row in cursor:
                resources.append(self._row_to_resource(row))
        return resources

    async def get_resource_by_name(self, name: str) -> Resource | None:
        """Get resource by exact name match from resources database"""
        async with aiosqlite.connect(self.resources_db) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM resources WHERE name = ? LIMIT 1",
                (name,)
            )
            row = await cursor.fetchone()
            return self._row_to_resource(row) if row else None

    async def search_resources(self, query: str, limit: int = 50) -> list[Resource]:
        """Search resources by name from resources database"""
        resources = []
        async with aiosqlite.connect(self.resources_db) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("""
                SELECT * FROM resources
                WHERE name LIKE ?
                ORDER BY name
                LIMIT ?
            """, (f"%{query}%", limit))

            async for row in cursor:
                resources.append(self._row_to_resource(row))
        return resources

    async def get_resources_by_tt_value(self, min_tt: float = 0, max_tt: float = 1000) -> list[Resource]:
        """Get resources within TT value range from resources database"""
        resources = []
        async with aiosqlite.connect(self.resources_db) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("""
                SELECT * FROM resources
                WHERE tt_value BETWEEN ? AND ?
                ORDER BY tt_value DESC
            """, (min_tt, max_tt))

            async for row in cursor:
                resources.append(self._row_to_resource(row))
        return resources

    async def get_all_blueprints(self) -> list[Blueprint]:
        """Get all blueprints with materials from crafting database"""
        blueprints = []
        async with aiosqlite.connect(self.crafting_db) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM blueprints ORDER BY name")

            async for row in cursor:
                blueprint = self._row_to_blueprint(row)
                blueprint.materials = await self._get_blueprint_materials(db, row['id'])
                blueprints.append(blueprint)
        return blueprints

    async def get_blueprint_by_name(self, name: str) -> Blueprint | None:
        """Get blueprint by name with materials from crafting database"""
        async with aiosqlite.connect(self.crafting_db) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM blueprints WHERE name = ? LIMIT 1",
                (name,)
            )
            row = await cursor.fetchone()
            if not row:
                return None

            blueprint = self._row_to_blueprint(row)
            blueprint.materials = await self._get_blueprint_materials(db, row['id'])
            return blueprint

    async def search_blueprints(self, query: str) -> list[Blueprint]:
        """Search blueprints by name from crafting database"""
        blueprints = []
        async with aiosqlite.connect(self.crafting_db) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("""
                SELECT * FROM blueprints
                WHERE name LIKE ?
                ORDER BY name
            """, (f"%{query}%",))

            async for row in cursor:
                blueprint = self._row_to_blueprint(row)
                blueprint.materials = await self._get_blueprint_materials(db, row['id'])
                blueprints.append(blueprint)
        return blueprints

    async def get_blueprints_by_material(self, material_name: str) -> list[Blueprint]:
        """Find blueprints that use a specific material"""
        blueprints = []
        async with aiosqlite.connect(self.crafting_db) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("""
                SELECT DISTINCT bp.* FROM blueprints bp
                JOIN blueprint_materials bm ON bp.id = bm.blueprint_id
                WHERE bm.material_name LIKE ?
                ORDER BY bp.name
            """, (f"%{material_name}%",))

            async for row in cursor:
                blueprint = self._row_to_blueprint(row)
                blueprint.materials = await self._get_blueprint_materials(db, row['id'])
                blueprints.append(blueprint)
        return blueprints

    async def calculate_blueprint_cost(self, blueprint_name: str, resource_values: dict[str, float] = None) -> float:
        """Calculate total material cost for a blueprint"""
        blueprint = await self.get_blueprint_by_name(blueprint_name)
        if not blueprint:
            return 0.0

        total_cost = 0.0
        for material in blueprint.materials:
            resource = await self.get_resource_by_name(material.material_name)
            if resource:
                tt_value = float(resource.tt_value)
                total_cost += tt_value * material.quantity
            elif resource_values and material.material_name in resource_values:
                total_cost += resource_values[material.material_name] * material.quantity

        return total_cost

    async def _get_blueprint_materials(self, db: aiosqlite.Connection, blueprint_id: str) -> list[BlueprintMaterial]:
        """Get materials for a blueprint from crafting database"""
        cursor = await db.execute("""
            SELECT * FROM blueprint_materials WHERE blueprint_id = ?
        """, (blueprint_id,))

        materials = []
        async for row in cursor:
            materials.append(BlueprintMaterial(
                blueprint_id=row['blueprint_id'],
                material_name=row['material_name'],
                quantity=row['quantity']
            ))
        return materials

    def _row_to_weapon(self, row) -> Weapon:
        return Weapon(
            id=row['id'],
            name=row['name'],
            ammo=row['ammo'],
            decay=Decimal(str(row['decay'])),
            weapon_type=row['weapon_type'],
            dps=Decimal(str(row['dps'])) if row['dps'] else None,
            eco=Decimal(str(row['eco'])) if row['eco'] else None,
            range_value=row['range_value'],
            damage=Decimal(str(row['damage'])) if row['damage'] else Decimal('0'),
            reload_time=Decimal(str(row['reload_time'])) if row['reload_time'] else Decimal('0'),
            hits=row['hits']
        )

    def _row_to_attachment(self, row) -> Attachment:
        return Attachment(
            id=row['id'],
            name=row['name'],
            attachment_type=row['attachment_type'],
            ammo=row['ammo'],
            decay=Decimal(str(row['decay'])),
            damage_bonus=Decimal(str(row['damage_bonus'])) if row['damage_bonus'] else Decimal('0'),
            ammo_bonus=Decimal(str(row['ammo_bonus'])) if row['ammo_bonus'] else Decimal('0'),
            decay_modifier=Decimal(str(row['decay_modifier'])) if row['decay_modifier'] else Decimal('0'),
            economy_bonus=Decimal(str(row['economy_bonus'])) if row['economy_bonus'] else Decimal('0'),
            range_bonus=row['range_bonus']
        )

    def _row_to_resource(self, row) -> Resource:
        return Resource(
            name=row['name'],
            tt_value=Decimal(str(row['tt_value'])),
            decay=Decimal(str(row['decay'])) if row['decay'] else Decimal('0')
        )

    def _row_to_blueprint(self, row) -> Blueprint:
        return Blueprint(
            id=row['id'],
            name=row['name'],
            materials=[],
            result_item=row['result_item'],
            result_quantity=row['result_quantity'],
            skill_required=row['skill_required'],
            condition_limit=row['condition_limit']
        )


class WeaponCalculator:
    """Calculator for weapon statistics using GameDataService"""

    def __init__(self):
        self.data_service = GameDataService()

    async def calculate_enhanced_stats(
        self,
        weapon_name: str,
        amplifier_name: str | None = None,
        scope_name: str | None = None,
        damage_enhancement: int = 0,
        economy_enhancement: int = 0
    ) -> EnhancedWeaponStats | None:
        """Calculate enhanced weapon statistics"""
        base_weapon = await self.data_service.get_weapon_stats(weapon_name)
        if not base_weapon:
            return None

        damage_multiplier = Decimal('1.0') + (Decimal('0.1') * damage_enhancement)
        economy_multiplier = Decimal('1.0') - (Decimal('0.01') * economy_enhancement)

        enhanced_damage = base_weapon.damage
        enhanced_ammo = base_weapon.ammo_burn
        enhanced_decay = base_weapon.decay

        enhanced_damage *= damage_multiplier
        enhanced_ammo *= damage_multiplier
        enhanced_decay *= economy_multiplier

        if amplifier_name:
            amp_stats = await self.data_service.get_attachment_stats(amplifier_name)
            if amp_stats:
                enhanced_damage += amp_stats.damage_bonus
                enhanced_ammo += amp_stats.ammo_bonus
                enhanced_decay += amp_stats.decay_modifier

        effective_range = base_weapon.range
        if scope_name:
            scope_stats = await self.data_service.get_attachment_stats(scope_name)
            if scope_stats:
                effective_range = base_weapon.range + scope_stats.range_bonus

        ammo_cost = enhanced_ammo / Decimal('10000')
        decay_cost = enhanced_decay
        total_cost_per_shot = ammo_cost + decay_cost

        dps = enhanced_damage / base_weapon.reload_time if base_weapon.reload_time > 0 else Decimal('0')

        total_cost_pec = total_cost_per_shot * Decimal('100')
        damage_per_pec = enhanced_damage / total_cost_pec if total_cost_pec > 0 else Decimal('0')

        return EnhancedWeaponStats(
            base_weapon=base_weapon,
            damage=enhanced_damage,
            ammo_burn=enhanced_ammo,
            decay=enhanced_decay,
            total_cost_per_shot=total_cost_per_shot,
            dps=dps,
            damage_per_ped=damage_per_pec,
            effective_range=effective_range
        )

    async def calculate_session_stats(
        self,
        weapon_name: str,
        shots_fired: int
    ) -> dict[str, Any] | None:
        """Calculate session statistics for a weapon"""
        enhanced = await self.calculate_enhanced_stats(weapon_name)
        if not enhanced:
            return None

        total_ammo_used = enhanced.ammo_burn * shots_fired
        total_decay = enhanced.decay * shots_fired
        total_cost = enhanced.total_cost_per_shot * shots_fired
        total_damage = enhanced.damage * shots_fired

        return {
            'weapon_name': weapon_name,
            'shots_fired': shots_fired,
            'total_ammo_used': float(total_ammo_used),
            'total_decay': float(total_decay),
            'total_cost': float(total_cost),
            'total_damage': float(total_damage),
            'average_cost_per_shot': float(enhanced.total_cost_per_shot),
            'average_dps': float(enhanced.dps),
            'damage_per_ped': float(enhanced.damage_per_ped)
        }


async def main():
    """Test the service"""
    logging.basicConfig(level=logging.INFO)
    service = GameDataService()

    counts = await service.get_counts()
    print("\nDatabase contents:")
    for table, count in counts.items():
        print(f"  {table}: {count}")

    print("\nSample weapons:")
    weapons = await service.get_best_weapons_by_dps(5)
    for w in weapons:
        print(f"  {w.name}: DPS={w.dps}, Eco={w.eco}, Type={w.weapon_type}")

    print("\nSample resources:")
    resources = await service.get_resources_by_tt_value(1, 10)
    for r in resources[:5]:
        print(f"  {r.name}: TT={r.tt_value}")


if __name__ == "__main__":
    asyncio.run(main())
