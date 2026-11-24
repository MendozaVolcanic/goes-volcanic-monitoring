r"""S21a1: ventana partida (10,9 menos 12,0 um) a 100 m con el control corregido escrito antes de medir.

Pregunta: la pluma de Nevados de Chillan, vista por Landsat a 100 m, ¿tiene diferencia 11 - 12 um negativa (firma de
ceniza) cuando el control no esta en su camino?

Por que asi (criterio_2026-11-24.md version 2, commiteado y empujado antes de leer el termico de la pasada):
  S20d pareo cada celda de pluma con nieve de la misma BT10 y la misma cota en todo el disco de 2 a 15 km. La mascara
  de reflectancia marca solo una parte de la pluma; lo mas frio de la pluma se pareo con pluma no marcada (su propia
  cola), y la BTD pareada quedo en cero. Aqui el control del pareo (T2) excluye un sector fijo de +-45 grados
  alrededor del eje de la pluma (azimut del centroide de la mascara de reflectancia vista desde el crater), de 2 a
  15 km, y los corrimientos del nulo tampoco pueden caer en el. Todo lo demas es el codigo de S20d
  (s20d_ventana_partida.prueba), que se importa; esta funcion lo copia con ese unico cambio, y el ensayo en seco
  comprueba que con el sector vacio da lo mismo que S20d hasta el ultimo decimal.

  T1 (contraste termico contra el anillo de 300 a 1.000 m) NO cambia: su anillo usa el control de S20d sin quitar el
  sector. Si se lo quitara, el anillo de una mascara que esta dentro del sector quedaria vacio (le paso al control
  post hoc (c) de S20d: T1 nulo).

Modos:
  python -I s21a1_medir.py seco    sinteticos sobre la geometria real y el dia de referencia sin pluma (no lee el
                                   termico de la pasada elegida)
  python -I s21a1_medir.py medir   la medida (solo despues de commitear y empujar el criterio version 2)
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
import s20d_ventana_partida as V  # noqa: E402

RES = os.path.join(os.path.dirname(AQUI), "resultados")
FIG = os.path.join(os.path.dirname(AQUI), "figuras")
A1 = r"D:\goes_notas\s21\a1"
DESC = r"D:\goes_notas\s20b\descargas"

# ------------------------------------------------------------------ reglas del criterio version 2
SEMI = 45.0                  # grados a cada lado del eje
SECTOR_KM = (2.0, 15.0)      # decide; informativo (2, 12) como el post hoc de S20d
SECTOR_KM_INF = (2.0, 12.0)
EROS = 3

# pasada que decide y dia de referencia sin pluma (criterio version 2, §2 y §4)
DIA = "2026-10-25"
HLS_DIA = os.path.join(DESC, "HLSL30", "HLS.L30.T19HBV.2026298T143431.v2.0", "HLS.L30.T19HBV.2026298T143431.v2.0.{}.tif")
MASCARA_DIA = os.path.join(S.TRABAJO, "mascara_2026-10-25.npz")
REF = "2026-10-17"
HLS_REF = os.path.join(DESC, "HLSL30_ref", "HLS.L30.T19HBV.2026290T143436.v2.0", "HLS.L30.T19HBV.2026290T143436.v2.0.{}.tif")
REF2 = "2026-09-15"           # segunda referencia sin pluma, informativa (no decide)
HLS_REF2 = os.path.join(A1, "hls", "HLS.L30.T19HBV.2026258T143426.v2.0", "HLS.L30.T19HBV.2026258T143426.v2.0.{}.tif")
H_TOPE_M = 14000 * 0.3048    # VAAC FL140 (criterio S20b §1.2)
GFS_HHMM = "14:30"


# ------------------------------------------------------------------ geometria
def geom():
    m = np.load(MASCARA_DIA)
    pl, nieve = m["pluma"], m["nieve"]
    d = S.hav(S.GLAT, S.GLON, *S.CRATER)
    dem = np.load(os.path.join(S.TRABAJO, "dem_local.npy")).astype(float)
    return pl, nieve, (d <= 15) & (d >= 2), dem, d


def azimut_celdas():
    return np.degrees(np.arctan2(S.GX - S.CX, S.GY - S.CY)) % 360


def sector_de(pl, d, km=SECTOR_KM):
    """Sector de +-SEMI grados alrededor del azimut del centroide de la mascara (vista desde el crater), de km[0] a
    km[1] del crater. Regla geometrica fija: no mira el termico."""
    eje = P.forma(pl)["azimut_centroide_desde_crater"]
    dif = np.abs((azimut_celdas() - eje + 180.0) % 360.0 - 180.0)
    return (dif <= SEMI) & (d >= km[0]) & (d <= km[1]), float(eje)


# ------------------------------------------------------------------ la prueba de S20d con el control corregido
def prueba_sector(bta, btb, z, valido, mascara_uso, disco, nieve, res_m, paso, excl_real, mascara_real, sector):
    """Copia de s20d_ventana_partida.prueba con UN cambio: el control del pareo de T2 (ctrl_par) y el lugar donde
    pueden caer los corrimientos excluyen `sector`. El anillo de T1 usa el control de S20d (ctrl_s20d), sin quitar
    el sector. Con sector vacio es identica a S20d (lo comprueba el ensayo en seco)."""
    btd = bta - btb
    dt_real = ndimage.distance_transform_edt(~mascara_real) * res_m
    ctrl_s20d = valido & disco & nieve & (dt_real > V.EXCL_CTRL)
    ctrl_par = ctrl_s20d & ~sector                                    # <- el cambio
    dt_uso = ndimage.distance_transform_edt(~mascara_uso) * res_m
    anillo_geo = (dt_uso > V.ANILLO[0]) & (dt_uso <= V.ANILLO[1])
    par = V.Pareo(bta, btd, z, ctrl_par)
    pr, pc = np.nonzero(mascara_uso)
    ar, ac = np.nonzero(anillo_geo)
    ny, nx = bta.shape

    cand = valido & disco & nieve
    bpm = np.full(bta.shape, np.nan)
    ci = np.nonzero(cand | (mascara_uso & valido))
    bpm[ci] = btd[ci] - par.valor(bta[ci], z[ci])

    def medir_en(dr, dc, real=False):
        r, c = pr + dr, pc + dc
        dentro = (r >= 0) & (r < ny) & (c >= 0) & (c < nx)
        if not real:
            if not dentro.all() or not disco[r, c].all():
                return None
            if ctrl_par[r, c].mean() < 0.5:
                return None
            sel = ctrl_par[r, c]
        else:
            sel = valido[r, c]
        r, c = r[sel], c[sel]
        a_r, a_c = ar + dr, ac + dc
        ok = (a_r >= 0) & (a_r < ny) & (a_c >= 0) & (a_c < nx)
        a_r, a_c = a_r[ok], a_c[ok]
        ok = ctrl_s20d[a_r, a_c]
        T1, n1 = V.t1_de(bta, z, (r, c), (a_r[ok], a_c[ok]))
        T2, n2 = V.t2_de(bpm, (r, c))
        return T1, T2, n1, n2

    T1r, T2r, n1r, n2r = medir_en(0, 0, real=True)
    lejos = ndimage.distance_transform_edt(~mascara_real) * res_m > excl_real
    nul, claves = [], []
    rng = range(-(ny // paso) * paso, (ny // paso) * paso + 1, paso)
    for dr in rng:
        for dc in rng:
            if dr == 0 and dc == 0:
                continue
            r, c = pr + dr, pc + dc
            if r.min() < 0 or c.min() < 0 or r.max() >= ny or c.max() >= nx:
                continue
            if not lejos[r, c].all():
                continue
            m = medir_en(dr, dc)
            if m is None or not (np.isfinite(m[0]) and np.isfinite(m[1])):
                continue
            nul.append(m[:2])
            claves.append((dr, dc))
    por_corr = dict(zip(claves, nul))
    nul = np.array(nul).reshape(-1, 2)
    out = {"T1_K": V.rnd(T1r), "T2_K": V.rnd(T2r), "celdas_T1": n1r, "celdas_T2": n2r,
           "celdas_mascara": int(mascara_uso.sum()), "celdas_mascara_validas": int((mascara_uso & valido).sum()),
           "celdas_control": int(ctrl_par.sum()), "celdas_anillo": int((anillo_geo & ctrl_s20d).sum()),
           "corrimientos": int(len(nul))}
    if len(nul):
        out.update({"p_bajo_T1": V.pfr(nul[:, 0] <= T1r), "p_bajo_T2": V.pfr(nul[:, 1] <= T2r),
                    "p_alto_T2": V.pfr(nul[:, 1] >= T2r),
                    "nulo_T1_p5_p50_p95": V.rnd(np.percentile(nul[:, 0], [5, 50, 95])),
                    "nulo_T2_p5_p50_p95": V.rnd(np.percentile(nul[:, 1], [5, 50, 95]))})
    out["T_sup_anillo_K"] = (V.rnd(float(np.median(bta[anillo_geo & ctrl_s20d])))
                             if (anillo_geo & ctrl_s20d).any() else None)
    return out, ctrl_par, bpm, {"real": (T1r, T2r), "nulo": por_corr}


def leer_hls(fmt):
    b10 = S.leer(fmt.format("B10"), escala=0.01, suma=273.15, rs=Resampling.nearest, nodata=-9999)
    b11 = S.leer(fmt.format("B11"), escala=0.01, suma=273.15, rs=Resampling.nearest, nodata=-9999)
    fm = S.leer(fmt.format("Fmask"), rs=Resampling.nearest, nodata=255)
    return b10, b11, fm


def landsat_dia(fmt, pl, u, nieve, disco, dem, sector):
    b10, b11, fm = leer_hls(fmt)
    ok = np.isfinite(b10) & np.isfinite(b11) & np.isfinite(dem)
    r, ctrl, bpm, crudo = prueba_sector(b10, b11, dem, ok, u, disco, nieve, 30.0, 10, 1000.0, pl, sector)
    fi = np.nan_to_num(fm).astype(int)
    r["fmask_nube_sombra_pluma"] = V.pfr(((fi[u & ok] >> 1) & 7) > 0)
    r["fmask_nube_sombra_control"] = V.pfr(((fi[ctrl] >> 1) & 7) > 0)
    r["fmask_nieve_pluma"] = V.pfr(((fi[u & ok] >> 4) & 1) == 1)
    r["BT10_pluma_mediana_K"] = V.rnd(float(np.median(b10[u & ok])))
    r["BTD_pluma_mediana_K"] = V.rnd(float(np.median((b10 - b11)[u & ok])))
    r["BTD_control_mediana_K"] = V.rnd(float(np.median((b10 - b11)[ctrl])))
    return r, crudo, (b10, b11, bpm)


def veredicto_final(r, rr, bc):
    """Tabla de S20b §3.2 y control de sitio de la enmienda 1 de S20d §2.1 (solo puede bajar el veredicto)."""
    v = V.veredicto_landsat(r, bc)
    sitio_ceniza = rr["T2_K"] is not None and rr["T2_K"] <= -0.3 and rr.get("p_bajo_T2", 1) <= 0.05
    sitio_agua = rr["T2_K"] is not None and rr["T2_K"] >= 0.3 and rr.get("p_alto_T2", 1) <= 0.05
    if (v == "FIRMA DE CENIZA" and sitio_ceniza) or (v == "FIRMA DE AGUA O HIELO" and sitio_agua):
        return v, "NO CONCLUYENTE (el sitio da la misma firma sin pluma)"
    return v, v


# ------------------------------------------------------------------ modos
def seco():
    """(1) Con sector vacio, prueba_sector == V.prueba (mismo codigo salvo el control).
    (2) Sinteticos de S20d con el sector: sin inyectar, ceniza, agua, gris.
    (3) Pluma no marcada: la ceniza se inyecta tambien en la nieve del sector fuera de la mascara (lo que vio S20d
        post hoc). Con el control de S20d debe perderse; con el sector, recuperarse.
    (4) Dia de referencia real sin pluma (REF) con la mascara y el sector del dia: falsa alarma del sitio."""
    rng = np.random.default_rng(21)
    pl, nieve, disco, dem, d = geom()
    u = ndimage.binary_erosion(pl, iterations=EROS)
    sect, eje = sector_de(pl, d)
    ok = np.isfinite(dem)
    ruido = ndimage.gaussian_filter(rng.normal(size=dem.shape), 3)
    ruido /= ruido.std()
    r2 = ndimage.gaussian_filter(rng.normal(size=dem.shape), 3)
    r2 /= r2.std()
    b10 = 300 - 0.0065 * np.nan_to_num(dem) + 1.0 * ruido
    base_btd = 0.4 + 0.0002 * (b10 - 280) + 0.15 * r2
    res = {"eje_grados": round(eje, 1), "sector_celdas": int(sect.sum()),
           "sector_nieve_disco_frac": V.pfr(sect[disco & nieve]), "mascara_en_sector_frac": V.pfr(sect[pl])}
    # (1) identidad
    a = b10.copy()
    btd = base_btd.copy()
    a[pl] -= 2
    btd[pl] -= 0.6
    r_v, _, bpm_v, _ = V.prueba(a, a - btd, dem, ok, u, disco, nieve, 30.0, 10, 1000.0, pl)
    r_s, _, bpm_s, _ = prueba_sector(a, a - btd, dem, ok, u, disco, nieve, 30.0, 10, 1000.0, pl,
                                     np.zeros_like(sect))
    iguales = (r_v == r_s) and np.array_equal(np.isnan(bpm_v), np.isnan(bpm_s)) and \
        np.allclose(np.nan_to_num(bpm_v), np.nan_to_num(bpm_s), atol=0, rtol=0)
    res["identidad_con_S20d_sector_vacio"] = bool(iguales)
    print("(1) identidad con S20d:", iguales, flush=True)
    # (2) sinteticos de S20d
    for etq, dT, dB in (("sin_inyectar", 0, 0), ("ceniza", -2, -0.6), ("agua", -2, 0.6), ("gris", -2, 0.0)):
        a = b10.copy()
        btd = base_btd.copy()
        a[pl] += dT
        btd[pl] += dB
        r, _, _, _ = prueba_sector(a, a - btd, dem, ok, u, disco, nieve, 30.0, 10, 1000.0, pl, sect)
        r["veredicto"] = V.veredicto_landsat(r, -0.5)
        res[etq] = r
        print("(2)", etq, json.dumps(r, ensure_ascii=False), flush=True)
    # (3) pluma no marcada en el sector (franja de 2 km de ancho a lo largo del eje, de 3 a 12 km), con su nucleo
    #     mas frio que el resto, como en S20d
    az = azimut_celdas()
    perp = d * np.sin(np.radians(az - eje))
    a_lo = d * np.cos(np.radians(az - eje))
    franja = (np.abs(perp) <= 1.0) & (a_lo >= 3) & (a_lo <= 12) & nieve & ~pl
    for etq, dTf in (("no_marcada_fria", -3.0), ("no_marcada_igual", -2.0)):
        a = b10.copy()
        btd = base_btd.copy()
        a[pl] -= 2
        btd[pl] -= 0.6
        a[franja] += dTf
        btd[franja] -= 0.6
        rv, _, _, _ = V.prueba(a, a - btd, dem, ok, u, disco, nieve, 30.0, 10, 1000.0, pl)
        rs, _, _, _ = prueba_sector(a, a - btd, dem, ok, u, disco, nieve, 30.0, 10, 1000.0, pl, sect)
        res[etq] = {"franja_celdas": int(franja.sum()), "franja_en_sector": V.pfr(sect[franja]),
                    "S20d": {k: rv[k] for k in ("T1_K", "T2_K", "p_bajo_T2", "corrimientos")},
                    "S20d_veredicto": V.veredicto_landsat(rv, -0.5),
                    "S21a1": {k: rs[k] for k in ("T1_K", "T2_K", "p_bajo_T2", "corrimientos")},
                    "S21a1_veredicto": V.veredicto_landsat(rs, -0.5)}
        print("(3)", etq, json.dumps(res[etq], ensure_ascii=False), flush=True)
    # (4) dias de referencia reales (REF decide el control de sitio; REF2 informativo)
    for dia_r, fmt in ((REF, HLS_REF), (REF2, HLS_REF2)):
        rr, _, _ = landsat_dia(fmt, pl, u, nieve, disco, dem, sect)
        rr["veredicto_si_fuera_evento"] = V.veredicto_landsat(rr, -0.5)
        res[f"referencia_{dia_r}_real"] = rr
        print("(4) referencia", dia_r, json.dumps(rr, ensure_ascii=False), flush=True)
    with open(os.path.join(RES, "s21a1_seco.json"), "w", encoding="utf-8") as fh:
        json.dump(res, fh, ensure_ascii=False, indent=1)


def medir():
    pl, nieve, disco, dem, d = geom()
    sect, eje = sector_de(pl, d)
    sect12, _ = sector_de(pl, d, SECTOR_KM_INF)
    T_tope = V.gfs_t_tope(DIA, GFS_HHMM, H_TOPE_M)
    out = {"dia": DIA, "referencia": REF, "eje_grados": round(eje, 1), "semi_grados": SEMI,
           "sector_km": SECTOR_KM, "sector_celdas": int(sect.sum()), "mascara_en_sector_frac": V.pfr(sect[pl]),
           "H_tope_m": round(H_TOPE_M), "T_tope_GFS_K": V.rnd(T_tope)}
    for etq, e, sc in (("decide_erosion_3_sector_2_15", 3, sect), ("inf_erosion_2_sector_2_15", 2, sect),
                       ("inf_erosion_3_sector_2_12", 3, sect12)):
        u = ndimage.binary_erosion(pl, iterations=e)
        r, crudo, arr = landsat_dia(HLS_DIA, pl, u, nieve, disco, dem, sc)
        e11, bc = V.btd_esperada(r["T1_K"], T_tope, r["T_sup_anillo_K"])
        r.update({"eps11_de_T1": e11, "BTD_ceniza_esperada_K": bc})
        rr, crudo_ref, _ = landsat_dia(HLS_REF, pl, u, nieve, disco, dem, sc)
        v, vf = veredicto_final(r, rr, bc)
        rr2, crudo_ref2, _ = landsat_dia(HLS_REF2, pl, u, nieve, disco, dem, sc)
        r.update({"veredicto_tabla": v, "veredicto": vf, f"referencia_{REF}": rr,
                  f"D_evento_menos_{REF}": V.diferencia(crudo, crudo_ref),
                  f"referencia_{REF2}_informativa": rr2,
                  f"D_evento_menos_{REF2}_informativa": V.diferencia(crudo, crudo_ref2)})
        out[etq] = r
        print(etq, json.dumps(r, ensure_ascii=False), flush=True)
        if etq.startswith("decide"):
            figura(arr, leer_hls(HLS_REF), pl, sect)
    with open(os.path.join(RES, "s21a1_resultado.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1)


def figura(ev, rf, pl, sect):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    c, w = S.N // 2, 400
    sl = (slice(c - w, c + w), slice(c - w, c + w))
    ext = [-12, 12, -12, 12]
    fig, ax = plt.subplots(1, 2, figsize=(11, 5), constrained_layout=True)
    for j, (tit, x) in enumerate(((f"{DIA} (pluma)", ev), (f"{REF} (referencia)", rf))):
        im = ax[j].imshow((x[0] - x[1])[sl], extent=ext, cmap="RdBu", vmin=-3, vmax=3)
        plt.colorbar(im, ax=ax[j], label="BT10 - BT11 (K)")
        ax[j].contour(pl[sl][::-1], levels=[0.5], colors="lime", linewidths=0.8, extent=ext)
        ax[j].contour(sect[sl][::-1], levels=[0.5], colors="k", linewidths=0.6, linestyles="--", extent=ext)
        ax[j].plot(0, 0, "^", mfc="none", mec="k", ms=9)
        ax[j].set_title(f"HLS L30 {tit}: BTD 10,9 - 12,0 um")
        ax[j].set_xlabel("km al E del crater")
        ax[j].set_ylabel("km al N")
    fig.suptitle("Nevados de Chillan. Verde: mascara de reflectancia. Trazos: sector excluido del control (regla fija)")
    fig.savefig(os.path.join(FIG, "s21a1_btd.png"), dpi=80)
    plt.close(fig)


if __name__ == "__main__":
    {"seco": seco, "medir": medir}[sys.argv[1]]()
