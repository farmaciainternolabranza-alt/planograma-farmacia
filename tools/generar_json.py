import pandas as pd
import json
from pathlib import Path

EXCEL = Path('UBICACION MEDICAMENTOS FARMACIA 2026 (1).xlsx')
SALIDA = Path('data/productos.json')

_df = pd.read_excel(EXCEL, engine='openpyxl')

for c in ['Producto','MUEBLE','ID_MUEBLE','UBICACION']:
    if c in _df.columns:
        _df[c] = _df[c].astype(str).str.strip()

out = _df[['Producto','MUEBLE','ID_MUEBLE','UBICACION']].copy()
out.columns = ['producto','mueble','id_mueble','ubicacion']
out['id_mueble'] = out['id_mueble'].replace({'nan':'','None':''})

SALIDA.parent.mkdir(parents=True, exist_ok=True)
SALIDA.write_text(json.dumps(out.to_dict(orient='records'), ensure_ascii=False, indent=2), encoding='utf-8')
print(f'OK: {SALIDA} ({len(out)} filas)')
