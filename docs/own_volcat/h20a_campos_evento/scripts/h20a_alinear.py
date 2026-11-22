"""H20a, paso previo: prueba de alineacion entre el recorte de cada archivo de evento y la grilla del L2,
y control positivo (BT de 11 um del evento contra la BT del canal 14 del L1), con su nulo de corrimiento.
No compara ningun campo de las hipotesis.

Uso: python -I h20a_alinear.py    -> resultados/alineacion.csv y resumen por pantalla
"""
import os
import sys
import csv
import numpy as np
import netCDF4 as nc
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from h20a_comun import (eventos_fuego, granulos_fuego, cargar_l2, ventana, recorte, acuerdo, arr, RES)

sys.stdout.reconfigure(encoding="utf-8")
os.makedirs(RES, exist_ok=True)
DESP = [(-1, 0), (1, 0), (0, -1), (0, 1)]


def main():
    filas = []
    casos = [("fuego_vcb", h, f) for h, f in eventos_fuego("342090")]
    casos += [("san_cristobal", h, f) for h, f in eventos_fuego("344020")]
    casos += [("granulo", h, f) for h, f in granulos_fuego()]
    for tipo, h, f in casos:
        ds = nc.Dataset(f)
        L = cargar_l2(h)
        v = ventana(ds, L["L2__pixel_latitude"].astype("f8"), L["L2__pixel_longitude"].astype("f8"))
        ny, nx = ds["latitude"].shape
        fila = {"tipo": tipo, "hora": h, "ny": ny, "nx": nx}
        for k in ("x_image_processing_bounds", "y_image_processing_bounds",
                  "x_image_feature_region_bounds", "y_image_feature_region_bounds"):
            if k in ds.variables:
                fila[k] = "%d-%d" % tuple(int(q) for q in ds[k][:])
        if v is None:
            fila["estado"] = "sin_latlon"
            filas.append(fila)
            ds.close()
            continue
        f0, c0, dlat, dlon, n = v
        fila.update({"fila0": f0, "col0": c0, "max_dlat": dlat, "max_dlon": dlon, "n_latlon": n})
        fila["alineado"] = int(n > 0 and dlat <= 1e-4 and dlon <= 1e-4)
        if tipo != "granulo" and fila["alineado"]:
            bt = arr(ds, "brightness_temperature_11micron")
            paso = float(getattr(ds["brightness_temperature_11micron"], "scale_factor", 0.01))
            b14 = L["L1__channel_14_brightness_temperature"].astype("f8")
            n1, a1 = acuerdo(bt, recorte(b14, f0, c0, ny, nx), paso * 1.01)
            nul = max(acuerdo(bt, recorte(b14, f0, c0, ny, nx, df, dc), paso * 1.01)[1] for df, dc in DESP)
            fila.update({"bt11_paso": paso, "bt11_n": n1, "bt11_acuerdo": round(a1, 5),
                         "bt11_nulo_corrido": round(nul, 5)})
        filas.append(fila)
        ds.close()
    cols = []
    for r in filas:
        for k in r:
            if k not in cols:
                cols.append(k)
    with open(os.path.join(RES, "alineacion.csv"), "w", newline="", encoding="utf-8") as fo:
        w = csv.DictWriter(fo, fieldnames=cols)
        w.writeheader()
        w.writerows(filas)
    for tipo in ("fuego_vcb", "san_cristobal", "granulo"):
        rs = [r for r in filas if r["tipo"] == tipo]
        al = [r for r in rs if r.get("alineado")]
        print("%s: %d archivos, alineados %d" % (tipo, len(rs), len(al)))
        if al:
            print("  max|dlat| %.2e  max|dlon| %.2e  ventanas (fila0,col0,ny,nx): %s" % (
                max(r["max_dlat"] for r in al), max(r["max_dlon"] for r in al),
                sorted(set((r["fila0"], r["col0"], r["ny"], r["nx"]) for r in al))[:6]))
            print("  bounds x/y proc:", sorted(set((r.get("x_image_processing_bounds"),
                                                     r.get("y_image_processing_bounds")) for r in rs))[:4])
            print("  bounds x/y region:", sorted(set((r.get("x_image_feature_region_bounds"),
                                                       r.get("y_image_feature_region_bounds")) for r in rs))[:4])
            if tipo != "granulo":
                print("  BT11 evento vs canal 14 L1: acuerdo min %.4f, nulo corrido max %.4f, n min %d" % (
                    min(r["bt11_acuerdo"] for r in al), max(r["bt11_nulo_corrido"] for r in al),
                    min(r["bt11_n"] for r in al)))
        for r in rs:
            if not r.get("alineado"):
                print("  NO ALINEADO:", r)


if __name__ == "__main__":
    main()
