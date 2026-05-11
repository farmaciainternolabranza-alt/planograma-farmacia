# Planograma Farmacia (Fotos reales + buscador)

Este repositorio publica una web (GitHub Pages) para buscar un producto y ver su **ubicación** en un **mueble**, pintando la zona correspondiente.

## Qué incluye
- Buscador por texto libre (encuentra coincidencias en cualquier parte del nombre).
- Datos desde `UBICACION MEDICAMENTOS FARMACIA 2026 (1).xlsx` → se convierten a `data/productos.json`.
- Configuración de muebles y zonas en `data/muebles.json`.
- **Fallback solicitado**: si un producto apunta a un mueble sin foto/configuración, el sistema muestra el texto del campo **MUEBLE** del Excel (sin imagen).

## Publicar en GitHub Pages
1. Sube todos los archivos del repo.
2. En GitHub: **Settings → Pages → Deploy from branch**
   - Branch: `main`
   - Folder: `/ (root)`

## Actualización automática
Cada vez que subas un `.xlsx`, GitHub Actions ejecuta `tools/generar_json.py` y actualiza `data/productos.json`.

## Agregar un nuevo mueble
1. Subir la foto original a `images/`.
2. Definir las zonas en `data/muebles.json`.
   - La clave debe coincidir con `ID_MUEBLE` (recomendado) o con `MUEBLE`.

---

Estilo destacado (highlight) usa el color: **#E82C9A**.
