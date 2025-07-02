import asyncio
import sqlite3
from models import async_session

async def migrate_database():
    """Add Hubstaff columns to existing database"""
    async with async_session() as session:
        # Add new columns if they don't exist
        await session.execute("""
            ALTER TABLE user ADD COLUMN hubstaff_access_token TEXT;
        """)
        await session.execute("""
            ALTER TABLE user ADD COLUMN hubstaff_refresh_token TEXT;
        """)
        await session.execute("""
            ALTER TABLE user ADD COLUMN hubstaff_id_token TEXT;
        """)
        await session.execute("""
            ALTER TABLE user ADD COLUMN hubstaff_token_expires_at INTEGER;
        """)
        await session.commit()

if __name__ == "__main__":
    asyncio.run(migrate_database()) 