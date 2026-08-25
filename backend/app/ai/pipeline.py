from __future__ import annotations

import re

ABBREVIATIONS = {
    "VLV": "VALVE", "SS": "STAINLESS STEEL", "CS": "CARBON STEEL",
    "MTR": "MOTOR", "BRG": "BEARING", "FLG": "FLANGED",
}
PRODUCTS = {"BALL VALVE": "BALL_VALVE", "GATE VALVE": "GATE_VALVE", "CENTRIFUGAL PUMP": "CENTRIFUGAL_PUMP", "ELECTRIC MOTOR": "ELECTRIC_MOTOR", "BEARING": "BEARING", "PIPE": "PIPE"}

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
    return attrs
