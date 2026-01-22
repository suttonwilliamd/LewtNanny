#!/usr/bin/env python3
"""
Data migration CLI tool for LewtNanny
Usage: python migrate_data.py [--force]
"""

import sys
import asyncio
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def main():
    force = '--force' in sys.argv or '-f' in sys.argv

    sys.path.insert(0, str(Path(__file__).parent))

    from src.services.data_migration_service import DataMigrationService

    print("=" * 60)
    print("LewtNanny Data Migration Tool")
    print("=" * 60)

    print("\nStarting data migration...")

    service = DataMigrationService()

    try:
        if force:
            print("\n*** FORCE MIGRATION ***")
            print("This will clear existing data and re-migrate from JSON files.")
            counts = asyncio.run(service.migrate_all(force=True))
        else:
            counts = asyncio.run(service.migrate_all(force=False))

        print("\n" + "=" * 60)
        print("MIGRATION COMPLETE")
        print("=" * 60)
        print(f"\nData migrated:")
        print(f"  Weapons:     {counts['weapons']:>6}")
        print(f"  Attachments: {counts['attachments']:>6}")
        print(f"  Scopes:      {counts.get('scopes', 'N/A'):>6}")
        print(f"  Sights:      {counts.get('sights', 'N/A'):>6}")
        print(f"  Resources:   {counts['resources']:>6}")
        print(f"  Blueprints:  {counts['blueprints']:>6}")
        print(f"  Materials:   {counts['blueprint_materials']:>6}")

        total = sum(v for k, v in counts.items() if isinstance(v, int))
        print(f"\n  TOTAL:       {total:>6} records")

        print("\n" + "=" * 60)
        print("VERIFICATION")
        print("=" * 60)

        verified = asyncio.run(service.verify_data())
        print(f"\nDatabase contains:")
        for table, count in verified.items():
            if isinstance(count, int):
                print(f"  {table}: {count}")

        print(f"\nSample weapons:")
        for name in verified.get('sample_weapons', [])[:5]:
            print(f"  - {name}")

        print(f"\nSample resources:")
        for name in verified.get('sample_resources', [])[:5]:
            print(f"  - {name}")

        print("\n" + "=" * 60)
        print("SUCCESS!")
        print("=" * 60)

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
