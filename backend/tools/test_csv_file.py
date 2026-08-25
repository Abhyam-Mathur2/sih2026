import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.services.upload_service import _read_csv_df

csv_path = Path(ROOT).parents[0] / "bmim_test_materials.csv"
print("Testing CSV at:", csv_path)
if not csv_path.exists():
    print("File not found:", csv_path)
    raise SystemExit(1)

content = csv_path.read_bytes()
print('\n--- RAW INSPECTION ---')
print('First 200 bytes repr:')
print(repr(content[:200]))
print('\nDecoded (utf-8-sig) first 5 lines:')
try:
    text = content.decode('utf-8-sig')
    lines = text.splitlines()
    for i, l in enumerate(lines[:5], start=1):
        print(f"{i}: {repr(l)}")
except Exception as e:
    print('Could not decode with utf-8-sig:', e)

try:
    df = _read_csv_df(content)
    print('DETECTED COLUMNS:', list(df.columns))
    print('SAMPLE ROWS:')
    print(df.head().to_dict(orient='records'))
except Exception as e:
    print('ERROR while parsing:', e)
    raise
