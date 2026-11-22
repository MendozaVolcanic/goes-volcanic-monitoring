"""S16 tarea 4a: probabilidad de ceniza por píxel que publica VOLCAT (imagen Ash_Probability del sitio) en la huella
event_idx de los 60 cuadros de evento de Chillán, con control pareado por BT11.

Criterio: docs/own_volcat/sitio_volcat/criterio_2026-11-22.md (commiteado antes de medir).

Entradas (solo lectura, fuera del repo):
  S16_EVENTOS  NetCDF de evento VOLCAT vid 357070 (licencia restringida, no se copian)
  S16_PNG      PNG Ash_Probability de Chile_Central_2_km bajados de volcano.ssec.wisc.edu
  S16_VOLC     capa VOLCANOES.CYAN del sector (control de georreferencia)
Uso: python -I prob_sitio.py
"""
import sys, os, glob, math, json, csv
import numpy as np
import netCDF4 as nc
from PIL import Image

sys.stdout.reconfigure(encoding="utf-8")
EV = os.environ.get("S16_EVENTOS", r"D:\goes_notas\busqueda_2026-11-20\volcat_eventos_357070")
PNG = os.environ.get("S16_PNG", r"D:\goes_notas\s16\sitio\png")
VOLC = os.environ.get("S16_VOLC", r"D:\goes_notas\s16\sitio\Chile_Central_2_km.VOLCANOES.CYAN.png")
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "resultados")

# proyección CE del PNG Chile_Central_2_km (la misma de h14_georef.py)
dp = math.degrees(72.80000305175781 / 206264.796875)
LAT0 = -31.8007698059082 + 36 * dp
LON0 = 278.9210815429688 - 360.0
CRATER = (-36.863, -71.377)

# barra: 15 bloques de 30 px desde x=503 (borde negro en 502), muestreados en su centro, fila 760
BARRA_X = [503 + 30 * i + 15 for i in range(15)]
BARRA_Y = 760
# P mínima de cada bloque en %: B0..B6 bajo 20 % (log), B7..B14 = 20, 30, ..., 90
B_MIN_20, B_MIN_50 = 7, 10
DIST_MAX, SAT_MIN = 30.0, 0.2
MAPA_FILAS = 740  # todo lo que está bajo esta fila es leyenda


def saturacion(a):
    mx, mn = a.max(-1), a.min(-1)
    return np.where(mx > 0, (mx - mn) / np.maximum(mx, 1), 0)


def decodifica(fn):
    """Devuelve (bloque por píxel del mapa: -1 sin color, -2 color no decodificable; colores de la barra)."""
    a = np.asarray(Image.open(fn).convert("RGB"), dtype="f8")
    barra = np.array([a[BARRA_Y, x] for x in BARRA_X])
    m = a[:MAPA_FILAS]
    out = np.full(m.shape[:2], -1, int)
    col = saturacion(m) >= SAT_MIN
    if col.any():
        d = np.linalg.norm(m[col][:, None, :] - barra[None], axis=-1)
        k = d.argmin(1)
        k[d.min(1) >= DIST_MAX] = -2
        out[col] = k
    # zonas no cartográficas: logos y globo (mismas máscaras de h14_georef.valido) y título
    out[:70] = -3; out[640:, :140] = -3; out[640:, 840:] = -3
    return out, barra


def a_pixel(lat, lon):
    return np.rint((LAT0 - lat) / dp).astype(int), np.rint((lon - LON0) / dp).astype(int)


def muestrea(B, lat, lon):
    out = np.full(lat.shape, -9, int)
    f = np.isfinite(lat) & np.isfinite(lon)
    rr = np.full(lat.shape, -1); cc = np.full(lat.shape, -1)
    rr[f], cc[f] = a_pixel(lat[f], lon[f])
    ins = f & (rr >= 0) & (rr < B.shape[0]) & (cc >= 0) & (cc < B.shape[1])
    out[ins] = B[rr[ins], cc[ins]]
    return out


def dilata(m, n):
    o = m.copy()
    for _ in range(n):
        p = o.copy()
        p[1:] |= o[:-1]; p[:-1] |= o[1:]; p[:, 1:] |= o[:, :-1]; p[:, :-1] |= o[:, 1:]
        o = p
    return o


def pareo_bt11(bt, huella, candidatos, tol=0.5):
    """1 a 1 sin reposición por BT11 (vecino más cercano). Devuelve índices planos del control."""
    hv = np.flatnonzero(huella.ravel()); cv = np.flatnonzero(candidatos.ravel())
    btf = bt.ravel()
    cv = cv[np.isfinite(btf[cv])]
    orden = np.argsort(btf[cv]); cv = cv[orden]; cb = btf[cv]
    usado = np.zeros(cv.size, bool); ctrl = []
    for h in hv:
        if not np.isfinite(btf[h]):
            continue
        i = np.searchsorted(cb, btf[h]); best = None
        for j in range(max(i - 50, 0), min(i + 50, cv.size)):
            if usado[j]:
                continue
            dj = abs(cb[j] - btf[h])
            if dj <= tol and (best is None or dj < best[0]):
                best = (dj, j)
        if best:
            usado[best[1]] = True; ctrl.append(cv[best[1]])
    return np.array(ctrl, int)


def metricas(v):
    v = v[v >= -2]  # fuera del mapa o zona no cartográfica no cuenta
    n = v.size
    if n == 0:
        return {"n": 0}
    color = v >= 0
    return {"n": int(n), "frac_color": round(float(color.mean()), 4),
            "frac_mezcla": round(float((v == -2).mean()), 4),
            "frac_ge20": round(float((v >= B_MIN_20).mean()), 4),
            "frac_ge50": round(float((v >= B_MIN_50).mean()), 4),
            "bloque_mediano": float(np.median(np.where(v >= 0, v, -1)))}


def main():
    os.makedirs(OUT, exist_ok=True)
    filas = []
    # control de georreferencia: centroide del glifo cian más cercano al cráter calculado
    vo = np.asarray(Image.open(VOLC).convert("RGBA"), dtype="f8")
    r0, c0 = a_pixel(np.array(CRATER[0]), np.array(CRATER[1]))
    # el glifo es un triángulo con el nombre a la derecha: se toma sólo la componente conexa más cercana
    # (las letras son componentes aparte y correrían el centroide al E)
    from scipy import ndimage
    lab, _ = ndimage.label(vo[..., 3] > 100)
    ys, xs = np.where(lab > 0)
    k = lab[ys[np.argmin(np.hypot(ys - r0, xs - c0))], xs[np.argmin(np.hypot(ys - r0, xs - c0))]]
    ty, tx = np.where(lab == k)
    geo = {"crater_calculado_rc": [int(r0), int(c0)],
           "triangulo_cian_centroide_rc": [round(float(ty.mean()), 1), round(float(tx.mean()), 1)],
           "triangulo_px": int(ty.size),
           "distancia_px": round(float(np.hypot(ty.mean() - r0, tx.mean() - c0)), 2)}
    barras = []
    for f in sorted(glob.glob(os.path.join(EV, "*.nc"))):
        ds = nc.Dataset(f)
        t = ds.getncattr("time_coverage_start")
        fn = os.path.join(PNG, f"GOES-19.ABI.{t[:10]}.{t[11:13]}-{t[14:16]}-30.Ash_Probability.Chile_Central_2_km.png")
        ev = np.asarray(ds["event_idx"][:]).astype(int) >= 0
        sza = float(np.ma.filled(ds["mean_feature_solar_zenith_angle"][:], np.nan).ravel()[0])
        r = {"inicio_scan": t, "evento": str(np.asarray(ds["event_type"][:]).ravel()[0]),
             "sza": round(sza, 1), "n_huella": int(ev.sum()), "png": os.path.exists(fn)}
        if not r["png"]:
            filas.append(r); ds.close(); continue
        B, barra = decodifica(fn); barras.append(barra)
        mapa = B[B >= -2]
        r["px_color_imagen"] = int((mapa >= 0).sum())
        rr, cc = np.mgrid[:B.shape[0], :B.shape[1]]
        en50 = np.hypot((rr - r0) * dp * 111.0, (cc - c0) * dp * 111.0 * math.cos(math.radians(CRATER[0]))) <= 50
        r["px_color_50km"] = int(((B >= 0) & en50).sum())
        r["bloque_max_50km"] = int(B[en50].max())
        lat = np.ma.filled(ds["latitude"][:].astype("f8"), np.nan); lon = np.ma.filled(ds["longitude"][:].astype("f8"), np.nan)
        bt = np.ma.filled(ds["brightness_temperature_11micron"][:].astype("f8"), np.nan)
        cand = ~dilata(ev, 2) & np.isfinite(lat)
        ctrl = pareo_bt11(bt, ev, cand)
        r["n_control"] = int(ctrl.size)
        for nombre, (dr, dc) in (("nom", (0, 0)), ("desf", (1, 1))):
            # PNG[r+dr, c+dc] contra evento[r, c] (convención de h14_georef: dr > 0 = PNG más al sur)
            la = np.full(lat.shape, np.nan); lo = np.full(lon.shape, np.nan)
            la[:lat.shape[0] - dr, :lat.shape[1] - dc] = lat[dr:, dc:]; lo[:lon.shape[0] - dr, :lon.shape[1] - dc] = lon[dr:, dc:]
            v = muestrea(B, la, lo)
            for k, x in metricas(v[ev]).items():
                r[f"{nombre}_huella_{k}"] = x
            for k, x in metricas(v.ravel()[ctrl]).items():
                r[f"{nombre}_ctrl_{k}"] = x
        filas.append(r); ds.close()
    # control de la barra: los 15 bloques iguales en todos los PNG
    bs = np.array(barras); barra_ok = float(np.abs(bs - bs[0]).max()) if len(bs) else None
    claves = sorted({k for r in filas for k in r}, key=lambda k: (k != "inicio_scan", k))
    with open(os.path.join(OUT, "por_cuadro.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, claves); w.writeheader(); w.writerows(filas)
    # veredicto
    res = {"geo": geo, "barra_rgb": bs[0].round().tolist() if len(bs) else None, "barra_dif_max_entre_png": barra_ok,
           "cuadros": len(filas), "con_png": sum(r["png"] for r in filas),
           "sin_color_en_imagen": sum(1 for r in filas if r.get("px_color_imagen") == 0)}
    for nombre in ("nom", "desf"):
        g = [r for r in filas if r.get("n_huella", 0) >= 5 and r.get("px_color_imagen", 0) > 0 and r.get(f"{nombre}_huella_n", 0) > 0]
        alta = [r for r in g if r[f"{nombre}_huella_frac_ge50"] >= 0.5 and r[f"{nombre}_huella_frac_ge50"] - r.get(f"{nombre}_ctrl_frac_ge50", 0) >= 0.3]
        baja = [r for r in g if r[f"{nombre}_huella_frac_ge20"] <= 0.1]
        med = lambda k: round(float(np.median([r[k] for r in g if k in r])), 4) if g else None
        v = "ALTA" if g and len(alta) >= 0.5 * len(g) else ("BAJA" if g and len(baja) >= 0.5 * len(g) else "NO CONCLUYENTE")
        res[nombre] = {"cuadros_ge5": len(g), "cumplen_alta": len(alta), "cumplen_baja": len(baja), "veredicto": v,
                       "mediana_huella_frac_color": med(f"{nombre}_huella_frac_color"), "mediana_ctrl_frac_color": med(f"{nombre}_ctrl_frac_color"),
                       "mediana_huella_frac_ge20": med(f"{nombre}_huella_frac_ge20"), "mediana_ctrl_frac_ge20": med(f"{nombre}_ctrl_frac_ge20"),
                       "max_huella_frac_ge20": max((r[f"{nombre}_huella_frac_ge20"] for r in g), default=None),
                       "max_huella_frac_ge50": max((r[f"{nombre}_huella_frac_ge50"] for r in g), default=None)}
    res["veredicto"] = res["nom"]["veredicto"] if res["nom"]["veredicto"] == res["desf"]["veredicto"] else "NO CONCLUYENTE (nominal y desfase difieren)"
    json.dump(res, open(os.path.join(OUT, "resumen.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print(json.dumps(res, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
