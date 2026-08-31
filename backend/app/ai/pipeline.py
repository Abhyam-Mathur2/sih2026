from __future__ import annotations

import re

ABBREVIATIONS = {
    "VLV": "VALVE", "SS": "STAINLESS STEEL", "CS": "CARBON STEEL",
    "MTR": "MOTOR", "BRG": "BEARING", "FLG": "FLANGED",
}
PRODUCTS = {
    "BALL VALVE": "BALL_VALVE", "GATE VALVE": "GATE_VALVE", "GLOBE VALVE": "GLOBE_VALVE",
    "CHECK VALVE": "CHECK_VALVE", "BUTTERFLY VALVE": "BUTTERFLY_VALVE",
    "PRESSURE RELIEF": "PRESSURE_RELIEF_VALVE", "VALVE": "VALVE",
    "CENTRIFUGAL PUMP": "CENTRIFUGAL_PUMP", "SUBMERSIBLE PUMP": "SUBMERSIBLE_PUMP",
    "POSITIVE DISPLACEMENT": "PD_PUMP", "MULTISTAGE": "MULTISTAGE_PUMP", "PUMP": "PUMP",
    "ELECTRIC MOTOR": "ELECTRIC_MOTOR", "MOTOR": "MOTOR", "TRANSFORMER": "TRANSFORMER",
    "BREAKER": "BREAKER", "CABLE": "CABLE",
    "BALL BEARING": "BALL_BEARING", "ROLLER BEARING": "ROLLER_BEARING",
    "TAPERED ROLLER": "TAPERED_ROLLER_BEARING", "SPHERICAL BEARING": "SPHERICAL_BEARING",
    "BEARING": "BEARING",
    "BOLT": "BOLT", "NUT": "NUT", "WASHER": "WASHER", "SCREW": "SCREW",
    "GASKET": "GASKET", "SEAL": "SEAL", "O-RING": "O_RING", "O RING": "O_RING",
    "PRESSURE GAUGE": "PRESSURE_GAUGE", "TEMPERATURE TRANSMITTER": "TEMP_TRANSMITTER",
    "FLOW METER": "FLOW_METER", "GAUGE": "GAUGE", "TRANSMITTER": "TRANSMITTER",
    "TUBE": "TUBE", "PIPE": "PIPE",
}
# Catches any inline "Key:Value" fragment embedded in free-text descriptions
# (e.g. "WELDED TUBE End Type:HEAVY" -> {"END TYPE": "HEAVY"}), so categories
# without a hardcoded PRODUCTS phrase still yield real, comparable attributes
# instead of an empty dict.
INLINE_ATTR_RE = re.compile(r"\b([A-Za-z][A-Za-z ]{2,30}?)\s*:\s*([A-Za-z0-9./\- ]{1,30})")

def normalize_description(value: str) -> str:
    text = value.upper().replace('"', ' INCH ').replace("'", ' INCH ')
    text = re.sub(r"\b(\d+(?:\.\d+)?)\s*(?:IN|INCHES)\b", r"\1 INCH", text)
    text = re.sub(r"SS\s*[- ]?\s*316\b", "STAINLESS STEEL 316", text)
    for short, full in ABBREVIATIONS.items():
        text = re.sub(rf"\b{short}\b", full, text)
    text = re.sub(r"[^A-Z0-9. ]", " ", text)
    return re.sub(r"\s+", " ", text).strip()

def extract_attributes(text: str) -> dict[str, str]:
    normal = normalize_description(text)
    attrs: dict[str, str] = {}
    for phrase, product in PRODUCTS.items():
        if phrase in normal:
            attrs["product_type"] = product; break
    size = re.search(r"\bDN\s?(\d+)\b|\b(\d+(?:\.\d+)?) INCH\b", normal)
    if size:
        if size.group(1): attrs["size"] = f"DN{size.group(1)}"
        else:
            inches = float(size.group(2)); attrs["size"] = {2.0:"DN50",4.0:"DN100",1.0:"DN25",0.5:"DN15"}.get(inches, f"{inches:g} INCH")
    grade = re.search(r"(?:STAINLESS STEEL\s*|SS\s*)(304|316|316L)\b", normal)
    if grade: attrs["material_grade"] = f"SS{grade.group(1)}"
    pressure = re.search(r"\bPN\s?(\d+)\b", normal)
    if pressure: attrs["pressure_rating"] = f"PN{pressure.group(1)}"
    if "FLANGED" in normal: attrs["connection"] = "FLANGED"

    # Generic fallback: pull any "Key:Value" fragment straight out of the raw
    # (un-normalized) text, so Fasteners/Electrical/Gaskets/Instruments -- none
    # of which are covered by the regexes above -- still produce real,
    # comparable attributes instead of an empty dict.
    for match in INLINE_ATTR_RE.finditer(text):
        key = re.sub(r"\s+", "_", match.group(1).strip().upper())
        value = match.group(2).strip().upper()
        if key and value and key not in attrs:
            attrs[key] = value
    return attrs
