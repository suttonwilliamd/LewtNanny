"""
Sample data generator for testing the analysis tab.
Run this script to populate the database with realistic sample hunting sessions.
"""

import asyncio
import aiosqlite
import random
from datetime import datetime, timedelta
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))

from src.core.database import DatabaseManager


async def generate_sample_data(db_manager: DatabaseManager):
    """Generate realistic sample hunting session data"""
    
    print("Generating sample hunting session data...")
    
    activities = ["hunting", "hunting", "hunting", "crafting", "mining"]
    creatures = ["Atrox", "Araneae", "Nexus", "Faucet", "Longtooth", "Keur", "Berytus"]
    
    sessions_created = 0
    
    for i in range(50):
        session_id = f"sample_session_{i:03d}"
        
        start_time = datetime.now() - timedelta(days=random.randint(1, 90), hours=random.randint(0, 23))
        
        activity = random.choice(activities)
        
        if activity == "hunting":
            cost = random.uniform(50, 500)
            roi = random.gauss(0.85, 0.35)
            if roi < 0:
                roi = random.uniform(0.3, 0.7)
            else:
                roi = random.uniform(0.9, 1.4)
            return_val = cost * roi
            markup = random.uniform(50, 200)
        elif activity == "crafting":
            cost = random.uniform(100, 1000)
            roi = random.gauss(0.75, 0.30)
            return_val = cost * max(roi, 0.1)
            markup = random.uniform(20, 100)
        else:
            cost = random.uniform(30, 300)
            roi = random.gauss(0.90, 0.25)
            return_val = cost * max(roi, 0.5)
            markup = random.uniform(10, 80)
        
        profit = return_val - cost
        
        try:
            async with aiosqlite.connect(db_manager.db_path) as db:
                await db.execute("""
                    INSERT INTO sessions (id, start_time, end_time, activity_type, total_cost, total_return, total_markup)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    session_id,
                    start_time,
                    start_time + timedelta(hours=random.uniform(0.5, 4.0)),
                    activity,
                    round(cost, 2),
                    round(return_val, 2),
                    round(markup, 2)
                ))
                await db.commit()
                sessions_created += 1
                
        except Exception as e:
            print(f"Error creating session {session_id}: {e}")
    
    print(f"Created {sessions_created} sample sessions")
    
    print("\nSample data generation complete!")
    print("\nTo view the analysis:")
    print("1. Run: python main.py")
    print("2. Click on the 'Analysis' tab")
    print("3. The charts should now show realistic data")


async def clear_sample_data(db_manager: DatabaseManager):
    """Clear all sample data"""
    print("Clearing sample data...")
    
    try:
        async with aiosqlite.connect(db_manager.db_path) as db:
            await db.execute("DELETE FROM events WHERE session_id LIKE 'sample_%'")
            await db.execute("DELETE FROM session_loot_items WHERE session_id LIKE 'sample_%'")
            await db.execute("DELETE FROM sessions WHERE id LIKE 'sample_%'")
            await db.commit()
        print("Sample data cleared")
    except Exception as e:
        print(f"Error clearing sample data: {e}")


async def main():
    """Main function"""
    import aiosqlite
    from src.utils.paths import get_user_data_dir, ensure_user_data_dir

    db_path = str(get_user_data_dir() / "lewtnanny.db")
    ensure_user_data_dir()

    db_manager = DatabaseManager(db_path)
    await db_manager.initialize()
    
    print("=" * 50)
    print("LewtNanny Sample Data Generator")
    print("=" * 50)
    print()
    
    import argparse
    parser = argparse.ArgumentParser(description="Generate sample data for testing")
    parser.add_argument("--clear", action="store_true", help="Clear sample data instead of generating")
    args = parser.parse_args()
    
    if args.clear:
        await clear_sample_data(db_manager)
    else:
        await generate_sample_data(db_manager)
    
    await db_manager.close()


if __name__ == "__main__":
    asyncio.run(main())
