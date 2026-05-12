import re, json, math
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image
import cv2
import pytesseract

# =========================
# Config (ajusta si cambias nombres)
# =========================
EXCEL = Path("UBICACION MEDICAMENTOS FARMACIA 2026 (1).xlsx")
SALIDA = Path("data/muebles.json")

IMG_BASE = {
    "EB": "Escritorio_blanco",
    "CAFE": "Mueble_cafe",
    "M01": "M01",
    "M02": "M02",
    "M03": "M03",
    "M04A": "M04A",
    "M04B": "M04B",
    "M05A": "M05A",
    "M05B": "M05B",
}

# Alias por nombre de mueble (fallback si faltara ID)
NAME_ALIAS = {
    "ESCRITORIO BLANCO": "EB",
    "MUEBLE CAFE": "CAFE",
    "MUEBLE NUEVO GRIS": "M01",
    "MUEBLE DOS PISOS": "M02",
    "VERTICAL GAVETAS": "M03",
    "ISLA CENTRAL": "M04A",  # cara por defecto (si faltara ID)
    "ISLA LATERAL": "M05A",  # cara por defecto (si faltara ID)
}

# =========================
# Helpers imagen
# =========================
def fill_holes(bin_img: np.ndarray) -> np.ndarray:
    h, w = bin_img.shape
    inv = cv2.bitwise_not(bin_img)
    flood = inv.copy()
    mask = np.zeros((h + 2, w + 2), np.uint8)
    cv2.floodFill(flood, mask, (0, 0), 255)
    flood_inv = cv2.bitwise_not(flood)
    return bin_img | flood_inv

def poly_from_mask(cc: np.ndarray):
    contours, _ = cv2.findContours(cc, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None
    cnt = max(contours, key=cv2.contourArea)
    peri = cv2.arcLength(cnt, True)
    eps = 0.01 * peri
    approx = cv2.approxPolyDP(cnt, eps, True)
    while len(approx) > 45 and eps < 0.06 * peri:
        eps *= 1.25
        approx = cv2.approxPolyDP(cnt, eps, True)

    poly = [(int(p[0][0]), int(p[0][1])) for p in approx]
    cxs = np.mean([p[0] for p in poly])
    cys = np.mean([p[1] for p in poly])
    poly = sorted(poly, key=lambda p: math.atan2(p[1] - cys, p[0] - cxs))
    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]
    bbox = (min(xs), min(ys), max(xs), max(ys))
    return poly, bbox

def components_simple(ori, rot, thr=25, sat_thr=0.02, min_area=800, dil=2):
    a = np.array(ori).astype(np.int16)
    b = np.array(rot).astype(np.int16)
    diff = np.abs(a - b).sum(axis=2)
    mask = diff > thr

    b_u = b.astype(np.uint8)
    mx = b_u.max(axis=2).astype(np.float32)
    mn = b_u.min(axis=2).astype(np.float32)
    sat = np.where(mx == 0, 0, (mx - mn) / mx)
    mask &= sat > sat_thr

    m = (mask.astype(np.uint8) * 255)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))

    num, labels, stats, centroids = cv2.connectedComponentsWithStats(m, connectivity=8)
    comps = []
    for i in range(1, num):
        area = int(stats[i, cv2.CC_STAT_AREA])
        if area < min_area:
            continue
        cc = (labels == i).astype(np.uint8) * 255
        cc = cv2.dilate(cc, np.ones((5, 5), np.uint8), iterations=dil)
        cc = fill_holes(cc)
        pb = poly_from_mask(cc)
        if pb is None:
            continue
        poly, bbox = pb
        cx, cy = centroids[i]
        comps.append({"area": area, "bbox": bbox, "c": (float(cx), float(cy)), "poly": poly})
    return comps

def components_by_color(ori, rot, thr=20, sat_thr=0.02, k=6, min_area=200):
    a = np.array(ori).astype(np.int16)
    b = np.array(rot).astype(np.int16)
    diff = np.abs(a - b).sum(axis=2)
    mask = diff > thr

    b_u = b.astype(np.uint8)
    mx = b_u.max(axis=2).astype(np.float32)
    mn = b_u.min(axis=2).astype(np.float32)
    sat = np.where(mx == 0, 0, (mx - mn) / mx)
    mask &= sat > sat_thr

    ys, xs = np.where(mask)
    if len(xs) == 0:
        return []

    cols = b_u[ys, xs].astype(np.float32)
    n = len(cols)
    if n > 120000:
        idx = np.random.choice(n, 120000, replace=False)
        sample = cols[idx]
    else:
        sample = cols

    from sklearn.cluster import MiniBatchKMeans
    km = MiniBatchKMeans(n_clusters=k, random_state=0, batch_size=4096, n_init=5)
    km.fit(sample)
    centers = km.cluster_centers_.astype(np.float32)

    labs = []
    chunk = 200000
    for i in range(0, n, chunk):
        c = cols[i:i + chunk]
        d = ((c[:, None, :] - centers[None, :, :]) ** 2).sum(axis=2)
        labs.append(d.argmin(axis=1))
    labs = np.concatenate(labs)

    h, w = mask.shape
    comps = []
    for lab in range(k):
        sel = labs == lab
        if sel.sum() == 0:
            continue
        m = np.zeros((h, w), dtype=np.uint8)
        m[ys[sel], xs[sel]] = 255
        m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))

        num, labels_cc, stats, centroids = cv2.connectedComponentsWithStats(m, connectivity=8)
        for i in range(1, num):
            area = int(stats[i, cv2.CC_STAT_AREA])
            if area < min_area:
                continue
            cc = (labels_cc == i).astype(np.uint8) * 255
            cc = cv2.dilate(cc, np.ones((3, 3), np.uint8), iterations=1)
            cc = fill_holes(cc)
            pb = poly_from_mask(cc)
            if pb is None:
                continue
            poly, bbox = pb
            cx, cy = centroids[i]
            comps.append({"area": area, "bbox": bbox, "c": (float(cx), float(cy)), "poly": poly})

    # dedupe overlaps
    comps = sorted(comps, key=lambda c: c["area"], reverse=True)
    final = []
    def iou(b1, b2):
        x1 = max(b1[0], b2[0]); y1 = max(b1[1], b2[1])
        x2 = min(b1[2], b2[2]); y2 = min(b1[3], b2[3])
        if x2 <= x1 or y2 <= y1:
            return 0
        inter = (x2 - x1) * (y2 - y1)
        a1 = (b1[2] - b1[0]) * (b1[3] - b1[1])
        a2 = (b2[2] - b2[0]) * (b2[3] - b2[1])
        return inter / (a1 + a2 - inter)

    for c in comps:
        if all(iou(c["bbox"], f["bbox"]) < 0.75 for f in final):
            final.append(c)
    return final

# =========================
# OCR helpers
# =========================
def ocr_label_white(rot_bgr, bbox, pad=6):
    x1, y1, x2, y2 = bbox
    h, w = rot_bgr.shape[:2]
    x1 = max(0, x1 - pad); y1 = max(0, y1 - pad)
    x2 = min(w - 1, x2 + pad); y2 = min(h - 1, y2 + pad)
    crop = rot_bgr[y1:y2, x1:x2]

    ch, cw = crop.shape[:2]
    crop = crop[int(ch * 0.15):int(ch * 0.85), int(cw * 0.15):int(cw * 0.85)]
    crop = cv2.resize(crop, None, fx=3.0, fy=3.0, interpolation=cv2.INTER_CUBIC)

    hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
    H, S, V = cv2.split(hsv)

    # texto blanco: saturación baja + valor alto
    mask = ((S < 95) & (V > 150)).astype(np.uint8) * 255
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8), iterations=2)

    inv = cv2.bitwise_not(mask)
    txt = pytesseract.image_to_string(
        inv,
        config="--psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
    )
    txt = re.sub(r"[^A-Za-z0-9]", "", txt).upper()
    return txt

def normalize_label(txt, mode="auto"):
    t = (txt or "").strip().upper()
    t = re.sub(r"\s+", "", t)
    if not t:
        return ""
    t = t.replace("O", "0")
    if mode == "num" or (mode == "auto" and re.fullmatch(r"[0-9SBIO]+", t)):
        t = t.replace("S", "5").replace("B", "8").replace("I", "1")

    m = re.fullmatch(r"([A-Z])S", t)
    if m:
        t = m.group(1) + "5"

    if t.startswith("BASKET"):
        rest = t[len("BASKET"):]
        if rest:
            t = "BASKET " + rest
    return t

def zone_dict(c):
    poly = [[int(x), int(y)] for x, y in c["poly"]]
    x1, y1, x2, y2 = c["bbox"]
    return {"poly": poly, "x": int(x1), "y": int(y1), "w": int(x2 - x1), "h": int(y2 - y1)}

# =========================
# Main
# =========================
def main():
    # Leer Excel (ubicaciones + planograma) [1](https://municitemuco-my.sharepoint.com/personal/farmacia_lb_temuco_cl).xlsx&action=default&mobileredirect=true)
    df = pd.read_excel(EXCEL, engine="openpyxl", sheet_name="ubicacion")
    for c in ["Producto", "MUEBLE", "ID_MUEBLE", "UBICACION"]:
        df[c] = df[c].astype(str).str.strip()
    df["ID_MUEBLE"] = df["ID_MUEBLE"].apply(lambda s: "" if str(s).lower() == "nan" else str(s).strip())
    df["UBICACION"] = df["UBICACION"].apply(lambda s: "" if str(s).lower() == "nan" else str(s).strip())

    expected = {}
    for id_, sub in df[df["ID_MUEBLE"] != ""].groupby("ID_MUEBLE"):
        expected[id_] = sorted(set([u for u in sub["UBICACION"].tolist() if u]))

    muebles = {}
    reporte = {}

    ids_build = ["EB", "M01", "M02", "M03", "M04A", "M04B", "M05A", "M05B", "CAFE"]

    for id_ in ids_build:
        base = IMG_BASE[id_]
        ori = Image.open(f"images/{base}_original.png").convert("RGB")
        rot = Image.open(f"images/{base}_rotulado.png").convert("RGB")
        rot_bgr = cv2.cvtColor(np.array(rot), cv2.COLOR_RGB2BGR)

        many = id_ in ["M01", "M02", "M03"]
        comps = components_by_color(ori, rot) if many else components_simple(ori, rot)

        # Ajustes finos por mueble
        if id_ == "M05A" and len(comps) < 4:
            best = comps
            for kk in [6, 8, 10]:
                cc = components_by_color(ori, rot, thr=15, sat_thr=0.01, k=kk, min_area=150)
                if len(cc) > len(best):
                    best = cc
            comps = best

        if id_ == "M04B" and len(comps) > 6:
            comps = sorted(comps, key=lambda c: c["area"], reverse=True)[:6]
        if id_ == "EB" and len(comps) > 4:
            comps = sorted(comps, key=lambda c: c["c"][1])[:4]
        if id_ == "CAFE" and len(comps) > 1:
            comps = sorted(comps, key=lambda c: c["area"], reverse=True)[:1]

        comp_map = {}
        for c in comps:
            raw = ocr_label_white(rot_bgr, c["bbox"])
            mode = "num" if id_ in ["M04A", "M04B", "M05A", "M05B", "EB"] else "auto"
            lab = normalize_label(raw, mode=mode)
            if not lab:
                continue
            if lab not in comp_map or c["area"] > comp_map[lab]["area"]:
                comp_map[lab] = c

        req = set([u for u in expected.get(id_, []) if u])
        if id_ == "EB":
            req = set(["1", "2", "3", "4"])
        if id_ == "M04A":
            req = set(["1", "2", "3", "4"])
        if id_ == "M05A":
            req = set(["1", "2", "3", "4"])
        if id_ == "M04B":
            req = set([str(i) for i in range(5, 11)])

        # M03: grilla completa (A..I, 4 o 5 columnas según fila)
        if id_ == "M03":
            from sklearn.cluster import KMeans
            pts = np.array([[c["c"][1]] for c in comps], dtype=np.float32)
            km = KMeans(n_clusters=9, random_state=0, n_init=10).fit(pts)
            centers = km.cluster_centers_.flatten()
            order = np.argsort(centers)
            letters = ["A", "B", "C", "D", "E", "F", "G", "H", "I"]
            row_counts = {}
            for idx, c in enumerate(comps):
                row = km.labels_[idx]
                rank = int(np.where(order == row)[0][0])
                row_counts.setdefault(letters[rank], 0)
                row_counts[letters[rank]] += 1
            full = set()
            for L, cnt in row_counts.items():
                cols = 5 if cnt >= 5 else 4
                for j in range(1, cols + 1):
                    full.add(f"{L}{j}")
            req = full

        zones = {}
        used = set()
        for lab in sorted(req):
            nl = normalize_label(lab)
            c = comp_map.get(nl)
            if c is None and nl.startswith("BASKET ") and nl.replace("BASKET ", "") in comp_map:
                c = comp_map[nl.replace("BASKET ", "")]
            if c is not None:
                zones[lab] = zone_dict(c)
                used.add(id(c))

        still = [lab for lab in sorted(req) if lab not in zones]
        avail = [c for c in comps if id(c) not in used]
        avail = sorted(avail, key=lambda c: (c["c"][1], c["c"][0]))

        def lab_key(s):
            s = s.strip().upper()
            m = re.match(r"^([A-Z]+)(\d+)$", s)
            if m:
                return (m.group(1), int(m.group(2)))
            m = re.match(r"^(\d+)$", s)
            if m:
                return ("", int(m.group(1)))
            return (s, 999)

        still = sorted(still, key=lab_key)
        for lab, c in zip(still, avail):
            zones[lab] = zone_dict(c)

        missing = still[len(avail):] if len(still) > len(avail) else []

        muebles[id_] = {"image": f"images/{base}_original.png", "zones": zones}
        reporte[id_] = {"components": len(comps), "ocr_labels": len(comp_map), "missing": missing}

    # Aliases por nombre (fallback)
    for name, mid in NAME_ALIAS.items():
        if mid in muebles:
            muebles[name] = muebles[mid]

    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    SALIDA.write_text(json.dumps(muebles, ensure_ascii=False, indent=2), encoding="utf-8")

    Path("data/reporte_muebles.json").write_text(json.dumps(reporte, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"OK: {SALIDA} (muebles={len(muebles)})")

if __name__ == "__main__":
    main()
``
