"""H14, camino C1, paso 3: georreferencia de nuestras huellas decodificadas del PNG VOLCAT contra event_idx.

Criterio: docs/own_volcat/eventos_h14/criterio_H14_2026-11-21.md, seccion "Georreferencia".

Decodificacion del PNG: la misma clasificacion de docs/own_volcat/reproducir_volcat/scripts/huella_png.py
(decodifica: saturacion >= 0,2, clase de la barra de src/process/volcat_colorbar, zona util del mapa, misma
proyeccion lat/lon del PNG de Chile_Central_2_km), pero muestreada en la latitud y longitud de cada pixel de la
grilla del archivo de evento en vez de la ventana de 83 x 94. No se importa huella_png porque arrastra los caches
de H11 (comun_h11) que aqui no hacen falta; las constantes de proyeccion se copian tal cual.

PNG: SOLO LECTURA. Busca en H14_PNG (lista de carpetas separadas por ';'). Del 13 y 18-11 no hay PNG en disco.

Uso:  python -I h14_georef.py
"""
import sys, os, glob, math, json, csv
import numpy as np
import netCDF4 as nc
from PIL import Image

sys.stdout.reconfigure(encoding="utf-8")
REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", ".."))
sys.path.insert(0, REPO)
from src.process import volcat_colorbar as vc  # noqa: E402

D = os.environ.get("H14_EVENTOS", r"D:\goes_notas\busqueda_2026-11-20\volcat_eventos_357070")
PNG_DIRS = os.environ.get("H14_PNG", r"C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes\data\raw\volcat_validacion\Chile_Central_2_km\frames;D:\goes_cache\h13\png").split(";")
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "resultados")

# proyeccion del PNG Chile_Central_2_km (copiada de huella_png.py)
dp = math.degrees(72.80000305175781 / 206264.796875)
LAT0 = -31.8007698059082 + 36 * dp
LON0 = 278.9210815429688 - 360.0
SHIFT = 5
CAJA = 10


def valido(shape):
    v = np.ones(shape, bool); v[:70] = False; v[640:, :140] = False; v[640:, 840:] = False
    return v


def ceniza_png(fn):
    """Mascara de ceniza del PNG en su propia grilla (misma clasificacion que huella_png.decodifica)."""
    a = np.asarray(Image.open(fn).convert("RGB"), dtype="float64"); hmap = int(vc.MAP_FRAC * a.shape[0])
    bins = vc.palette_bins(a[hmap:])
    if bins is None:
        return None
    m = a[:hmap]; cm = vc._saturation(m) >= 0.2
    ok = np.zeros(cm.shape, bool)
    if cm.any():
        ok[cm] = vc.classify_pixels(m[cm], bins)["ok"]
    return ok & valido(a.shape[:2])[:hmap]


def muestrea(ok, lat, lon):
    """Valor del PNG en cada (lat, lon); False fuera del mapa o donde lat/lon es NaN."""
    out = np.zeros(lat.shape, bool)
    f = np.isfinite(lat) & np.isfinite(lon)
    rr = np.full(lat.shape, -1); cc = np.full(lat.shape, -1)
    rr[f] = np.rint((LAT0 - lat[f]) / dp).astype(int); cc[f] = np.rint((lon[f] - LON0) / dp).astype(int)
    ins = f & (rr >= 0) & (rr < ok.shape[0]) & (cc >= 0) & (cc < ok.shape[1])
    out[ins] = ok[rr[ins], cc[ins]]
    return out


def png_de(t):
    pat = f"GOES-19.ABI.{t[:10]}.{t[11:13]}-{t[14:16]}-30.Ash_Height.Chile_Central_2_km.png"
    for d in PNG_DIRS:
        for fn in glob.glob(os.path.join(d, "*" + pat)):
            return fn
    return None


def iou(a, b):
    u = (a | b).sum()
    return float((a & b).sum() / u) if u else None


def main():
    filas = []
    for f in sorted(glob.glob(os.path.join(D, "*.nc"))):
        ds = nc.Dataset(f)
        t = ds.getncattr("time_coverage_start")
        fn = png_de(t)
        ev = np.asarray(ds["event_idx"][:]).astype(int) >= 0
        r = {"inicio_scan": t, "n_px_evento": int(ev.sum()), "png": os.path.basename(fn) if fn else None}
        if fn is None:
            filas.append(r); ds.close(); continue
        ok = ceniza_png(fn)
        if ok is None:
            r["png"] += " (sin barra)"; filas.append(r); ds.close(); continue
        lat = np.ma.filled(ds["latitude"][:].astype("f8"), np.nan); lon = np.ma.filled(ds["longitude"][:].astype("f8"), np.nan)
        plat = np.ma.filled(ds["pc_latitude"][:].astype("f8"), np.nan); plon = np.ma.filled(ds["pc_longitude"][:].astype("f8"), np.nan)
        png = muestrea(ok, lat, lon)
        rows, cols = np.where(ev)
        r0, r1 = max(rows.min() - CAJA, SHIFT), min(rows.max() + CAJA + 1, ev.shape[0] - SHIFT)
        c0, c1 = max(cols.min() - CAJA, SHIFT), min(cols.max() + CAJA + 1, ev.shape[1] - SHIFT)
        E = ev[r0:r1, c0:c1]
        P0 = png[r0:r1, c0:c1]
        r.update({"n_px_png_caja": int(P0.sum()), "iou_0": iou(E, P0),
                  "frac_evento_en_png_0": round(float((E & P0).sum() / E.sum()), 4),
                  "frac_png_en_evento_0": (round(float((E & P0).sum() / P0.sum()), 4) if P0.sum() else None)})
        # desfase: PNG[r+dr, c+dc] contra evento[r, c]; dr > 0 = el PNG cae dr filas mas al SUR
        mejor = (-1, 0, 0)
        for dr in range(-SHIFT, SHIFT + 1):
            for dc in range(-SHIFT, SHIFT + 1):
                P = png[r0 + dr:r1 + dr, c0 + dc:c1 + dc]
                v = iou(E, P)
                if v is not None and (v > mejor[0] or (v == mejor[0] and abs(dr) + abs(dc) < abs(mejor[1]) + abs(mejor[2]))):
                    mejor = (v, dr, dc)
        r.update({"iou_mejor": round(mejor[0], 4), "dr_filas": mejor[1], "dc_columnas": mejor[2]})
        # con paralaje: cuantos pixeles del evento, puestos en su lat/lon corregida, caen sobre ceniza del PNG
        pp = muestrea(ok, plat, plon)
        vp = ev & np.isfinite(plat)
        r["frac_evento_en_png_paralaje"] = round(float(pp[vp].mean()), 4) if vp.any() else None
        r["frac_evento_en_png_nominal"] = round(float(png[ev].mean()), 4)
        filas.append(r); ds.close()
    cols = list(dict.fromkeys(c for r in filas for c in r))
    with open(os.path.join(OUT, "georef.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols); w.writeheader(); w.writerows(filas)
    con = [r for r in filas if r.get("iou_0") is not None or "n_px_png_caja" in r]
    g5 = [r for r in con if r["n_px_evento"] >= 5]
    def mediana(k, rs):
        v = [r[k] for r in rs if r.get(k) is not None]
        return float(np.median(v)) if v else None
    res = {"cuadros_netcdf": len(filas), "cuadros_con_png": len(con),
           "sin_png": sorted({r["inicio_scan"][:10] for r in filas if r.get("png") is None}),
           "cuadros_huella_ge5": len(g5),
           "mediana_dr_filas_ge5": mediana("dr_filas", g5), "mediana_dc_columnas_ge5": mediana("dc_columnas", g5),
           "mediana_iou_0_ge5": mediana("iou_0", g5), "mediana_iou_mejor_ge5": mediana("iou_mejor", g5),
           "mediana_frac_evento_en_png_nominal_ge5": mediana("frac_evento_en_png_nominal", g5),
           "mediana_frac_evento_en_png_paralaje_ge5": mediana("frac_evento_en_png_paralaje", g5),
           "mediana_frac_png_en_evento_0_ge5": mediana("frac_png_en_evento_0", g5),
           "cuadros_png_sin_ceniza_en_caja": sum(1 for r in con if r["n_px_png_caja"] == 0),
           "desfases_ge5": [[r["inicio_scan"][11:16], r["dr_filas"], r["dc_columnas"], r["iou_mejor"]] for r in g5]}
    json.dump(res, open(os.path.join(OUT, "georef_resumen.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(res, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
