import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import asyncio
from app.db.session import AsyncSessionLocal
from sqlalchemy import select
from app.models.user import User

async def main():
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(User))
        rows = res.scalars().all()
        print('Users:', [ (u.id, u.email, u.role, u.cpse_id) for u in rows ])

if __name__ == '__main__':
    asyncio.run(main())
