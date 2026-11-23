r"""H29, paso previo al criterio (NO mira temperaturas de la pluma): huella del 08-11 desde los PNG, cobertura en la
ventana del cubo, georreferencia contra la grilla y la capa de volcanes, y cuantos dias de fondo despejado hay en
esos pixeles y horas segun la ACMF.

Por que primero esto: H24 mostro que la tarde de primavera casi no tiene fondo despejado. Antes de escribir una regla
hay que saber cuantos pixeles lejanos publica VOLCAT ese dia y cuantos dias sirven de comparacion.

Salidas: resultados/preparar_por_cuadro.csv (conteos sin posiciones), resultados/preparar_resumen.json, y la huella
por pixel en D:\goes_notas\s19\h29\huella_0811.npz (derivada de SSEC, no va al repo).
Uso: python -I h29_preparar.py
"""
import csv
import json
import os
import sys
from datetime import datetime, timedelta

import numpy as np
from PIL import Image
from scipy import ndimage

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import h29_comun as C  # noqa: E402

T0 = datetime(2026, 9, 21)
NDIAS = 62
DIA_EV = (datetime(2026, 11, 8) - T0).days
LEJOS_KM = 30.0
MEDIO_KM = 15.0
# dias con objeto VOLCAT, marca VOLCAT (H21), pulso REAV o VCB: los mismos que excluye H24 (con su enmienda 1)
EXCLUIDOS = ["2026-10-25", "2026-10-27", "2026-10-28", "2026-11-10", "2026-11-12", "2026-10-24", "2026-10-29",
             "2026-10-30", "2026-11-06", "2026-11-07", "2026-11-08", "2026-11-13", "2026-11-14", "2026-11-18",
             "2026-10-22", "2026-11-11", "2026-11-16"]
DIA_EXCL = np.zeros(NDIAS, bool)
for s in EXCLUIDOS:
    DIA_EXCL[(datetime.strptime(s, "%Y-%m-%d") - T0).days] = True
VENT_DIAS = 21


def cargar_acm():
    partes = [(r"D:\goes_notas\s17\h23\acm_oct.npz", datetime(2026, 9, 21)),
              (r"D:\goes_notas\s18\h24\acm_oct.npz", datetime(2026, 10, 24)),
              (r"D:\goes_notas\s17\h23\acm_nov.npz", datetime(2026, 11, 1))]
    acm = np.full((NDIAS * 144, C.NY * C.NX), 255, "uint8")
    for f, t0 in partes:
        a = np.load(f)["acm"]
        i0 = (t0 - T0).days * 144
        acm[i0:i0 + a.shape[0]] = a.reshape(a.shape[0], -1)
    return acm.reshape(NDIAS, 144, C.NY, C.NX)


def georef():
    """Grilla LATLON.CYAN: centro de cada linea contra la posicion calculada. VOLCANOES.CYAN: esquina del glifo."""
    out = {}
    g = np.asarray(Image.open(os.path.join(C.CAPAS, "Chile_Central_2_km.LATLON.CYAN.png")).convert("RGBA"), "f8")[..., 3]
    filas, cols = [], []
    for lat in (-34, -36, -38, -40, -42):
        p = (C.LAT0 - lat) / C.DP
        r0 = int(round(p))
        prof = g[r0 - 5:r0 + 6, 600:700].mean(1)
        rr = np.arange(r0 - 5, r0 + 6)
        filas.append({"lat": lat, "calc": round(p, 2), "centro_linea": round(float((prof * rr).sum() / prof.sum()), 2),
                      "borde_sup": int(rr[np.argmax(prof > 20)])})
    for lon in (-75, -70):
        p = (lon - C.LON0) / C.DP
        c0 = int(round(p))
        prof = g[400:500, c0 - 5:c0 + 6].mean(0)
        cc = np.arange(c0 - 5, c0 + 6)
        cols.append({"lon": lon, "calc": round(p, 2), "centro_linea": round(float((prof * cc).sum() / prof.sum()), 2),
                     "borde_izq": int(cc[np.argmax(prof > 20)])})
    out["grilla_filas"], out["grilla_cols"] = filas, cols
    v = np.asarray(Image.open(os.path.join(C.CAPAS, "Chile_Central_2_km.VOLCANOES.CYAN.png")).convert("RGBA"), "f8")[..., 3]
    lab, n = ndimage.label(v > 100)
    sl = ndimage.find_objects(lab)
    volc = {"chillan": (-36.86, -71.38), "antuco": (-37.41, -71.35), "callaqui": (-37.92, -71.45),
            "copahue": (-37.85, -71.17), "longavi": (-36.19, -71.16)}
    vv = []
    for k, (la, lo) in volc.items():
        r, c = (C.LAT0 - la) / C.DP, (lo - C.LON0) / C.DP
        best = min(range(n), key=lambda i: abs(sl[i][0].start - r) + abs(sl[i][1].start - c))
        vv.append({"volcan": k, "calc_rc": [round(r, 1), round(c, 1)],
                   "glifo_esquina_rc": [sl[best][0].start, sl[best][1].start],
                   "glifo_alto_ancho": [sl[best][0].stop - sl[best][0].start, sl[best][1].stop - sl[best][1].start]})
    out["volcanes"] = vv
    return out


def main():
    os.makedirs(C.RES, exist_ok=True)
    os.makedirs(C.TRABAJO, exist_ok=True)
    geo = georef()
    print(json.dumps(geo, ensure_ascii=False))
    acm = cargar_acm()
    # H23 E1: >= 80 % del terreno bajo de Chillan (10 a 30 km, cota < 1.300 m) despejado
    la, lo, h = -36.86, -71.38, 3212
    d = C.hav(C.LAT, C.LON, la - 0.93 * h / 1000.0 / 111.2, lo)
    bajo = (d >= 10) & (d <= 30) & (C.ZDEM < 1300)
    E1 = (acm[:, :, bajo] <= 1).mean(2) >= 0.80                    # (dia, slot)
    nulos = [dd for dd in range(DIA_EV - VENT_DIAS, DIA_EV + VENT_DIAS + 1) if 0 <= dd < NDIAS and not DIA_EXCL[dd]]
    filas, huellas = [], {}
    for fn in C.frames_del_dia():
        t = C.dt_de(fn)
        ok, mid, bok = C.decodifica_png(fn)
        if not bok:
            filas.append({"hora": f"{t:%H:%M}", "barra": False})
            continue
        fu, de = C.fuera_de_ventana(ok)
        s = t.hour * 6 + t.minute // 10
        for nombre, desf in (("h14", C.DESF_H14), ("nom", (0, 0))):
            ash, hh = C.a_abi(ok, mid, desf)
            huellas[f"{nombre}_{t:%H%M}"] = ash
            huellas[f"alt_{nombre}_{t:%H%M}"] = hh
            if nombre != "h14":
                continue
            lej = ash & (C.DIST > LEJOS_KM)
            med = ash & (C.DIST > MEDIO_KM) & (C.DIST <= LEJOS_KM)
            f = {"hora": f"{t:%H:%M}", "barra": True, "png_px_ventana": de, "png_px_fuera_200km": fu,
                 "n_huella": int(ash.sum()), "n_15_30km": int(med.sum()), "n_mas30km": int(lej.sum()),
                 "dist_max_km": round(float(C.DIST[ash].max()), 1) if ash.any() else "",
                 "alt_mediana_lejos_km": round(float(np.nanmedian(hh[lej])), 2) if lej.any() else "",
                 "cota_mediana_lejos_m": round(float(np.median(C.ZDEM[lej]))) if lej.any() else "",
                 "E1_0811": bool(E1[DIA_EV, s])}
            for zona, m in (("mas30", lej), ("15_30", med)):
                if not m.any():
                    continue
                f[f"acm_despej_0811_{zona}"] = round(float((acm[DIA_EV, s][m] <= 1).mean()), 2)
                # entorno: 2 a 6 pixeles alrededor de la huella, fuera de la huella
                ent = ndimage.binary_dilation(m, iterations=6) & ~ndimage.binary_dilation(ash, iterations=1)
                f[f"acm_entorno_0811_{zona}"] = round(float((acm[DIA_EV, s][ent] <= 1).mean()), 2)
                # dias nulos con el pixel despejado en la misma hora (slot s), con y sin E1
                pix = np.array([(acm[dd, s][m] <= 1).mean() for dd in nulos])
                e1 = np.array([E1[dd, s] for dd in nulos])
                f[f"nulos_px80_{zona}"] = int((pix >= 0.8).sum())
                f[f"nulos_px80_E1_{zona}"] = int(((pix >= 0.8) & e1).sum())
            f["nulos_E1"] = int(sum(E1[dd, s] for dd in nulos))
            filas.append(f)
    np.savez_compressed(os.path.join(C.TRABAJO, "huella_0811.npz"), **huellas)
    claves = []
    for f in filas:
        claves += [k for k in f if k not in claves]
    with open(os.path.join(C.RES, "preparar_por_cuadro.csv"), "w", newline="", encoding="utf-8") as fo:
        w = csv.DictWriter(fo, claves)
        w.writeheader()
        w.writerows(filas)
    lej = [f for f in filas if f.get("n_mas30km")]
    resumen = {"cuadros": len(filas), "barra_ok": sum(f["barra"] for f in filas),
               "pixeles_cuadro_mas30km": sum(f.get("n_mas30km", 0) for f in filas),
               "pixeles_cuadro_15_30km": sum(f.get("n_15_30km", 0) for f in filas),
               "cuadros_con_lejanos": [f["hora"] for f in lej],
               "png_px_fuera_ventana_200km": sum(f.get("png_px_fuera_200km", 0) for f in filas),
               "dias_nulos_candidatos": [f"{T0 + timedelta(days=dd):%Y-%m-%d}" for dd in nulos],
               "georef": geo}
    json.dump(resumen, open(os.path.join(C.RES, "preparar_resumen.json"), "w", encoding="utf-8"), indent=1,
              ensure_ascii=False)
    print(json.dumps({k: v for k, v in resumen.items() if k != "georef"}, ensure_ascii=False, indent=1))
    for f in filas:
        if f.get("n_huella"):
            print({k: v for k, v in f.items() if k not in ("barra",)})


if __name__ == "__main__":
    main()
