r"""S28b F4: la zona de S25a y las de S27a/S28a contra la cumbre APARENTE (línea de vista exacta al elipsoide), y
cuánto gira la tajada de una pluma por paralaje según la distancia al cráter.

Por qué: la georreferencia del ABI es la del elipsoide. La cumbre de 3,2 km y una pluma de 1 a 2 km sobre ella se ven
corridas ~3 a 5 km hacia el SSE. Las regiones del detector (zona < 4 km, anillo 4 a 40 km, tajadas de 30°) se miden
desde la coordenada VERDADERA del cráter sobre esa georreferencia. Aquí se mide con src.process.vrp_nocturno (línea de
vista exacta, la misma que usa S26b) y con el paralaje de 1er orden de src.process.parallax (el de S27a/S27b).

Uso: python -I f4_zona_paralaje.py   (D:\goes_notas\s28\s28b\f4\f4_zona_paralaje.json)
"""
import json
import os
import sys

import numpy as np
from pyproj import Geod

sys.stdout.reconfigure(encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
OV = os.path.abspath(os.path.join(AQUI, "..", "..", ".."))
REPO = os.path.abspath(os.path.join(OV, "..", ".."))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(OV, "s25a_crater", "scripts"))
import s25a_medir as Z  # noqa: E402
from src.process import vrp_nocturno as V  # noqa: E402
from src.process.parallax import parallax_shift  # noqa: E402

M, C29, H24 = Z.M, Z.C29, Z.H24
G = Geod(ellps="GRS80")
OUT = r"D:\goes_notas\s28\s28b\f4"
LAT, LON = C29.LAT, C29.LON
NX = LAT.shape[1]


def px(p):
    return f"({p // NX},{p % NX})"


def zona_info(nombre, la, lo, cota_m, zona):
    out = {"pixeles_zona": len(zona)}
    for h in (cota_m / 1000.0, cota_m / 1000.0 + 1.0, cota_m / 1000.0 + 2.0):
        a_la, a_lo = V.cumbre_aparente(la, lo, h * 1000.0)
        d = C29.hav(LAT, LON, a_la, a_lo).ravel()
        k = int(np.argmin(d))
        dz = d[zona]
        az, _, dd = G.inv(lo, la, a_lo, a_la)
        out[f"h_{h:.2f}_km"] = {
            "aparente": [round(float(a_la), 4), round(float(a_lo), 4)],
            "corrimiento_km": round(dd / 1000, 2), "rumbo": round(az % 360, 1),
            "pixel_que_la_contiene": px(k), "ese_pixel_en_la_zona": bool(k in set(zona.tolist())),
            "dist_de_cada_pixel_de_la_zona_km": {px(p): round(float(x), 2) for p, x in zip(zona, dz)},
            "pixeles_zona_a_mas_de_4km_del_aparente": int((dz >= 4.0).sum()),
            "pixeles_a_menos_de_4km_del_aparente_fuera_de_la_zona": [px(p) for p in np.flatnonzero(d < 4.0)
                                                                      if p not in set(zona.tolist())]}
    return out


def main():
    res = {}
    la, lo = C29.CRATER
    res["chillan_S25a"] = zona_info("chillan", la, lo, 3212.0, Z.ZONA)
    for nom in ("antuco", "longavi"):
        la_, lo_, z_ = H24.SITIOS[nom]
        dist = C29.hav(LAT, LON, la_, lo_)
        i, j = np.unravel_index(np.argmin(dist), dist.shape)
        bl = np.zeros_like(dist, bool)
        bl[i - 1:i + 2, j - 1:j + 2] = True
        zona = np.flatnonzero(((dist < 4.0) | bl).ravel())        # = s27a_medir.zona_de
        r = zona_info(nom, la_, lo_, float(z_), zona)
        r["bloque_centrado_en"] = f"({i},{j}) (píxel más cercano a la coordenada verdadera)"
        res[nom] = r
    res["chillan_S25a"]["bloque_centrado_en"] = f"{tuple(M.CRATER_PX)} (CRATER_PX fijo); píxel más cercano a la " \
        f"coordenada verdadera: {px(int(np.argmin(C29.DIST)))}"
    # giro de tajada de la pluma por paralaje, por distancia (acimut del detector desde el cráter verdadero)
    giro = {}
    for hp in (4.2, 5.2):
        por_r = {}
        for rr in (5.0, 8.0, 10.0, 15.0, 20.0, 30.0, 40.0):
            n = c = 0
            dif = []
            for th in np.arange(0.0, 360.0, 1.0):
                lo2, la2, _ = G.fwd(lo, la, th, rr * 1000)
                # aparente = inversa de parallax_shift (1er orden, 4 iteraciones como s27b_comun.aparente)
                a_la, a_lo = la2, lo2
                for _ in range(4):
                    cl, co = parallax_shift(a_la, a_lo, hp * 1000.0, sat_lon=-75.0)
                    a_la, a_lo = a_la - (cl - la2), a_lo - (co - lo2)
                x = (a_lo - lo) * 111.32 * np.cos(np.radians(la))      # el acimut del detector (s22a)
                y = (a_la - la) * 110.57
                az = (np.degrees(np.arctan2(x, y)) + 360) % 360
                n += 1
                c += int(th // 30) != int(az // 30)
                dif.append(((az - th + 180) % 360) - 180)
            dif = np.abs(dif)
            por_r[f"{rr:.0f}km"] = {"frac_cambia_tajada": round(c / n, 3), "giro_medio_deg": round(float(dif.mean()), 1),
                                    "giro_max_deg": round(float(dif.max()), 1)}
        giro[f"pluma_{hp}km"] = por_r
    res["giro_tajada_por_paralaje"] = giro
    os.makedirs(OUT, exist_ok=True)
    json.dump(res, open(os.path.join(OUT, "f4_zona_paralaje.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(res, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
