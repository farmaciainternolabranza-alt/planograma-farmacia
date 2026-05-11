import pandas as pd
import json
from pathlib import Path

EXCEL = Path('UBICACION MEDICAMENTOS FARMACIA 2026 (1).xlsx')
SALIDA = Path('data/productos.json')

# Lee Excel
_df = pd.read_excel(EXCEL, engine='openpyxl')
for c in ['Producto','MUEBLE','UBICACION']:
    _df[c] = _df[c].astype(str).str.strip()

# Deja solo columnas necesarias
out = _df[['Producto','MUEBLE','UBICACION']].copy()
out.columns = ['producto','mueble','ubicacion']

# Guarda JSON
SALIDA.parent.mkdir(parents=True, exist_ok=True)
SALIDA.write_text(json.dumps(out.to_dict(orient='records'), ensure_ascii=False, indent=2), encoding='utf-8')
print(f'OK: {SALIDA} ({len(out)} filas)')
