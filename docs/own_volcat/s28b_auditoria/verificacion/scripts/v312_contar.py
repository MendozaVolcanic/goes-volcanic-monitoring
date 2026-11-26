r"""V312: ¿`contar` reescribe el CSV de clases entero, y el conteo del gatillo puede bajar entre corridas?

Ensayo sobre la COPIA de `s23b_confirmar.py` (ver v301_preparar.py), con días ya vistos: arranque 09-11-2026 y días
"nuevos" 10-11 y 11-11-2026 (PNG de VOLCAT guardados en D:\goes_notas\s22\volcat_png, sólo lectura).

Lo único que se desactiva es el respaldo desde SSEC (`s23_volcat_respaldo.py`, que pide el listado a la red): la
auditoría no baja nada de SSEC. `contar` corre tal cual desde la línea siguiente.

Tres pruebas:
  1. contar hasta el 11-11 y después hasta el 10-11: ¿el CSV se trunca y el conteo de P baja?
  2. contar con las carpetas de PNG ausentes (D: sin montar o carpeta movida): ¿queda un CSV sólo con encabezado?
  3. estabilidad de la clase cuando llegan cuadros nuevos: se clasifica el 10-11 con los PNG "disponibles hasta la hora
     t" y se compara con la clase final. P no debería cambiar (depende sólo de su cuadro); N puede pasar a "otro".

Uso (variables de entorno puestas por el propio script): python -I -B v312_contar.py
"""
import csv
import io
import os
import sys
from contextlib import redirect_stdout
from datetime import datetime

sys.stdout.reconfigure(encoding="utf-8")
V = r"D:\goes_notas\s28\s28b\v301"
CSV_ENSAYO = os.path.join(V, "v312_clases_ensayo.csv")
os.environ["V301_TRAB"] = os.path.join(V, "trab_base")
os.environ["V301_ARRANQUE"] = "2026-11-09"
os.environ["V301_CLASES"] = CSV_ENSAYO
sys.path.insert(0, os.path.join(V, "repo", "docs", "own_volcat", "s23_fondo_2025", "scripts"))


def leer():
    with open(CSV_ENSAYO, encoding="utf-8") as f:
        filas = list(csv.DictReader(f))
    return len(filas), sum(1 for r in filas if r["clase"] == "P"), sorted({r["dt"][:10] for r in filas})


def main():
    import s23b_confirmar as SB
    assert SB.__file__.startswith(V), SB.__file__
    assert SB.CLASES == CSV_ENSAYO
    SB.subprocess.run = lambda *a, **k: None          # sin respaldo desde SSEC (no se baja nada)
    import s22b_volcat_clases as VC
    dirs0 = list(VC.PNG_DIRS)

    def contar(hasta):
        VC.PNG_DIRS[:] = dirs0                         # contar antepone PNG_S23 en cada llamada; se parte de lo mismo
        buf = io.StringIO()
        with redirect_stdout(buf):
            SB.contar(hasta)
        return buf.getvalue().strip().splitlines()[-1]

    print("== 1. contar hasta 2026-11-11 y después hasta 2026-11-10")
    print(contar("2026-11-11"))
    print("CSV:", leer())
    print(contar("2026-11-10"))
    print("CSV:", leer())

    print("== 2. contar con las carpetas de PNG ausentes")
    VC_PNG_S23, SB.PNG_S23 = SB.PNG_S23, os.path.join(V, "no_existe_a")
    dirs_malos = [os.path.join(V, "no_existe_b"), os.path.join(V, "no_existe_c")]
    dirs_buenos = list(dirs0)
    dirs0[:] = dirs_malos
    try:
        print(contar("2026-11-11"))
    except Exception as e:  # noqa: BLE001
        print("EXCEPCION", repr(e)[:200])
    print("CSV:", leer())
    SB.PNG_S23 = VC_PNG_S23
    dirs0[:] = dirs_buenos

    print("== 3. clase con los PNG disponibles hasta la hora t, contra la clase final (día 2026-11-10)")
    VC.PNG_DIRS[:] = [SB.PNG_S23] + dirs_buenos
    inv = VC.inventario({"2026-11-09", "2026-11-10", "2026-11-11"})
    final = VC.clases(inv)
    for hh in (15, 16, 18, 20, 22, 23):
        t = datetime(2026, 11, 10, hh, 0)
        parcial = VC.clases({dt: r for dt, r in inv.items() if dt <= t})
        cambios = {}
        for dt, c in parcial.items():
            if dt.date() == t.date() and c != final[dt]:
                cambios[(c, final[dt])] = cambios.get((c, final[dt]), 0) + 1
        nP = sum(1 for dt, c in parcial.items() if dt.date() == t.date() and c == "P")
        nPf = sum(1 for dt, c in final.items() if dt.date() == t.date() and dt <= t and c == "P")
        print(f"t = 10-11 {hh:02d}:00  P con lo disponible {nP}, P finales hasta t {nPf}, cambios de clase {cambios}")
    # todos los cortes de 10 min de los dos días: cuántos (corte, cuadro) cambian de clase y de qué a qué
    from datetime import timedelta
    tot, cortes_con_cambio, baja_P = {}, 0, 0
    t = datetime(2026, 11, 10, 0, 0)
    while t <= datetime(2026, 11, 11, 23, 50):
        parcial = VC.clases({dt: r for dt, r in inv.items() if dt <= t})
        hubo = False
        for dt, c in parcial.items():
            if dt >= datetime(2026, 11, 10) and c != final[dt]:
                tot[(c, final[dt])] = tot.get((c, final[dt]), 0) + 1
                hubo = True
        nP = sum(1 for dt, c in parcial.items() if dt >= datetime(2026, 11, 10) and c == "P")
        nPf = sum(1 for dt, c in final.items() if datetime(2026, 11, 10) <= dt <= t and c == "P")
        baja_P += nP != nPf
        cortes_con_cambio += hubo
        t += timedelta(minutes=10)
    print(f"288 cortes de 10 min (10-11 y 11-11): cortes con algún cambio de clase {cortes_con_cambio}; "
          f"cortes en que el conteo de P difiere del final {baja_P}; pares (corte, cuadro) por tipo de cambio {tot}")
    os.remove(CSV_ENSAYO)


if __name__ == "__main__":
    main()
