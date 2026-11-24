r"""S21b prueba 2, controles POST HOC (escritos despues de ver SIN SENAL y poder 0,02 a 0,05; no cambian el veredicto).

Por que: el 28-10 cambia MENOS entre cuadros que las tardes de control (p 0,72 a 0,98 en los tres pulsos), y la franja
del 25-10 pintada encima casi nunca supera al nulo. Dos preguntas:
 (a) ¿el nulo es ruidoso por nubes de cumbre que la regla E1 no ve? E1 mira el terreno bajo (10 a 30 km, cota menor
     que 1.300 m); un cumulo sobre la cordillera pasa. Se mide en cada cuadro del nulo la fraccion del anillo de
     Chillan (1 a 10 km) con rho05 > 0,30 (nube de agua; la nieve esta bajo 0,15 a 1,6 um) y se compara T con y sin
     esos pares;
 (b) nulo del mismo dia: T de todos los pares de cuadros del 28-10 de 16:00 a 22:30 con el mismo salto que cada pulso,
     y el rango de los pares del pulso entre ellos (lo que S19 pidio literalmente: "rasgo en los cuadros del pulso y
     ausente en los previos"). VOLCAT marco casi toda esa tarde, asi que si la pluma es continua este nulo la contiene.
     Mismo calculo en Antuco como referencia.
Uso: python -I s21b_posthoc2.py  -> ../resultados/posthoc2.json, posthoc2.log
"""
import json
import os
import sys
from datetime import timedelta

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import s21b_prueba2 as P2  # noqa: E402

LOG = []


def log(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    LOG.append(s)


def nube(t):
    anillo = P2.sectores("C05", "chillan")[0]
    return float(np.nanmean(P2.rho(t)["C05"][anillo] > 0.30))


def main():
    out = {"a_nubes_nulo": {}, "b_nulo_mismo_dia": {}}
    log("== (a) nubes de agua en el anillo de Chillan en los pares nulos (rho05 > 0,30)")
    for pid, ini, hr, hp, _ in P2.PULSOS:
        R, P = P2.dt(P2.DIA, hr), P2.dt(P2.DIA, hp)
        vent = 60
        for vent in (60, 90, 120):
            nul = P2.pares_nulos(R, P, vent)
            if len(nul) >= 39:
                break
        fn = np.array([max(nube(F), nube(G)) for F, G in nul])
        fila = {"nube_evento": [round(nube(R), 3), round(nube(P), 3)], "n": len(nul),
                "pares_con_nube_mas_1pct": int(np.sum(fn > 0.01))}
        for b in P2.DECIDEN:
            T0 = P2.T_de(P2.rho(P)[b] - P2.rho(R)[b], b, "chillan")[0]
            Tn = np.array([P2.T_de(P2.rho(G)[b] - P2.rho(F)[b], b, "chillan")[0] for F, G in nul])
            lim = Tn[fn <= 0.01]
            fila[b] = {"T": round(T0, 4), "p_todos": round(float((1 + np.sum(Tn >= T0)) / (1 + len(Tn))), 3),
                       "T_nulo_mediana_con_nube": round(float(np.median(Tn[fn > 0.01])), 4) if np.any(fn > 0.01) else None,
                       "T_nulo_mediana_sin_nube": round(float(np.median(lim)), 4) if len(lim) else None,
                       "p_sin_nube": round(float((1 + np.sum(lim >= T0)) / (1 + len(lim))), 3), "n_sin_nube": int(len(lim))}
        out["a_nubes_nulo"][pid] = fila
        log(f"  {pid}: {json.dumps(fila, ensure_ascii=False)}")

    log("== (b) nulo del mismo dia (28-10, 16:00 a 22:30): rango del par del pulso entre todos los pares con el mismo salto")
    t0, t1 = P2.dt(P2.DIA, "16:00"), P2.dt(P2.DIA, "22:30")
    for pid, ini, hr, hp, _ in P2.PULSOS:
        R, P = P2.dt(P2.DIA, hr), P2.dt(P2.DIA, hp)
        d = P - R
        fila = {}
        for sitio in ("chillan", "antuco"):
            for b in P2.DECIDEN:
                vals = []
                F = t0
                while F + d <= t1:
                    if P2.rho(F) is not None and P2.rho(F + d) is not None and P2.con_luz(F) and P2.con_luz(F + d):
                        vals.append((F.strftime("%H:%M"), P2.T_de(P2.rho(F + d)[b] - P2.rho(F)[b], b, sitio)))
                    F += timedelta(minutes=10)
                T0 = dict(vals)[hr][0]
                Ts = np.array([v[0] for _, v in vals])
                rango = int(np.sum(Ts >= T0))
                fila[f"{sitio}_{b}"] = {"T": round(T0, 4), "rango_desde_arriba": rango, "pares": len(vals),
                                        "mediana": round(float(np.median(Ts)), 4), "max": round(float(Ts.max()), 4),
                                        "par_max": max(vals, key=lambda v: v[1][0])[0]}
        # poder contra el nulo del mismo dia: la franja del 25-10 pintada en el segundo cuadro de cada par del dia
        # (8 direcciones), acierto si supera el percentil 95 de los pares sin pintar en C02 o en C05
        acierto, acierto_m = [], []
        p95 = {}
        pares = []
        F = t0
        while F + d <= t1:
            if P2.rho(F) is not None and P2.rho(F + d) is not None and P2.con_luz(F) and P2.con_luz(F + d):
                pares.append((F, F + d))
            F += timedelta(minutes=10)
        for b in P2.DECIDEN:
            p95[b] = np.percentile([P2.T_de(P2.rho(G)[b] - P2.rho(F)[b], b, "chillan")[0] for F, G in pares], 95)
        for F, G in pares:
            for az in range(0, 360, 45):
                for fac, lista in ((1.0, acierto), (0.5, acierto_m)):
                    ok = False
                    for b in P2.DECIDEN:
                        Bg = P2.rho(G)[b]
                        Gi = Bg + fac * P2.C.esperado(P2.franja(b, az), Bg, b)
                        ok |= P2.T_de(Gi - P2.rho(F)[b], b, "chillan")[0] > p95[b]
                    lista.append(ok)
        fila["poder_nulo_mismo_dia"] = round(float(np.mean(acierto)), 3)
        fila["poder_nulo_mismo_dia_mitad"] = round(float(np.mean(acierto_m)), 3)
        log(f"  {pid}: poder contra el nulo del mismo dia (p95): {fila['poder_nulo_mismo_dia']}, "
            f"mitad {fila['poder_nulo_mismo_dia_mitad']}")
        out["b_nulo_mismo_dia"][pid] = fila
        log(f"  {pid}: " + "; ".join(f"{k}: T {v['T']:.4f}, puesto {v['rango_desde_arriba']} de {v['pares']} "
                                     f"(mediana {v['mediana']:.4f}, max {v['max']:.4f} en {v['par_max']})"
                                     for k, v in fila.items() if isinstance(v, dict)))
    res = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "resultados")
    json.dump(out, open(os.path.join(res, "posthoc2.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1)
    open(os.path.join(res, "posthoc2.log"), "w", encoding="utf8").write("\n".join(LOG) + "\n")


if __name__ == "__main__":
    main()
