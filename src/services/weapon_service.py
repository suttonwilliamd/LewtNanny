"""Weapon data models and calculations
Separated business logic from UI components
"""

import json
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any


@dataclass
class WeaponStats:
    """Weapon statistics data model"""
    id: str
    name: str
    damage: Decimal
    ammo_burn: Decimal
    decay: Decimal
    hits: int
    range: int
    reload_time: Decimal
    weapon_type: str

    def calculate_base_cost_per_shot(self) -> Decimal:
        """Calculate base cost per shot without attachments"""
        return self.decay + (self.ammo_burn / Decimal('10000'))

    def calculate_base_dps(self) -> Decimal:
        """Calculate base damage per second"""
        if self.reload_time > 0:
            return self.damage / self.reload_time
        return Decimal('0')

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'damage': float(self.damage),
            'ammo_burn': float(self.ammo_burn),
            'decay': float(self.decay),
            'hits': self.hits,
            'range': self.range,
            'reload_time': float(self.reload_time),
            'weapon_type': self.weapon_type
        }


@dataclass
class AttachmentStats:
    """Attachment statistics data model"""
    id: str
    name: str
    attachment_type: str
    damage_bonus: Decimal
    ammo_bonus: Decimal
    decay_modifier: Decimal
    economy_bonus: Decimal

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'type': self.attachment_type,
            'damage_bonus': float(self.damage_bonus),
            'ammo_bonus': float(self.ammo_bonus),
            'decay_modifier': float(self.decay_modifier),
            'economy_bonus': float(self.economy_bonus)
        }


@dataclass
class EnhancedWeaponStats:
    """Enhanced weapon statistics after applying attachments and enhancements"""
    base_weapon: WeaponStats
    damage: Decimal
    ammo_burn: Decimal
    decay: Decimal
    total_cost_per_shot: Decimal
    dps: Decimal
    damage_per_ped: Decimal
    effective_range: int

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary"""
        return {
            'weapon_name': self.base_weapon.name,
            'damage': float(self.damage),
            'ammo_burn': float(self.ammo_burn),
            'decay': float(self.decay),
            'total_cost_per_shot': float(self.total_cost_per_shot),
            'dps': float(self.dps),
            'damage_per_ped': float(self.damage_per_ped),
            'effective_range': self.effective_range,
            'base_weapon': self.base_weapon.to_dict()
        }


class WeaponCalculator:
    """Calculator for weapon statistics and costs"""

    @staticmethod
    def calculate_enhanced_stats(
        base_weapon: WeaponStats,
        amplifier: AttachmentStats | None = None,
        scope: AttachmentStats | None = None,
        damage_enhancement: int = 0,
        economy_enhancement: int = 0
    ) -> EnhancedWeaponStats:
        """Calculate enhanced weapon statistics"""
        # Calculate enhancement multipliers
        damage_multiplier = Decimal('1.0') + (Decimal('0.1') * damage_enhancement)
        economy_multiplier = Decimal('1.0') - (Decimal('0.01') * economy_enhancement)

        # Start with base stats
        enhanced_damage = base_weapon.damage
        enhanced_ammo = base_weapon.ammo_burn
        enhanced_decay = base_weapon.decay

        # Apply damage enhancement
        enhanced_damage *= damage_multiplier
        enhanced_ammo *= damage_multiplier

        # Apply economy enhancement to decay
        enhanced_decay *= economy_multiplier

        # Apply amplifier
        if amplifier:
            enhanced_damage += amplifier.damage_bonus
            enhanced_ammo += amplifier.ammo_bonus
            enhanced_decay += amplifier.decay_modifier

        # Apply scope effects (typically range and accuracy)
        effective_range = base_weapon.range
        if scope:
            # Scopes typically increase effective range
            effective_range = int(base_weapon.range * Decimal('1.2'))

        # Calculate costs
        ammo_cost = enhanced_ammo / Decimal('10000')
        decay_cost = enhanced_decay
        total_cost_per_shot = ammo_cost + decay_cost

        # Calculate performance metrics
        dps = enhanced_damage / base_weapon.reload_time if base_weapon.reload_time > 0 else Decimal('0')

        # Calculate DPP (Damage per PEC) - 100 PEC = 1 PED
        # DPP = Total Damage / Total Cost in PEC
        total_cost_pec = total_cost_per_shot * Decimal('100')  # Convert PED to PEC
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

    @staticmethod
    def calculate_session_stats(
        weapon: EnhancedWeaponStats,
        shots_fired: int
    ) -> dict[str, Any]:
        """Calculate session statistics"""
        total_ammo_used = weapon.ammo_burn * shots_fired
        total_decay = weapon.decay * shots_fired
        total_cost = weapon.total_cost_per_shot * shots_fired
        total_damage = weapon.damage * shots_fired

        return {
            'shots_fired': shots_fired,
            'total_ammo_used': float(total_ammo_used),
            'total_decay': float(total_decay),
            'total_cost': float(total_cost),
            'total_damage': float(total_damage),
            'average_cost_per_shot': float(weapon.total_cost_per_shot),
            'average_dps': float(weapon.dps),
            'damage_per_ped': float(weapon.damage_per_ped)
        }


class WeaponDataManager:
    """Manager for weapon and attachment data"""

    def __init__(self, data_path: Path | None = None):
        self.data_path = data_path or Path.cwd()
        self.weapons: dict[str, WeaponStats] = {}
        self.attachments: dict[str, AttachmentStats] = {}

    def load_weapons_from_dict(self, weapons_data: list[dict[str, Any]]):
        """Load weapons from dictionary data"""
        for weapon_dict in weapons_data:
            weapon = WeaponStats(
                id=str(weapon_dict.get('id', '')),
                name=weapon_dict.get('name', ''),
                damage=Decimal(str(weapon_dict.get('damage', 0))),
                ammo_burn=Decimal(str(weapon_dict.get('ammo_burn', 0))),
                decay=Decimal(str(weapon_dict.get('decay', 0))),
                hits=int(weapon_dict.get('hits', 0)),
                range=int(weapon_dict.get('range', 0)),
                reload_time=Decimal(str(weapon_dict.get('reload_time', 0))),
                weapon_type=weapon_dict.get('weapon_type', '')
            )
            self.weapons[weapon.id] = weapon

    def load_weapons_from_json(self, file_path: str):
        """Load weapons from JSON file"""
        try:
            with open(file_path, encoding='utf-8') as f:
                data = json.load(f)
                weapons_list = data if isinstance(data, list) else data.get('weapons', [])
                self.load_weapons_from_dict(weapons_list)
        except Exception as e:
            print(f"Error loading weapons from {file_path}: {e}")

    def load_attachments_from_dict(self, attachments_data: list[dict[str, Any]]):
        """Load attachments from dictionary data"""
        for attachment_dict in attachments_data:
            attachment = AttachmentStats(
                id=str(attachment_dict.get('id', '')),
                name=attachment_dict.get('name', ''),
                attachment_type=attachment_dict.get('type', ''),
                damage_bonus=Decimal(str(attachment_dict.get('damage_bonus', 0))),
                ammo_bonus=Decimal(str(attachment_dict.get('ammo_bonus', 0))),
                decay_modifier=Decimal(str(attachment_dict.get('decay_modifier', 0))),
                economy_bonus=Decimal(str(attachment_dict.get('economy_bonus', 0)))
            )
            self.attachments[attachment.id] = attachment

    def load_attachments_from_json(self, file_path: str):
        """Load attachments from JSON file"""
        try:
            with open(file_path, encoding='utf-8') as f:
                data = json.load(f)
                attachments_list = data if isinstance(data, list) else data.get('data', [])
                self.load_attachments_from_dict(attachments_list)
        except Exception as e:
            print(f"Error loading attachments from {file_path}: {e}")

    def get_weapon_by_id(self, weapon_id: str) -> WeaponStats | None:
        """Get weapon by ID"""
        return self.weapons.get(weapon_id)

    def get_attachment_by_id(self, attachment_id: str) -> AttachmentStats | None:
        """Get attachment by ID"""
        return self.attachments.get(attachment_id)

    def get_weapons_by_type(self, weapon_type: str) -> list[WeaponStats]:
        """Get weapons by type"""
        return [w for w in self.weapons.values() if w.weapon_type == weapon_type]

    def get_attachments_by_type(self, attachment_type: str) -> list[AttachmentStats]:
        """Get attachments by type"""
        return [a for a in self.attachments.values() if a.attachment_type == attachment_type]

    def search_weapons(self, query: str) -> list[WeaponStats]:
        """Search weapons by name"""
        query_lower = query.lower()
        return [w for w in self.weapons.values() if query_lower in w.name.lower()]

    def search_attachments(self, query: str) -> list[AttachmentStats]:
        """Search attachments by name"""
        query_lower = query.lower()
        return [a for a in self.attachments.values() if query_lower in a.name.lower()]

    def get_all_weapons(self) -> list[WeaponStats]:
        """Get all weapons"""
        return list(self.weapons.values())

    def get_all_attachments(self) -> list[AttachmentStats]:
        """Get all attachments"""
        return list(self.attachments.values())

    def load_sample_data(self):
        """Load sample data for demonstration"""
        # Sample weapons
        sample_weapons = [
            {
                'id': '1', 'name': 'Korss H400 (L)', 'damage': 28, 'ammo_burn': 11,
                'decay': 0.10, 'hits': 36, 'range': 55, 'reload_time': 3.0, 'weapon_type': 'Pistol'
            },
            {
                'id': '2', 'name': 'HL11 (L)', 'damage': 32, 'ammo_burn': 16,
                'decay': 0.20, 'hits': 27, 'range': 58, 'reload_time': 3.2, 'weapon_type': 'Rifle'
            },
            {
                'id': '3', 'name': 'Opalo', 'damage': 12, 'ammo_burn': 6,
                'decay': 0.03, 'hits': 30, 'range': 45, 'reload_time': 2.8, 'weapon_type': 'Pistol'
            },
            {
                'id': '4', 'name': 'MMA', 'damage': 15, 'ammo_burn': 8,
                'decay': 0.05, 'hits': 28, 'range': 50, 'reload_time': 2.5, 'weapon_type': 'Rifle'
            }
        ]

        # Sample attachments
        sample_attachments = [
            {
                'id': 'a1', 'name': 'A106 Amplifier', 'type': 'amplifier',
                'damage_bonus': 0.5, 'ammo_bonus': 0, 'decay_modifier': 0.25, 'economy_bonus': 0
            },
            {
                'id': 'a2', 'name': 'A204 Amplifier', 'type': 'amplifier',
                'damage_bonus': 1.0, 'ammo_bonus': 0, 'decay_modifier': 0.50, 'economy_bonus': 0
            },
            {
                'id': 's1', 'name': 'Laser Sight', 'type': 'scope',
                'damage_bonus': 0, 'ammo_bonus': 0, 'decay_modifier': 0.01, 'economy_bonus': 0.1
            },
            {
                'id': 's2', 'name': 'Optical Scope', 'type': 'scope',
                'damage_bonus': 0, 'ammo_bonus': 0, 'decay_modifier': 0.02, 'economy_bonus': 0.2
            }
        ]

        self.load_weapons_from_dict(sample_weapons)
        self.load_attachments_from_dict(sample_attachments)
