import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.services.upload_service import _read_csv_df

sample = b'''legacy_material_code,original_description
MAT001,High strength structural steel grade
MAT002,Industrial stainless steel sheet
'''

try:
    df = _read_csv_df(sample)
    print('DETECTED:', list(df.columns))
except Exception as e:
    print('ERROR', e)
