r"""H16 §5 del criterio: probabilidad de OBJETO de VOLCAT (IR, validada en Mauna Loa) en la huella de Chillán.

Reutiliza sin editarla la cadena de la etapa 3 (PR 79): escena L1b, cielo despejado por cota, nube negra en el punto
frío, εtot, β(12/11) total con corrección de vapor, β(7,3/11), β(8,5/11) y β opaco (e3_cadena.py). Agrega lo que la
tabla de objeto pide y la etapa 3 no guardaba: β(8,5/11) opaco, desviación de BT11 en 3 × 3 y área por píxel.

Píxeles: huella y controles salen de E3_DIR\e3_pixeles_completo.csv (pareo de la etapa 3, BT11 ± 0,5 K, mismo
cuadro). Objeto huella = todos los píxeles de huella del cuadro. Control k = el k-ésimo control de cada píxel.
Bandas: S0 (decide), S1 y S2 (informan). Escribe resultados/chillan_objetos.csv (sin posiciones) y
resultados/chillan_tablas.csv (aporte por tabla en la huella).
Uso: python -I h16_chillan.py
"""
import csv
import os
import sys
from datetime import datetime

import numpy as np
import pandas as pd
from numpy.lib.stride_tricks import sliding_window_view

sys.stdout.reconfigure(encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
E3S = os.path.join(os.path.dirname(os.path.dirname(AQUI)), "lut_h15", "etapa3_chillan", "scripts")
sys.path.insert(0, E3S)
sys.path.insert(0, AQUI)
import e3_cadena as E  # noqa: E402
import h16_objeto as O  # noqa: E402

RES = os.path.join(os.path.dirname(AQUI), "resultados")
VAR = dict(sdregla="tal", desempate="menor", b73="finito")    # elegida en Mauna Loa (validacion_mauna_loa.json)
NCTRL = 5


def area_pixel():
    """km² por píxel desde la grilla lat/lon de la ventana (diferencias centradas, esfera de 6.371 km)."""
    R = 6371.0
    lat, lon = np.radians(E.C.LAT), np.radians(E.C.LON)
    dlat_y, dlat_x = np.gradient(lat)
    dlon_y, dlon_x = np.gradient(lon)
    c = np.cos(lat)
    ax, ay = R * dlat_x, R * c * dlon_x
    bx, by = R * dlat_y, R * c * dlon_y
    return np.abs(ax * by - ay * bx)


def sdev3(bt):
    return np.nanstd(sliding_window_view(np.pad(bt, 1, mode="edge"), (3, 3)), axis=(2, 3))


def main():
    d = pd.read_csv(os.path.join(E.K.E3DIR, "e3_pixeles_completo.csv"))
    d = d[d.banda == "S0"]
    AREA = area_pixel()
    ev = E.eventos(sorted(d.cuadro.unique()))
    filas, aportes = [], []
    for c, g in d.groupby("cuadro", sort=True):
        dt = datetime.strptime(c, "%Y%m%d_%H%M")
        rad, bt, co = E.escena(dt)
        px = E.a_pixeles(E.nodos_t(dt))
        f0 = E.campos(rad, bt, co, px, 0.0)
        espesa = np.isfinite(f0["eps"]) & (f0["eps"] >= 0.5)
        dth = E.ndimage.distance_transform_edt(~espesa) if espesa.any() else np.full(E.ZDEM.shape, np.inf)
        d2 = np.select([dth < u for u, _ in E.S2_TRAMOS], [v for _, v in E.S2_TRAMOS])
        sd = sdev3(bt[14])
        # objetos: huella y k-ésimo control (orden del CSV = orden del pareo)
        g = g.reset_index(drop=True)
        miembros = {"h": []} | {f"c{k}": [] for k in range(NCTRL)}
        for _, gh in g.groupby("id_huella", sort=False):
            h = gh[gh.rol == "h"]
            miembros["h"].append((int(h.fila.iloc[0]), int(h.col.iloc[0])))
            for k, (_, r) in enumerate(gh[gh.rol == "c"].iterrows()):
                miembros[f"c{k}"].append((int(r.fila), int(r.col)))
        for banda, delta in (("S0", 0.0), ("S1", -0.86), ("S2", d2)):
            f = f0 if banda == "S0" else E.campos(rad, bt, co, px, delta)
            for rol, mm in miembros.items():
                if not mm:
                    continue
                ys = np.array([m[0] for m in mm]); xs = np.array([m[1] for m in mm])
                bo = np.array([E.beta_op(rad, f, px, y, x) for y, x in zip(ys, xs)])
                pxo = {"eps": f["eps"][ys, xs], "b": f["b_tot"][ys, xs], "bop": bo[:, 0], "b85": f["b85"][ys, xs],
                       "b85op": bo[:, 1], "b73": f["b73"][ys, xs], "sd": sd[ys, xs]}
                la, lc, det = O.termino(pxo, AREA[ys, xs], detalle=True, **VAR)
                # sensibilidad: desviación de BT11 en bin 0 (el 14 % de Mauna Loa que no reproducimos)
                px0 = dict(pxo); px0["sd"] = np.zeros(len(ys))
                la0, lc0 = O.termino(px0, AREA[ys, xs], **VAR)
                filas.append(dict(cuadro=c, evento=ev[c], banda=banda, rol=rol, n_px=len(ys),
                                  area_km2=round(float(AREA[ys, xs].sum()), 1),
                                  eps_med=round(float(np.nanmedian(pxo["eps"])), 4),
                                  b_med=round(float(np.nanmedian(pxo["b"])), 4),
                                  l10_Tceniza=round(la, 4), l10_Tnube=round(lc, 4), P_obj=float(O.prob(la, lc)),
                                  P_obj_sd0=float(O.prob(la0, lc0))))
                if banda == "S0":
                    for r in det:
                        aportes.append(dict(cuadro=c, rol=rol, **r))
        print(c, "ev", ev[c], "huella", len(miembros["h"]),
              "P_h S0 %.3g" % [x for x in filas if x["cuadro"] == c and x["rol"] == "h" and x["banda"] == "S0"][0]["P_obj"],
              flush=True)
    os.makedirs(RES, exist_ok=True)
    for nombre, datos in (("chillan_objetos.csv", filas), ("chillan_tablas.csv", aportes)):
        with open(os.path.join(RES, nombre), "w", newline="", encoding="utf-8") as fo:
            w = csv.DictWriter(fo, fieldnames=list(datos[0]))
            w.writeheader(); w.writerows(datos)


if __name__ == "__main__":
    main()
