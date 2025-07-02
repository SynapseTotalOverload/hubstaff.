import asyncio
import sqlite3
from models import async_session
import sqlalchemy as sa

async def migrate_database():
    """Add missing columns to existing database"""
    async with async_session() as session:
        try:
            # Add is_admin column if it doesn't exist
            await session.execute(sa.text("""
                ALTER TABLE user ADD COLUMN is_admin BOOLEAN DEFAULT 0;
            """))
            print("✅ Added is_admin column successfully")
        except Exception as e:
            if "duplicate column name" in str(e):
                print("ℹ️ is_admin column already exists")
            else:
                print(f"❌ Error adding is_admin column: {e}")
        
        await session.commit()
        print("✅ Database migration completed")

if __name__ == "__main__":
    asyncio.run(migrate_database()) 