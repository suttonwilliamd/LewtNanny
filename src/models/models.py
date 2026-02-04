"""Core data models for LewtNanny"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any


class EventType(Enum):
    COMBAT = "combat"
    LOOT = "loot"
    CRAFTING = "crafting"
    SKILL_GAIN = "skill_gain"
    GLOBAL = "global"
    HOF = "hof"
    SYSTEM = "system"
    TRADE = "trade"
    LOCATION = "location"


class ActivityType(Enum):
    HUNTING = "hunting"
    CRAFTING = "crafting"
    MINING = "mining"
    TRADING = "trading"
    EXPLORING = "exploring"


@dataclass
class Weapon:
    id: str
    name: str
    ammo: int
    decay: Decimal
    weapon_type: str
    dps: Decimal | None = None
    eco: Decimal | None = None
    range_: int | None = None

    def __post_init__(self):
        """Post-initialization hook to convert string values to Decimal."""
        # Convert string values to Decimal
        if isinstance(self.decay, str):
            self.decay = Decimal(self.decay)
        if self.dps and isinstance(self.dps, str):
            self.dps = Decimal(self.dps)
        if self.eco and isinstance(self.eco, str):
            self.eco = Decimal(self.eco)


@dataclass
class CraftingBlueprint:
    id: str
    name: str
    materials: list[tuple]  # List of (name, quantity)
    result_item: str | None = None
    result_quantity: int | None = None
    skill_required: str | None = None
    condition_limit: int | None = None


@dataclass
class GameEvent:
    id: int | None
    timestamp: datetime
    event_type: EventType
    activity_type: ActivityType
    raw_message: str
    parsed_data: dict[str, Any]
    session_id: str


@dataclass
class Session:
    id: str
    start_time: datetime
    end_time: datetime | None
    activity_type: ActivityType
    total_cost: Decimal
    total_return: Decimal
    total_markup: Decimal
    events: list[GameEvent]


@dataclass
class LootItem:
    name: str
    quantity: int
    tt_value: Decimal
    markup_value: Decimal
    total_value: Decimal

    def __post_init__(self):
        """Post-initialization hook to convert string values to Decimal."""
        # Convert string values to Decimal
        if isinstance(self.tt_value, str):
            self.tt_value = Decimal(self.tt_value)
        if isinstance(self.markup_value, str):
            self.markup_value = Decimal(self.markup_value)
        if isinstance(self.total_value, str):
            self.total_value = Decimal(self.total_value)


@dataclass
class CombatStats:
    session_id: str
    weapon_id: str
    shots_fired: int
    total_damage: Decimal
    critical_hits: int
    misses: int
    total_ammo_used: int
    total_decay: Decimal

    def __post_init__(self):
        """Post-initialization hook to convert string values to Decimal."""
        if isinstance(self.total_damage, str):
            self.total_damage = Decimal(self.total_damage)
        if isinstance(self.total_decay, str):
            self.total_decay = Decimal(self.total_decay)


@dataclass
class CraftingResult:
    session_id: str
    blueprint_id: str
    attempts: int
    successes: int
    failures: int
    total_cost: Decimal
    total_return: Decimal
    result_items: list[LootItem]

    def __post_init__(self):
        """Post-initialization hook to convert string values to Decimal."""
        if isinstance(self.total_cost, str):
            self.total_cost = Decimal(self.total_cost)
        if isinstance(self.total_return, str):
            self.total_return = Decimal(self.total_return)
