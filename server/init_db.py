#!/usr/bin/env python3
"""
Simple database initialization script.
Creates all tables without Alembic migrations to avoid conflicts.
"""

import asyncio
import sys
import os

# Add the server directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db.session import async_engine
from app.db.base import Base
from app.models import *  # Import all models


async def create_tables():
    """Create all tables in the database."""
    try:
        print("Creating database tables...")
        
        # Create all tables
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        print("✅ Database tables created successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return False


async def main():
    """Main function."""
    print("🚀 Initializing EduAnalytics database...")
    
    success = await create_tables()
    
    if success:
        print("🎉 Database initialization completed!")
    else:
        print("💥 Database initialization failed!")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
