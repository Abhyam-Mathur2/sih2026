"""
Classification service – auto-assigns MaterialCategory based on extracted product_type.

PS requirement: "Intelligent classification and categorization of materials."
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.material_category import MaterialCategory

# Maps product_type values from extract_attributes() to category codes.
# Categories are seeded in seed.py; this map covers all PRODUCTS dict entries.
PRODUCT_TYPE_TO_CATEGORY: dict[str, str] = {
    # Valves
    "BALL_VALVE": "VLV", "GATE_VALVE": "VLV", "GLOBE_VALVE": "VLV",
    "CHECK_VALVE": "VLV", "BUTTERFLY_VALVE": "VLV", "PLUG_VALVE": "VLV",
    "NEEDLE_VALVE": "VLV", "CONTROL_VALVE": "VLV", "SAFETY_VALVE": "VLV",
    "PRESSURE_RELIEF_VALVE": "VLV", "DIAPHRAGM_VALVE": "VLV", "VALVE": "VLV",

    # Pumps
    "CENTRIFUGAL_PUMP": "PMP", "SUBMERSIBLE_PUMP": "PMP",
    "PD_PUMP": "PMP", "MULTISTAGE_PUMP": "PMP", "GEAR_PUMP": "PMP",
    "DIAPHRAGM_PUMP": "PMP", "PUMP": "PMP",

    # Motors
    "ELECTRIC_MOTOR": "MTR", "INDUCTION_MOTOR": "MTR", "MOTOR": "MTR",

    # Electrical Components
    "TRANSFORMER": "ELC", "CIRCUIT_BREAKER": "ELC", "BREAKER": "ELC",
    "SWITCH": "ELC", "CABLE": "ELC", "CONTACTOR": "ELC", "RELAY": "ELC",

    # Bearings
    "BALL_BEARING": "BRG", "ROLLER_BEARING": "BRG",
    "TAPERED_ROLLER_BEARING": "BRG", "SPHERICAL_BEARING": "BRG",
    "THRUST_BEARING": "BRG", "DEEP_GROOVE_BEARING": "BRG", "BEARING": "BRG",

    # Fasteners
    "SOCKET_HEAD_BOLT": "FST", "HEX_BOLT": "FST", "STUD_BOLT": "FST",
    "STUD": "FST", "BOLT": "FST", "HEX_NUT": "FST", "LOCK_NUT": "FST",
    "NUT": "FST", "LOCK_WASHER": "FST", "SPRING_WASHER": "FST",
    "FLAT_WASHER": "FST", "WASHER": "FST", "SCREW": "FST",

    # Gaskets & Seals
    "SPIRAL_WOUND_GASKET": "GSK", "GASKET": "GSK", "MECHANICAL_SEAL": "GSK",
    "OIL_SEAL": "GSK", "O_RING": "GSK", "SEAL": "GSK", "PACKING": "GSK",

    # Instruments
    "PRESSURE_GAUGE": "INS", "TEMP_GAUGE": "INS", "GAUGE": "INS",
    "PRESSURE_TRANSMITTER": "INS", "TEMP_TRANSMITTER": "INS",
    "FLOW_TRANSMITTER": "INS", "LEVEL_TRANSMITTER": "INS",
    "FLOW_METER": "INS", "THERMOCOUPLE": "INS", "RTD": "INS",
    "TRANSMITTER": "INS",

    # Pipes, Tubes, Flanges & Plates
    "PIPE": "PIP", "TUBE": "PIP", "FLANGE": "PIP", "ELBOW": "PIP",
    "TEE": "PIP", "REDUCER": "PIP", "PLATE": "PIP", "SHEET": "PIP",
}

# Cache: code → id (populated lazily per session)
_category_cache: dict[str, int] = {}


async def classify_material(
    db: AsyncSession, product_type: str | None
) -> int | None:
    """Return the MaterialCategory.id for the given product_type, or None."""
    if not product_type:
        return None

    cat_code = PRODUCT_TYPE_TO_CATEGORY.get(product_type)
    if not cat_code:
        return None

    # Check in-memory cache first
    if cat_code in _category_cache:
        return _category_cache[cat_code]

    result = await db.execute(
        select(MaterialCategory.id).where(MaterialCategory.code == cat_code)
    )
    cat_id = result.scalar_one_or_none()
    if cat_id is not None:
        _category_cache[cat_code] = cat_id
    return cat_id
