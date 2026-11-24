r"""S22c: altura propia de los píxeles que marca el detector S22a. Implementa criterio_2026-11-24.md (commit bdd73e7,
empujado antes de medir).

Método (a), principal: la pluma viaja con el viento de su altura. Para cada altura candidata h se corrige por paralaje
la posición de los píxeles (GOES-19 ve algo a h km corrido hacia el sur), se mide hacia dónde quedan desde el cráter y
se compara con la dirección del viento GFS a esa h. Las h donde calzan (30 grados o menos, viento de 3 m/s o más) son
las alturas compatibles. No usa la temperatura, así que no depende de la opacidad de la pluma.

Método (b), secundario y sólo en el píxel de la verdad: corrección de emisividad (capa única, f conocido, beta 0,7)
contra el fondo despejado del mismo píxel. Se espera que no restrinja (límite de capa delgada, §1 del criterio).

Uso: python -I s22c_medir.py pruebas | medir
"""
import json
import math
import os
import sys
import warnings
from datetime import datetime, timedelta

import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
warnings.simplefilter("ignore", RuntimeWarning)
AQUI = os.path.dirname(os.path.abspath(__file__))
OV = os.path.abspath(os.path.join(AQUI, "..", ".."))
REPO = os.path.abspath(os.path.join(OV, "..", ".."))
RES = os.path.join(os.path.dirname(AQUI), "resultados")
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(OV, "s22a_detector_sectores", "scripts"))
sys.path.insert(0, os.path.join(OV, "h24_pulsos_reav", "scripts"))
sys.path.insert(0, os.path.join(OV, "h29_pluma_0811", "scripts"))
from src.process.parallax import parallax_shift  # noqa: E402
import h29_comun as C29  # noqa: E402

GFS_DIR = r"D:\goes_notas\s22\s22c\gfs"
SAT_LON = -75.2
CLAT_W, CLON_W = -36.8677, -71.3793          # punto de interpolación del viento (el de H10)
CLAT, CLON = C29.CRATER                      # cráter para acimutes (el de S20b, H29 y S22a)
ZC_KM, ZMAX_KM, DZ = 3.2, 14.0, 0.1
ZS = np.round(np.arange(ZC_KM, ZMAX_KM + 1e-9, DZ), 3)
TAU, TAU_SENS, VMIN = 30.0, (20.0, 45.0), 3.0
ANCHO_MAX, TOL_VERDAD = 3.0, 1.0
H_SOMBRA = 4.7
VERDAD_FINA = {"2026-11-08": {"hora": "14:53", "az": 207.0, "dist_km": 1.6, "h_ref": 4.7, "ref": "sombra Sentinel-2"},
               "2026-10-25": {"hora": "14:34", "az": 253.0, "dist_km": 4.6, "h_ref": 4.3, "ref": "VAAC (no es sombra)"}}
DIAS_DET = ["2026-11-08", "2026-11-14"]
BETA, BETA_SENS, F_PIX = 0.7, (0.6, 0.8), 0.43
PIX_B, CUADROS_B = (44, 46), ("14:40", "14:50")
RES_MAX_B = 0.2
KX = 111.32 * math.cos(math.radians(CLAT))
KY = 110.57


# ---------- geometría ----------
def az_dist(lat, lon):
    dx = (np.asarray(lon) - CLON) * KX
    dy = (np.asarray(lat) - CLAT) * KY
    return (np.degrees(np.arctan2(dx, dy)) + 360.0) % 360.0, np.hypot(dx, dy)


def dang(a, b):
    return np.abs((np.asarray(a) - np.asarray(b) + 180.0) % 360.0 - 180.0)


def media_circ(az):
    r = np.radians(np.asarray(az, float))
    s, c = np.sin(r).mean(), np.cos(r).mean()
    return float((math.degrees(math.atan2(s, c)) + 360.0) % 360.0), float(np.hypot(s, c))


def rumbo_obs(lat, lon, aparente=True):
    """θo(h) para cada h de ZS: media circular del acimut de los píxeles, corregidos por paralaje a h si su posición
    es la que ve GOES-19 (aparente); si la posición viene de una imagen casi vertical, no se corrige."""
    lat, lon = np.atleast_1d(lat).astype(float), np.atleast_1d(lon).astype(float)
    out = np.empty(len(ZS))
    for i, h in enumerate(ZS):
        if aparente:
            la, lo = parallax_shift(lat, lon, h * 1000.0, sat_lon=SAT_LON)
        else:
            la, lo = lat, lon
        out[i] = media_circ(az_dist(np.atleast_1d(la), np.atleast_1d(lo))[0])[0]
    return out


# ---------- viento ----------
def _bil(campo, la, lo, LAT_, LON_):
    i = np.interp(la, LAT_[::-1], np.arange(len(LAT_))[::-1])
    j = np.interp(lo, LON_, np.arange(len(LON_)))
    i0, j0 = int(np.floor(i)), int(np.floor(j))
    di, dj = i - i0, j - j0
    return ((1 - di) * (1 - dj) * campo[..., i0, j0] + di * (1 - dj) * campo[..., i0 + 1, j0]
            + (1 - di) * dj * campo[..., i0, j0 + 1] + di * dj * campo[..., i0 + 1, j0 + 1])


_PERFIL = {}


def perfil_hora(h):
    """(u, v) en ZS (m/s) en el cráter para la hora entera h, desde el npz de s22c_viento.py."""
    if h not in _PERFIL:
        fn = os.path.join(GFS_DIR, f"gfsv_{h:%Y%m%d%H}.npz")
        if not os.path.exists(fn):
            _PERFIL[h] = None
        else:
            d = np.load(fn)
            u = _bil(d["u"], CLAT_W, CLON_W, d["lat"], d["lon"])
            v = _bil(d["v"], CLAT_W, CLON_W, d["lat"], d["lon"])
            z = _bil(d["z"], CLAT_W, CLON_W, d["lat"], d["lon"]) / 1000.0
            o = np.argsort(z)
            _PERFIL[h] = (np.interp(ZS, z[o], u[o]), np.interp(ZS, z[o], v[o]))
    return _PERFIL[h]


def viento(dt):
    """(θw hacia donde sopla, V) en ZS, lineal en el tiempo entre las dos horas que rodean dt. None si falta una."""
    h0 = dt.replace(minute=0, second=0, microsecond=0)
    h1 = h0 + timedelta(hours=1)
    p0, p1 = perfil_hora(h0), perfil_hora(h1)
    if p0 is None or p1 is None:
        return None
    w = (dt - h0).total_seconds() / 3600.0
    u = (1 - w) * p0[0] + w * p1[0]
    v = (1 - w) * p0[1] + w * p1[1]
    return (np.degrees(np.arctan2(u, v)) + 360.0) % 360.0, np.hypot(u, v)


def altura_rumbo(theta_o, vw, tau=TAU):
    """Alturas compatibles, h*, banda y ancho a partir de θo(h) y del viento (θw(h), V(h)). Criterio §2."""
    tw, V = vw
    mis = dang(theta_o, tw)
    ok = (mis <= tau) & (V >= VMIN)
    if not ok.any():
        return {"h": None, "banda": None, "ancho": None, "restringe": False, "n_compat": 0}
    hs = ZS[ok]
    k = np.flatnonzero(ok)[np.argmin(mis[ok])]
    ancho = float(hs.max() - hs.min())
    return {"h": float(ZS[k]), "desajuste": round(float(mis[k]), 1), "V_h": round(float(V[k]), 1),
            "banda": [float(hs.min()), float(hs.max())], "ancho": round(ancho, 2),
            "restringe": bool(ancho <= ANCHO_MAX + 1e-9), "n_compat": int(ok.sum()),
            "toca_verdad": bool(((hs >= H_SOMBRA - TOL_VERDAD - 1e-9) & (hs <= H_SOMBRA + TOL_VERDAD + 1e-9)).any())}


def veredicto_21(r, h_ref):
    if r["h"] is None or not r["restringe"]:
        return "NO RESTRINGE"
    return "ACIERTA" if abs(r["h"] - h_ref) <= TOL_VERDAD + 1e-9 else "FALLA"


def resumen_perfil(vw):
    tw, V = vw
    return [{"z_km": float(z), "hacia": round(float(tw[i]), 0), "V": round(float(V[i]), 1)}
            for i, z in enumerate(ZS) if abs(z * 2 - round(z * 2)) < 1e-6]        # cada 0,5 km


# ---------- 2.1 verdad fina ----------
def prueba_verdad():
    out = {}
    for dia, v in VERDAD_FINA.items():
        dt = datetime.strptime(f"{dia} {v['hora']}", "%Y-%m-%d %H:%M")
        vw = viento(dt)
        if vw is None:
            out[dia] = {"error": "falta viento"}
            continue
        th = np.full(len(ZS), v["az"])            # posición de la imagen fina: sin paralaje
        r = {f"tau_{int(t)}": altura_rumbo(th, vw, t) for t in (TAU,) + TAU_SENS}
        out[dia] = {**v, "principal": r[f"tau_{int(TAU)}"], "sensibilidad": r,
                    "veredicto": veredicto_21(r[f"tau_{int(TAU)}"], v["h_ref"]),
                    "decide": dia == "2026-11-08", "perfil": resumen_perfil(vw)}
    return out


# ---------- 2.2 y 2.3 píxeles del detector ----------
def volcat_cuadro(dia, s):
    nombre = f"{dia}_{s // 6:02d}-{s % 6 * 10:02d}-30.png"
    for d in (C29.FRAMES, r"D:\goes_notas\s22\volcat_png\Chile_Central_2_km\frames"):
        fn = os.path.join(d, nombre)
        if os.path.exists(fn):
            ok, mid, bok = C29.decodifica_png(fn)
            if ok is None:
                return {"estado": "PNG sin barra"}
            ash, hh = C29.a_abi(ok, mid)
            sel = ash & (C29.DIST <= 50.0)
            if not sel.any():
                return {"estado": "sin ceniza a 50 km"}
            return {"estado": "ceniza", "n": int(sel.sum()), "h_mediana": float(np.nanmedian(hh[sel])),
                    "h_max": float(np.nanmax(hh[sel]))}
    return {"estado": "sin PNG"}


def pixeles_detector(dia):
    """Cuadros en que S22a dispara y sus 8 píxeles (filas, columnas), sin cambiar nada del detector."""
    import s22a_mapas as G
    import s22a_medir as M
    m1, S, K, F, U, rol = G.tablas(dia)
    out = []
    for s in range(144):
        if not F[s]:
            continue
        idx = np.flatnonzero(M.SEC == K[s])
        v = m1[s][idx]
        o = np.argsort(np.where(np.isfinite(v), v, np.inf))[:M.NCOLA]
        flat = M.AP[idx[o]]
        out.append((s, int(K[s]), flat // M.NX, flat % M.NX))
    return out, rol


def prueba_detector(dia):
    filas = []
    for s, k, rr, cc in pixeles_detector(dia)[0]:
        dt = datetime.strptime(dia, "%Y-%m-%d") + timedelta(minutes=10 * s + 5)     # centro del barrido de 10 min
        vw = viento(dt)
        lat, lon = C29.LAT[rr, cc], C29.LON[rr, cc]
        th = rumbo_obs(lat, lon, aparente=True)
        az_ap, d_ap = az_dist(lat, lon)
        f = {"slot": s, "hora": f"{s // 6:02d}:{s % 6 * 10:02d}", "tajada": k,
             "rumbo_aparente": round(media_circ(az_ap)[0], 1), "dist_aparente_km": round(float(np.median(d_ap)), 1),
             "filas": rr.tolist(), "cols": cc.tolist()}
        if vw is None:
            f["error"] = "falta viento"
        else:
            f["principal"] = altura_rumbo(th, vw, TAU)
            f["sensibilidad"] = {f"tau_{int(t)}": altura_rumbo(th, vw, t) for t in TAU_SENS}
            if f["principal"]["h"] is not None:
                f["rumbo_corregido"] = round(float(th[np.argmin(np.abs(ZS - f["principal"]["h"]))]), 1)
        f["volcat"] = volcat_cuadro(dia, s)
        filas.append(f)
    return filas


def resumen_dia(filas):
    con = [f for f in filas if f.get("principal", {}).get("h") is not None]
    n = len(filas)
    if not con:
        return {"n_disparos": n, "n_con_altura": 0, "veredicto_22": "NO RESTRINGE"}
    hs = np.array([f["principal"]["h"] for f in con])
    an = np.array([f["principal"]["ancho"] for f in con])
    toca = np.array([f["principal"]["toca_verdad"] for f in con])
    med_h, med_a = float(np.median(hs)), float(np.median(an))
    if len(con) < 0.5 * n or med_a > ANCHO_MAX:
        ver = "NO RESTRINGE"
    elif abs(med_h - H_SOMBRA) <= TOL_VERDAD and toca.mean() >= 0.5:
        ver = "CALZA"
    elif abs(med_h - H_SOMBRA) > TOL_VERDAD:
        ver = "NO CALZA"
    else:
        ver = "NO RESTRINGE"      # mediana cerca pero menos de la mitad toca 3,7 a 5,7 km: no cumple CALZA
    vol = [f["volcat"]["h_mediana"] for f in con if f["volcat"].get("estado") == "ceniza"]
    dif = [f["principal"]["h"] - f["volcat"]["h_mediana"] for f in con if f["volcat"].get("estado") == "ceniza"]
    return {"n_disparos": n, "n_con_altura": len(con), "h_mediana": round(med_h, 2),
            "h_p25_p75": [round(float(np.percentile(hs, 25)), 2), round(float(np.percentile(hs, 75)), 2)],
            "ancho_mediano": round(med_a, 2), "frac_banda_toca_3p7_5p7": round(float(toca.mean()), 3),
            "frac_restringe": round(float(np.mean([f["principal"]["restringe"] for f in con])), 3),
            "volcat_n_cuadros_con_ceniza": len(vol),
            "volcat_h_mediana": round(float(np.median(vol)), 2) if vol else None,
            "dif_h_menos_volcat_mediana": round(float(np.median(dif)), 2) if dif else None,
            "veredicto_22": ver}


# ---------- método (b) ----------
def metodo_b():
    import h24_medir as H24
    sp = json.load(open(os.path.join(OV, "s20b_verdad_alta_res", "resultados", "posthoc.json"), encoding="utf-8"))
    serie = sp["2026-11-08"]["serie_pixel_mayor_f"]
    assert (serie["fila"], serie["col"]) == PIX_B
    base = [x["dia"] for x in serie["dias"] if not (x["evento"] or x["excluido_H24"] or x["otro_evento"])]
    r14, r15, _, co14, co15 = H24.cargar()
    p = PIX_B[0] * C29.NX + PIX_B[1]
    d_ev = (datetime(2026, 11, 8) - H24.T0).days
    zs_m = ZS * 1000.0
    Tz = H24.gfs_t(zs_m)                                   # (dias, 144, nz)
    eps = np.arange(0.005, 1.0001, 0.005)
    Tc = np.arange(200.0, 300.0001, 0.25)
    E, TT = np.meshgrid(eps, Tc, indexing="ij")
    B11, B12 = C29.rad_de_bt(TT, co14), C29.rad_de_bt(TT, co15)
    out = {"base": base, "pixel": PIX_B, "f": F_PIX, "por_beta": {}}
    for beta in (BETA,) + BETA_SENS:
        sol = []
        for c in CUADROS_B:
            s = int(c[:2]) * 6 + int(c[3:]) // 10
            R11, R12 = float(r14[d_ev, s, p]), float(r15[d_ev, s, p])
            bt11o, bt12o = float(C29.bt_de_rad(R11, co14)), float(C29.bt_de_rad(R12, co15))
            prof = Tz[d_ev, s]
            for b in base:
                db = (datetime.strptime(b, "%Y-%m-%d") - H24.T0).days
                R11b, R12b = float(r14[db, s, p]), float(r15[db, s, p])
                e12 = 1 - (1 - E) ** beta
                m11 = (1 - F_PIX * E) * R11b + F_PIX * E * B11
                m12 = (1 - F_PIX * e12) * R12b + F_PIX * e12 * B12
                res = np.maximum(np.abs(C29.bt_de_rad(m11, co14) - bt11o), np.abs(C29.bt_de_rad(m12, co15) - bt12o))
                i, j = np.unravel_index(np.nanargmin(res), res.shape)
                fila = {"cuadro": c, "base": b, "bt11_obs": round(bt11o, 2), "btd_obs": round(bt11o - bt12o, 2),
                        "bt11_base": round(float(C29.bt_de_rad(R11b, co14)), 2),
                        "btd_base": round(float(C29.bt_de_rad(R11b, co14) - C29.bt_de_rad(R12b, co15)), 2),
                        "residuo_K": round(float(res[i, j]), 3)}
                # cuántas combinaciones (ε, T) caben en el residuo: mide la degeneración
                fila["n_soluciones_res_ok"] = int((res <= RES_MAX_B).sum())
                if res[i, j] <= RES_MAX_B:
                    tc = float(TT[i, j])
                    fila["eps11"] = round(float(E[i, j]), 3)
                    fila["T_pluma"] = tc
                    # alturas de todas las soluciones dentro del residuo (rango de la degeneración)
                    oks = res <= RES_MAX_B
                    fila["T_rango_sol"] = [float(TT[oks].min()), float(TT[oks].max())]
                    fila["eps_rango_sol"] = [float(E[oks].min()), float(E[oks].max())]
                    fila["h_km"] = h_de_T(tc, prof)
                    fila["h_rango_sol"] = [h_de_T(float(TT[oks].max()), prof), h_de_T(float(TT[oks].min()), prof)]
                sol.append(fila)
        hs = [x["h_km"] for x in sol if x.get("h_km") is not None]
        r = {"soluciones": sol, "n": len(sol), "n_con_altura": len(hs)}
        if hs:
            r["h_mediana"] = float(np.median(hs))
            r["banda"] = [float(min(hs)), float(max(hs))]
            r["ancho"] = round(float(max(hs) - min(hs)), 2)
            pr = {"h": r["h_mediana"], "restringe": r["ancho"] <= ANCHO_MAX}
            r["veredicto"] = veredicto_21(pr, H_SOMBRA) if len(hs) >= 0.5 * len(sol) else "NO RESTRINGE"
        else:
            r["veredicto"] = "NO RESTRINGE"
        out["por_beta"][str(beta)] = r
    out["T_aire_3p2_4p7_6_km"] = [round(float(np.interp(z, ZS, Tz[d_ev, 88])), 2) for z in (3.2, 4.7, 6.0)]
    return out


def h_de_T(tc, prof):
    """Primera altura sobre el cráter (en ZS) donde el aire GFS llega a tc; None si tc es más tibio que el aire a la
    cota del cráter o más frío que todo el perfil hasta 14 km."""
    if not np.isfinite(prof).all():
        return None
    for i in range(len(ZS) - 1):
        a, b = prof[i], prof[i + 1]
        if (a - tc) * (b - tc) <= 0 and a != b:
            return round(float(ZS[i] + (a - tc) / (a - b) * DZ), 2)
    return None


# ---------- pruebas del código ----------
def pruebas():
    # acimut: al norte 0, al este 90
    assert dang(az_dist(CLAT + 0.1, CLON)[0], 0) < 1e-6
    assert abs(az_dist(CLAT, CLON + 0.1)[0] - 90) < 1e-6
    # paralaje: algo a 4,7 km sobre el cráter, visto por GOES-19, aparece unos 4 km al sur; al corregir vuelve
    la_v, lo_v = CLAT - 0.20, CLON + 0.15             # píxel aparente al SE
    th = rumbo_obs(la_v, lo_v, aparente=True)
    assert dang(th[0], th[-1]) > 5                    # la corrección cambia el rumbo con h
    # rumbo corregido a h es el del punto movido hacia el subsatélite (más al N), o sea menos al S que el aparente
    a0 = az_dist(la_v, lo_v)[0]
    assert dang(th[np.argmin(np.abs(ZS - 8.0))], 0) < dang(a0, 0)
    # altura_rumbo: viento que gira de 90 a 180 entre 3,2 y 14 km; rumbo fijo 135 da h cerca de la mitad
    tw = 90 + 90 * (ZS - ZS[0]) / (ZS[-1] - ZS[0])
    r = altura_rumbo(np.full(len(ZS), 135.0), (tw, np.full(len(ZS), 10.0)), tau=5)
    assert abs(r["h"] - 8.6) < 0.15 and r["restringe"], r
    # viento uniforme en dirección: no restringe
    r = altura_rumbo(np.full(len(ZS), 135.0), (np.full(len(ZS), 130.0), np.full(len(ZS), 10.0)))
    assert not r["restringe"] and r["ancho"] > 10
    # calma: sin altura
    r = altura_rumbo(np.full(len(ZS), 135.0), (np.full(len(ZS), 135.0), np.full(len(ZS), 1.0)))
    assert r["h"] is None
    assert veredicto_21({"h": 5.5, "restringe": True}, 4.7) == "ACIERTA"
    assert veredicto_21({"h": 6.0, "restringe": True}, 4.7) == "FALLA"
    assert veredicto_21({"h": 4.7, "restringe": False}, 4.7) == "NO RESTRINGE"
    # h_de_T: perfil lineal de 270 K a 3,2 km bajando 6,5 K/km
    prof = 270 - 6.5 * (ZS - 3.2)
    assert abs(h_de_T(260.25, prof) - 4.7) < 0.02 and h_de_T(275.0, prof) is None
    print("pruebas: 10 de 10 OK")


def main():
    os.makedirs(RES, exist_ok=True)
    out = {"criterio": "criterio_2026-11-24.md (commit bdd73e7)", "tau": TAU, "vmin": VMIN, "ancho_max": ANCHO_MAX,
           "verdad_km": H_SOMBRA}
    out["prueba_21_verdad"] = prueba_verdad()
    for dia, r in out["prueba_21_verdad"].items():
        print(f"2.1 {dia}: {r.get('veredicto')}  {r.get('principal')}", flush=True)
    out["dias"] = {}
    for dia in DIAS_DET:
        filas = prueba_detector(dia)
        out["dias"][dia] = {"resumen": resumen_dia(filas), "cuadros": filas}
        print(f"2.2/2.3 {dia}: {out['dias'][dia]['resumen']}", flush=True)
    out["metodo_b"] = metodo_b()
    for b, r in out["metodo_b"]["por_beta"].items():
        print(f"(b) beta {b}: {r['veredicto']}  h_med {r.get('h_mediana')} banda {r.get('banda')} "
              f"({r['n_con_altura']}/{r['n']} con altura)", flush=True)
    v1 = out["prueba_21_verdad"]["2026-11-08"]["veredicto"]
    v2 = out["dias"]["2026-11-08"]["resumen"]["veredicto_22"]
    if v1 == "ACIERTA":
        conj = "ALTURA PROPIA ÚTIL" if v2 == "CALZA" else "SÓLO EL MÉTODO"
    elif v1 == "FALLA":
        conj = "NO SIRVE"
    else:
        conj = "NO DECIDIBLE"
    out["veredicto_conjunto"] = conj
    print("VEREDICTO CONJUNTO:", conj)
    with open(os.path.join(RES, "s22c_resultado.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    if sys.argv[1:] == ["pruebas"]:
        pruebas()
    elif sys.argv[1:] == ["medir"]:
        main()
    else:
        print(__doc__)
