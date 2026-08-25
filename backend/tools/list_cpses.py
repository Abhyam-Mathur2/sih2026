import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import asyncio
from app.db.session import AsyncSessionLocal
from sqlalchemy import select
from app.models.cpse import CPSE

async def main():
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(CPSE))
        rows = res.scalars().all()
        print('CPSEs:', [ (c.id, c.name, c.short_code) for c in rows ])

if __name__ == '__main__':
    asyncio.run(main())
