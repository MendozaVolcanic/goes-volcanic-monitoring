r"""S21a2: repite la prueba 1 de S20b en las pasadas Sentinel-2 del 29-10 y del 13-11 con EL MISMO CODIGO.

Este archivo no implementa nada: importa `s20b_preparar.py`, `s20b_medir.py` y `s20b_posthoc.py` de
`docs/own_volcat/s20b_verdad_alta_res/scripts/` (sin tocarlos, regla del commit 4126049) y sustituye solo las
constantes que en S20b estaban fijas a las fechas del 25-10 y del 08-11:

  - escena objetivo y su hora (`OBJ` de preparar, `EVENTOS` de medir), tomadas del catalogo STAC de Element 84;
  - altura de respaldo del VAAC si la sombra no vale (`VAAC_H`), del aviso declarado en el criterio S21a2;
  - carpeta de los L1b de donde sale la hora de inicio del cuadro (`L1B`);
  - carpetas de salida: resultados y figuras en `docs/own_volcat/s21a2_prueba1_s2/`, datos en D:\goes_notas\s21\a2
    (las escenas ya bajadas en S20b estan ahi como enlaces duros: no ocupan disco de nuevo).

Por que asi: la tarea es repetir sin cambiar la regla. Si se copiara el codigo, cualquier diferencia futura entre
copias seria una regla distinta; asi el codigo que mide es el mismo archivo que midio en S20b.

Regla de "sin huella" del criterio S21a2 (§3): si la mascara no marca ninguna celda, la pasada es SIN HUELLA; si la
suma de f de los pixeles con f >= 0,02 fuera del bloque del crater es < 0,20, es SIN DATO (umbral de S20b). En los
dos casos la pasada no entra a `esperado` ni a `medir` (el codigo de S20b no esta hecho para una huella vacia) y la
mascara no se ajusta.

Uso: python -I s21a2_correr.py preparar | esperado | medir | posthoc
"""
import json
import os
import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
S20B = os.path.normpath(os.path.join(AQUI, "..", "..", "s20b_verdad_alta_res", "scripts"))
sys.path.insert(0, S20B)
import s20b_comun as C  # noqa: E402

BASE = os.path.dirname(AQUI)
RES = os.path.join(BASE, "resultados")
FIG = os.path.join(BASE, "figuras")
C.TRABAJO = r"D:\goes_notas\s21\a2"

# --- lo unico que cambia: fechas (criterio S21a2 §1) ---
OBJ = {
    "2026-10-29": {"id": "S2C_19HBV_20261029_0_L2A", "fuente": "e84", "hora": "14:53:03"},
    "2026-11-13": {"id": "S2B_19HBV_20261113_0_L2A", "fuente": "e84", "hora": "14:53:06"},
}
VAAC_H = {"2026-10-29": 14000 * 0.3048,    # aviso 2026/042, OBS 29/1230Z, SFC/FL140
          "2026-11-13": 14000 * 0.3048}    # aviso 2026/053, PIREP 131429Z ceniza FL130/140 (tope FL140)
EVENTOS = {d: {"hora": o["hora"], "cuadros": ["14:40", "14:50"]} for d, o in OBJ.items()}
L1B = {"2026-10-29": r"D:\goes_notas\s18\h24\l1b", "2026-11-13": r"D:\goes_notas\s17\h23\l1b"}
F_PESO, SUMA_F_MIN = 0.02, 0.20            # los de s20b_medir (se comprueba abajo que no cambiaron)


def estado_huella():
    """SIN HUELLA / SIN DATO / OK por pasada, desde preparar_resumen.json y la mascara en D:."""
    with open(os.path.join(RES, "preparar_resumen.json"), encoding="utf-8") as fh:
        res = json.load(fh)
    out = {}
    for d in OBJ:
        if res[d]["celdas_pluma"] == 0:
            out[d] = ("SIN HUELLA", 0.0)
            continue
        z = np.load(os.path.join(C.TRABAJO, f"mascara_{d}.npz"))
        f = z["f"]
        sf = float(f[(f >= F_PESO) & ~z["bloque"]].sum())
        out[d] = ("OK" if sf >= SUMA_F_MIN else "SIN DATO", round(sf, 3))
    return out


def main():
    modo = sys.argv[1]
    os.makedirs(RES, exist_ok=True)
    os.makedirs(FIG, exist_ok=True)
    if modo == "preparar":
        import s20b_preparar as P
        P.RES, P.FIG, P.OBJ, P.VAAC_H = RES, FIG, OBJ, VAAC_H
        P.main()
        est = estado_huella()
        print("estado de la huella:", est, flush=True)
        with open(os.path.join(RES, "estado_huella.json"), "w", encoding="utf-8") as fh:
            json.dump(est, fh, ensure_ascii=False, indent=1)
        return
    import s20b_medir as X
    assert (X.F_PESO, X.SUMA_F_MIN) == (F_PESO, SUMA_F_MIN)
    est = estado_huella()
    X.RES = RES
    X.L1B = L1B
    X.EVENTOS = {d: e for d, e in EVENTOS.items() if est[d][0] == "OK"}
    print("pasadas que se miden:", list(X.EVENTOS), "estado:", est, flush=True)
    if not X.EVENTOS:
        return
    if modo == "posthoc":
        import s20b_posthoc as PH
        PH.main()
        return
    sys.argv = [sys.argv[0], modo]
    X.main()


if __name__ == "__main__":
    main()
