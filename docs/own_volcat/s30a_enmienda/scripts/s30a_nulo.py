r"""S30a: el nulo por días de la enmienda (enmienda_2026-11-26.md §2). Lo usan la calibración (s30a_calibrar.py) y la
medida (s30a_confirmar.py), así que la regla que se calibra es, línea por línea, la que se mide.

Por qué por días: los disparos de cada regla vienen en rachas dentro del día (S28b, V201: varianza del conteo diario 16 a
30 veces la del Poisson binomial). La unidad que se repite es el día, no el cuadro de 10 minutos.

Estadístico: R = P evaluados alcanzados / P evaluados de los días nuevos (misma `alcanzado`, misma compuerta, misma regla
de cada confirmación).
Nulo: las horas de TODOS los P de cada día nuevo con P (evaluados o no) se colocan, sin moverlas, sobre días distintos
de un fondo (2025;
2024 y 2026 sin VOLCAT como fondos aparte), una k-tupla ordenada de días distintos por colocación, y en cada colocación
se mide R con los disparos de ese fondo. Sólo cuentan las colocaciones decidibles (al menos MIN_P_EVAL P evaluados y de
al menos 2 días, el mismo mínimo del criterio). Con todas las horas P (y no sólo las evaluadas) el día observado es
una colocación más del nulo: si los días son intercambiables, p_día es válido por construcción. p_día = (1 + colocaciones con R >= R observado) / (1 + colocaciones
válidas). Con k <= 3 se enumeran todas; con k >= 4, N_MC colocaciones al azar (semilla fija).
"""
import numpy as np

MIN_P_EVAL, MIN_DIAS = 10, 2
N_MC, SEMILLA = 200_000, 20261126
W_MH = 18                                   # +-3 h para el pN estratificado (enmienda §4)


def alcanzado_dia(F, ev):
    """Alcanzado por cuadro de un día con la regla de s22b_medir.alcanzado (el cuadro, el anterior o el siguiente)."""
    F = np.asarray(F, bool)
    ev = np.asarray(ev, bool)
    v = F.copy()
    v[1:] |= F[:-1]
    v[:-1] |= F[1:]
    return ev & v


def tabla_fondo(mascaras, EV, AL):
    """Para cada máscara de horas (k, 144) y cada día del fondo (nd, 144): evaluados y alcanzados (k, nd)."""
    Mk = np.asarray(mascaras, float)
    e = Mk @ np.asarray(EV, float).T
    a = Mk @ (np.asarray(EV, bool) & np.asarray(AL, bool)).astype(float).T
    return e.astype(int), a.astype(int)


def _tuplas(nd_pool, k, rng):
    if k == 2:
        i, j = np.meshgrid(np.arange(nd_pool), np.arange(nd_pool), indexing="ij")
        m = i != j
        return np.stack([i[m], j[m]], 1)
    if k == 3:
        g = np.stack(np.meshgrid(*[np.arange(nd_pool)] * 3, indexing="ij"), -1).reshape(-1, 3)
        m = (g[:, 0] != g[:, 1]) & (g[:, 0] != g[:, 2]) & (g[:, 1] != g[:, 2])
        return g[m]
    out = np.array([rng.choice(nd_pool, k, replace=False) for _ in range(N_MC)])
    return out


def p_dia(e_obs, a_obs, e_fondo, a_fondo, pool):
    """p_día de un caso. e_obs, a_obs: (k,) evaluados y alcanzados de cada día nuevo con P evaluado.
    e_fondo, a_fondo: (k, nd) de tabla_fondo con las máscaras de esos mismos días. pool: índices de días del fondo que se
    pueden usar. Devuelve (p, R_obs, colocaciones válidas, colocaciones con R >= R_obs, cuántas posibles)."""
    e_obs = np.asarray(e_obs)
    a_obs = np.asarray(a_obs)
    k = len(e_obs)
    R = a_obs.sum() / e_obs.sum()
    pool = np.asarray(pool)
    rng = np.random.default_rng(SEMILLA)
    T = pool[_tuplas(len(pool), k, rng)]                     # (n, k) días del fondo
    E = e_fondo[np.arange(k)[None, :], T]                    # (n, k)
    A = a_fondo[np.arange(k)[None, :], T]
    Et, At = E.sum(1), A.sum(1)
    valido = (Et >= MIN_P_EVAL) & ((E > 0).sum(1) >= MIN_DIAS)
    ge = valido & (At >= R * Et - 1e-12)
    nv, ng = int(valido.sum()), int(ge.sum())
    return (1 + ng) / (1 + nv), float(R), nv, ng, len(T)


def decidible(e_obs):
    e_obs = np.asarray(e_obs)
    return int(e_obs.sum()) >= MIN_P_EVAL and int((e_obs > 0).sum()) >= MIN_DIAS


def veredicto(e_obs, a_obs, p25, nv25, alfa, r_min):
    """Rótulo de la enmienda (§3), en orden. INVÁLIDA la decide el envoltorio antes de llegar aquí."""
    if not decidible(e_obs):
        return "NO DECIDIBLE"
    if 1.0 / (1 + nv25) > alfa:
        return "NO DECIDIBLE (el nulo no tiene resolución)"
    R = np.sum(a_obs) / np.sum(e_obs)
    if p25 <= alfa and R >= r_min:
        return "CONFIRMA"
    if p25 <= alfa:
        return "PARCIAL"
    return "NO CONFIRMA"


def mantel_haenszel(tablas):
    """pN estratificado por día (informativo): lista de (Pa, Pn, Na, Nn) por día, P alcanzados / no y N alcanzados / no
    (N del mismo día a <= 3 h de un P evaluado). Devuelve razón de odds común de Mantel-Haenszel y p unilateral (P más
    alcanzado que N) por la aproximación normal de Cochran-Mantel-Haenszel, sin corrección de continuidad."""
    from scipy import stats
    num = den = s_dif = s_var = 0.0
    n_estratos = 0
    for a, b, c, d in tablas:
        n = a + b + c + d
        if n < 2 or (a + b) == 0 or (c + d) == 0:
            continue
        n_estratos += 1
        num += a * d / n
        den += b * c / n
        m1, n1, m0 = a + c, a + b, b + d
        s_dif += a - n1 * m1 / n
        s_var += n1 * (c + d) * m1 * m0 / (n * n * (n - 1)) if n > 1 else 0.0
    orr = num / den if den > 0 else (np.inf if num > 0 else np.nan)
    p = float(stats.norm.sf(s_dif / np.sqrt(s_var))) if s_var > 0 else None
    return {"razon_odds_MH": None if not np.isfinite(orr) else float(orr), "p_unilateral": p, "estratos": n_estratos}


def tablas_mh(Pm, EV, AL, CLN):
    """Tablas por día para mantel_haenszel. Pm, EV, AL, CLN: (nd, 144) bool (P, evaluado, alcanzado, N de VOLCAT)."""
    out = []
    for d in range(len(Pm)):
        pe = Pm[d] & EV[d]
        if not pe.any():
            continue
        cerca = np.zeros(144, bool)
        for s in np.flatnonzero(pe):
            for x in range(-W_MH, W_MH + 1):
                if 0 <= s + x < 144:
                    cerca[s + x] = True
        ne = CLN[d] & EV[d] & cerca
        out.append((int((pe & AL[d]).sum()), int((pe & ~AL[d]).sum()), int((ne & AL[d]).sum()),
                    int((ne & ~AL[d]).sum())))
    return out


def pruebas():
    # alcanzado_dia contra la definición de s22b_medir.alcanzado
    F = np.zeros(144, bool)
    ev = np.zeros(144, bool)
    F[[0, 50, 143]] = True
    ev[[0, 1, 49, 51, 52, 142, 143]] = True
    esp = np.array([bool(ev[s] and F[max(0, s - 1):min(144, s + 2)].any()) for s in range(144)])
    assert np.array_equal(alcanzado_dia(F, ev), esp)
    # p_día: dos días nuevos, fondo de 5 días; un solo par de días del fondo iguala R
    e_obs, a_obs = np.array([6, 6]), np.array([6, 6])
    e_f = np.full((2, 5), 6)
    a_f = np.zeros((2, 5), int)
    a_f[:, 2] = 6
    p, R, nv, ng, n = p_dia(e_obs, a_obs, e_f, a_f, np.arange(5))
    assert n == 20 and nv == 20 and ng == 0 and abs(p - 1 / 21) < 1e-12 and R == 1.0, (p, nv, ng, n)
    a_f[0, 2] = 6
    a_f[1, 3] = 6
    p, R, nv, ng, n = p_dia(e_obs, a_obs, e_f, a_f, np.arange(5))
    assert ng == 1 and abs(p - 2 / 21) < 1e-12        # (2, 3) es la única colocación con R = 1
    # decidibilidad: 12 P de un solo día no decide
    assert not decidible([12, 0]) and decidible([5, 5]) and not decidible([4, 5])
    e_f[0, :] = 0
    p, R, nv, ng, n = p_dia(e_obs, a_obs, e_f, a_f, np.arange(5))
    assert nv == 0 and p == 1.0
    assert veredicto([6, 6], [6, 6], 1.0, 0, 0.01, 0.4).startswith("NO DECIDIBLE (el nulo")
    assert veredicto([6, 6], [6, 6], 0.001, 2000, 0.01, 0.4) == "CONFIRMA"
    assert veredicto([6, 6], [2, 2], 0.001, 2000, 0.01, 0.4) == "PARCIAL"
    assert veredicto([6, 6], [6, 6], 0.02, 2000, 0.01, 0.4) == "NO CONFIRMA"
    # k = 3 enumera 5*4*3 tuplas
    p, R, nv, ng, n = p_dia([4, 4, 4], [0, 0, 0], np.full((3, 5), 4), np.zeros((3, 5), int), np.arange(5))
    assert n == 60 and nv == 60 and ng == 60 and p == 1.0
    # Mantel-Haenszel: P todos alcanzados, N ninguno, en dos días: p chico
    r = mantel_haenszel([(5, 0, 0, 5), (5, 0, 0, 5)])
    assert r["p_unilateral"] < 0.001 and r["estratos"] == 2
    print("pruebas de s30a_nulo OK")


if __name__ == "__main__":
    pruebas()
