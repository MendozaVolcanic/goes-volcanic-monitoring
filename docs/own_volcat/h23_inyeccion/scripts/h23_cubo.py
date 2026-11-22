r"""H23: arma un cubo por bloque (tiempo, fila, columna) con la radiancia de C14 y C15 desde los npz bajados, y
hace las comprobaciones de instrumento I1 a I3 del criterio (cobertura, mismo scan en las dos bandas, rango
fisico y cuadros no congelados). Si alguna falla, sale con codigo 1 y no deja cubo.

Salida: H23_DIR\cubo_<bloque>.npz (rad14, rad15 float32 con NaN donde no hay cuadro; co14, co15; t0) y
resultados\instrumento_<bloque>.json. Uso: python -I h23_cubo.py oct|nov
"""
import json
import os
import sys
from datetime import timedelta

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import h23_comun as K  # noqa: E402

RES = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "resultados")


def main(nombre):
    bloque = {"oct": K.BLOQUE_OCT, "nov": K.BLOQUE_NOV}[nombre]
    dias = list(K.dias(bloque))
    nt = len(dias) * 144
    rad = {b: np.full((nt, K.NY, K.NX), np.nan, "float32") for b in (14, 15)}
    co = {14: [], 15: []}
    presentes, scan_distinto, relleno = 0, 0, 0
    for i in range(nt):
        dt = dias[0] + timedelta(minutes=10 * i)
        f = os.path.join(K.L1B, K.clave(dt) + ".npz")
        if not os.path.exists(f):
            continue
        with np.load(f) as z:
            k14, k15 = str(z["key14"]), str(z["key15"])
            # I2: mismo inicio de scan (campo _sYYYYDDDHHMMSSs del nombre) en las dos bandas
            s14, s15 = k14.split("_s")[1][:14], k15.split("_s")[1][:14]
            if s14 != s15 or s14[:11] != f"{dt:%Y}{dt.timetuple().tm_yday:03d}{dt:%H%M}":
                scan_distinto += 1
                continue
            for b in (14, 15):
                rad[b][i] = z[f"rad{b}"]
                co[b].append(z[f"co{b}"])
        presentes += 1
        relleno += int(np.isnan(rad[14][i]).sum() + np.isnan(rad[15][i]).sum())
    out = {"bloque": nombre, "dias": len(dias), "cuadros_esperados": nt, "cuadros_presentes": presentes,
           "cobertura": presentes / nt, "scan_distinto": scan_distinto, "pixeles_relleno": relleno}
    # Coeficientes de Planck: se usa la mediana y se informa cuanto varian entre archivos
    cof = {}
    for b in (14, 15):
        c = np.array(co[b])
        cof[b] = np.median(c, axis=0)
        out[f"co{b}"] = cof[b].tolist()
        out[f"co{b}_variacion_max_rel"] = float(np.max(np.abs(c / cof[b] - 1)))
    bt = K.bt_de_rad(rad[14].astype("float64"), cof[14])
    val = np.isfinite(bt)
    out["bt11_en_rango"] = float(((bt > 180) & (bt < 330))[val].mean())
    out["bt11_min"], out["bt11_max"] = float(np.nanmin(bt)), float(np.nanmax(bt))
    # Cuadros congelados: dos cuadros consecutivos presentes con la ventana de C14 identica
    hay = np.isfinite(rad[14]).any(axis=(1, 2))
    cong = 0
    for i in range(1, nt):
        if hay[i] and hay[i - 1] and np.array_equal(rad[14][i], rad[14][i - 1], equal_nan=True):
            cong += 1
    out["cuadros_congelados"] = cong
    # Huecos por dia (para leer I1)
    por_dia = hay.reshape(len(dias), 144).sum(1)
    out["cuadros_por_dia"] = {f"{d:%Y-%m-%d}": int(n) for d, n in zip(dias, por_dia)}
    falla = []
    if out["cobertura"] < 0.95:
        falla.append("I1 cobertura")
    if scan_distinto:
        falla.append("I2 scan")
    if out["bt11_en_rango"] < 0.999 or cong:
        falla.append("I3 rango o congelados")
    out["fallas"] = falla
    os.makedirs(RES, exist_ok=True)
    json.dump(out, open(os.path.join(RES, f"instrumento_{nombre}.json"), "w"), indent=1)
    print(json.dumps({k: v for k, v in out.items() if k != "cuadros_por_dia"}, indent=1))
    print("dias con menos de 130 cuadros:", {k: v for k, v in out["cuadros_por_dia"].items() if v < 130})
    if falla:
        print("FALLA DE INSTRUMENTO:", falla)
        sys.exit(1)
    np.savez(os.path.join(K.H23, f"cubo_{nombre}.npz"), rad14=rad[14], rad15=rad[15], co14=cof[14], co15=cof[15],
             t0=np.array(f"{dias[0]:%Y-%m-%d}"))
    print("cubo guardado", nombre, rad[14].shape)


if __name__ == "__main__":
    main(sys.argv[1])
