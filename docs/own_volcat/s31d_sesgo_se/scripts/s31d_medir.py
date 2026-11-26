r"""S31d: por qué el anillo de S26a dispara hacia el SE en oct-nov 2025, un año sin pluma.
Implementa criterio_2026-11-26.md de esta carpeta (commit 8872a7a, empujado antes de cruzar disparos con covariables).

Por qué así: el anillo marca la tajada de 30° con la cola baja de BTD más baja del cuadro. Esa elección puede preferir
un lado por tres razones que dejan huellas distintas: el método (cuántos píxeles válidos tiene cada tajada en el
cuadro), la dispersión fija de cada píxel (la alta cordillera al SE varía más de un día a otro) o algo coherente en la
atmósfera de sotavento, que entonces tiene que seguir al viento de ese día. La medida va en escalera: M1 sólo con la
máscara del cuadro y ruido igual; M2 con los residuos propios de cada píxel sorteados por separado; M3 con el viento GFS.

Uso: python -I -B s31d_medir.py pruebas | viento [k n] | medir
  pruebas  comprueba el estadístico vectorizado contra s22a_medir.estadistico, la hora sinóptica y los nulos.
  viento   baja GFS 1,0° (s27a_viento.bajar sin cambios) de las horas que faltan de 2025 a D:\goes_notas\s31\s31d\gfs.
  medir    corre M1 a M4 y la réplica 2024 una sola vez; escribe resultados/s31d_resultado.json.
"""
import itertools
import json
import math
import os
import shutil
import sys
import time
import warnings
from datetime import timedelta

import numpy as np
from scipy import stats

sys.stdout.reconfigure(encoding="utf-8")
warnings.simplefilter("ignore", RuntimeWarning)
AQUI = os.path.dirname(os.path.abspath(__file__))
OV = os.path.abspath(os.path.join(AQUI, "..", ".."))
RES = os.path.join(os.path.dirname(AQUI), "resultados")
sys.path.insert(0, os.path.join(OV, "s23_fondo_2025", "scripts"))
sys.path.insert(0, os.path.join(OV, "s25b_fondo_2024", "scripts"))
sys.path.insert(0, os.path.join(OV, "s27a_noche_causa", "scripts"))
import s23_medir as S  # noqa: E402  (Detector, disparos: sin cambios)
B, M, C29 = S.B, S.M, S.C29

TRAB = r"D:\goes_notas\s31\s31d"
GFS_NUEVO = os.path.join(TRAB, "gfs")
GFS_S27A = r"D:\goes_notas\s27\s27a\gfs"
MIN_LIBRE_GB = 6.0

# ---------- parámetros del criterio ----------
P_STAR = 4.75
SE = (4, 5, 6)
REPRO = {0: 9, 1: 10, 2: 1, 4: 41, 5: 13, 6: 35, 7: 16, 8: 6, 9: 1, 10: 4, 11: 2}
N_MC, PCT_COLA = 2000, 4.75
N_BOOT, MARGEN_EXPLICA = 10_000, 0.10
W_POZO, MIN_POZO_PIX = 9, 20
NIVEL, NIVEL_SENS = 700.0, 500.0
V_MIN = 5.0
ALFA, PISO_MAX, PODER_MIN, N_MIN_CLASE = 0.05, 0.01, 0.5, 3
DELTA_MIN, CUOTA_FUERA_MIN = 0.20, 0.45
MAX_ENUM, B_PERM, N_PODER, B_PERM_PODER = 100_000, 9_999, 1_000, 999
B_ANG = 9_999
SEMILLA = 0
T0 = S.T0R                         # 21-09-2025
ND = S.NR                          # 62 días


# ---------- estadístico vectorizado (idéntico a s22a_medir.estadistico, por filas) ----------
def estadistico_lote(X):
    """X (n, NA) residuos con NaN. Devuelve S (n), k* (n, -1 si no evaluado) y Q (n, 12)."""
    n = X.shape[0]
    Q = np.full((n, M.NSEC), np.nan)
    for k in range(M.NSEC):
        V = X[:, M.SEC == k]
        cnt = np.isfinite(V).sum(1)
        Vs = np.sort(V, axis=1)                         # NaN al final
        q = Vs[:, :M.NCOLA].mean(1)
        ok = (cnt >= 0.5 * M.NPS[k]) & (cnt >= M.NCOLA)
        Q[ok, k] = q[ok]
    nv = np.isfinite(Q).sum(1)
    ev = nv >= M.MIN_SEC
    Sx = np.full(n, np.nan)
    K = np.full(n, -1, int)
    if ev.any():
        Qe = Q[ev]
        K[ev] = np.nanargmin(Qe, 1)
        Sx[ev] = np.nanmin(Qe, 1) - np.nanmedian(Qe, 1)
    return Sx, K, Q


def p_se_cola(Sx, K):
    """Fracción de k* en SE entre las réplicas con S en su propio percentil 4,75."""
    ok = np.isfinite(Sx)
    if ok.sum() < 20:
        return np.nan
    u = np.percentile(Sx[ok], PCT_COLA)
    sel = ok & (Sx <= u)
    return float(np.isin(K[sel], SE).mean())


# ---------- viento ----------
def horas_2025():
    hs = []
    for k in range(ND + 1):                          # +1: las 00 del 22-11 para los cuadros de 22:30 en adelante
        d = T0 + timedelta(days=k)
        hs += [d + timedelta(hours=x) for x in range(0, 24, 3) if k < ND or x == 0]
    return hs


def ruta_gfs(h):
    for base in (GFS_S27A, GFS_NUEVO):
        f = os.path.join(base, f"gfst1_{h:%Y%m%d%H}.npz")
        if os.path.exists(f):
            return f
    return None


def viento_bajar(k=0, n=1):
    import s27a_viento as V
    import s3fs
    V.OUT = GFS_NUEVO                                # sólo cambia dónde guarda; el descargador no se toca
    os.makedirs(GFS_NUEVO, exist_ok=True)
    s3 = s3fs.S3FileSystem(anon=True)
    falta = [h for h in horas_2025() if ruta_gfs(h) is None][k::n]
    print(f"faltan {len(falta)} horas en esta porción", flush=True)
    for h in falta:
        if shutil.disk_usage("D:\\").free / 1e9 < MIN_LIBRE_GB:
            raise RuntimeError("D: bajo el piso de 6 GB")
        for intento in range(3):
            try:
                print(h, V.bajar(h, s3), flush=True)
                break
            except Exception as e:  # noqa: BLE001
                if intento == 2:
                    print(h, "FALLA", repr(e), flush=True)


def hora_sinoptica(d, s):
    """Hora GFS (datetime) más cercana al cuadro (d, s); empate a la anterior."""
    t = s / 6.0
    lo = math.floor(t / 3.0) * 3
    h = lo if (t - lo) <= 1.5 else lo + 3
    return T0 + timedelta(days=d, hours=h)


def bilineal(campo, lat, lon, la, lo):
    """campo (nlat, nlon) en grilla regular; lat decreciente."""
    i = np.interp(la, lat[::-1], np.arange(len(lat))[::-1])
    j = np.interp(lo, lon, np.arange(len(lon)))
    i0, j0 = int(np.floor(i)), int(np.floor(j))
    di, dj = i - i0, j - j0
    i1, j1 = min(i0 + 1, len(lat) - 1), min(j0 + 1, len(lon) - 1)
    return float((1 - di) * (1 - dj) * campo[i0, j0] + di * (1 - dj) * campo[i1, j0]
                 + (1 - di) * dj * campo[i0, j1] + di * dj * campo[i1, j1])


_VC = {}


def viento(h, nivel):
    """(rumbo hacia donde sopla en grados, rapidez m/s) en el cráter, o (nan, nan) si falta la hora."""
    key = (h, nivel)
    if key not in _VC:
        f = ruta_gfs(h)
        if f is None:
            _VC[key] = (np.nan, np.nan)
        else:
            with np.load(f) as z:
                ip = int(np.flatnonzero(z["p"] == nivel)[0])
                u = bilineal(z["u"][ip], z["lat"], z["lon"], *C29.CRATER)
                v = bilineal(z["v"][ip], z["lat"], z["lon"], *C29.CRATER)
            _VC[key] = ((math.degrees(math.atan2(u, v)) + 360.0) % 360.0, math.hypot(u, v))
    return _VC[key]


def media_circular(angs):
    a = np.radians(np.asarray(angs, float))
    return (math.degrees(math.atan2(np.sin(a).mean(), np.cos(a).mean())) + 360.0) % 360.0


def en_se(theta):
    return 120.0 <= theta < 210.0


def dist_ang(a, b):
    x = np.abs((np.asarray(a) - np.asarray(b)) % 360.0)
    return np.minimum(x, 360.0 - x)


# ---------- nulos por días ----------
def delta_permutacion(f, clase, rng, b_azar=B_PERM):
    """f: fracción SE por día; clase: True = sotavento SE, False = fuera. Δ, p unilateral (Δ* >= Δ), piso, modo."""
    f = np.asarray(f, float)
    clase = np.asarray(clase, bool)
    n, n_out = len(f), int((~clase).sum())
    n_in = n - n_out
    delta = f[clase].mean() - f[~clase].mean()
    tot = f.sum()
    C = math.comb(n, n_out)
    if C <= MAX_ENUM:
        idx = np.array(list(itertools.combinations(range(n), n_out)), int)
        so = f[idx].sum(1)
        dd = (tot - so) / n_in - so / n_out
        p = float((dd >= delta - 1e-12).mean())
        return float(delta), p, 1.0 / C, "exacta"
    cnt = 0
    for _ in range(b_azar):
        perm = rng.permutation(clase)
        cnt += f[perm].mean() - f[~perm].mean() >= delta - 1e-12
    return float(delta), (1 + cnt) / (b_azar + 1), 1.0 / (b_azar + 1), "azar"


def bootstrap_exceso(O, N, E, rng):
    O, N, E = (np.asarray(x, float) for x in (O, N, E))
    x0 = O.sum() / N.sum() - E.sum() / N.sum()
    idx = rng.integers(0, len(O), (N_BOOT, len(O)))
    xs = O[idx].sum(1) / N[idx].sum(1) - E[idx].sum(1) / N[idx].sum(1)
    lo, hi = np.percentile(xs, [2.5, 97.5])
    return float(x0), float(lo), float(hi)


def rotulo_exceso(x, lo, hi):
    if lo <= 0 <= hi and abs(x) <= MARGEN_EXPLICA:
        return "EXPLICA"
    if lo > 0:
        return "NO EXPLICA"
    if hi < 0:
        return "SOBREEXPLICA"
    return "NO DECIDIBLE"


# ---------- pruebas de código ----------
def pruebas():
    rng = np.random.default_rng(3)
    X = rng.standard_normal((300, M.NA)).astype(np.float32)
    X[rng.random(X.shape) < 0.3] = np.nan
    X[:40, M.SEC == 4] = np.nan                          # tajadas enteras borradas
    X[40:60] = np.nan                                    # cuadros no evaluados
    X[60:70, np.isin(M.SEC, (0, 1, 2, 3))] = np.nan      # menos de 9 tajadas
    Sx, K, _ = estadistico_lote(X)
    for i in range(300):
        s, k, _ = M.estadistico(X[i])
        assert (np.isnan(s) and np.isnan(Sx[i]) and K[i] == -1) or (abs(s - Sx[i]) < 1e-5 and k == K[i]), i
    assert hora_sinoptica(0, 9) == T0 + timedelta(hours=0)            # 01:30 empata: a la anterior
    assert hora_sinoptica(0, 10) == T0 + timedelta(hours=3)           # 01:40
    assert hora_sinoptica(0, 141) == T0 + timedelta(days=1)           # 23:30
    # Δ exacta: con f = clase perfecta, p = piso
    d, p, piso, modo = delta_permutacion([1, 1, 1, 0, 0, 0], [True] * 3 + [False] * 3, rng)
    assert modo == "exacta" and abs(p - 1 / 20) < 1e-12 and abs(piso - 1 / 20) < 1e-12 and d == 1.0
    d, p, _, _ = delta_permutacion([0.5] * 6, [True] * 3 + [False] * 3, rng)
    assert p == 1.0
    assert en_se(120.0) and en_se(209.9) and not en_se(210.0) and not en_se(119.9)
    assert abs(media_circular([350, 10]) % 360) < 1e-9 or abs(media_circular([350, 10]) - 360) < 1e-9
    assert dist_ang(355, 5) == 10
    x, lo, hi = bootstrap_exceso([5, 5], [10, 10], [5, 5], rng)
    assert x == 0 and lo == 0 and hi == 0 and rotulo_exceso(x, lo, hi) == "EXPLICA"
    assert rotulo_exceso(0.3, 0.1, 0.5) == "NO EXPLICA" and rotulo_exceso(-0.3, -0.5, -0.1) == "SOBREEXPLICA"
    assert rotulo_exceso(0.2, -0.05, 0.4) == "NO DECIDIBLE"
    print("pruebas OK")


# ---------- medida ----------
def disparos_anio(SR, KR, dias, umbral_de_dia):
    out = []
    for d in dias:
        U = umbral_de_dia(d)
        F, _ = S.disparos(SR, KR, d, U)
        out += [(d, int(s), int(KR[d, s])) for s in np.flatnonzero(F)]
    return out


def residuos_pozo(mm, gate, base_d, dias, d, s):
    """Residuos (filas, NA) de los otros días a +-90 min, en cuadros que pasan la compuerta, con la base base_d."""
    filas = []
    for dd in dias:
        if dd == d:
            continue
        for x in range(144):
            if M.dslot(x, s) <= W_POZO and gate[dd, x]:
                filas.append(mm[dd, x] - base_d[x])
    return np.array(filas, np.float32)


def modelos_cuadro(r, pozo, semilla):
    """p0, p1, p2 de un cuadro: r residuo real (su máscara), pozo para M2."""
    mask = np.isfinite(r)
    rng = np.random.default_rng(semilla)
    Z = rng.standard_normal((N_MC, M.NA))
    p0 = p_se_cola(*estadistico_lote(Z)[:2])
    Z[:, ~mask] = np.nan
    p1 = p_se_cola(*estadistico_lote(Z)[:2])
    X = np.full((N_MC, M.NA), np.nan, np.float32)
    todos = pozo[np.isfinite(pozo)]
    for i in np.flatnonzero(mask):
        v = pozo[:, i]
        v = v[np.isfinite(v)]
        if len(v) < MIN_POZO_PIX:
            v = todos
        X[:, i] = v[rng.integers(0, len(v), N_MC)]
    p2 = p_se_cola(*estadistico_lote(X)[:2])
    return p0, p1, p2


def escalera(disp, residuo, pozo_de, etiqueta):
    t = time.time()
    filas = []
    for j, (d, s, k) in enumerate(disp):
        p0, p1, p2 = modelos_cuadro(residuo(d, s), pozo_de(d, s), 1000 * d + s)
        filas.append((d, s, k, p0, p1, p2))
        if j % 20 == 0:
            print(f"  {etiqueta} {j + 1}/{len(disp)} {time.time() - t:.0f} s", flush=True)
    dias = sorted({d for d, *_ in filas})
    O = [sum(k in SE for dd, _, k, *_ in filas if dd == d) for d in dias]
    N = [sum(1 for dd, *_ in filas if dd == d) for d in dias]
    out = {"disparos": len(filas), "dias": len(dias), "cuota_obs": sum(O) / sum(N)}
    rng = np.random.default_rng(SEMILLA)
    for nombre, col in (("E0", 3), ("E1", 4), ("E2", 5)):
        E = [sum(f[col] for f in filas if f[0] == d) for d in dias]
        out[nombre] = sum(E) / sum(N)
        if nombre != "E0":
            x, lo, hi = bootstrap_exceso(O, N, E, rng)
            out[f"exceso_{nombre}"] = {"X": x, "IC95": [lo, hi], "rotulo": rotulo_exceso(x, lo, hi)}
    den = out["cuota_obs"] - out["E0"]
    out["fraccion_explicada"] = {"M1": (out["E1"] - out["E0"]) / den if den else None,
                                 "M2": (out["E2"] - out["E0"]) / den if den else None}
    out["por_cuadro"] = [{"dia": f"{T0 + timedelta(days=d):%Y-%m-%d}", "hora": M.hhmm(s), "k": k,
                          "p0": _r(p0), "p1": _r(p1), "p2": _r(p2)} for d, s, k, p0, p1, p2 in filas]
    return out


def _r(x):
    return None if (x is None or not np.isfinite(x)) else round(float(x), 4)


def prueba_viento(disp, nivel, rng):
    """M3: clases por día, Δ con nulo por permutación de días, piso y poder con el medio oráculo."""
    dias = sorted({d for d, *_ in disp})
    fila_dia = []
    for d in dias:
        fr = [(s, k) for dd, s, k in disp if dd == d]
        th = [viento(hora_sinoptica(d, s), nivel) for s, _ in fr]
        if any(not np.isfinite(a) for a, _ in th):
            fila_dia.append({"d": d, "clase": "sin_gfs"})
            continue
        tm, vm = media_circular([a for a, _ in th]), float(np.mean([v for _, v in th]))
        clase = "debil" if vm < V_MIN else ("SE" if en_se(tm) else "fuera")
        fila_dia.append({"d": d, "dia": f"{T0 + timedelta(days=d):%Y-%m-%d}", "n": len(fr),
                         "f_SE": float(np.mean([k in SE for _, k in fr])), "theta": round(tm, 1),
                         "v": round(vm, 1), "clase": clase, "theta_cuadros": [round(a, 1) for a, _ in th],
                         "k": [k for _, k in fr]})
    usa = [x for x in fila_dia if x["clase"] in ("SE", "fuera")]
    n_se = sum(x["clase"] == "SE" for x in usa)
    n_fu = len(usa) - n_se
    out = {"nivel_hPa": nivel, "dias": fila_dia, "n_SE": n_se, "n_fuera": n_fu,
           "n_debil": sum(x["clase"] == "debil" for x in fila_dia),
           "n_sin_gfs": sum(x["clase"] == "sin_gfs" for x in fila_dia)}
    if n_se < 1 or n_fu < 1:
        out.update({"decidible": False, "rotulo": "SIN PODER", "motivo": "una clase vacía"})
        return out
    f = [x["f_SE"] for x in usa]
    cl = [x["clase"] == "SE" for x in usa]
    delta, p, piso, modo = delta_permutacion(f, cl, rng)
    O_fu = sum(sum(k in SE for k in x["k"]) for x in usa if x["clase"] == "fuera")
    N_fu = sum(x["n"] for x in usa if x["clase"] == "fuera")
    O_se = sum(sum(k in SE for k in x["k"]) for x in usa if x["clase"] == "SE")
    N_se = sum(x["n"] for x in usa if x["clase"] == "SE")
    # poder: medio oráculo de sotavento
    ks = np.array([k for _, _, k in disp])
    dist_k = np.bincount(ks, minlength=12) / len(ks)
    rp = np.random.default_rng(SEMILLA)
    acierto = 0
    for _ in range(N_PODER):
        fo = []
        for x in usa:
            kk = [int(a // 30) % 12 if rp.random() < 0.5 else int(rp.choice(12, p=dist_k)) for a in x["theta_cuadros"]]
            fo.append(np.mean([k in SE for k in kk]))
        _, po, _, _ = delta_permutacion(fo, cl, rp, b_azar=B_PERM_PODER)
        acierto += po <= ALFA
    poder = acierto / N_PODER
    decid = n_se >= N_MIN_CLASE and n_fu >= N_MIN_CLASE and piso <= PISO_MAX and poder >= PODER_MIN
    cuota_fu = O_fu / N_fu
    if not decid:
        rot = "SIN PODER"
    elif p <= ALFA and delta >= DELTA_MIN:
        rot = "(b) SOSTIENE"
    elif p > ALFA and cuota_fu >= CUOTA_FUERA_MIN:
        rot = "(b) NO SOSTIENE"
    else:
        rot = "NO CONCLUYENTE"
    out.update({"delta": delta, "p": p, "piso": piso, "modo_nulo": modo, "poder_medio_oraculo": poder,
                "cuota_SE_dias_sotavento_SE": O_se / N_se, "cuota_SE_dias_sotavento_fuera": cuota_fu,
                "disparos_SE_y_fuera": [N_se, N_fu], "decidible": decid, "rotulo": rot})
    return out


def prueba_angular(disp, nivel, rng):
    """Secundaria: distancia entre la tajada que dispara y el sotavento, contra el viento de otro día a la misma hora."""
    dias = sorted({d for d, *_ in disp})
    pord = {d: [(s, k) for dd, s, k in disp if dd == d] for d in dias}

    def dist_media(asig):
        md = []
        for d in dias:
            th = [viento(hora_sinoptica(asig[d], s), nivel)[0] for s, _ in pord[d]]
            if not all(np.isfinite(th)):
                continue
            md.append(float(np.mean(dist_ang([30 * k + 15 for _, k in pord[d]], th))))
        return float(np.mean(md))

    obs = dist_media({d: d for d in dias})
    cnt = 0
    for _ in range(B_ANG):
        asig = {d: int(rng.choice([x for x in range(ND) if x != d])) for d in dias}
        cnt += dist_media(asig) <= obs + 1e-12
    return {"nivel_hPa": nivel, "distancia_media_obs": obs, "p": (1 + cnt) / (B_ANG + 1),
            "rotulo": "secundaria, no decide"}


def secundarias_m4(disp, rng):
    dias = sorted({d for d, *_ in disp})
    f = np.array([np.mean([k in SE for dd, _, k in disp if dd == d]) for d in dias])
    temprano = np.array([d <= 30 for d in dias])
    out = {}
    if temprano.any() and (~temprano).any():
        dobs = f[temprano].mean() - f[~temprano].mean()
        cnt = 0
        for _ in range(B_PERM):
            pm = rng.permutation(temprano)
            cnt += abs(f[pm].mean() - f[~pm].mean()) >= abs(dobs) - 1e-12
        out["fecha"] = {"dias_21sep_21oct": int(temprano.sum()), "dias_22oct_21nov": int((~temprano).sum()),
                        "f_SE_temprano": float(f[temprano].mean()), "f_SE_tarde": float(f[~temprano].mean()),
                        "p_bilateral": (1 + cnt) / (B_PERM + 1)}
    difs = []
    for d in dias:
        a = [k in SE for dd, s, k in disp if dd == d and s >= 72]
        b = [k in SE for dd, s, k in disp if dd == d and s < 72]
        if a and b:
            difs.append(np.mean(a) - np.mean(b))
    pos, neg = sum(x > 0 for x in difs), sum(x < 0 for x in difs)
    out["hora"] = {"dias_con_las_dos_mitades": len(difs), "dia_mas_SE": pos, "noche_mas_SE": neg,
                   "p_signos": float(stats.binomtest(pos, pos + neg).pvalue) if pos + neg else None,
                   "cuota_SE_12a24": _r(np.mean([k in SE for _, s, k in disp if s >= 72])),
                   "cuota_SE_00a12": _r(np.mean([k in SE for _, s, k in disp if s < 72])),
                   "n_12a24": sum(s >= 72 for _, s, _ in disp), "n_00a12": sum(s < 72 for _, s, _ in disp)}
    return out


def descripcion_tajadas(D):
    """Geometría y estadística por tajada sobre los cuadros evaluados de 2025 (no prueba nada)."""
    filas = [(d, s) for d in D.DIASR for s in range(144) if np.isfinite(D.SR[d, s])]
    X = np.array([D.mmR[d, s] - D.base(d)[s] for d, s in filas], np.float32)
    Sx, K, Q = estadistico_lote(X)
    rel = Q - np.nanmedian(Q, 1, keepdims=True)
    sd_pix = np.nanstd(X, 0)
    z = M.ZDEM[M.AP]
    npar = np.array([len(c) for c in M.CTRL_COTA])
    out = {"cuadros_evaluados": len(filas), "tajadas": []}
    for k in range(M.NSEC):
        m = M.SEC == k
        out["tajadas"].append({
            "k": k, "grados": f"{30 * k}-{30 * k + 30}", "pixeles": int(m.sum()),
            "cota_mediana_m": round(float(np.median(z[m]))), "cota_sd_m": round(float(z[m].std())),
            "controles_cota_mediana": int(np.median(npar[m])),
            "frac_valida": _r(np.isfinite(Q[:, k]).mean()),
            "pixeles_validos_media": _r(np.isfinite(X[:, m]).sum(1).mean()),
            "sd_residuo_pixel_mediana_K": _r(np.nanmedian(sd_pix[m])),
            "p5_Qk_menos_mediana_K": _r(np.nanpercentile(rel[:, k], 5)),
            "frac_argmin_todos_evaluados": _r((K == k).mean())})
    ok = np.isfinite(sd_pix)
    out["spearman_sd_vs_cota"] = _r(stats.spearmanr(sd_pix[ok], z[ok])[0])
    out["spearman_sd_vs_controles"] = _r(stats.spearmanr(sd_pix[ok], npar[ok])[0])
    return out


def medir():
    os.makedirs(RES, exist_ok=True)
    t = time.time()
    B.PCT_U = P_STAR
    D = S.Detector(ref="2025", con_blanco=False)
    disp = disparos_anio(D.SR, D.KR, D.DIASR, lambda d: D.umbral(d)[0])
    cuenta ={int(a): int(b) for a, b in zip(*np.unique([k for *_, k in disp], return_counts=True))}
    res = {"criterio": "criterio_2026-11-26.md (commit 8872a7a)", "reproduce": cuenta == REPRO, "tajadas_2025": cuenta}
    print(f"2025: {len(disp)} disparos, reproduce {res['reproduce']} ({time.time() - t:.0f} s)", flush=True)
    if not res["reproduce"]:
        res["veredicto"] = "INVÁLIDA"
        json.dump(res, open(os.path.join(RES, "s31d_resultado.json"), "w", encoding="utf-8"), ensure_ascii=False,
                  indent=1)
        return
    # M1 y M2
    res["M1_M2_2025"] = escalera(
        disp, lambda d, s: D.mmR[d, s] - D.base(d)[s],
        lambda d, s: residuos_pozo(D.mmR, D.GATER, D.base(d), D.DIASR, d, s), "2025")
    print(json.dumps({k: v for k, v in res["M1_M2_2025"].items() if k != "por_cuadro"}, ensure_ascii=False), flush=True)
    # M3 (espera a que termine la bajada de viento, hasta 2 h; lo que falte queda "sin_gfs")
    t_esp = time.time()
    while any(ruta_gfs(h) is None for h in horas_2025()) and time.time() - t_esp < 7200:
        print(f"  esperando viento: faltan {sum(ruta_gfs(h) is None for h in horas_2025())} horas", flush=True)
        time.sleep(60)
    res["horas_gfs_faltantes"] = [f"{h:%Y-%m-%d %H}" for h in horas_2025() if ruta_gfs(h) is None]
    rng = np.random.default_rng(SEMILLA)
    res["M3_700"] = prueba_viento(disp, NIVEL, rng)
    res["M3_500_sensibilidad"] = prueba_viento(disp, NIVEL_SENS, np.random.default_rng(SEMILLA))
    print(json.dumps({k: v for k, v in res["M3_700"].items() if k != "dias"}, ensure_ascii=False), flush=True)
    res["M3_angular_700"] = prueba_angular(disp, NIVEL, np.random.default_rng(SEMILLA))
    res["M3_angular_500"] = prueba_angular(disp, NIVEL_SENS, np.random.default_rng(SEMILLA))
    print(res["M3_angular_700"], res["M3_angular_500"], flush=True)
    # M4 y descripción
    res["M4"] = secundarias_m4(disp, np.random.default_rng(SEMILLA))
    res["descripcion_tajadas"] = descripcion_tajadas(D)
    # veredicto
    r1 = res["M1_M2_2025"]["exceso_E1"]["rotulo"]
    r2 = res["M1_M2_2025"]["exceso_E2"]["rotulo"]
    rb = res["M3_700"]["rotulo"]
    if r1 == "EXPLICA":
        ver = "MÉTODO"
    elif r1 == "NO EXPLICA" and r2 == "EXPLICA":
        ver = "RUIDO FIJO POR PÍXEL (terreno o pareo)"
    elif r1 == "NO EXPLICA" and r2 == "NO EXPLICA":
        ver = {"(b) SOSTIENE": "SOTAVENTO", "(b) NO SOSTIENE": "TERRENO COHERENTE O ALGO QUE NO SIGUE AL VIENTO"}.get(
            rb, "NO DECIDIBLE entre terreno y sotavento")
    else:
        ver = "NO DECIDIBLE"
    res["veredicto"] = ver
    json.dump(res, open(os.path.join(RES, "s31d_resultado.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("VEREDICTO:", ver, flush=True)
    # réplica 2024 (sólo M1 y M2)
    import s25b_medir as X24
    D24 = X24._detector_2024()
    acm24, m124 = np.load(X24._npy24("acm")), np.load(X24._npy24("m1"))
    FD24, mm24 = D._nubes(acm24, m124, D24.ESTAT)
    gate24 = FD24 <= B.G_MAX
    B0 = D.base(None)
    S24 = np.full(acm24.shape[:2], np.nan)
    K24 = np.full(acm24.shape[:2], -1, int)
    for d in range(X24.ND):
        for s in range(144):
            if gate24[d, s]:
                S24[d, s], K24[d, s], _ = M.estadistico(mm24[d, s] - B0[s])
    U0, _ = D.umbral(None)
    disp24 = disparos_anio(S24, K24, range(X24.ND), lambda d: U0)
    esc24 = escalera(disp24, lambda d, s: mm24[d, s] - B0[s],
                     lambda d, s: residuos_pozo(mm24, gate24, B0, range(X24.ND), d, s), "2024")
    esc24["rotulo"] = "réplica: las cuotas de 2024 ya se vieron (S25b); sólo repite la descomposición"
    esc24["tajadas_2024"] = {int(a): int(b) for a, b in zip(*np.unique([k for *_, k in disp24], return_counts=True))}
    res["replica_2024"] = esc24
    print(json.dumps({k: v for k, v in esc24.items() if k != "por_cuadro"}, ensure_ascii=False), flush=True)
    json.dump(res, open(os.path.join(RES, "s31d_resultado.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"listo en {time.time() - t:.0f} s", flush=True)


if __name__ == "__main__":
    a = sys.argv[1]
    if a == "pruebas":
        pruebas()
    elif a == "viento":
        viento_bajar(*(int(x) for x in sys.argv[2:4])) if len(sys.argv) > 3 else viento_bajar()
    elif a == "medir":
        medir()
