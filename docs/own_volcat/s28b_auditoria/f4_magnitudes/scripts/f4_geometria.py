r"""S28b F4: censo geométrico del detector (grilla ABI, píxel, paralaje, zona, anillo, vecinas).

Por qué: el detector mide distancias y rumbos sobre la georreferencia del ABI, que es la del ELIPSOIDE (sin terreno).
Una cumbre a 3,2 km y una pluma a 1 a 2 km sobre ella se ven corridas hacia afuera del subsatélite; si ese corrimiento
es comparable al radio de la zona (4 km) o al ancho de una tajada, la geometría que el criterio describe no es la que el
código mide. Sólo lee: latlon.npz, dem_ventana.npz, window.json y las constantes de los scripts auditados (importados).
No corre el detector ni abre cuadros GOES.

Uso: python -I f4_geometria.py   (escribe D:\goes_notas\s28\s28b\f4\f4_geometria.json y lo imprime)
"""
import json
import math
import os
import sys

import numpy as np
from pyproj import Geod, Proj

sys.stdout.reconfigure(encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
OV = os.path.abspath(os.path.join(AQUI, "..", "..", ".."))
REPO = os.path.abspath(os.path.join(OV, "..", ".."))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(OV, "s22a_detector_sectores", "scripts"))
import s22a_medir as M  # noqa: E402
from src.process.parallax import parallax_shift, satellite_zenith_angle  # noqa: E402

C29, H24 = M.C29, M.H24
OUT = r"D:\goes_notas\s28\s28b\f4"
WIN = json.load(open(r"D:\goes_notas\local_f3a7d295\cache_rescatada\reproducir_volcat\window.json"))
H_SAT = 35786023.0
G = Geod(ellps="GRS80")
LAT, LON = C29.LAT, C29.LON
NY, NX = LAT.shape
SITIOS = {"chillan_C29": (C29.CRATER[0], C29.CRATER[1], 3212), "chillan_VENT": (H24.VENT[0], H24.VENT[1], 3212),
          "antuco": H24.SITIOS["antuco"], "longavi": H24.SITIOS["longavi"]}


def fixed_grid_latlon(lon0):
    i = np.arange(WIN["x0"], WIN["x1"])
    j = np.arange(WIN["y0"], WIN["y1"])
    x = -0.151844 + 5.6e-5 * i
    y = 0.151844 - 5.6e-5 * j
    XX, YY = np.meshgrid(x * H_SAT, y * H_SAT)
    p = Proj(proj="geos", lon_0=lon0, h=H_SAT, ellps="GRS80", sweep="x")
    lo, la = p(XX, YY, inverse=True)
    return la, lo


def aparente(la, lo, h_km, sat_lon):
    """Posición aparente (sobre el elipsoide) de un punto verdadero a h_km: lo opuesto de parallax_shift."""
    lc, oc = parallax_shift(la, lo, h_km * 1000.0, sat_lon=sat_lon)
    return 2 * la - lc, 2 * lo - oc


def px_de(la, lo):
    d = C29.hav(LAT, LON, la, lo)
    i, j = np.unravel_index(np.argmin(d), d.shape)
    return int(i), int(j), float(d[i, j])


def espaciado(i, j):
    ns = float(C29.hav(LAT[i - 1, j], LON[i - 1, j], LAT[i + 1, j], LON[i + 1, j]) / 2)
    eo = float(C29.hav(LAT[i, j - 1], LON[i, j - 1], LAT[i, j + 1], LON[i, j + 1]) / 2)
    return ns, eo


def main():
    out = {}
    # 1) ¿con qué origen de proyección se hizo latlon.npz?, y la grilla fija
    for lon0 in (-75.0, -75.2):
        la, lo = fixed_grid_latlon(lon0)
        out[f"latlon_vs_grilla_fija_lon0_{lon0}"] = {
            "max_dlat_deg": float(np.nanmax(np.abs(la - LAT))), "max_dlon_deg": float(np.nanmax(np.abs(lo - LON)))}
    out["ventana"] = {"window_json": WIN, "lat": [float(LAT.min()), float(LAT.max())],
                      "lon": [float(LON.min()), float(LON.max())], "NY_NX": [NY, NX]}
    # 2) píxel y paralaje por sitio
    for nom, (la, lo, z) in SITIOS.items():
        r = {}
        for sat_lon in (-75.0, -75.2):
            vza = float(np.degrees(satellite_zenith_angle(la, lo, sat_lon, H_SAT)))
            r[f"vza_deg_sat{sat_lon}"] = round(vza, 3)
            r[f"paralaje_km_por_km_sat{sat_lon}"] = round(math.tan(math.radians(vza)), 4)
        i, j, dmin = px_de(la, lo)
        ns, eo = espaciado(i, j)
        r.update({"pixel_del_punto_verdadero": [i, j], "dist_al_centro_km": round(dmin, 3),
                  "espaciado_NS_km": round(ns, 3), "espaciado_EO_km": round(eo, 3),
                  "area_pixel_km2": round(ns * eo, 2), "zdem_pixel_m": round(float(C29.ZDEM[i, j]), 0)})
        # máximo del DEM a <= 6 km del punto: ¿la cumbre está donde dicen las coordenadas?
        d = C29.hav(LAT, LON, la, lo)
        m = d <= 6.0
        k = np.argmax(np.where(m, C29.ZDEM, -1))
        ki, kj = np.unravel_index(k, d.shape)
        r["dem_max_a_6km"] = {"pixel": [int(ki), int(kj)], "zdem_m": round(float(C29.ZDEM[ki, kj]), 0),
                              "dist_km": round(float(d[ki, kj]), 2)}
        for h in (z / 1000.0, z / 1000.0 + 1.0, z / 1000.0 + 2.0):
            a_la, a_lo = aparente(la, lo, h, -75.0)
            az, _, dist = G.inv(lo, la, a_lo, a_la)
            ii, jj, dd = px_de(a_la, a_lo)
            r[f"aparente_h{h:.2f}km"] = {"corrimiento_km": round(dist / 1000, 3), "rumbo_deg": round(az % 360, 1),
                                         "pixel": [ii, jj], "dist_al_centro_km": round(dd, 3),
                                         "dist_desde_punto_verdadero_km": round(float(C29.hav(a_la, a_lo, la, lo)), 3)}
        out[nom] = r
    # 3) la zona de S25a: 11 píxeles, ¿qué contienen?
    dist = C29.DIST
    zona = ((dist < 4.0) | M.BLOQUE)
    zi = np.argwhere(zona)
    la, lo, z = SITIOS["chillan_C29"]
    filas = []
    for (i, j) in zi:
        filas.append({"pixel": [int(i), int(j)], "dist_crater_km": round(float(dist[i, j]), 3),
                      "por_dist_lt4": bool(dist[i, j] < 4.0), "por_bloque": bool(M.BLOQUE[i, j]),
                      "zdem_m": round(float(C29.ZDEM[i, j]), 0)})
    zz = {"n": int(zona.sum()), "n_dist_lt4": int((dist < 4.0).sum()), "n_solo_bloque": int((M.BLOQUE & ~(dist < 4.0)).sum()),
          "n_dist_lt4_fuera_bloque": int(((dist < 4.0) & ~M.BLOQUE).sum()),
          "CRATER_PX": list(M.CRATER_PX), "argmin_DIST": list(np.unravel_index(np.argmin(dist), dist.shape)),
          "pixeles": filas}
    # ¿cuántos píxeles de la zona quedan a < 4 km del punto APARENTE de la cumbre y de la pluma?
    for h in (3.212, 4.2, 5.2):
        a_la, a_lo = aparente(la, lo, h, -75.0)
        da = C29.hav(LAT, LON, a_la, a_lo)
        zz[f"centrada_en_aparente_h{h}"] = {
            "n_a_menos_de_4km": int((da < 4.0).sum()),
            "de_esos_en_la_zona": int(((da < 4.0) & zona).sum()),
            "zona_fuera_de_4km_del_aparente": int((zona & ~(da < 4.0)).sum()),
            "pixel_aparente": list(px_de(a_la, a_lo)[:2]),
            "pixel_aparente_en_zona": bool(zona[px_de(a_la, a_lo)[:2]])}
    out["zona_S25a"] = zz
    # 4) anillo: píxeles por tajada, y cuántos cambian de tajada o salen/entran al anillo por paralaje de pluma
    AZ = M.AZ
    sec = (AZ // 30).astype(int) % 12
    # acimut geodésico exacto (GRS80) contra el aproximado de s22a (111,32 cos, 110,57)
    az_g, _, d_g = G.inv(np.full(LAT.shape, lo), np.full(LAT.shape, la), LON, LAT)
    az_g = az_g % 360
    sec_g = (az_g // 30).astype(int) % 12
    amask = M.AMASK
    out["anillo_chillan"] = {"NA": int(M.NA), "pixeles_por_tajada": M.NPS.tolist(),
                             "tajada_distinta_con_acimut_geodesico": int((sec_g != sec)[amask].sum()),
                             "max_dif_acimut_deg": float(np.max(np.abs(((az_g - AZ + 180) % 360) - 180)[amask])),
                             "dist_haversine_vs_geodesica_max_rel": float(np.max((np.abs(dist - d_g / 1000) / (d_g / 1000))[amask])),
                             "pixeles_que_cambian_de_anillo_con_dist_geodesica": int(
                                 (((d_g / 1000 >= 4) & (d_g / 1000 <= 40)) != ((dist >= 4) & (dist <= 40)))[~M.BLOQUE].sum()),
                             "pixeles_que_cambian_de_zona_con_dist_geodesica": int(((d_g / 1000 < 4) != (dist < 4)).sum())}
    # pluma a la altura H: un punto verdadero a (r, theta) del cráter se ve en el aparente; ¿en qué tajada cae?
    res = {}
    for hp in (4.2, 5.2, 6.2):
        cambia, sale_zona, total = 0, 0, 0
        por_rumbo = {}
        for th in np.arange(0, 360, 5.0):
            for rr in (2.0, 3.0, 4.5, 6.0, 8.0, 10.0, 15.0, 20.0, 30.0):
                lo2, la2, _ = G.fwd(lo, la, th, rr * 1000)
                a_la, a_lo = aparente(la2, lo2, hp, -75.0)
                az2, _, d2 = G.inv(lo, la, a_lo, a_la)
                k0, k1 = int(th // 30) % 12, int((az2 % 360) // 30) % 12
                if rr >= 4.5:
                    total += 1
                    cambia += k0 != k1
                    por_rumbo.setdefault(int(th), 0)
                    por_rumbo[int(th)] += k0 != k1
                if rr <= 3.0:
                    sale_zona += d2 / 1000 >= 4.0
        res[f"h{hp}"] = {"puntos_anillo": total, "cambian_de_tajada": cambia, "frac": round(cambia / total, 3),
                         "puntos_a_2_o_3_km_que_quedan_a_4km_o_mas": int(sale_zona)}
    out["pluma_paralaje_tajadas"] = res
    # 5) vecinas: ¿el anillo y los controles caben en la ventana?
    vec = {}
    for nom in ("antuco", "longavi"):
        la_, lo_, z_ = SITIOS[nom]
        d = C29.hav(LAT, LON, la_, lo_)
        i, j, _ = px_de(la_, lo_)
        bl = np.zeros_like(d, bool)
        bl[i - 1:i + 2, j - 1:j + 2] = True
        ring = (d >= 4) & (d <= 40) & ~bl
        # anillo completo esperado: área del anillo / área del píxel local
        ns, eo = espaciado(i, j)
        esperado = (math.pi * (40 ** 2 - 4 ** 2)) / (ns * eo) - 9
        # distancia del sitio al borde de la ventana
        bordes = {"N_fila0_km": float(C29.hav(LAT[0, j], LON[0, j], la_, lo_)),
                  "S_fila_ult_km": float(C29.hav(LAT[-1, j], LON[-1, j], la_, lo_)),
                  "O_col0_km": float(C29.hav(LAT[i, 0], LON[i, 0], la_, lo_)),
                  "E_col_ult_km": float(C29.hav(LAT[i, -1], LON[i, -1], la_, lo_))}
        azv = (np.degrees(np.arctan2((LON - lo_) * 111.32 * np.cos(np.radians(la_)), (LAT - la_) * 110.57)) + 360) % 360
        secv = (azv[ring] // 30).astype(int) % 12
        vec[nom] = {"pixel": [i, j], "anillo_en_ventana": int(ring.sum()), "anillo_esperado_completo": round(esperado),
                    "frac_en_ventana": round(ring.sum() / esperado, 3),
                    "pixeles_por_tajada_sin_excluir": np.bincount(secv, minlength=12).tolist(),
                    "bordes_km": {k: round(v, 1) for k, v in bordes.items()},
                    "controles_mas_45_de_ambos": int(((C29.DIST > 45) & (d > 45)).sum()),
                    "zona_n": int(((d < 4) | bl).sum())}
    ch_ns, ch_eo = espaciado(*M.CRATER_PX)
    vec["chillan"] = {"anillo": int(M.NA), "anillo_esperado_completo": round(math.pi * (40 ** 2 - 4 ** 2) / (ch_ns * ch_eo) - 9),
                      "controles": int(len(M.CTRL)),
                      "bordes_km": {"N": round(float(C29.hav(LAT[0, 46], LON[0, 46], la, lo)), 1),
                                    "S": round(float(C29.hav(LAT[-1, 46], LON[-1, 46], la, lo)), 1),
                                    "O": round(float(C29.hav(LAT[42, 0], LON[42, 0], la, lo)), 1),
                                    "E": round(float(C29.hav(LAT[42, -1], LON[42, -1], la, lo)), 1)}}
    out["vecinas"] = vec
    # 6) rumbos fijos de S28a contra la geometría
    for nom in ("antuco", "longavi"):
        la_, lo_, _ = SITIOS[nom]
        az_, _, dd = G.inv(lo, la, lo_, la_)
        out.setdefault("rumbo_chillan_a_vecina", {})[nom] = {"geodesico_deg": round(az_ % 360, 2),
                                                            "dist_km": round(dd / 1000, 1)}
    os.makedirs(OUT, exist_ok=True)
    json.dump(out, open(os.path.join(OUT, "f4_geometria.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1,
              default=lambda o: o.item() if hasattr(o, "item") else str(o))
    print("ok")


if __name__ == "__main__":
    main()
