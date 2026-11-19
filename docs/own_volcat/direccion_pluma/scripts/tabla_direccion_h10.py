"""H10: tabla de direccion por jornada y veredicto (criterio secciones 4, 5 y 7).
Lee h10/direccion_cuadros.json (direccion_volcat_h10.py) y los perfiles h10/gfs/gfsv_*.npz
(fetch_gfs_viento_h10.py). Los cuadros de una jornada se cuentan una vez aunque caigan en dos ventanas; la
altura usada para el paralaje y la capa de viento es la del episodio asignado con la misma regla que
senal_h10.py (la columna mas reciente). Uso: python -I tabla_direccion_h10.py"""
import os, sys, json
from datetime import datetime
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import comun_h10 as C  # noqa: E402
import fetch_gfs_viento_h10 as G  # noqa: E402

F = json.load(open(os.path.join(C.WORK, "direccion_cuadros.json")))
EPI = {e[0]: e for e in C.EP}


def asignado(j, slot):
    es = [EPI[f["ep"]] for f in F if f["jornada"] == j and f["slot"] == slot]
    s = datetime.strptime(slot, "%Y-%m-%d %H:%M")
    prev = [e for e in es if C.P(e[2]) <= s]
    return max(prev, key=lambda e: C.P(e[2])) if prev else min(es, key=lambda e: C.P(e[2]))


def clase(d0, d1):
    if d0 <= 45 and d1 <= 45:
        return "coincide"
    if d0 >= 90 and d1 >= 90:
        return "discrepa"
    return "no concluyente"


def viento(slot, H, z0=None):
    h = G.hora(datetime.strptime(slot, "%Y-%m-%d %H:%M"))
    if not os.path.exists(G.ruta(h)):
        return None
    zc = C.ZC_KM if z0 is None else z0
    return G.viento_capa(h, zc + H / 2000.0, zc + H / 1000.0)


if __name__ == "__main__":
    out = []
    jornadas = sorted({f["jornada"] for f in F}, key=lambda j: min(f["slot"] for f in F if f["jornada"] == j))
    for j in jornadas:
        filas = {}
        for f in F:
            if f["jornada"] == j and f["slot"] not in filas:
                e = asignado(j, f["slot"])
                filas[f["slot"]] = next(g for g in F if g["jornada"] == j and g["slot"] == f["slot"] and g["ep"] == e[0])
        res = [f for f in filas.values() if f["estado"] == "resuelta"]
        from collections import Counter
        cnt = Counter(f["estado"] for f in filas.values())
        print(f"\n== Jornada {j}: {len(filas)} slots; estados {dict(cnt)}")
        vs = []
        for f in sorted(res, key=lambda f: f["slot"]):
            w = viento(f["slot"], f["H"])
            ws = viento(f["slot"], f["H"], None) if w is None else None
            wfull = None
            h = G.hora(datetime.strptime(f["slot"], "%Y-%m-%d %H:%M"))
            if os.path.exists(G.ruta(h)):
                wfull = G.viento_capa(h, C.ZC_KM, C.ZC_KM + f["H"] / 1000.0)
            vs.append((f, w, wfull))
            txt = (f"  {f['slot'][11:]} {f['ep']:4s} npx={f['npx']:3d} P1 az={f['P1_az']:5.0f} d={f['P1_dist']:4.1f} km"
                   f" | P0 az={f['P0_az']:5.0f} d={f['P0_dist']:4.1f} km")
            if f["az_reav"] is not None:
                txt += f" | dREAV P1={C.dang(f['P1_az'], f['az_reav']):4.0f} P0={C.dang(f['P0_az'], f['az_reav']):4.0f}"
            if w is not None:
                txt += f" | GFS hacia {w[0]:4.0f} a {w[1]:4.1f} m/s (capa {C.ZC_KM + f['H']/2000:.1f}-{C.ZC_KM + f['H']/1000:.1f} km)"
            print(txt)
        if not res:
            out.append(dict(jornada=j, resueltas=0)); continue
        m1, r1 = C.media_circ([f["P1_az"] for f in res]); m0, r0 = C.media_circ([f["P0_az"] for f in res])
        az_r = res[0]["az_reav"]
        fila = dict(jornada=j, resueltas=len(res), P1_media=round(m1, 1), P1_R=round(r1, 2), P0_media=round(m0, 1), P0_R=round(r0, 2),
                    frac45_P1=round(np.mean([C.dang(f["P1_az"], m1) <= 45 for f in res]), 2),
                    frac45_P0=round(np.mean([C.dang(f["P0_az"], m0) <= 45 for f in res]), 2))
        ws = [w for f, w, _ in vs if w is not None]
        if ws:
            uu = np.mean([w[2] for w in ws]); vv = np.mean([w[3] for w in ws])
            fila.update(gfs_hacia=round(C.azimut(uu, vv), 1), gfs_ms=round(float(np.hypot(uu, vv)), 1), gfs_n=len(ws))
            wf = [w for _, _, w in vs if w is not None]
            fila["gfs_capa_completa_hacia"] = round(C.azimut(np.mean([w[2] for w in wf]), np.mean([w[3] for w in wf])), 1)
            fila["huella_vs_gfs"] = clase(C.dang(m0, fila["gfs_hacia"]), C.dang(m1, fila["gfs_hacia"]))
            fila["d_huella_gfs"] = [round(C.dang(m0, fila["gfs_hacia"]), 1), round(C.dang(m1, fila["gfs_hacia"]), 1)]
        if az_r is not None:
            fila.update(az_reav=az_r, d_P0=round(C.dang(m0, az_r), 1), d_P1=round(C.dang(m1, az_r), 1))
            fila["huella_vs_reav"] = clase(fila["d_P0"], fila["d_P1"]) if len(res) >= 2 else "no concluyente (menos de 2 escenas)"
            if "gfs_hacia" in fila:
                fila["reav_vs_gfs"] = clase(C.dang(az_r, fila["gfs_hacia"]), C.dang(az_r, fila["gfs_hacia"]))
                fila["d_reav_gfs"] = round(C.dang(az_r, fila["gfs_hacia"]), 1)
        print("  ->", fila)
        out.append(fila)
    # Viento GFS a la hora de cada REAV con direccion, aunque VOLCAT no dibuje (explica, no decide)
    print("\n== Viento GFS a la hora de cada REAV (capa H/2 a H sobre el crater)")
    reav = []
    for e in C.EP:
        h = G.hora(C.P(e[2]))
        if os.path.exists(G.ruta(h)):
            w = G.viento_capa(h, C.ZC_KM + e[4] / 2000.0, C.ZC_KM + e[4] / 1000.0)
            sens = [G.viento_capa(h, z + e[4] / 2000.0, z + e[4] / 1000.0)[0] for z in (2.9, 3.5)]
            d = None if e[5] is None else round(C.dang(e[5], w[0]), 1)
            reav.append(dict(ep=e[0], hora=e[2], az_reav=e[5], gfs_hacia=round(w[0], 1), gfs_ms=round(w[1], 1), d=d,
                             sens_crater_29_35=[round(x, 1) for x in sens]))
            print(f"  {e[0]:4s} {e[2]} REAV {e[5]} | GFS hacia {w[0]:5.1f} a {w[1]:4.1f} m/s | dif {d} | crater 2,9/3,5 km: {sens[0]:.0f}/{sens[1]:.0f}")
    resol = [f for f in out if f.get("az_reav") is not None and f.get("resueltas", 0) > 0]
    clases = [f["huella_vs_reav"] for f in resol]
    if clases and all(c == "coincide" for c in clases):
        v = "H10 se falsa"
    elif clases and all(c == "discrepa" for c in clases):
        v = "H10 se sostiene"
    else:
        v = "no concluyente"
    print("\nVEREDICTO H10 (criterio seccion 7):", v, "| jornadas con direccion y escenas VOLCAT:", [(f["jornada"], f["huella_vs_reav"]) for f in resol])
    json.dump(dict(jornadas=out, reav_gfs=reav, veredicto=v), open(os.path.join(C.WORK, "tabla_direccion_h10.json"), "w"), indent=1)
