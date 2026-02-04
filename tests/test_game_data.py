#!/usr/bin/env python3
"""Test and demo script for the new GameDataService
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.services.game_data_service import GameDataService, WeaponCalculator


async def main():
    print("=" * 60)
    print("LewtNanny GameDataService Demo")
    print("=" * 60)

    service = GameDataService()
    calculator = WeaponCalculator()

    # Get counts
    print("\n[STATS] DATABASE STATISTICS")
    print("-" * 40)
    counts = await service.get_counts()
    for table, count in counts.items():
        print(f"  {table}: {count:,}")

    # Best weapons by DPS
    print("\n[FIRE] TOP 10 WEAPONS BY DPS")
    print("-" * 40)
    weapons = await service.get_best_weapons_by_dps(10)
    for i, w in enumerate(weapons, 1):
        dps_str = f"{w.dps:.2f}" if w.dps else "N/A"
        eco_str = f"{w.eco:.2f}" if w.eco else "N/A"
        print(f"  {i:2}. {w.name[:40]:<40} DPS: {dps_str:>8} Eco: {eco_str}")

    # Best weapons by economy
    print("\n[COIN] TOP 10 WEAPONS BY ECONOMY")
    print("-" * 40)
    weapons = await service.get_best_weapons_by_eco(10)
    for i, w in enumerate(weapons, 1):
        dps_str = f"{w.dps:.2f}" if w.dps else "N/A"
        eco_str = f"{w.eco:.2f}" if w.eco else "N/A"
        print(f"  {i:2}. {w.name[:40]:<40} Eco: {eco_str:>8} DPS: {dps_str}")

    # Search weapons
    print("\n[SEARCH] SEARCH WEAPONS: 'ArMatrix'")
    print("-" * 40)
    weapons = await service.search_weapons("ArMatrix", 5)
    for w in weapons:
        print(f"  - {w.name} ({w.weapon_type})")

    # Get attachments by type
    print("\n[TARGET] SAMPLE AMPLIFIERS (BLP Amp)")
    print("-" * 40)
    amps = await service.get_attachments_by_type("BLP Amp")
    for a in amps[:5]:
        print(f"  - {a.name} (decay: {a.decay})")

    # Get scopes
    print("\n[VIEW] SAMPLE SCOPES")
    print("-" * 40)
    scopes = await service.get_attachments_by_type("Scope")
    for s in scopes[:5]:
        print(f"  - {s.name} (range bonus: +{s.range_bonus})")

    # Get high-value resources
    print("\n[GEM] HIGH-VALUE RESOURCES (TT > 10)")
    print("-" * 40)
    resources = await service.get_resources_by_tt_value(10, 1000)
    for r in resources[:10]:
        print(f"  - {r.name}: {r.tt_value} PED")

    # Search blueprints
    print("\n[LIST] SEARCH BLUEPRINTS: 'Ranger'")
    print("-" * 40)
    bps = await service.search_blueprints("Ranger")
    for bp in bps[:5]:
        print(f"  - {bp.name}")

    # Get blueprints using specific material
    print("\n[GEAR] BLUEPRINTS USING 'Kaisenite Ingot'")
    print("-" * 40)
    bps = await service.get_blueprints_by_material("Kaisenite Ingot")
    for bp in bps[:5]:
        material_count = len(bp.materials)
        print(f"  - {bp.name} ({material_count} materials)")

    # Calculate blueprint cost
    print("\n[COIN] CALCULATE BLUEPRINT COST")
    print("-" * 40)
    bp = await service.get_blueprint_by_name("A.R.C. Ranger Helmet Blueprint (L)")
    if bp:
        cost = await service.calculate_blueprint_cost(bp.name)
        print(f"  Blueprint: {bp.name}")
        print("  Materials:")
        for mat in bp.materials[:5]:
            print(f"    - {mat.material_name}: {mat.quantity}")
        if len(bp.materials) > 5:
            print(f"    ... and {len(bp.materials) - 5} more")
        print(f"  Estimated cost: {cost:.2f} PED")

    # Calculate weapon stats
    print("\n[SWORD] WEAPON CALCULATIONS")
    print("-" * 40)
    weapon_name = "ArMatrix BC-100 (L)"
    stats = await calculator.calculate_session_stats(weapon_name, 1000)
    if stats:
        print(f"  Weapon: {stats['weapon_name']}")
        print(f"  Shots fired: {stats['shots_fired']:,}")
        print(f"  Total damage: {stats['total_damage']:.1f}")
        print(f"  Total cost: {stats['total_cost']:.2f} PED")
        print(f"  DPS: {stats['average_dps']:.1f}")
        print(f"  Damage/PED: {stats['damage_per_ped']:.1f}")

    print("\n" + "=" * 60)
    print("[OK] Demo complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
