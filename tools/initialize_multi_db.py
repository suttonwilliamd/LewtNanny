#!/usr/bin/env python3
"""
Initialize multi-database structure for LewtNanny
Initialize multiple specialized databases
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


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    if exit_code == 0:
        print("\n" + "=" * 50)
        print("Multi-database system initialized successfully!")
