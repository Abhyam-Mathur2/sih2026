from __future__ import annotations
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.ai.pipeline import extract_attributes, normalize_description
from app.core.security import get_password_hash
from app.models import CPSE, Material, MaterialAttribute, MaterialCategory, User, UserRole

async def seed_database(db: AsyncSession) -> None:
    if (await db.execute(select(CPSE.id).limit(1))).scalar_one_or_none(): return
    cpses = [CPSE(name=n, short_code=c, description="Synthetic demonstration organization") for n,c in [("Chennai Petroleum Corporation Limited","CPCL"),("Indian Oil Corporation Limited","IOCL"),("Steel Authority of India Limited","SAIL"),("Bharat Heavy Electricals Limited","BHEL")]]
    categories = [MaterialCategory(name=n, code=c) for n,c in [("Valves","VLV"),("Pipes & Tubes","PIP"),("Pumps","PMP"),("Motors","MTR"),("Bearings","BRG"),("Electrical Components","ELC"),("Fasteners","FST"),("Gaskets & Seals","GSK"),("Instruments","INS")]]
    db.add_all(cpses + categories); await db.flush()
    db.add_all([User(name="BMIM Administrator", email="admin@bmim.gov.in", password_hash=get_password_hash("admin_secure_password_2026"), role=UserRole.ADMIN), User(name="Technical Reviewer", email="reviewer@bmim.gov.in", password_hash=get_password_hash("Reviewer@123"), role=UserRole.TECHNICAL_REVIEWER), User(name="CPSE Manager", email="manager@bmim.gov.in", password_hash=get_password_hash("Manager@123"), role=UserRole.CPSE_MANAGER, cpse_id=cpses[0].id)])
    templates=[("BALL VLV 2\" SS-316 PN16 FLG","2 INCH BALL VALVE STAINLESS STEEL 316 PN16 FLANGED","BALL VALVE DN50 SS316 PN16 FLANGED"),("BALL VLV 4\" SS-316 PN16","4 INCH BALL VALVE STAINLESS STEEL 316 PN16","BALL VALVE DN100 SS316 PN16"),("GATE VLV 2\" CS PN16","2 INCH GATE VALVE CARBON STEEL PN16","GATE VALVE DN50 CS PN16"),("CENTRIFUGAL PUMP 5HP","CENTRIFUGAL PUMP 5 HP","PUMP CENTRIFUGAL 5HP"),("ELECTRIC MTR 3HP","ELECTRIC MOTOR 3 HP","3 HP ELECTRIC MOTOR"),("BRG 6205","BEARING 6205","BALL BEARING 6205")]
    for group, variants in enumerate(templates):
        for i, desc in enumerate(variants):
            for extra in range(4):
                material=Material(cpse_id=cpses[i].id, legacy_material_code=f"{cpses[i].short_code}-{group+1:02d}{extra:02d}", original_description=desc if extra==0 else f"{desc} LOT {extra+1}", normalized_description=normalize_description(desc), category_id=categories[min(group,5)].id, unit_of_measure="EA")
                db.add(material); await db.flush()
                for key,val in extract_attributes(desc).items(): db.add(MaterialAttribute(material_id=material.id, attribute_name=key, attribute_value=val, normalized_value=val))
    await db.flush()
