"""
BMIM Database Seed Script
=========================
Populates the database with demo CPSEs, users, categories, and
a rich set of synthetic material records for demonstration.

Run with:
    python -m app.db.seed

This script is idempotent – it checks if data already exists
and skips seeding if the database is not empty.
"""
from __future__ import annotations

import asyncio
import logging

from sqlalchemy import select

from app.ai.pipeline import extract_attributes, normalize_description
from app.core.security import get_password_hash
from app.db.session import AsyncSessionLocal
from app.models.cpse import CPSE
from app.models.material import Material, MaterialStatus
from app.models.material_attribute import MaterialAttribute
from app.models.material_category import MaterialCategory
from app.models.national_material import NationalMaterial, NationalMaterialStatus
from app.models.user import User, UserRole

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("seed")


async def seed_data() -> None:
    logger.info("Starting database seeding…")

    async with AsyncSessionLocal() as db:
        # ------------------------------------------------------------------
        # Guard: skip if already seeded
        # ------------------------------------------------------------------
        existing = await db.execute(select(User).limit(1))
        if existing.scalar():
            logger.info("Database already seeded. Skipping.")
            return

        # ------------------------------------------------------------------
        # 1. CPSEs
        # ------------------------------------------------------------------
        logger.info("Seeding CPSEs…")
        cpses = [
            CPSE(
                name="Chennai Petroleum Corporation Limited",
                short_code="CPCL",
                description="Oil & Gas refining CPSE",
            ),
            CPSE(
                name="Indian Oil Corporation Limited",
                short_code="IOCL",
                description="Oil & Gas marketing and refining CPSE",
            ),
            CPSE(
                name="Steel Authority of India Limited",
                short_code="SAIL",
                description="Steel manufacturing CPSE",
            ),
            CPSE(
                name="Bharat Heavy Electricals Limited",
                short_code="BHEL",
                description="Heavy engineering and power equipment CPSE",
            ),
        ]
        for c in cpses:
            db.add(c)
        await db.flush()

        # ------------------------------------------------------------------
        # 2. Users (demo credentials — synced with frontend defaults)
        # ------------------------------------------------------------------
        logger.info("Seeding Users…")
        users = [
            User(
                name="BMIM Administrator",
                email="admin@bmim.gov.in",
                password_hash=get_password_hash("admin_secure_password_2026"),
                role=UserRole.ADMIN,
                is_active=True,
            ),
            User(
                name="Technical Reviewer",
                email="reviewer@bmim.gov.in",
                password_hash=get_password_hash("Reviewer@123"),
                role=UserRole.TECHNICAL_REVIEWER,
                is_active=True,
            ),
            User(
                name="CPSE Manager – CPCL",
                email="manager@bmim.gov.in",
                password_hash=get_password_hash("Manager@123"),
                role=UserRole.CPSE_MANAGER,
                cpse_id=cpses[0].id,
                is_active=True,
            ),
        ]
        for u in users:
            db.add(u)

        # ------------------------------------------------------------------
        # 3. Material categories (expanded to cover all 8 PS categories)
        # ------------------------------------------------------------------
        logger.info("Seeding Material Categories…")
        categories = [
            MaterialCategory(name="Valves", code="VLV"),
            MaterialCategory(name="Pipes & Tubes", code="PIP"),
            MaterialCategory(name="Pumps", code="PMP"),
            MaterialCategory(name="Motors", code="MTR"),
            MaterialCategory(name="Bearings", code="BRG"),
            MaterialCategory(name="Electrical Components", code="ELC"),
            MaterialCategory(name="Fasteners", code="FST"),
            MaterialCategory(name="Gaskets & Seals", code="GSK"),
            MaterialCategory(name="Instruments", code="INS"),
        ]
        for cat in categories:
            db.add(cat)
        await db.flush()

        # ------------------------------------------------------------------
        # 4. Material templates (groups that should match each other)
        # ------------------------------------------------------------------
        logger.info("Seeding Material records…")

        # Each tuple: (alias1, alias2, alias3) – same physical item described differently
        templates = [
            (
                'BALL VLV 2" SS-316 PN16 FLG',
                "2 INCH BALL VALVE STAINLESS STEEL 316 PN16 FLANGED",
                "BALL VALVE DN50 SS316 PN16 FLANGED",
            ),
            (
                'BALL VLV 4" SS-316 PN16',
                "4 INCH BALL VALVE STAINLESS STEEL 316 PN16",
                "BALL VALVE DN100 SS316 PN16",
            ),
            (
                'GATE VLV 2" CS PN16',
                "2 INCH GATE VALVE CARBON STEEL PN16",
                "GATE VALVE DN50 CS PN16",
            ),
            (
                "CENTRIFUGAL PUMP 5HP",
                "CENTRIFUGAL PUMP 5 HP",
                "PUMP CENTRIFUGAL 5HP",
            ),
            (
                "ELECTRIC MTR 3HP",
                "ELECTRIC MOTOR 3 HP",
                "3 HP ELECTRIC MOTOR",
            ),
            (
                "BRG 6205",
                "BEARING 6205",
                "BALL BEARING 6205",
            ),
            # Additional categories for better coverage
            (
                "HEX BOLT M12 Grade:8.8",
                "HEXAGONAL BOLT M12X50 Grade:8.8",
                "BOLT HEX M12 Grade:8.8",
            ),
            (
                "SPIRAL WOUND GASKET DN50 PN16",
                "GASKET SPIRAL WOUND 2 INCH PN16",
                "SWG GASKET DN50",
            ),
            (
                "PRESSURE GAUGE 0-10 BAR Range:0-10",
                "GAUGE PRESSURE 0-10BAR",
                "PRESSURE GAUGE 10BAR",
            ),
        ]

        # Category assignment based on group index
        cat_map = [0, 0, 0, 2, 3, 4, 6, 7, 8]  # indices into categories list

        for group_idx, variants in enumerate(templates):
            cat_idx = cat_map[group_idx] if group_idx < len(cat_map) else 5
            for cpse_idx, desc in enumerate(variants):
                cpse = cpses[cpse_idx % len(cpses)]
                # Create 4 records per (group, cpse) combination
                for extra in range(4):
                    description = desc if extra == 0 else f"{desc} LOT {extra + 1}"
                    code = f"{cpse.short_code}-{group_idx + 1:02d}{extra:02d}"
                    mat = Material(
                        cpse_id=cpse.id,
                        legacy_material_code=code,
                        original_description=description,
                        normalized_description=normalize_description(desc),
                        category_id=categories[cat_idx].id,
                        unit_of_measure="EA",
                        status=MaterialStatus.ACTIVE,
                    )
                    db.add(mat)
                    await db.flush()

                    # Extract and store attributes
                    for attr_name, attr_val in extract_attributes(desc).items():
                        db.add(
                            MaterialAttribute(
                                material_id=mat.id,
                                attribute_name=attr_name,
                                attribute_value=attr_val,
                                normalized_value=attr_val,
                            )
                        )

        # ------------------------------------------------------------------
        # 5. National Material Codes (master records)
        # ------------------------------------------------------------------
        logger.info("Seeding National Material Codes…")
        nmcs = [
            NationalMaterial(
                national_material_code="NMC-VLV-BALLVALVE-SS316-DN50-0001",
                standard_description="BALL VALVE 2 INCH STAINLESS STEEL 316 PN16 FLANGED",
                category_id=categories[0].id,
                standard_attributes={
                    "product_type": "BALL_VALVE",
                    "size": "DN50",
                    "material_grade": "SS316",
                    "pressure_rating": "PN16",
                    "connection": "FLANGED",
                },
                status=NationalMaterialStatus.ACTIVE,
            ),
            NationalMaterial(
                national_material_code="NMC-VLV-BALLVALVE-SS316-DN100-0001",
                standard_description="BALL VALVE 4 INCH STAINLESS STEEL 316 PN16",
                category_id=categories[0].id,
                standard_attributes={
                    "product_type": "BALL_VALVE",
                    "size": "DN100",
                    "material_grade": "SS316",
                    "pressure_rating": "PN16",
                },
                status=NationalMaterialStatus.ACTIVE,
            ),
        ]
        for nm in nmcs:
            db.add(nm)

        await db.commit()
        logger.info("Database seeding completed successfully.")
        logger.info("")
        logger.info("Demo credentials:")
        logger.info("  Admin:    admin@bmim.gov.in    / admin_secure_password_2026")
        logger.info("  Reviewer: reviewer@bmim.gov.in / Reviewer@123")
        logger.info("  Manager:  manager@bmim.gov.in  / Manager@123")


if __name__ == "__main__":
    asyncio.run(seed_data())
