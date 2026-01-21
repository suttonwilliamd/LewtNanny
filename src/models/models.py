"""
Core data models for LewtNanny
"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional, List, Dict, Any


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
    dps: Optional[Decimal] = None
    eco: Optional[Decimal] = None
    range_: Optional[int] = None
    
    def __post_init__(self):
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
    materials: List[tuple]  # List of (name, quantity)
    result_item: Optional[str] = None
    result_quantity: Optional[int] = None
    skill_required: Optional[str] = None
    condition_limit: Optional[int] = None


@dataclass
class GameEvent:
    id: Optional[int]
    timestamp: datetime
    event_type: EventType
    activity_type: ActivityType
    raw_message: str
    parsed_data: Dict[str, Any]
    session_id: str


@dataclass
class Session:
    id: str
    start_time: datetime
    end_time: Optional[datetime]
    activity_type: ActivityType
    total_cost: Decimal
    total_return: Decimal
    total_markup: Decimal
    events: List[GameEvent]


@dataclass
class LootItem:
    name: str
    quantity: int
    tt_value: Decimal
    markup_value: Decimal
    total_value: Decimal
    
    def __post_init__(self):
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
    result_items: List[LootItem]
    
    def __post_init__(self):
        if isinstance(self.total_cost, str):
            self.total_cost = Decimal(self.total_cost)
        if isinstance(self.total_return, str):
            self.total_return = Decimal(self.total_return)