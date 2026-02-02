#!/usr/bin/env python3
"""
Initialize multi-database structure for LewtNanny
Replaces the single large lewtnanny.db with multiple specialized databases
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from core.multi_database_manager import MultiDatabaseManager

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


async def main():
    """Main initialization function"""
    print("🚀 Initializing LewtNanny Multi-Database Structure")
    print("=" * 50)

    # Initialize the multi-database manager
    db_manager = MultiDatabaseManager()

    try:
        # Initialize all databases
        await db_manager.initialize_all()

        print("\n✅ Database initialization completed successfully!")

        # Get counts to verify
        print("\n📊 Database Status:")
        counts = await db_manager.get_all_counts()

        for db_name, count in counts.items():
            print(f"   {db_name}: {count} records")

        # Show database files
        print(f"\n📁 Database files created in: {db_manager.db_dir}")
        for db_name, db_path in db_manager.databases.items():
            if db_path.exists():
                size = db_path.stat().st_size
                print(f"   {db_name}.db: {size:,} bytes")

        await db_manager.close_all()

        print("\n🎉 Multi-database setup complete!")
        print("\n💡 Benefits:")
        print("   • Better performance with smaller, focused databases")
        print("   • Easier maintenance and updates")
        print("   • Reduced locking and contention")
        print("   • Better data organization")

    except Exception as e:
        logger.error(f"Initialization failed: {e}")
        print(f"\n❌ Error: {e}")
        return 1

    return 0


async def cleanup_old_database():
    """Optional cleanup of old database after verification"""
    db_manager = MultiDatabaseManager()
    old_db = db_manager.db_dir / "lewtnanny.db"

    if not old_db.exists():
        print("ℹ️  No old lewtnanny.db found")
        return

    # Check if new databases have data
    counts = await db_manager.get_all_counts()
    total_new_records = sum(counts.values())

    if total_new_records > 0:
        print(
            f"\n🗑️  Old database found. New databases contain {total_new_records} records."
        )
        response = input(
            "Would you like to backup and remove the old lewtnanny.db? (y/N): "
        )

        if response.lower() in ["y", "yes"]:
            backup_path = old_db.with_suffix(".db.backup")
            old_db.rename(backup_path)
            print(f"✅ Old database backed up to: {backup_path}")
        else:
            print("ℹ️  Keeping old database for safety")
    else:
        print("⚠️  New databases appear empty, keeping old database")


if __name__ == "__main__":
    if "--cleanup" in sys.argv:
        asyncio.run(cleanup_old_database())
    else:
        exit_code = asyncio.run(main())
        if exit_code == 0:
            print("\n" + "=" * 50)
            response = input("Would you like to cleanup the old database now? (y/N): ")
            if response.lower() in ["y", "yes"]:
                asyncio.run(cleanup_old_database())
