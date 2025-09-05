#!/usr/bin/env python3
import asyncio
from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.models.user import User, UserRole
from app.core.security import get_password_hash


ADMIN_USERNAME = "admin@eduanalytics.local"
ADMIN_PASSWORD = "admin_password"


async def seed_admin() -> None:
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.username == ADMIN_USERNAME))
        user = result.scalars().first()
        if user:
            print("Admin exists")
            return
        user = User(
            username=ADMIN_USERNAME,
            role=UserRole.admin,
            hashed_password=get_password_hash(ADMIN_PASSWORD),
        )
        db.add(user)
        await db.commit()
        print("Admin created")


if __name__ == "__main__":
    asyncio.run(seed_admin())



