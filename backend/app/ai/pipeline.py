from __future__ import annotations

import re

ABBREVIATIONS = {
    # Valves & Piping
    "VLV": "VALVE", "BALL VLV": "BALL VALVE", "GATE VLV": "GATE VALVE",
    "GLOBE VLV": "GLOBE VALVE", "CHK VLV": "CHECK VALVE", "CHECK VLV": "CHECK VALVE",
    "BFLY VLV": "BUTTERFLY VALVE", "PRV": "PRESSURE RELIEF VALVE",
    "FLG": "FLANGED", "FLGD": "FLANGED", "THD": "THREADED", "THRD": "THREADED",
    "SW": "SOCKET WELD", "BW": "BUTT WELD", "SCRD": "SCREWED",
    "PLT": "PLATE", "PL": "PLATE", "SHT": "SHEET",
    "ELB": "ELBOW", "RED": "REDUCER", "CPG": "COUPLING", "NIP": "NIPPLE",

    # Materials
    "SS": "STAINLESS STEEL", "CS": "CARBON STEEL", "MS": "MILD STEEL",
    "AS": "ALLOY STEEL", "CI": "CAST IRON", "DI": "DUCTILE IRON",
    "GI": "GALVANIZED IRON", "AL": "ALUMINIUM", "ALUM": "ALUMINIUM",
    "CU": "COPPER", "BRS": "BRASS", "BRZ": "BRONZE",

    # Fasteners & Gaskets
    "BLT": "BOLT", "WSHR": "WASHER", "GSK": "GASKET", "PKKG": "PACKING",

    # Electrical & Mechanical
    "MTR": "MOTOR", "BRG": "BEARING", "PMP": "PUMP",
    "XFMR": "TRANSFORMER", "TRFR": "TRANSFORMER", "BKR": "BREAKER",
    "CB": "CIRCUIT BREAKER", "CBL": "CABLE",

    # Instrumentation
    "GAU": "GAUGE", "TX": "TRANSMITTER", "XMTR": "TRANSMITTER",
    "TEMP": "TEMPERATURE", "PRESS": "PRESSURE", "DP": "DIFFERENTIAL PRESSURE",

    # Standards & Specs
    "GR": "GRADE", "GR.": "GRADE",
    "SCH": "SCHEDULE", "SCH.": "SCHEDULE",
    "CL": "CLASS", "CL.": "CLASS",
    "STD": "STANDARD", "SPEC": "SPECIFICATION", "DIM": "DIMENSION",
    "THK": "THICKNESS", "DIA": "DIAMETER", "OD": "OUTSIDE DIAMETER", "ID": "INSIDE DIAMETER",
}

PRODUCTS = {
    # Valves
    "BALL VALVE": "BALL_VALVE", "GATE VALVE": "GATE_VALVE", "GLOBE VALVE": "GLOBE_VALVE",
    "CHECK VALVE": "CHECK_VALVE", "BUTTERFLY VALVE": "BUTTERFLY_VALVE",
    "PLUG VALVE": "PLUG_VALVE", "NEEDLE VALVE": "NEEDLE_VALVE",
    "CONTROL VALVE": "CONTROL_VALVE", "SAFETY VALVE": "SAFETY_VALVE",
    "RELIEF VALVE": "PRESSURE_RELIEF_VALVE", "PRESSURE RELIEF": "PRESSURE_RELIEF_VALVE",
    "DIAPHRAGM VALVE": "DIAPHRAGM_VALVE", "VALVE": "VALVE",

    # Pumps
    "CENTRIFUGAL PUMP": "CENTRIFUGAL_PUMP", "SUBMERSIBLE PUMP": "SUBMERSIBLE_PUMP",
    "POSITIVE DISPLACEMENT": "PD_PUMP", "MULTISTAGE PUMP": "MULTISTAGE_PUMP",
    "MULTISTAGE": "MULTISTAGE_PUMP", "GEAR PUMP": "GEAR_PUMP",
    "DIAPHRAGM PUMP": "DIAPHRAGM_PUMP", "PUMP": "PUMP",

    # Electrical & Motors
    "ELECTRIC MOTOR": "ELECTRIC_MOTOR", "INDUCTION MOTOR": "INDUCTION_MOTOR",
    "SYNCHRONOUS MOTOR": "MOTOR", "MOTOR": "MOTOR",
    "CIRCUIT BREAKER": "CIRCUIT_BREAKER", "BREAKER": "CIRCUIT_BREAKER",
    "SWITCH": "SWITCH", "TRANSFORMER": "TRANSFORMER", "CABLE": "CABLE",
    "WIRE": "CABLE", "CONTACTOR": "CONTACTOR", "RELAY": "RELAY",

    # Bearings
    "BALL BEARING": "BALL_BEARING", "ROLLER BEARING": "ROLLER_BEARING",
    "TAPERED ROLLER": "TAPERED_ROLLER_BEARING", "SPHERICAL BEARING": "SPHERICAL_BEARING",
    "SPHERICAL ROLLER": "SPHERICAL_BEARING", "THRUST BEARING": "THRUST_BEARING",
    "DEEP GROOVE": "DEEP_GROOVE_BEARING", "BEARING": "BEARING",

    # Fasteners
    "SOCKET HEAD BOLT": "SOCKET_HEAD_BOLT", "HEX BOLT": "HEX_BOLT",
    "STUD BOLT": "STUD_BOLT", "STUD": "STUD", "BOLT": "BOLT",
    "HEX NUT": "HEX_NUT", "LOCK NUT": "LOCK_NUT", "NUT": "NUT",
    "LOCK WASHER": "LOCK_WASHER", "SPRING WASHER": "SPRING_WASHER",
    "FLAT WASHER": "FLAT_WASHER", "WASHER": "WASHER", "SCREW": "SCREW",

    # Gaskets & Seals
    "SPIRAL WOUND GASKET": "SPIRAL_WOUND_GASKET", "GASKET": "GASKET",
    "MECHANICAL SEAL": "MECHANICAL_SEAL", "OIL SEAL": "OIL_SEAL",
    "O-RING": "O_RING", "O RING": "O_RING", "SEAL": "SEAL",
    "GLAND PACKING": "PACKING", "PACKING": "PACKING",

    # Instruments
    "PRESSURE GAUGE": "PRESSURE_GAUGE", "TEMPERATURE GAUGE": "TEMP_GAUGE",
    "PRESSURE TRANSMITTER": "PRESSURE_TRANSMITTER", "TEMPERATURE TRANSMITTER": "TEMP_TRANSMITTER",
    "FLOW TRANSMITTER": "FLOW_TRANSMITTER", "LEVEL TRANSMITTER": "LEVEL_TRANSMITTER",
    "FLOW METER": "FLOW_METER", "THERMOCOUPLE": "THERMOCOUPLE", "RTD": "RTD",
    "GAUGE": "GAUGE", "TRANSMITTER": "TRANSMITTER",

    # Piping & Structural
    "SEAMLESS PIPE": "PIPE", "WELDED PIPE": "PIPE", "PIPE": "PIPE",
    "WELDED TUBE": "TUBE", "TUBING": "TUBE", "TUBE": "TUBE",
    "FLANGE": "FLANGE", "ELBOW": "ELBOW", "TEE": "TEE", "REDUCER": "REDUCER",
    "STEEL PLATE": "PLATE", "PLATE": "PLATE", "SHEET": "SHEET",
}

# Standard inch to DN mapping for nominal sizes
INCH_TO_DN: dict[float, str] = {
    0.25: "DN8",
    0.375: "DN10",
    0.5: "DN15",
    0.75: "DN20",
    1.0: "DN25",
    1.25: "DN32",
    1.5: "DN40",
    2.0: "DN50",
    2.5: "DN65",
    3.0: "DN80",
    4.0: "DN100",
    5.0: "DN125",
    6.0: "DN150",
    8.0: "DN200",
    10.0: "DN250",
    12.0: "DN300",
    14.0: "DN350",
    16.0: "DN400",
    18.0: "DN450",
    20.0: "DN500",
    24.0: "DN600",
}

# Fraction conversion mapping for regex
FRACTIONS: dict[str, float] = {
    "1/4": 0.25,
    "3/8": 0.375,
    "1/2": 0.5,
    "3/4": 0.75,
    "1-1/4": 1.25, "1 1/4": 1.25,
    "1-1/2": 1.5, "1 1/2": 1.5,
    "2-1/2": 2.5, "2 1/2": 2.5,
    "3-1/2": 3.5, "3 1/2": 3.5,
}

INLINE_ATTR_RE = re.compile(r"\b([A-Za-z][A-Za-z0-9 _-]{1,30}?)\s*:\s*([A-Za-z0-9./#% -]{1,35})")


def normalize_description(value: str) -> str:
    """Normalize raw material descriptions while preserving technically meaningful specs."""
    if not value:
        return ""

    text = value.upper()

    # 1. Replace quotes and inch symbols
    text = text.replace('"', ' INCH ').replace("''", ' INCH ').replace("'", ' INCH ')

    # 2. Normalize fractions before words (e.g. 1/2" -> 0.5 INCH, 1-1/2" -> 1.5 INCH)
    for frac_str, dec_val in FRACTIONS.items():
        text = re.sub(rf"\b{re.escape(frac_str)}\s*(?:IN|INCH|INCHES)?\b", f"{dec_val:g} INCH", text)

    # 3. Standardize integer/decimal inches
    text = re.sub(r"\b(\d+(?:\.\d+)?)\s*(?:IN|INCHES)\b", r"\1 INCH", text)

    # 4. Standardize Stainless Steel grades (e.g. SS304, SS-316, SS316L)
    text = re.sub(r"\bSS\s*[- ]?\s*(\d{3}[A-Z]?)\b", r"STAINLESS STEEL \1", text)

    # 5. Standardize Pressure Class ratings (e.g., #150, 150#, 150 LBS, CL 150, CLASS 150)
    text = re.sub(r"#\s*(\d+)\b", r"CLASS \1", text)
    text = re.sub(r"\b(\d+)\s*#\b", r"CLASS \1", text)
    text = re.sub(r"\b(\d+)\s*(?:LBS|LB)\b", r"CLASS \1", text)
    text = re.sub(r"\bCL(?:ASS)?\.?\s*[- ]?\s*(\d+)\b", r"CLASS \1", text)

    # 6. Standardize pipe schedules (e.g. SCH 40, SCH-40, SCH40, SCH 80S, SCH XXS)
    text = re.sub(r"\bSCH(?:EDULE)?\.?\s*[- ]?\s*(\d+[A-Z]?|STD|XS|XXS)\b", r"SCHEDULE \1", text)

    # 7. Standardize nominal diameters (e.g. DN 100, DN-100, DN100)
    text = re.sub(r"\bDN\s*[- ]?\s*(\d+)\b", r"DN\1", text)

    # 8. Standardize PN ratings (e.g. PN 16, PN-16, PN16)
    text = re.sub(r"\bPN\s*[- ]?\s*(\d+)\b", r"PN\1", text)

    # 9. Standardize Grades (e.g. GR B, GR.B, GRADE B)
    text = re.sub(r"\bGR(?:ADE)?\.?\s*([A-Z0-9]+)\b", r"GRADE \1", text)

    # 10. Expand standard abbreviations
    for short, full in ABBREVIATIONS.items():
        text = re.sub(rf"\b{re.escape(short)}\b", full, text)

    # 11. Normalize unit spacing
    text = re.sub(r"\b(\d+(?:\.\d+)?)\s*(MM|CM|METER|METERS|MTR|MTRS|M)\b", r"\1 MM" if "MM" in text else r"\1 METER", text)
    # Restore explicit MM vs METER if captured correctly
    text = re.sub(r"\b(\d+(?:\.\d+)?)\s*MM\b", r"\1 MM", text)
    text = re.sub(r"\b(\d+(?:\.\d+)?)\s*(?:MTR|MTRS|METER|METERS)\b", r"\1 METER", text)
    text = re.sub(r"\b(\d+(?:\.\d+)?)\s*(?:FT|FEET)\b", r"\1 FT", text)
    text = re.sub(r"\b(\d+(?:\.\d+)?)\s*(?:SQ\s*MM|SQMM)\b", r"\1 SQ MM", text)
    text = re.sub(r"\b(\d+(?:\.\d+)?)\s*HP\b", r"\1 HP", text)
    text = re.sub(r"\b(\d+(?:\.\d+)?)\s*KW\b", r"\1 KW", text)
    text = re.sub(r"\b(\d+(?:\.\d+)?)\s*KV\b", r"\1 KV", text)
    text = re.sub(r"\b(\d+(?:\.\d+)?)\s*V\b", r"\1 V", text)
    text = re.sub(r"\b(\d+(?:\.\d+)?)\s*BAR\b", r"\1 BAR", text)
    text = re.sub(r"\b(\d+(?:\.\d+)?)\s*PSI\b", r"\1 PSI", text)
    text = re.sub(r"\b(\d+(?:\.\d+)?)\s*RPM\b", r"\1 RPM", text)
    text = re.sub(r"\b(\d+(?:\.\d+)?)\s*HZ\b", r"\1 HZ", text)

    # 12. Strip unneeded special characters while preserving decimals, slashes in grades/specs
    text = re.sub(r"[^A-Z0-9.:/ -]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


KNOWN_KEY_PHRASES = [
    "WALL THICKNESS", "INSIDE DIAMETER", "OUTSIDE DIAMETER", "INNER DIAMETER", "OUTER DIAMETER",
    "OUTPUT SIGNAL", "PROCESS CONNECTION", "HOUSING MATERIAL", "IMPELLER MATERIAL",
    "BODY MATERIAL", "END CONNECTION", "TEMPERATURE RATING", "PRESSURE RATING",
    "CURRENT RATING", "POWER RATING", "CONDUCTOR MATERIAL", "INSULATION TYPE",
    "MATERIAL GRADE", "END TYPE", "LOAD RATING", "SEAL TYPE", "THREAD PITCH",
    "FLOW RATE", "DIAMETER", "THICKNESS", "LENGTH", "WIDTH", "RANGE", "ACCURACY",
    "FINISH", "THREAD", "HEAD", "POWER", "SPEED", "VOLTAGE", "MATERIAL",
]


def extract_attributes(text: str) -> dict[str, str]:
    """Extract structured engineering attributes from normalized or raw descriptions."""
    if not text:
        return {}

    normal = normalize_description(text)
    attrs: dict[str, str] = {}

    # 1. Product Type
    for phrase, product in PRODUCTS.items():
        if re.search(rf"\b{re.escape(phrase)}\b", normal):
            attrs["product_type"] = product
            break

    # 2. Size / Dimensions
    # Case A: DN size
    dn_match = re.search(r"\bDN\s*(\d+)\b", normal)
    if dn_match:
        attrs["size"] = f"DN{dn_match.group(1)}"
    else:
        # Case B: Inch size (map to canonical DN if standard nominal size)
        inch_match = re.search(r"\b(\d+(?:\.\d+)?)\s*INCH\b", normal)
        if inch_match:
            val = float(inch_match.group(1))
            attrs["size"] = INCH_TO_DN.get(val, f"{val:g} INCH")
        else:
            # Case C: Metric bolt size (M12, M16, etc.)
            m_bolt = re.search(r"\bM(\d+(?:\.\d+)?)\b", normal)
            if m_bolt:
                attrs["size"] = f"M{m_bolt.group(1)}"
            else:
                # Case D: Dimension string (e.g. 1000 MM X 2000 MM X 5 MM or 10 MM)
                dim_match = re.search(r"\b(\d+\s*MM\s*X\s*\d+\s*MM\s*X\s*\d+\s*MM|\d+\s*X\s*\d+\s*X\s*\d+\s*MM)\b", normal)
                if dim_match:
                    attrs["size"] = re.sub(r"\s+", " ", dim_match.group(1))
                else:
                    thick_match = re.search(r"\b(\d+(?:\.\d+)?)\s*MM\b", normal)
                    if thick_match:
                        attrs["size"] = f"{thick_match.group(1)} MM"

    # 3. Material Grade
    # Case A: Stainless Steel (SS304, SS316, etc.)
    ss_grade = re.search(r"(?:STAINLESS STEEL|SS)\s*[- ]?\s*(304L|316L|304|316|321|347|410|904L|2205|2507)\b", normal)
    if ss_grade:
        attrs["material_grade"] = f"SS{ss_grade.group(1)}"
    else:
        # Case B: ASTM Standards (e.g. ASTM A106 GRADE B, ASTM A105, ASTM A216 WCB)
        astm_match = re.search(r"\b(ASTM\s*[A-Z]\d+(?:\s*GRADE\s*[A-Z0-9]+)?)\b", normal)
        if astm_match:
            attrs["material_grade"] = re.sub(r"\s+", " ", astm_match.group(1))
        elif "IS 2062" in normal:
            attrs["material_grade"] = "IS 2062"
        elif "CARBON STEEL" in normal or re.search(r"\bCS\b", text.upper()):
            attrs["material_grade"] = "CARBON STEEL"
        elif "MILD STEEL" in normal:
            attrs["material_grade"] = "MILD STEEL"
        elif "ALLOY STEEL" in normal:
            attrs["material_grade"] = "ALLOY STEEL"
        elif "CAST IRON" in normal:
            attrs["material_grade"] = "CAST IRON"
        elif "DUCTILE IRON" in normal:
            attrs["material_grade"] = "DUCTILE IRON"
        elif "BRONZE" in normal:
            attrs["material_grade"] = "BRONZE"
        elif "BRASS" in normal:
            attrs["material_grade"] = "BRASS"
        elif "COPPER" in normal:
            attrs["material_grade"] = "COPPER"
        elif "ALUMINIUM" in normal:
            alum_grade = re.search(r"\bALUMINIUM\s*(?:GRADE\s*)?(\d{4}[A-Z]?)\b", normal)
            attrs["material_grade"] = f"ALUMINIUM {alum_grade.group(1)}" if alum_grade else "ALUMINIUM"
        elif "PVC" in normal:
            attrs["material_grade"] = "PVC"
        elif "PTFE" in normal:
            attrs["material_grade"] = "PTFE"

    # 4. Pressure Rating / Class
    class_match = re.search(r"\bCLASS\s*(\d+)\b", normal)
    if class_match:
        attrs["pressure_rating"] = f"CLASS {class_match.group(1)}"
    else:
        pn_match = re.search(r"\bPN\s*(\d+)\b", normal)
        if pn_match:
            attrs["pressure_rating"] = f"PN{pn_match.group(1)}"
        else:
            psi_match = re.search(r"\b(\d+)\s*PSI\b", normal)
            if psi_match:
                attrs["pressure_rating"] = f"{psi_match.group(1)} PSI"
            else:
                bar_match = re.search(r"\b(\d+(?:-\d+)?)\s*BAR\b", normal)
                if bar_match:
                    attrs["pressure_rating"] = f"{bar_match.group(1)} BAR"

    # 5. Schedule
    sch_match = re.search(r"\bSCHEDULE\s*(\d+[A-Z]?|STD|XS|XXS)\b", normal)
    if sch_match:
        attrs["schedule"] = f"SCH {sch_match.group(1)}"

    # 6. Connection
    if "FLANGED" in normal:
        attrs["connection"] = "FLANGED"
    elif "THREADED" in normal or "SCREWED" in normal:
        attrs["connection"] = "THREADED"
    elif "SOCKET WELD" in normal:
        attrs["connection"] = "SOCKET_WELD"
    elif "BUTT WELD" in normal:
        attrs["connection"] = "BUTT_WELD"
    elif "WAFER" in normal:
        attrs["connection"] = "WAFER"

    # 7. Voltage & Power Ratings
    volt_match = re.search(r"\b(\d+(?:\.\d+)?\s*(?:KV|V))\b", normal)
    if volt_match:
        attrs["voltage"] = re.sub(r"\s+", "", volt_match.group(1))

    power_match = re.search(r"\b(\d+(?:\.\d+)?\s*(?:HP|KW|MW))\b", normal)
    if power_match:
        attrs["power_rating"] = re.sub(r"\s+", " ", power_match.group(1))

    # 8. Bearing Number
    brg_match = re.search(r"\b(60\d{2}|62\d{2}|63\d{2}|64\d{2}|72\d{2}|73\d{2}|222\d{2}|223\d{2}|302\d{2}|303\d{2}|322\d{2}|323\d{2})\b", normal)
    if brg_match and (attrs.get("product_type") == "BEARING" or "BEARING" in normal):
        attrs["bearing_number"] = brg_match.group(1)
        if "size" not in attrs:
            attrs["size"] = brg_match.group(1)

    # 9. Generic Inline "Key:Value" extraction
    matched_spans: list[tuple[int, int]] = []
    for phrase in KNOWN_KEY_PHRASES:
        for m in re.finditer(rf"\b{re.escape(phrase)}\s*:\s*([A-Za-z0-9./#% -]+?)(?=\s+[A-Za-z0-9 _-]+:|$)", text, re.IGNORECASE):
            clean_k = phrase.lower().replace(" ", "_")
            clean_v = m.group(1).strip().upper()
            if clean_k not in attrs and clean_v:
                attrs[clean_k] = clean_v
                matched_spans.append((m.start(), m.end()))

    for m in re.finditer(r"\b([A-Za-z][A-Za-z0-9_-]*)\s*:\s*([A-Za-z0-9./#% -]+?)(?=\s+[A-Za-z0-9 _-]+:|$)", text):
        if any(start <= m.start() <= end for start, end in matched_spans):
            continue
        k = re.sub(r"[^A-Za-z0-9_]", "_", m.group(1).strip().lower())
        val = m.group(2).strip().upper()
        if k and val and k not in attrs:
            attrs[k] = val
            matched_spans.append((m.start(), m.end()))

    return attrs

