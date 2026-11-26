r"""F2 (S28b): el azar de S23a, S25a y S26a con el DÍA como bloque, no el cuadro.

Por qué: p25 (Poisson binomial) y pN (Fisher) suponen que cada cuadro P se alcanza por azar con independencia de los
demás. Pero los P vienen en episodios de pocos días (100 P en 10 días, 33 en el 14-11) y los disparos vienen en rachas:
un día de 2025 que dispara de tarde alcanza muchos cuadros seguidos, y un día de 2026 en que la zona dispara todo el día
también. Con cuadros independientes, un solo día "encendido" parece imposible por azar; con días como unidad, no.

Nulos (los dos conservan la estructura dentro del día y la hora de cada P):
- D25 (contra el azar de 2025, el de p25): a cada día de 2026 con P evaluados se le asigna un día de 2025 al azar; cada P
  (hora h) toma el "alcanzado" del cuadro evaluado de ese día de 2025 más cercano a h dentro de ±60 min (la ventana del
  azar por hora de los criterios), con la base y el umbral de 2025 sin ese día (el ensayo en seco tal cual). Si ese día
  no tiene cuadro evaluado a ±60 min, el P toma el de otro día de 2025 al azar que sí lo tenga.
- DN (contra los N de 2026, el de pN): igual, pero con los cuadros N evaluados de un día de 2026 al azar.
Estadístico: P alcanzados totales (el mismo de R). p = (1 + #{T_nulo >= T}) / (1 + NB), NB = 20.000, semilla 0.
Control: el p25 por cuadro recomputado desde estos arreglos tiene que dar el publicado (dentro de la tolerancia del
plan), y un placebo de población (horas de los P en días de 2026 sin P) dice cuánto cumple p25 sin VOLCAT.
Uso: python -I f2_bloques.py   (lee D:\goes_notas\s28\s28b\f2\cubos_f2.npz de f2_cubos.py)
"""
import json
import os
import sys

import numpy as np
from scipy import stats

sys.stdout.reconfigure(encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
OV = os.path.abspath(os.path.join(AQUI, "..", "..", ".."))
sys.path.insert(0, os.path.join(OV, "s23_fondo_2025", "scripts"))
import s23_medir as S  # noqa: E402

SAL = r"D:\goes_notas\s28\s28b\f2"
NB, W = 20000, 6
CONF = {"S23a": ("s23a", "a500", 0.05), "S23b_desarrollo": ("a500", "a500", 0.01),
        "S25a": ("z500", "z500", 0.01), "S26a_desarrollo": ("u475", "u475", 0.01)}


def cercano(ev, A, s):
    """alcanzado del cuadro evaluado más cercano a s (±W) en un día; NaN si no hay."""
    for k in range(W + 1):
        for x in ((s - k, s + k) if k else (s,)):
            if 0 <= x < 144 and ev[x]:
                return float(A[x])
    return np.nan


def tabla(ev, A):
    V = np.full(ev.shape, np.nan)
    for d in range(ev.shape[0]):
        if ev[d].any():
            for s in range(144):
                V[d, s] = cercano(ev[d], A[d], s)
    return V


def nulo(V, Pdias, rng):
    """Pdias: lista de arrays de horas de P por día de 2026. Devuelve NB totales."""
    dias = np.flatnonzero(np.isfinite(V).any(1))
    tot = np.zeros(NB)
    for sl in Pdias:
        dd = rng.choice(dias, NB)
        v = V[dd[:, None], sl[None, :]]                      # (NB, nP)
        miss = ~np.isfinite(v)
        while miss.any():                                    # relleno por P con otro día que tenga cuadro a ±60 min
            ii, jj = np.nonzero(miss)
            d2 = rng.choice(dias, len(ii))
            v[ii, jj] = V[d2, sl[jj]]
            miss = ~np.isfinite(v)
        tot += v.sum(1)
    return tot


def main():
    Z = np.load(os.path.join(SAL, "cubos_f2.npz"))
    CL = Z["CL"]
    out = {}
    rng = np.random.default_rng(0)
    for nom, (k26, k25, umb) in CONF.items():
        ev26, A26 = Z[f"ev26_{k26}"], Z[f"A26_{k26}"]
        ev25, A25 = Z[f"ev25_{k25}"], Z[f"A25_{k25}"]
        P = [(d, s) for d, s in zip(*np.nonzero((CL == "P") & ev26))]
        T = int(sum(A26[d, s] for d, s in P))
        # p25 por cuadro (el del criterio) recomputado
        sl25 = [s for d in range(62) for s in np.flatnonzero(ev25[d])]
        al25 = [A25[d, s] for d in range(62) for s in np.flatnonzero(ev25[d])]
        r25 = S.azar_por_hora(sl25, al25)
        p25 = S.poisson_binomial_cola([r25[s] for _, s in P], T)
        # pN por cuadro (Fisher contra N a ±60 min de algún P), como S25a y S26a
        psl = {s for _, s in P}
        Nc = [(d, s) for d, s in zip(*np.nonzero((CL == "N") & ev26))
              if any(min(abs(s - x) % 144, 144 - abs(s - x) % 144) <= W for x in psl)]
        nh = int(sum(A26[d, s] for d, s in Nc))
        pN = float(stats.fisher_exact([[T, len(P) - T], [nh, len(Nc) - nh]], alternative="greater")[1])
        Pdias = [np.array([s for dd, s in P if dd == d]) for d in sorted({d for d, _ in P})]
        V25 = tabla(ev25, A25)
        evN = ev26 & (CL == "N")
        VN = tabla(evN, A26)
        t25 = nulo(V25, Pdias, rng)
        tN = nulo(VN, Pdias, rng)
        pb25 = (1 + (t25 >= T).sum()) / (1 + NB)
        pbN = (1 + (tN >= T).sum()) / (1 + NB)
        por_dia = {str(d): [int(sum(A26[d, s] for dd, s in P if dd == d)), int(sum(1 for dd, _ in P if dd == d))]
                   for d in sorted({d for d, _ in P})}
        out[nom] = {"P_evaluados": len(P), "P_alcanzados": T, "dias_con_P": len(Pdias),
                    "p25_por_cuadro": p25, "pN_por_cuadro_fisher": pN, "N_cerca": [nh, len(Nc)],
                    "p25_bloque_dias_2025": float(pb25), "pN_bloque_dias_N_2026": float(pbN),
                    "nulo25_media_p95_p99": [float(t25.mean()), float(np.percentile(t25, 95)),
                                             float(np.percentile(t25, 99))],
                    "nuloN_media_p95_p99": [float(tN.mean()), float(np.percentile(tN, 95)),
                                            float(np.percentile(tN, 99))],
                    "umbral_p25_criterio": umb, "piso": 1 / (1 + NB), "por_dia_2026_idx": por_dia}
        print(nom, json.dumps({k: v for k, v in out[nom].items() if k != "por_dia_2026_idx"}), flush=True)
    # placebo de población (informativo): las horas de los P puestas en días de 2026 SIN P (con clase), con el
    # alcanzado del cuadro evaluado más cercano (todos los cuadros, no sólo N), contra el nulo D25. Si una fracción grande
    # de estos placebo da p <= 0,01, p25 no separa VOLCAT de "un día cualquiera de 2026" (pluma diaria o depósito).
    for nom, k in (("S25a", "z500"), ("S26a_desarrollo", "u475"), ("S23b_desarrollo", "a500")):
        ev26, A26 = Z[f"ev26_{k}"], Z[f"A26_{k}"]
        V25 = tabla(Z[f"ev25_{k}"], Z[f"A25_{k}"])
        V26 = tabla(ev26, A26)
        P = [(d, s) for d, s in zip(*np.nonzero((CL == "P") & ev26))]
        Pdias = [np.array([s for dd, s in P if dd == d]) for d in sorted({d for d, _ in P})]
        sinP = [d for d in range(CL.shape[0]) if (CL[d] != "").any() and not (CL[d] == "P").any()
                and np.isfinite(V26[d]).any()]
        rr = np.random.default_rng(2)
        t0 = nulo(V25, Pdias, np.random.default_rng(3))
        ev25, A25 = Z[f"ev25_{k}"], Z[f"A25_{k}"]
        r25 = S.azar_por_hora([s for d in range(62) for s in np.flatnonzero(ev25[d])],
                              [A25[d, s] for d in range(62) for s in np.flatnonzero(ev25[d])])
        qs = [r25[s] for sl in Pdias for s in sl]
        ps, Ts, pc = [], [], []
        for _ in range(500):
            dd = rr.choice(sinP, len(Pdias), replace=False)
            T = 0.0
            for d, sl in zip(dd, Pdias):
                v = V26[d, sl]
                v = np.where(np.isfinite(v), v, 0.0)          # sin cuadro evaluado a ±60 min: no alcanzado
                T += v.sum()
            Ts.append(T)
            pc.append(S.poisson_binomial_cola(qs, int(round(T))))
            ps.append(float((1 + (t0 >= T).sum()) / (1 + NB)))
        ps = np.array(ps)
        out[f"placebo_dias_2026_sin_P_{nom}"] = {"dias_sin_P_disponibles": len(sinP), "replicas": len(ps),
                                                 "T_placebo_mediana_p95": [float(np.median(Ts)),
                                                                           float(np.percentile(Ts, 95))],
                                                 "frac_p25bloque_le_0.01": float((ps <= 0.01).mean()),
                                                 "frac_p25bloque_le_0.05": float((ps <= 0.05).mean()),
                                                 "frac_p25_por_cuadro_le_0.01": float((np.array(pc) <= 0.01).mean()),
                                                 "frac_p25_por_cuadro_le_0.05": float((np.array(pc) <= 0.05).mean())}
        print("placebo", nom, out[f"placebo_dias_2026_sin_P_{nom}"], flush=True)
    json.dump(out, open(os.path.join(SAL, "bloques.json"), "w", encoding="utf-8"), indent=1)


if __name__ == "__main__":
    main()
