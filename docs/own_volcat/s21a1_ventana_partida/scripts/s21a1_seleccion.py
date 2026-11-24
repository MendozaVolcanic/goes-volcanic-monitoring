r"""S21a1: aplica la regla del criterio §1 (version 1, commit d91f2eb) para elegir la pasada de Landsat.

Solo reflectancia (Landsat C2 L2 de Planetary Computer, regla de mascara de s20b_preparar sin cambios) y la Fmask de
HLS L30. No lee ninguna banda termica ni BTD.

Por que asi: la pasada se elige por lo que se ve en el visible y en 1,6 um (pluma translucida sobre nieve, cumbre
despejada), nunca por el termico, para que la medida de la ventana partida no influya en que caso se mide.

Cache de reflectancia: se reusa la de S20b (D:\goes_notas\s20b, solo lectura); lo nuevo va a D:\goes_notas\s21\a1.
Salida: resultados/seleccion.json y mascara_<dia>.npz en D:\goes_notas\s21\a1.

Uso: python -I s21a1_seleccion.py
"""
import json
import os
import sys

import numpy as np
from rasterio.enums import Resampling
from scipy import ndimage

sys.stdout.reconfigure(encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
S20B = os.path.join(AQUI, "..", "..", "s20b_verdad_alta_res", "scripts")
sys.path.insert(0, S20B)
import s20b_comun as S  # noqa: E402
import s20b_preparar as P  # noqa: E402

RES = os.path.join(os.path.dirname(AQUI), "resultados")
A1 = r"D:\goes_notas\s21\a1"
HLS_A1 = os.path.join(A1, "hls")
HLS_S20 = r"D:\goes_notas\s20b\descargas"

# regla del criterio §1
FMASK_MAX_DISCO, FMASK_MAX_CUMBRE = 0.30, 0.30     # nube o sombra en 2 a 15 km y en 0 a 5 km
MIN_EROS3, FMASK_MAX_MASC, DMIN_MAX = 100, 0.20, 6.0

CAND = {  # dia: (id Landsat C2 L2 fila 085 o None, granulo HLS o None, nube catalogo PC, nube catalogo HLS)
    "2026-09-15": ("LC09_L2SP_233085_20260915_02_T1", "HLS.L30.T19HBV.2026258T143426.v2.0", 4.16, 0),
    "2026-09-23": ("LC08_L2SP_233085_20260923_02_T2", None, 100.0, None),
    "2026-10-01": ("LC09_L2SP_233085_20261001_02_T1", "HLS.L30.T19HBV.2026274T143434.v2.0", 53.59, 91),
    "2026-10-09": ("LC08_L2SP_233085_20261009_02_T1", "HLS.L30.T19HBV.2026282T143431.v2.0", 47.71, 77),
    "2026-10-17": ("LC09_L2SP_233085_20261017_02_T1", "HLS.L30.T19HBV.2026290T143436.v2.0", 22.92, 56),
    "2026-11-02": ("LC09_L2SP_233085_20261102_02_T1", "HLS.L30.T19HBV.2026306T143434.v2.0", 17.94, 13),
    "2026-11-10": (None, "HLS.L30.T19HBV.2026314T143439.v2.0", None, 93),
    "2026-11-18": ("LC09_L2SP_233085_20261118_02_T1", "HLS.L30.T19HBV.2026322T143436.v2.0", 53.17, 83),
}

_bandas_orig = P.bandas


def bandas(it):
    """Reflectancia con cache: primero la de S20b (solo lectura), si no, baja y guarda en D:\\goes_notas\\s21\\a1."""
    viejo = os.path.join(S.TRABAJO, it["id"] + ".npz")
    if os.path.exists(viejo):
        return dict(np.load(viejo))
    S.TRABAJO = A1
    try:
        return _bandas_orig(it)
    finally:
        S.TRABAJO = r"D:\goes_notas\s20b"


P.bandas = bandas


def fmask_de(gran):
    for base in (HLS_A1, os.path.join(HLS_S20, "HLSL30_ref"), os.path.join(HLS_S20, "HLSL30")):
        f = os.path.join(base, gran, f"{gran}.Fmask.tif")
        if os.path.exists(f):
            fm = S.leer(f, rs=Resampling.nearest, nodata=255)
            fi = np.nan_to_num(fm, nan=255).astype(int)
            return np.isfinite(fm), ((fi >> 1) & 7) > 0, ((fi >> 4) & 1) == 1
    raise FileNotFoundError(gran)


def mascara(dia, iid):
    it = P.item_pc(iid)
    bo = bandas(it)
    br, quien, usadas = P.referencia_compuesta(dia, iid)
    nieve = P.nieve_de(br)
    ok = np.isfinite(bo["swir16"]) & np.isfinite(bo["red"])
    with np.errstate(invalid="ignore"):
        pl = (nieve & ok & ((bo["swir16"] - br["swir16"]) > P.DSW1_MIN) & (bo["red"] > P.ROJO_MIN)
              & (P.ndsi(bo) < P.NDSI_OBJ_MAX))
    pl = P.limpiar(pl)
    np.savez_compressed(os.path.join(A1, f"mascara_{dia}.npz"), pluma=pl, nieve=nieve, ok=ok, quien=quien)
    return pl, nieve, ok, usadas, bo


def main():
    os.makedirs(RES, exist_ok=True)
    d = S.hav(S.GLAT, S.GLON, *S.CRATER)
    disco, cumbre = (d >= 2) & (d <= 15), d <= 5
    out = {"regla": {"FMASK_MAX_DISCO": FMASK_MAX_DISCO, "FMASK_MAX_CUMBRE": FMASK_MAX_CUMBRE,
                     "MIN_EROS3": MIN_EROS3, "FMASK_MAX_MASC": FMASK_MAX_MASC, "DMIN_MAX_km": DMIN_MAX}}
    for dia, (iid, gran, cc_pc, cc_hls) in CAND.items():
        r = {"landsat_c2": iid, "hls": gran, "nube_catalogo_pc": cc_pc, "nube_catalogo_hls": cc_hls}
        out[dia] = r
        if gran is None:
            r.update({"sirve": False, "motivo": "paso 0: 100 % de nube en Planetary Computer y sin granulo HLS"})
            print(dia, json.dumps(r, ensure_ascii=False), flush=True)
            continue
        val, nube, nv = fmask_de(gran)
        r["fmask_nube_sombra_2_15km"] = P_(nube[disco & val])
        r["fmask_nube_sombra_0_5km"] = P_(nube[cumbre & val])
        r["fmask_nieve_0_5km"] = P_(nv[cumbre & val])
        if r["fmask_nube_sombra_2_15km"] > FMASK_MAX_DISCO or r["fmask_nube_sombra_0_5km"] > FMASK_MAX_CUMBRE:
            r.update({"sirve": False, "motivo": "paso 1: cumbre o disco con nube"})
            print(dia, json.dumps(r, ensure_ascii=False), flush=True)
            continue
        if iid is None:
            r.update({"sirve": None, "motivo": "paso 1 pasa pero no hay C2 L2 en Planetary Computer: falta HLS"})
            print(dia, json.dumps(r, ensure_ascii=False), flush=True)
            continue
        pl, nieve, ok, usadas, _ = mascara(dia, iid)
        e3 = ndimage.binary_erosion(pl, iterations=3)
        fo = P.forma(pl)
        r.update({"referencias": [(u["id"], u["celdas_aportadas"]) for u in usadas],
                  "frac_nieve_ref_2_15km": P_(nieve[disco]), "celdas_mascara": int(pl.sum()),
                  "celdas_erosion_3": int(e3.sum()), "forma": fo,
                  "fmask_nube_sombra_mascara": P_(nube[pl & val]) if pl.any() else None})
        motivos = []
        if e3.sum() < MIN_EROS3:
            motivos.append(f"paso 3: {int(e3.sum())} celdas erosionadas (< {MIN_EROS3})")
        if pl.any() and r["fmask_nube_sombra_mascara"] > FMASK_MAX_MASC:
            motivos.append("paso 3: Fmask marca nube o sombra en la mascara")
        if pl.any() and fo.get("dist_min_km", 99) > DMIN_MAX:
            motivos.append("paso 3: la mascara empieza a mas de 6 km del crater")
        r.update({"sirve": not motivos, "motivo": "; ".join(motivos) or "cumple los pasos 1 a 3"})
        print(dia, json.dumps({k: v for k, v in r.items() if k != "referencias"}, ensure_ascii=False), flush=True)
    sirven = [k for k, v in out.items() if isinstance(v, dict) and v.get("sirve") is True]
    sirven.sort(key=lambda k: -out[k]["celdas_erosion_3"])
    out["elegida"] = sirven[0] if sirven else None
    out["tambien_sirven"] = sirven[1:]
    print("elegida", out["elegida"], "tambien", out["tambien_sirven"], flush=True)
    with open(os.path.join(RES, "seleccion.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1)


def P_(b):
    return round(float(np.mean(b)), 4) if b.size else None


if __name__ == "__main__":
    main()
