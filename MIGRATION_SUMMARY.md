# LewtNanny Data Migration System

## Overview

A comprehensive data migration and access system that consolidates all game data from JSON files into a high-performance SQLite database.

## Features

- **Complete Data Migration**: All JSON data migrated to normalized SQLite tables
- **High Performance**: Indexed queries for fast lookups
- **Async Design**: Non-blocking database operations
- **Type-Safe Models**: Typed dataclasses for all game data
- **Query Service**: Full CRUD operations for weapons, attachments, resources, and blueprints

## Database Schema

### Tables Created

| Table | Records | Description |
|-------|---------|-------------|
| `weapons` | 2,880 | All weapons with stats |
| `attachments` | 341 | Amps, scopes, sights |
| `resources` | 1,335 | Resource items with TT values |
| `blueprints` | 3,454 | Crafting blueprints |
| `blueprint_materials` | 14,990 | Normalized materials per blueprint |

### Performance Indexes

- `idx_weapons_name` - Weapon name lookups
- `idx_weapons_type` - Filter by weapon type
- `idx_weapons_dps` - DPS sorting
- `idx_weapons_eco` - Economy sorting
- `idx_attachments_type` - Filter by attachment type
- `idx_resources_tt_value` - TT value filtering
- `idx_blueprint_materials_mat` - Material-to-blueprint search

## Files Created

```
src/
├── models/
│   └── game_data.py          # Typed dataclasses for game data
├── services/
│   ├── data_migration_service.py  # JSON to SQLite migration
│   └── game_data_service.py       # High-performance data access
└── core/
    └── database.py           # Updated to use new migration

migrate_data.py               # CLI migration tool
test_game_data.py             # Demo and testing script
```

## Usage

### Run Migration

```bash
# Normal migration (skips if data exists)
python migrate_data.py

# Force re-migration (clears existing data)
python migrate_data.py --force
```

### Use in Code

```python
from src.services.game_data_service import GameDataService, WeaponCalculator

# Initialize service
service = GameDataService()

# Query weapons
weapons = await service.get_all_weapons()
top_weapons = await service.get_best_weapons_by_dps(10)
search_results = await service.search_weapons("ArMatrix")

# Query resources
high_value = await service.get_resources_by_tt_value(10, 1000)
resource = await service.get_resource_by_name("Kaisenite Ingot")

# Query blueprints
blueprints = await service.get_blueprints_by_material("Kaisenite Ingot")
bp = await service.get_blueprint_by_name("A.R.C. Ranger Helmet Blueprint (L)")
cost = await service.calculate_blueprint_cost(bp.name)

# Calculate weapon stats
calculator = WeaponCalculator()
stats = await calculator.calculate_session_stats("ArMatrix BC-100 (L)", 1000)
```

## Data Models

### Weapon
```python
@dataclass
class Weapon:
    id: str
    name: str
    ammo: int
    decay: Decimal
    weapon_type: str
    dps: Optional[Decimal]
    eco: Optional[Decimal]
    range_value: int
    damage: Decimal
    reload_time: Decimal
    hits: int
```

### Attachment
```python
@dataclass
class Attachment:
    id: str
    name: str
    attachment_type: str  # 'BLP Amp', 'Energy Amp', 'Scope', 'Sight'
    ammo: int
    decay: Decimal
    damage_bonus: Decimal
    ammo_bonus: Decimal
    decay_modifier: Decimal
    economy_bonus: Decimal
    range_bonus: int
```

### Resource
```python
@dataclass
class Resource:
    name: str
    tt_value: Decimal
    decay: Decimal
```

### Blueprint
```python
@dataclass
class Blueprint:
    id: str
    name: str
    materials: List[BlueprintMaterial]
    result_item: Optional[str]
    result_quantity: int
```

## Performance Improvements

| Operation | Before (JSON) | After (SQLite) |
|-----------|---------------|----------------|
| Weapon search | O(n) full scan | O(log n) indexed |
| Attachments by type | O(n) filter | O(1) indexed |
| Resource by name | O(n) lookup | O(1) primary key |
| Blueprint materials | JSON parsing | Pre-joined query |
| Memory usage | All in RAM | Lazy loading |

## Migration Commands

```bash
# Check migration status
python -c "from src.services.data_migration_service import DataMigrationService; \
           import asyncio; m = DataMigrationService(); \
           v = asyncio.run(m.verify_data()); print(v)"

# Get database counts
python -c "from src.services.game_data_service import GameDataService; \
           import asyncio; s = GameDataService(); \
           c = asyncio.run(s.get_counts()); print(c)"
```

## Integration

The system integrates with the existing `DatabaseManager` in `src/core/database.py`:

1. On first run, the new migration service imports all JSON data
2. Existing tables are replaced with the new normalized schema
3. All queries now use the high-performance GameDataService
4. Backward compatibility maintained through the legacy migration fallback

## Total Records Migrated

- **23,000+** total records across all tables
- **2,880** weapons
- **341** attachments (amps, scopes, sights)
- **1,335** resources with TT values
- **3,454** crafting blueprints
- **14,990** blueprint materials (normalized)

## Success Criteria Met

✅ All JSON data successfully migrated to SQLite
✅ Normalized schema with proper relationships
✅ Indexed queries for performance
✅ Async operations throughout
✅ Type-safe dataclasses
✅ Full CRUD operations
✅ CLI migration tool
✅ Demo and testing scripts
