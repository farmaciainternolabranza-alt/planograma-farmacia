# Demo Planograma – ESCRITORIO BLANCO

Esta demo usa:
- `data/productos.json` generado desde el Excel.
- `data/muebles.json` con las **zonas (cajones 1–4)** del mueble **ESCRITORIO BLANCO**.
- Imagen base: `images/escritorio_blanco.png`.

## Cómo publicar en GitHub Pages
1. Crea un repositorio (ej: `planograma-farmacia`).
2. Sube **todo el contenido** de esta carpeta.
3. En GitHub: **Settings → Pages → Deploy from branch → main / root**.
4. Abre la URL que te entrega GitHub Pages.

## Cómo actualizar productos (rápido)
- Opción simple: reemplaza `data/productos.json` por uno nuevo.
- Opción recomendada (1 comando):

```bash
python tools/generar_json.py
```

> Nota: este script lee el archivo Excel `UBICACION MEDICAMENTOS FARMACIA 2026 (1).xlsx`.

## Estructura de zonas del mueble
Las zonas (cajones) están en `data/muebles.json` y son coordenadas en pixeles de la imagen.

---

Hecho para una estética minimalista y funcional.
