r"""S31g: cataloga la Sentinel-2C del 25-11-2026 14:43 UTC como verdad fina (criterio_2026-11-27.md §2).

Que hace y por que:
  (a) aplica la mascara de S20b SIN CAMBIOS (s20b_preparar: referencia compuesta a +-10 dias, primero las
      anteriores; nieve de referencia; SWIR1, rojo y NDSI del dia) para saber si hay algo sobre la nieve que
      ensucie el 1,6 um, y donde;
  (b) dibuja color verdadero (TCI de 10 m) y el compuesto SWIR del dia y de la referencia que mas celdas aporta, para
      que el rotulo (PLUMA VISIBLE, BOCANADA CHICA, SIN PLUMA VISIBLE, NO DECIDIBLE) se lea en la imagen y no solo en
      la mascara, que en Sentinel-2 marca borde de nieve en fusion (S21a2).
  No lee GOES, ni termico, ni VIIRS.

Cache: reflectancias ya bajadas por S20b, S21a1 y S21a2 en D: (solo lectura); lo nuevo va a D:\goes_notas\s31\s31g.
Salidas: resultados/s2_2026-11-25.json, figuras/s2_2026-11-25_color.png y s2_2026-11-25_swir.png.

Uso: python -I -B s31g_s2_25nov.py
"""
import json
import math
import os
import sys

import numpy as np
import rasterio
from rasterio.enums import Resampling
from rasterio.transform import from_origin
from rasterio.vrt import WarpedVRT
from scipy import ndimage

sys.stdout.reconfigure(encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
S20B = os.path.join(AQUI, "..", "..", "s20b_verdad_alta_res", "scripts")
sys.path.insert(0, S20B)
import s20b_comun as C  # noqa: E402
import s20b_preparar as P  # noqa: E402

RES = os.path.join(os.path.dirname(AQUI), "resultados")
FIG = os.path.join(os.path.dirname(AQUI), "figuras")
TRAB = r"D:\goes_notas\s31\s31g"
CACHES = [r"D:\goes_notas\s20b", r"D:\goes_notas\s21\a1", r"D:\goes_notas\s21\a2"]
DIA = "2026-11-25"
OBJ_ID = "S2C_19HBV_20261125_0_L2A"

_bandas_orig = P.bandas


def bandas(it):
    """Reflectancia con cache: primero las de sesiones anteriores (solo lectura), si no, baja a TRAB."""
    for c in CACHES + [TRAB]:
        f = os.path.join(c, it["id"] + ".npz")
        if os.path.exists(f):
            return dict(np.load(f))
    viejo = C.TRABAJO
    C.TRABAJO = TRAB
    try:
        return _bandas_orig(it)
    finally:
        C.TRABAJO = viejo


P.bandas = bandas


def tci(it, medio_m=10000.0, res=10.0):
    """Color verdadero (asset visual, 10 m) en UTM 19 S, +-medio_m alrededor del crater."""
    n = int(2 * medio_m / res)
    tr = from_origin(C.CX - medio_m, C.CY + medio_m, res, res)
    with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR", GDAL_HTTP_MAX_RETRY="4"):
        with rasterio.open(it["assets"]["visual"]["href"]) as ds:
            with WarpedVRT(ds, crs=C.CRS, transform=tr, width=n, height=n, resampling=Resampling.bilinear) as v:
                return np.moveaxis(v.read([1, 2, 3]), 0, -1)


def main():
    os.makedirs(TRAB, exist_ok=True)
    os.makedirs(RES, exist_ok=True)
    os.makedirs(FIG, exist_ok=True)
    dem = np.load(os.path.join(r"D:\goes_notas\s20b", "dem_local.npy")).astype(float)
    it = P.item_e84(OBJ_ID)
    bo = bandas(it)
    br, quien, usadas = P.referencia_compuesta(DIA, OBJ_ID)
    nieve = P.nieve_de(br)
    ok = np.isfinite(bo["swir16"]) & np.isfinite(bo["red"])
    with np.errstate(invalid="ignore"):
        pl = (nieve & ok & ((bo["swir16"] - br["swir16"]) > P.DSW1_MIN) & (bo["red"] > P.ROJO_MIN)
              & (P.ndsi(bo) < P.NDSI_OBJ_MAX))
    pl = P.limpiar(pl)
    d = C.hav(C.GLAT, C.GLON, *C.CRATER)
    p = it["properties"]
    fo = P.forma(pl)
    alt, _ = P.altura_por_sombra(pl, nieve & ok, bo, br, p["view:sun_azimuth"], p["view:sun_elevation"], dem,
                                 fo.get("azimut_eje_grados_0_180", 0.0))
    pl6 = pl & (d <= 6)
    lab, nc = ndimage.label(pl, structure=np.ones((3, 3)))
    comp = []
    for k in range(1, nc + 1):
        m = lab == k
        comp.append({"celdas": int(m.sum()), "dist_min_km": round(float(d[m].min()), 2),
                     "azimut_centroide": P.forma(m).get("azimut_centroide_desde_crater")})
    comp.sort(key=lambda x: x["dist_min_km"])
    with np.errstate(invalid="ignore"):
        nube_dia = bo["nube"] & (d <= 15)
    out = {"objetivo": OBJ_ID, "hora_utc": p["datetime"], "nube_catalogo": p.get("eo:cloud_cover"),
           "sol_azimut": round(p["view:sun_azimuth"], 1), "sol_elevacion": round(p["view:sun_elevation"], 1),
           "referencias": usadas, "frac_nieve_ref_15km": round(float(nieve[d <= 15].mean()), 3),
           "frac_nieve_ref_0_5km": round(float(nieve[d <= 5].mean()), 3),
           "scl_nube_0_15km": round(float(nube_dia.sum() / (d <= 15).sum()), 4),
           "scl_nube_0_5km": round(float((bo["nube"] & (d <= 5)).sum() / (d <= 5).sum()), 4),
           "celdas_mascara": int(pl.sum()), "area_mascara_km2": round(pl.sum() * 9e-4, 3),
           "area_mascara_0_6km_km2": round(pl6.sum() * 9e-4, 3), "forma": fo, "altura_sombra": alt,
           "componentes": len(comp), "componentes_mas_cercanos": comp[:10]}
    with open(os.path.join(RES, f"s2_{DIA}.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in out.items() if k != "referencias"}, ensure_ascii=False, indent=1))
    for u in usadas:
        print("referencia", u, flush=True)
    figuras(it, bo, br, pl, usadas)


def figuras(it, bo, br, pl, usadas):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    # referencia que mas celdas aporto, para el color verdadero de comparacion
    ref_id = max(usadas, key=lambda u: u["celdas_aportadas"])["id"]
    ref_it = P.item_e84(ref_id) if ref_id.startswith("S2") else None
    a = tci(it)
    fig, ax = plt.subplots(1, 2 if ref_it else 1, figsize=(16 if ref_it else 8, 8), constrained_layout=True)
    ax = np.atleast_1d(ax)
    ext = [-10, 10, -10, 10]
    c, w = C.N // 2, int(10000 / C.RES_M)
    sl = (slice(c - w, c + w), slice(c - w, c + w))
    for j, (tit, img) in enumerate([(f"{DIA} 14:43 UTC, Sentinel-2C", a)] +
                                   ([(f"referencia {ref_id}", tci(ref_it))] if ref_it else [])):
        ax[j].imshow(img, extent=ext)
        ax[j].contour(pl[sl][::-1], levels=[0.5], colors="magenta", linewidths=0.7, extent=ext)
        ax[j].plot(0, 0, "^", mfc="none", mec="yellow", ms=10)
        for r in (1, 6):
            t = np.linspace(0, 2 * math.pi, 200)
            ax[j].plot(r * np.sin(t), r * np.cos(t), "y:", lw=0.7)
        ax[j].set_title(f"Color verdadero {tit}")
        ax[j].set_xlabel("km al E del crater")
        ax[j].set_ylabel("km al N")
    fig.suptitle("Nevados de Chillan. Magenta: mascara de S20b. Circulos punteados: 1 y 6 km del crater")
    fig.savefig(os.path.join(FIG, f"s2_{DIA}_color.png"), dpi=70)
    plt.close(fig)

    def st(b, lo, hi):
        return np.clip((np.nan_to_num(b) - lo) / (hi - lo), 0, 1)
    fig, ax = plt.subplots(1, 2, figsize=(16, 8), constrained_layout=True)
    for j, (tit, b) in enumerate(((f"{DIA} (dia)", bo), ("referencia compuesta", br))):
        rgb = np.dstack([st(b["swir22"], 0, 0.4), st(b["swir16"], 0, 0.4), st(b["red"], 0, 1.2)])[sl]
        ax[j].imshow(rgb, extent=ext)
        ax[j].contour(pl[sl][::-1], levels=[0.5], colors="magenta", linewidths=0.7, extent=ext)
        ax[j].plot(0, 0, "^", mfc="none", mec="yellow", ms=10)
        ax[j].set_title(f"SWIR2, SWIR1, rojo: {tit}. Nieve azul oscura; nube o ceniza clara")
        ax[j].set_xlabel("km al E del crater")
    fig.savefig(os.path.join(FIG, f"s2_{DIA}_swir.png"), dpi=70)
    plt.close(fig)


if __name__ == "__main__":
    main()
