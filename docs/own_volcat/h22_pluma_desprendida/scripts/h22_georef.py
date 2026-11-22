r"""H22, comprobacion del instrumento (no mira pluma contra control): la grilla de cada archivo de evento se ubica
en la ventana L1b con x/y_image_feature_region_bounds. Si la ubicacion es exacta, (a) la lat/lon del archivo coincide
con la de la ventana y (b) la BT de 11 y 12 um del archivo coincide con la BT de C14 y C15 de la L1b del mismo scan
en todos los pixeles comunes, y deja de coincidir al correr 1 pixel. Tambien cuenta rellenos.

Escribe resultados/georef_por_cuadro.csv (numeros por cuadro, sin grillas). Uso: python -I h22_georef.py
"""
import csv
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import h22_comun as C  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")


def main():
    P = C.Pila()
    filas = []
    for c, f in C.eventos():
        e = C.leer_evento(f)
        m = C.dentro(e["wy"], e["wx"])
        wy, wx = e["wy"][m], e["wx"][m]
        hu = e["ei"] >= 0
        fila = dict(cuadro=c, tipo=e["tipo"], n_huella=int(hu.sum()), n_huella_en_ventana=int((hu & m).sum()),
                    en_pila=c in P.pos)
        dlat = np.abs(e["lat"][m] - C.LAT[wy, wx])
        dlon = np.abs(e["lon"][m] - C.LON[wy, wx])
        fila.update(n_comun=int(m.sum()), max_dlat=round(float(np.nanmax(dlat)), 5),
                    max_dlon=round(float(np.nanmax(dlon)), 5))
        if c in P.pos:
            i = P.pos[c]
            for nom, ev, l1 in (("11", e["bt11"], P.b14[i]), ("12", e["bt12"], P.b15[i])):
                a = ev[m]
                ok = np.isfinite(a)
                res = {}
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        yy, xx = wy + dy, wx + dx
                        g = ok & C.dentro(yy, xx)
                        b = l1[np.clip(yy, 0, C.LAT.shape[0] - 1), np.clip(xx, 0, C.LAT.shape[1] - 1)]
                        g &= np.isfinite(b)
                        res[(dy, dx)] = float(np.median(np.abs(a[g] - b[g])))
                mejor = min(res, key=res.get)
                otros = min(v for k, v in res.items() if k != (0, 0))
                b0 = l1[wy, wx]
                g = ok & np.isfinite(b0)
                fila.update({f"mad{nom}_0": round(res[(0, 0)], 4), f"mad{nom}_mejor_corrido": round(otros, 3),
                             f"mejor{nom}": f"{mejor[0]},{mejor[1]}",
                             f"max_abs{nom}": round(float(np.max(np.abs(a[g] - b0[g]))), 3),
                             f"n_relleno_ev{nom}": int((~ok).sum()), f"n_nan_l1b{nom}": int((~np.isfinite(b0)).sum())})
            hw = hu & m
            fila["huella_l1b_finita"] = int(np.isfinite(P.b14[i][e["wy"][hw], e["wx"][hw]]).sum())
        filas.append(fila)
    cols = sorted({k for r in filas for k in r}, key=lambda k: (k != "cuadro", k))
    os.makedirs(C.RES, exist_ok=True)
    with open(os.path.join(C.RES, "georef_por_cuadro.csv"), "w", newline="", encoding="utf-8") as fo:
        w = csv.DictWriter(fo, cols)
        w.writeheader()
        w.writerows(filas)
    con = [r for r in filas if r["en_pila"]]
    print("cuadros de evento", len(filas), "con L1b en la pila", len(con))
    print("sin L1b:", [r["cuadro"] for r in filas if not r["en_pila"]])
    print("huella fuera de la ventana:", sum(r["n_huella"] - r["n_huella_en_ventana"] for r in filas))
    print("max |dlat|, |dlon| (grados):", max(r["max_dlat"] for r in filas), max(r["max_dlon"] for r in filas))
    for nom in ("11", "12"):
        print(f"BT{nom}: mediana |evento - L1b| sin correr: max entre cuadros {max(r[f'mad{nom}_0'] for r in con):.4f} K;",
              f"mejor alternativa corrida 1 px: min entre cuadros {min(r[f'mad{nom}_mejor_corrido'] for r in con):.3f} K;",
              "cuadros donde gana (0,0):", sum(r[f"mejor{nom}"] == "0,0" for r in con), "de", len(con),
              f"; max |dif| {max(r[f'max_abs{nom}'] for r in con):.3f} K",
              "; rellenos evento", sum(r[f"n_relleno_ev{nom}"] for r in con), "NaN L1b", sum(r[f"n_nan_l1b{nom}"] for r in con))
    print("pixeles de huella con L1b finita:", sum(r.get("huella_l1b_finita", 0) for r in con), "de",
          sum(r["n_huella_en_ventana"] for r in con))


if __name__ == "__main__":
    main()
