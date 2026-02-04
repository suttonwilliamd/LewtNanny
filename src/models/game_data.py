"""Game data models for weapons, attachments, resources, and blueprints
Provides typed dataclasses for all game item data
"""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any


@dataclass
class Weapon:
    """Weapon statistics data model"""

    id: str
    name: str
    ammo: int
    decay: Decimal
    weapon_type: str
    dps: Decimal | None = None
    eco: Decimal | None = None
    range_value: int = 0
    damage: Decimal = Decimal("0")
    reload_time: Decimal = Decimal("0")
    hits: int = 0
    data_updated: datetime | None = None

    def __post_init__(self):
        """Post-initialization hook to convert string values to Decimal."""
        if isinstance(self.decay, str):
            self.decay = Decimal(self.decay)
        if self.dps and isinstance(self.dps, str):
            self.dps = Decimal(self.dps)
        if self.eco and isinstance(self.eco, str):
            self.eco = Decimal(self.eco)
        if self.damage and isinstance(self.damage, str):
            self.damage = Decimal(self.damage)
        if self.reload_time and isinstance(self.reload_time, str):
            self.reload_time = Decimal(self.reload_time)


@dataclass
class Attachment:
    """Weapon attachment (amps, scopes, sights) data model"""

    id: str
    name: str
    attachment_type: str
    ammo: int
    decay: Decimal
    damage_bonus: Decimal = Decimal("0")
    ammo_bonus: Decimal = Decimal("0")
    decay_modifier: Decimal = Decimal("0")
    economy_bonus: Decimal = Decimal("0")
    range_bonus: int = 0
    data_updated: datetime | None = None

    def __post_init__(self):
        """Post-initialization hook to convert string values to Decimal."""
        if isinstance(self.decay, str):
            self.decay = Decimal(self.decay)
        if self.damage_bonus and isinstance(self.damage_bonus, str):
            self.damage_bonus = Decimal(self.damage_bonus)
        if self.ammo_bonus and isinstance(self.ammo_bonus, str):
            self.ammo_bonus = Decimal(self.ammo_bonus)
        if self.decay_modifier and isinstance(self.decay_modifier, str):
            self.decay_modifier = Decimal(self.decay_modifier)
        if self.economy_bonus and isinstance(self.economy_bonus, str):
            self.economy_bonus = Decimal(self.economy_bonus)


@dataclass
class Resource:
    """Resource item with TT value"""

    name: str
    tt_value: Decimal
    decay: Decimal = Decimal("0")
    data_updated: datetime | None = None

    def __post_init__(self):
        """Post-initialization hook to convert string values to Decimal."""
        if isinstance(self.tt_value, str):
            self.tt_value = Decimal(self.tt_value)
        if isinstance(self.decay, str):
            self.decay = Decimal(self.decay)


@dataclass
class BlueprintMaterial:
    """Single material requirement for a blueprint"""

    blueprint_id: str
    material_name: str
    quantity: int


@dataclass
class Blueprint:
    """Crafting blueprint with materials"""

    id: str
    name: str
    materials: list[BlueprintMaterial] = field(default_factory=list)
    result_item: str | None = None
    result_quantity: int = 1
    skill_required: str | None = None
    condition_limit: int | None = None
    data_updated: datetime | None = None


@dataclass
class WeaponStats:
    """Detailed weapon statistics for calculations"""

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
        return self.decay + (self.ammo_burn / Decimal("10000"))

    def calculate_base_dps(self) -> Decimal:
        """Calculate base damage per second"""
        if self.reload_time > 0:
            return self.damage / self.reload_time
        return Decimal("0")


@dataclass
class AttachmentStats:
    """Attachment statistics for weapon enhancement calculations"""

    id: str
    name: str
    attachment_type: str
    damage_bonus: Decimal = Decimal("0")
    ammo_bonus: Decimal = Decimal("0")
    decay_modifier: Decimal = Decimal("0")
    economy_bonus: Decimal = Decimal("0")
    range_bonus: int = 0


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
        """Convert to dictionary for JSON serialization"""
        return {
            "damage": float(self.damage),
            "ammo_burn": float(self.ammo_burn),
            "decay": float(self.decay),
            "total_cost_per_shot": float(self.total_cost_per_shot),
            "dps": float(self.dps),
            "damage_per_ped": float(self.damage_per_ped),
            "effective_range": self.effective_range,
            "base_weapon": {
                "name": self.base_weapon.name,
                "damage": float(self.base_weapon.damage),
                "ammo_burn": float(self.base_weapon.ammo_burn),
                "decay": float(self.base_weapon.decay),
                "weapon_type": self.base_weapon.weapon_type,
            },
        }
