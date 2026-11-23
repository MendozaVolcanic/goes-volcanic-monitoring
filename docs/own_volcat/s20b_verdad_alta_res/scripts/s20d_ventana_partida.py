r"""S20d: prueba 2 de S20b, ventana partida (11 menos 12 um) a 100 m (Landsat 8 TIRS vía HLS) y 70 m (ECOSTRESS).

Pregunta: cuando el pixel resuelve la pluma de Chillan, ¿tiene diferencia 11 - 12 um negativa (firma de ceniza)?
Si no la tiene ni a 100 m, el limite de lo que ve GOES esta en la ceniza (gruesa, humeda, poca o muy delgada), no en
el tamaño del pixel. Si la tiene, la firma que vio GOES en la prueba 1 viene de la ceniza y no de la mezcla de
superficies dentro del pixel de 2 km.

Por que asi (criterio §3 y enmienda 1 de S20d, ambos commiteados antes de medir):
  T1 = contraste termico de la pluma contra su anillo de 300 a 1.000 m, a igual cota (+-150 m): dice si la pluma se
       ve en el termico a esa resolucion. Sin contraste no se puede juzgar la ventana partida.
  T2 = BTD de la pluma menos la BTD de celdas control con la misma BT10 (+-0,5 K) y la misma cota (+-150 m): la BTD
       de una superficie depende de su temperatura y de la columna de vapor sobre ella (cota); al parear por las dos
       queda lo que pone la pluma.
  Nulo: la mascara corrida rigida por el disco; p = fraccion de corrimientos con T igual o mas extremo.

Modos:
  python -I s20d_ventana_partida.py seco    datos sinteticos sobre la geometria real (no lee termico): prueba que el
                                            codigo encuentra una firma inyectada y no la inventa sin ella
  python -I s20d_ventana_partida.py medir   la medida (solo despues de commitear y empujar la enmienda)
"""
import glob
import json
import os
import sys
from datetime import datetime

import numpy as np
import rasterio
from pyproj import Transformer
from rasterio.enums import Resampling
from scipy import ndimage

sys.stdout.reconfigure(encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
sys.path.insert(0, os.path.join(AQUI, "..", "..", "h29_pluma_0811", "scripts"))
sys.path.insert(0, os.path.join(AQUI, "..", "..", "h24_pulsos_reav", "scripts"))
import s20b_comun as S  # noqa: E402
import h29_comun as H29  # noqa: E402  (huella del PNG de VOLCAT, leida de D:, nada al repo)

RES = os.path.join(os.path.dirname(AQUI), "resultados")
DESC = r"D:\goes_notas\s20b\descargas"
HLS = os.path.join(DESC, "HLSL30", "HLS.L30.T19HBV.2026298T143431.v2.0", "HLS.L30.T19HBV.2026298T143431.v2.0.{}.tif")
ECO = {"2026-10-25": os.path.join(DESC, "ECO_L1CT_RAD", "ECOv002_L1CT_RAD_47096_019_19HBV_20261025T173555_0713_01"),
       "2026-11-08": os.path.join(DESC, "ECO_L1CT_RAD", "ECOv002_L1CT_RAD_47316_030_19HBV_20261108T192803_0713_02"),
       "2026-10-17": os.path.join(DESC, "ECO_L1CT_RAD_ref", "ECOv002_L1CT_RAD_46974_024_19HBV_20261017T204204_0713_02")}
ECO_V3 = {"2026-10-25": os.path.join(DESC, "ECO_L1CT_RAD", "ECOv003_L1CT_RAD_47096_019_19HBV_20261025T173555_03"),
          "2026-11-08": os.path.join(DESC, "ECO_L1CT_RAD", "ECOv003_L1CT_RAD_47316_030_19HBV_20261108T192804_05")}
ALTURA_LSTE = glob.glob(os.path.join(DESC, "ECO_L2T_LSTE", "ECOv002*20261108T192803*", "*_height.tif"))[0]

# reglas (criterio §3 y enmienda 1)
EROS = 3                       # celdas de 30 m que se erosiona la mascara de Landsat (pie de 100 m del TIRS)
ANILLO = (300.0, 1000.0)       # m, desde la mascara
EXCL_CTRL = 300.0              # m, el control no toca la pluma
DZ, DBT, MIN_PAR = 150.0, 0.5, 20
RBT, RZ = 0.1, 25.0            # tabla del pareo: BT redondeada a 0,1 K y cota a 25 m
MIN_CELDAS = 10                # celdas con par para que un corrimiento cuente
MIN_CORR = 30
C1, C2 = 1.191042e8, 1.4387752e4   # W um4 m-2 sr-1 y um K (Planck en longitud de onda)
H_25 = 14000 * 0.3048          # m, altura del VAAC (criterio §1.2)
AREA_REG, BTD_REG = 0.1, -1.0  # km2 y K, regiones del mapa descriptivo de ECOSTRESS 25-10
AZ_OSO = (225.0, 270.0)        # sector de la pluma de la mañana del 25-10 (OSO, centroide a 253 grados)


# ---------------------------------------------------------------------------------------------- lectura
def bt_planck(L, lam_um):
    with np.errstate(invalid="ignore", divide="ignore"):
        return C2 / (lam_um * np.log(C1 / (lam_um ** 5 * L) + 1.0))


def eco_grilla(dia_ref="2026-11-08", medio_m=42000.0):
    """Ventana de la grilla nativa de 70 m de ECOSTRESS (tesela 19HBV, UTM 19 S) alrededor del crater."""
    f = glob.glob(os.path.join(ECO[dia_ref], "*_radiance_4.tif"))[0]
    with rasterio.open(f) as ds:
        t = Transformer.from_crs(4326, ds.crs, always_xy=True)
        x0, y0 = t.transform(S.CRATER[1], S.CRATER[0])
        r0, c0 = ds.index(x0, y0)
        n = int(medio_m / 70)
        win = rasterio.windows.Window(c0 - n, r0 - n, 2 * n + 1, 2 * n + 1)
        T = ds.window_transform(win)
        crs, tr = ds.crs, ds.transform
    rr, cc = np.mgrid[:2 * n + 1, :2 * n + 1]
    X, Y = T.c + (cc + .5) * T.a, T.f + (rr + .5) * T.e
    LON, LAT = Transformer.from_crs(crs, 4326, always_xy=True).transform(X, Y)
    return {"win": win, "tr": tr, "X": X, "Y": Y, "LAT": LAT, "LON": LON, "x0": x0, "y0": y0,
            "dist": np.hypot(X - x0, Y - y0) / 1000.0, "az": np.degrees(np.arctan2(X - x0, Y - y0)) % 360}


def eco_leer(carpeta, g):
    """BT a 10,5 y 12,0 um (bandas 4 y 5, longitudes de onda del propio archivo) y celdas validas."""
    meta = json.load(open(glob.glob(os.path.join(carpeta, "*.json"))[0]))
    lam = meta.get("ProductMetadata", {}).get("BandSpecification")

    def rd(suf):
        with rasterio.open(glob.glob(os.path.join(carpeta, f"*_{suf}.tif"))[0]) as ds:
            assert ds.transform == g["tr"]
            return ds.read(1, window=g["win"], boundless=True, fill_value=np.nan if "radiance" in suf else 255)
    l4, l5 = rd("radiance_4").astype(float), rd("radiance_5").astype(float)
    q4, q5 = rd("data_quality_4"), rd("data_quality_5")
    nube = rd("cloud") if glob.glob(os.path.join(carpeta, "*_cloud.tif")) else rd("prelim_cloud_mask")
    agua = rd("water")
    lam4, lam5 = (float(lam[4]), float(lam[5])) if lam else (10.5, 12.0)
    a, b = bt_planck(l4, lam4), bt_planck(l5, lam5)
    ok = np.isfinite(a) & np.isfinite(b) & (q4 == 0) & (q5 == 0) & (nube == 0) & (agua == 0)
    return a, b, ok, {"lambda_um": [lam4, lam5], "celdas_validas": int(ok.sum())}


def eco_cota(g):
    with rasterio.open(ALTURA_LSTE) as ds:
        assert ds.transform == g["tr"]
        return ds.read(1, window=g["win"], boundless=True, fill_value=np.nan).astype(float)


def gfs_t_tope(dia="2026-10-25", hhmm="14:30", h=H_25):
    import h24_medir as H24
    d = (datetime.strptime(dia, "%Y-%m-%d") - H24.T0).days
    s = int(hhmm[:2]) * 6 + int(hhmm[3:]) // 10
    return float(H24.gfs_t(np.array([h]))[d, s, 0])


# ---------------------------------------------------------------------------------------------- medidas
class Pareo:
    """Mediana de la BTD de las celdas control con |BTa - bt| <= DBT y |z - zc| <= DZ, en tabla redondeada."""

    def __init__(self, bta, btd, z, ctrl):
        o = np.argsort(bta[ctrl])
        self.bt, self.btd, self.z = bta[ctrl][o], btd[ctrl][o], z[ctrl][o]
        self.tab = {}

    def valor(self, bt, z):
        kb, kz = np.rint(bt / RBT).astype(int), np.rint(z / RZ).astype(int)
        out = np.full(bt.shape, np.nan)
        for i, (a, b) in enumerate(zip(kb, kz)):
            k = (a, b)
            if k not in self.tab:
                lo, hi = np.searchsorted(self.bt, [a * RBT - DBT, a * RBT + DBT], side="left")
                hi = np.searchsorted(self.bt, a * RBT + DBT, side="right")
                zz = self.z[lo:hi]
                sel = np.abs(zz - b * RZ) <= DZ
                self.tab[k] = float(np.median(self.btd[lo:hi][sel])) if sel.sum() >= MIN_PAR else np.nan
            out[i] = self.tab[k]
        return out


def t1_de(bta, z, celdas, anillo):
    """T1: mediana sobre las celdas de [BT - mediana de BT del anillo con cota +-DZ] (>= MIN_PAR en el anillo)."""
    ri, ci = celdas
    ra, ca = anillo
    if len(ri) == 0 or len(ra) < MIN_PAR:
        return np.nan, 0
    o = np.argsort(z[ra, ca])
    zr, br = z[ra, ca][o], bta[ra, ca][o]
    zc = z[ri, ci]
    kz = np.rint(zc / 10.0).astype(int)
    ref = {}
    for k in np.unique(kz):
        lo, hi = np.searchsorted(zr, [k * 10.0 - DZ, k * 10.0 + DZ])
        ref[k] = float(np.median(br[lo:hi])) if hi - lo >= MIN_PAR else np.nan
    d = bta[ri, ci] - np.array([ref[k] for k in kz])
    d = d[np.isfinite(d)]
    return (float(np.median(d)) if d.size >= MIN_CELDAS else np.nan), int(d.size)


def t2_de(btd_menos_par, celdas):
    v = btd_menos_par[celdas]
    v = v[np.isfinite(v)]
    return (float(np.median(v)) if v.size >= MIN_CELDAS else np.nan), int(v.size)


def prueba(bta, btb, z, valido, mascara_uso, disco, nieve, res_m, paso, excl_real, mascara_real):
    """T1, T2 y su nulo. mascara_uso: celdas de pluma que se miden (y se corren). mascara_real: la pluma entera (el
    control no la toca a menos de EXCL_CTRL). nieve: clase de superficie exigida al control y al anillo (o todo True)."""
    btd = bta - btb
    dt_real = ndimage.distance_transform_edt(~mascara_real) * res_m
    ctrl = valido & disco & nieve & (dt_real > EXCL_CTRL)
    dt_uso = ndimage.distance_transform_edt(~mascara_uso) * res_m
    anillo_geo = (dt_uso > ANILLO[0]) & (dt_uso <= ANILLO[1])
    par = Pareo(bta, btd, z, ctrl)
    pr, pc = np.nonzero(mascara_uso)
    ar, ac = np.nonzero(anillo_geo)
    ny, nx = bta.shape

    # tabla de pareo para todas las celdas que algun corrimiento puede usar
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
            if ctrl[r, c].mean() < 0.5:
                return None
            sel = ctrl[r, c]
        else:
            sel = valido[r, c]
        r, c = r[sel], c[sel]
        a_r, a_c = ar + dr, ac + dc
        ok = (a_r >= 0) & (a_r < ny) & (a_c >= 0) & (a_c < nx)
        a_r, a_c = a_r[ok], a_c[ok]
        ok = ctrl[a_r, a_c]
        T1, n1 = t1_de(bta, z, (r, c), (a_r[ok], a_c[ok]))
        T2, n2 = t2_de(bpm, (r, c))
        return T1, T2, n1, n2

    T1r, T2r, n1r, n2r = medir_en(0, 0, real=True)
    # corrimientos: la mascara corrida mas su kilometro alrededor no toca la pluma real
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
    out = {"T1_K": rnd(T1r), "T2_K": rnd(T2r), "celdas_T1": n1r, "celdas_T2": n2r,
           "celdas_mascara": int(mascara_uso.sum()), "celdas_mascara_validas": int((mascara_uso & valido).sum()),
           "celdas_control": int(ctrl.sum()), "celdas_anillo": int((anillo_geo & ctrl).sum()),
           "corrimientos": int(len(nul))}
    if len(nul):
        out.update({"p_bajo_T1": pfr(nul[:, 0] <= T1r), "p_bajo_T2": pfr(nul[:, 1] <= T2r),
                    "p_alto_T2": pfr(nul[:, 1] >= T2r),
                    "nulo_T1_p5_p50_p95": rnd(np.percentile(nul[:, 0], [5, 50, 95])),
                    "nulo_T2_p5_p50_p95": rnd(np.percentile(nul[:, 1], [5, 50, 95]))})
    extra = {"T_sup_anillo_K": rnd(float(np.median(bta[anillo_geo & ctrl]))) if (anillo_geo & ctrl).any() else None}
    out.update(extra)
    return out, ctrl, bpm, {"real": (T1r, T2r), "nulo": por_corr}


def rnd(x, k=3):
    if isinstance(x, np.ndarray):
        return [round(float(v), k) for v in x]
    return None if x is None or not np.isfinite(x) else round(float(x), k)


def pfr(b):
    return round(float(np.mean(b)), 4)


def veredicto_landsat(r, btd_ceniza):
    T1, T2 = r["T1_K"], r["T2_K"]
    if r["corrimientos"] < MIN_CORR or T1 is None or T2 is None:
        return "NO CONCLUYENTE (sin nulo)"
    if T1 > -0.5 or r["p_bajo_T1"] > 0.05:
        return "SIN CONTRASTE"
    if T2 <= -0.3 and r["p_bajo_T2"] <= 0.05:
        return "FIRMA DE CENIZA"
    if T2 >= 0.3 and r["p_alto_T2"] <= 0.05:
        return "FIRMA DE AGUA O HIELO"
    if r["p_bajo_T2"] > 0.20 and btd_ceniza is not None and T2 > btd_ceniza / 2:
        return "SIN FIRMA"
    return "NO CONCLUYENTE"


def btd_esperada(T1, T_tope, T_sup):
    """Criterio §3.2: eps11 = T1/(T_tope - T_sup); eps12 = 1 - (1 - eps11)^0,7; BTD = -(eps11 - eps12)(T_sup - T_tope)."""
    if T1 is None or T1 >= 0 or T_sup is None or T_tope >= T_sup:
        return None, None
    e11 = min(T1 / (T_tope - T_sup), 1.0)
    e12 = 1 - (1 - e11) ** 0.7
    return rnd(e11), rnd(-(e11 - e12) * (T_sup - T_tope))


# ---------------------------------------------------------------------------------------------- piezas por dato
def geom_landsat(eros=EROS):
    m = np.load(os.path.join(S.TRABAJO, "mascara_2026-10-25.npz"))
    pl, nieve = m["pluma"], m["nieve"]
    uso = ndimage.binary_erosion(pl, iterations=eros) if eros else pl.copy()
    d = S.hav(S.GLAT, S.GLON, *S.CRATER)
    dem = np.load(os.path.join(S.TRABAJO, "dem_local.npy")).astype(float)
    return pl, uso, nieve, (d <= 15) & (d >= 2), dem


def mascara_eco_0811(g):
    """Huella VOLCAT de 19:20 (H29, corrida segun H14), cada pixel a su altura VOLCAT, mas 1 pixel ABI alrededor, en
    el suelo: celdas cuya posicion a la altura del pixel cae en el bloque de 3 x 3 alrededor de el."""
    ok, mid, _ = H29.decodifica_png(os.path.join(H29.FRAMES, "2026-11-08_19-20-30.png"))
    ash, hh = H29.a_abi(ok, mid)
    mask = np.zeros(g["X"].shape, bool)
    for r, c in zip(*np.nonzero(ash)):
        rv, cv = S.a_ventana(g["LAT"], g["LON"], float(hh[r, c]) * 1000.0)
        mask |= (np.abs(np.rint(rv) - r) <= 1) & (np.abs(np.rint(cv) - c) <= 1)
    return mask, int(ash.sum()), sorted({float(x) for x in hh[ash]})


def regiones(bpm, valido_disco, g):
    """Regiones conexas (8 vecinos) con BTD pareada < BTD_REG y area >= AREA_REG, dentro del disco."""
    m = valido_disco & np.isfinite(bpm) & (bpm < BTD_REG)
    lab, n = ndimage.label(m, structure=np.ones((3, 3)))
    regs = []
    if n:
        cnt = np.bincount(lab.ravel())
        for k in np.nonzero(cnt * 0.0049 >= AREA_REG)[0]:
            if k == 0:
                continue
            rr, cc = np.nonzero(lab == k)
            regs.append({"km2": round(len(rr) * 0.0049, 3), "dist_km": round(float(g["dist"][rr, cc].mean()), 1),
                         "azimut": round(float(np.degrees(np.arctan2(g["X"][rr, cc].mean() - g["x0"],
                                                                       g["Y"][rr, cc].mean() - g["y0"])) % 360), 1),
                         "btd_pareada_mediana": round(float(np.median(bpm[rr, cc])), 2)})
    regs.sort(key=lambda x: -x["km2"])
    oso = [x for x in regs if AZ_OSO[0] <= x["azimut"] <= AZ_OSO[1]]
    return {"n_regiones": len(regs), "km2_total": round(sum(x["km2"] for x in regs), 3),
            "n_en_OSO": len(oso), "km2_en_OSO": round(sum(x["km2"] for x in oso), 3),
            "frac_celdas_bajo_-1K": round(float(m.sum() / max(valido_disco.sum(), 1)), 4), "regiones": regs[:15]}


def mapa_eco(dia, g, z):
    a, b, ok, meta = eco_leer(ECO[dia], g)
    disco = (g["dist"] <= 25) & (g["dist"] >= 2)
    ctrl = ok & disco
    par = Pareo(a, a - b, z, ctrl)
    bpm = np.full(a.shape, np.nan)
    idx = np.nonzero(ctrl)
    bpm[idx] = (a - b)[idx] - par.valor(a[idx], z[idx])
    out = regiones(bpm, ctrl, g)
    out.update(meta)
    out["btd_pareada_p1_p50_p99"] = rnd(np.nanpercentile(bpm[ctrl], [1, 50, 99]))
    return out


# ---------------------------------------------------------------------------------------------- modos
def seco():
    """Sintetico sobre la geometria real: BT10 con gradiente de cota y ruido espacial, BTD de fondo con ruido.
    (a) sin inyectar, (b) pluma con -2 K y BTD -0,6 K, (c) pluma con -2 K y BTD +0,6 K, (d) -2 K y BTD 0."""
    rng = np.random.default_rng(20)
    pl, uso, nieve, disco, dem = geom_landsat()
    ok = np.isfinite(dem)
    ruido = ndimage.gaussian_filter(rng.normal(size=dem.shape), 3)
    ruido /= ruido.std()
    r2 = ndimage.gaussian_filter(rng.normal(size=dem.shape), 3)
    r2 /= r2.std()
    b10 = 300 - 0.0065 * np.nan_to_num(dem) + 1.0 * ruido
    base_btd = 0.4 + 0.0002 * (b10 - 280) + 0.15 * r2
    res = {}
    for etq, dT, dB in (("sin_inyectar", 0, 0), ("ceniza", -2, -0.6), ("agua", -2, 0.6), ("gris", -2, 0.0)):
        a = b10.copy()
        btd = base_btd.copy()
        a[pl] += dT
        btd[pl] += dB
        r, _, _, _ = prueba(a, a - btd, dem, ok, uso, disco, nieve, 30.0, 10, 1000.0, pl)
        r["veredicto"] = veredicto_landsat(r, -0.5)
        res[etq] = r
        print(etq, json.dumps(r, ensure_ascii=False), flush=True)
    # Landsat 9 real de un dia sin evento (17-10 14:34) con la mascara del 25-10: falsa alarma del sitio
    ref = os.path.join(DESC, "HLSL30_ref", "HLS.L30.T19HBV.2026290T143436.v2.0", "HLS.L30.T19HBV.2026290T143436.v2.0.{}.tif")
    r, _, _ = landsat_dia(ref.format("B10"), ref.format("B11"), ref.format("Fmask"), pl, uso, nieve, disco, dem)
    r["veredicto_si_fuera_evento"] = veredicto_landsat(r, -0.5)
    res["landsat_1017_con_mascara_2510"] = r
    print("Landsat 17-10 seco", json.dumps(r, ensure_ascii=False), flush=True)
    # ECOSTRESS real de un dia sin evento (17-10 20:42, la referencia) con la mascara del 08-11: falsa alarma
    g = eco_grilla()
    z = eco_cota(g)
    mask, npx, alts = mascara_eco_0811(g)
    a, b, ok, meta = eco_leer(ECO["2026-10-17"], g)
    ok &= np.isfinite(z)
    disco = (g["dist"] <= 40) & (g["dist"] >= 2)
    r, _, _, _ = prueba(a, b, z, ok, mask & (g["dist"] >= 2), disco, np.ones_like(ok), 70.0, 14, 300.0, mask)
    r.update(meta)
    r.update({"huella_px_19_20": npx, "alturas_volcat_km": alts, "mascara_km2": round(mask.sum() * 0.0049, 2)})
    res["ecostress_1017_con_mascara_0811"] = r
    print("ECOSTRESS 17-10 seco", json.dumps(r, ensure_ascii=False), flush=True)
    with open(os.path.join(RES, "s20d_seco.json"), "w", encoding="utf-8") as fh:
        json.dump(res, fh, ensure_ascii=False, indent=1)


def diferencia(ev, ref):
    """D = T(evento) - T(referencia sin pluma), en la mascara real y en cada corrimiento valido los dos dias."""
    comunes = sorted(set(ev["nulo"]) & set(ref["nulo"]))
    out = {"corrimientos_comunes": len(comunes)}
    for k, nom in ((0, "T1"), (1, "T2")):
        Dr = ev["real"][k] - ref["real"][k]
        Dn = np.array([ev["nulo"][c][k] - ref["nulo"][c][k] for c in comunes])
        out[f"D_{nom}_K"] = rnd(Dr)
        if len(Dn) and np.isfinite(Dr):
            out[f"p_bajo_D_{nom}"] = pfr(Dn <= Dr)
            out[f"p_alto_D_{nom}"] = pfr(Dn >= Dr)
            out[f"nulo_D_{nom}_p5_p50_p95"] = rnd(np.percentile(Dn, [5, 50, 95]))
    return out


def landsat_dia(f_b10, f_b11, f_fm, pl, u, nieve, disco, dem):
    b10 = S.leer(f_b10, escala=0.01, suma=273.15, rs=Resampling.nearest, nodata=-9999)
    b11 = S.leer(f_b11, escala=0.01, suma=273.15, rs=Resampling.nearest, nodata=-9999)
    fm = S.leer(f_fm, rs=Resampling.nearest, nodata=255)
    ok = np.isfinite(b10) & np.isfinite(b11) & np.isfinite(dem)
    r, ctrl, bpm, crudo = prueba(b10, b11, dem, ok, u, disco, nieve, 30.0, 10, 1000.0, pl)
    fi = np.nan_to_num(fm).astype(int)
    r["fmask_nube_sombra_pluma"] = pfr(((fi[u & ok] >> 1) & 7) > 0)
    r["fmask_nube_sombra_control"] = pfr(((fi[ctrl] >> 1) & 7) > 0)
    r["fmask_nieve_pluma"] = pfr(((fi[u & ok] >> 4) & 1) == 1)
    r["BT10_pluma_mediana_K"] = rnd(float(np.median(b10[u & ok])))
    r["BTD_pluma_mediana_K"] = rnd(float(np.median((b10 - b11)[u & ok])))
    r["BTD_control_mediana_K"] = rnd(float(np.median((b10 - b11)[ctrl])))
    return r, crudo, (b10, b11, bpm)


def medir():
    out = {"regla": {"EROS": EROS, "ANILLO_m": ANILLO, "EXCL_CTRL_m": EXCL_CTRL, "DZ_m": DZ, "DBT_K": DBT,
                     "MIN_PAR": MIN_PAR, "tabla_BT_K": RBT, "tabla_z_m": RZ, "MIN_CELDAS": MIN_CELDAS,
                     "MIN_CORR": MIN_CORR}}
    # --- Landsat 25-10 (decide) y control de sitio 17-10 (enmienda 1, solo puede bajar el veredicto)
    pl, _, nieve, disco, dem = geom_landsat()
    T_tope = gfs_t_tope()
    ref = os.path.join(DESC, "HLSL30_ref", "HLS.L30.T19HBV.2026290T143436.v2.0", "HLS.L30.T19HBV.2026290T143436.v2.0.{}.tif")
    L = {}
    for etq, e in (("erosion_3_decide", 3), ("erosion_2_informativo", 2)):
        u = ndimage.binary_erosion(pl, iterations=e)
        r, crudo, arr = landsat_dia(HLS.format("B10"), HLS.format("B11"), HLS.format("Fmask"), pl, u, nieve, disco, dem)
        e11, bc = btd_esperada(r["T1_K"], T_tope, r["T_sup_anillo_K"])
        r.update({"T_tope_GFS_K": rnd(T_tope), "eps11_de_T1": e11, "BTD_ceniza_esperada_K": bc})
        rr, crudo_ref, _ = landsat_dia(ref.format("B10"), ref.format("B11"), ref.format("Fmask"), pl, u, nieve, disco, dem)
        sitio_ceniza = (rr["T2_K"] is not None and rr["T2_K"] <= -0.3 and rr.get("p_bajo_T2", 1) <= 0.05)
        sitio_agua = (rr["T2_K"] is not None and rr["T2_K"] >= 0.3 and rr.get("p_alto_T2", 1) <= 0.05)
        v = veredicto_landsat(r, bc)
        v_final = v
        if (v == "FIRMA DE CENIZA" and sitio_ceniza) or (v == "FIRMA DE AGUA O HIELO" and sitio_agua):
            v_final = "NO CONCLUYENTE (el sitio da la misma firma sin pluma)"
        r.update({"veredicto_criterio": v, "veredicto": v_final, "control_sitio_2026-10-17": rr,
                  "D_evento_menos_17-10": diferencia(crudo, crudo_ref)})
        if e == 3:
            b10, b11, bpm = arr
            np.savez_compressed(os.path.join(S.TRABAJO, "s20d_landsat.npz"), b10=b10, b11=b11, bpm=bpm, uso=u)
        L[etq] = r
        print("Landsat", etq, json.dumps(r, ensure_ascii=False), flush=True)
    out["landsat_2026-10-25"] = L
    # --- ECOSTRESS 08-11 19:28 contra 17-10 20:42 (lectura, sin veredicto)
    g = eco_grilla()
    z = eco_cota(g)
    mask, npx, alts = mascara_eco_0811(g)
    disco = (g["dist"] <= 40) & (g["dist"] >= 2)
    uso = mask & (g["dist"] >= 2)
    E = {"huella_px_19_20": npx, "alturas_volcat_km": alts, "mascara_km2": round(mask.sum() * 0.0049, 2)}
    leidos = {etq: eco_leer(carpeta, g) for etq, carpeta in
              (("v002", ECO["2026-11-08"]), ("v003", ECO_V3["2026-11-08"]), ("ref", ECO["2026-10-17"]))}
    a_r, b_r, ok_r, meta_r = leidos["ref"]
    for etq in ("v002", "v003"):
        a, b, ok, meta = leidos[etq]
        r, _, _, _ = prueba(a, b, z, ok & np.isfinite(z), uso, disco, np.ones_like(ok), 70.0, 14, 300.0, mask)
        r.update(meta)
        E[etq] = r
        print("ECOSTRESS 08-11", etq, json.dumps(r, ensure_ascii=False), flush=True)
        # D sobre las celdas validas los dos dias
        comun = ok & ok_r & np.isfinite(z)
        re_, _, _, ce = prueba(a, b, z, comun, uso, disco, np.ones_like(ok), 70.0, 14, 300.0, mask)
        rr, _, _, cr = prueba(a_r, b_r, z, comun, uso, disco, np.ones_like(ok), 70.0, 14, 300.0, mask)
        E[f"D_{etq}_menos_17-10"] = {"evento_celdas_comunes": re_, "ref_2026-10-17_celdas_comunes": rr,
                                     **diferencia(ce, cr)}
        print("ECOSTRESS D", etq, json.dumps(E[f"D_{etq}_menos_17-10"], ensure_ascii=False), flush=True)
    out["ecostress_2026-11-08"] = E
    # --- ECOSTRESS 25-10 17:35 y referencia 17-10 20:42 (descriptivo)
    g = eco_grilla("2026-10-25", 27000.0)
    z = eco_cota(g)
    D = {}
    for dia in ("2026-10-25", "2026-10-17"):
        D[dia] = mapa_eco(dia, g, z)
        print("ECOSTRESS mapa", dia, json.dumps(D[dia], ensure_ascii=False), flush=True)
    out["ecostress_mapa"] = D
    with open(os.path.join(RES, "s20d_resultado.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    {"seco": seco, "medir": medir}[sys.argv[1]]()
