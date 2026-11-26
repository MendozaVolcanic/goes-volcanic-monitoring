r"""V301: arma la copia de ensayo de las tres confirmaciones (S23b, S25a, S26a) apuntada a días YA VISTOS.

Por qué una copia: los scripts reales escriben su resultado en `resultados/` del repo y leen el cubo de
`D:\goes_notas\s23\s23b`. Un ensayo sobre los originales gastaría la medida o dejaría un `s23b_resultado.json` en la
carpeta auditada. La copia conserva la estructura de carpetas, así que `OV`, `RES` y `REPO` (que cada script deriva de
su propia ruta) caen dentro de la copia y nada se escribe en el repo ni en `D:\goes_notas\s23`.

Qué se cambia en la copia (y nada más): cuatro constantes de `s23b_confirmar.py` pasan a leerse de variables de
entorno, para apuntar a días ya vistos: TRAB (carpeta con l1b, acm y la copia del estat), ARRANQUE, NUEVO0 y CLASES.
`s26a_medir.py` usa esas mismas constantes a través de `SB.`, así que no se toca. El diff se imprime.

Días de ensayo: arranque 07-11-2026 y "nuevos" 08 a 11-11-2026 (cuadros por archivo de H23, ya mirados por S22 a S26).
Clases: las reales de `calor_rayos/resultados/frames_calor.csv` (08-11 13 P, 09-11 0 P, 10-11 12 P, 11-11 3 P).

Uso: python -I -B v301_preparar.py
"""
import csv
import difflib
import hashlib
import os
import shutil
import sys

sys.stdout.reconfigure(encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(AQUI, "..", "..", "..", "..", ".."))
V = r"D:\goes_notas\s28\s28b\v301"
COPIA = os.path.join(V, "repo")
OVO = os.path.join(REPO, "docs", "own_volcat")
OVC = os.path.join(COPIA, "docs", "own_volcat")
H23 = r"D:\goes_notas\s17\h23"
ESTAT = r"D:\goes_notas\s23\s23b\estat_2026.npy"
DIAS = ["20261107", "20261108", "20261109", "20261110", "20261111"]

SCRIPTS = ["s22a_detector_sectores", "s22b_pluma_vs_nubes", "s23_fondo_2025", "s25a_crater", "s26a_combinado",
           "h23_inyeccion", "h24_pulsos_reav", "h29_pluma_0811"]
RESULTADOS = {"calor_rayos": ["frames_calor.csv"],
              "s22b_pluma_vs_nubes": ["volcat_clases_22a24nov.csv", "seco.json"],
              "s23_fondo_2025": ["seco.json", "poder.json", "instrumento_2025.json", "sensibilidad_costumbre_2026.json"],
              "s25a_crater": ["instrumento.json", "s25a_resultado.json"],
              "s26a_combinado": ["s26a_seco.json", "s26a_desarrollo.json"]}

PARCHES = [
    ('TRAB = r"D:\\goes_notas\\s23\\s23b"', 'TRAB = os.environ["V301_TRAB"]'),
    ("ARRANQUE = datetime(2026, 11, 24) ", 'ARRANQUE = datetime.strptime(os.environ["V301_ARRANQUE"], "%Y-%m-%d") '),
    ("NUEVO0 = datetime(2026, 11, 25)", "NUEVO0 = ARRANQUE + timedelta(days=1)"),
    ('CLASES = os.path.join(S.RES, "volcat_clases_desde_25nov.csv")', 'CLASES = os.environ["V301_CLASES"]'),
]


def copiar_py(carpeta):
    o, c = os.path.join(OVO, carpeta, "scripts"), os.path.join(OVC, carpeta, "scripts")
    os.makedirs(c, exist_ok=True)
    for f in os.listdir(o):
        if f.endswith(".py"):
            shutil.copyfile(os.path.join(o, f), os.path.join(c, f))


def main():
    os.makedirs(COPIA, exist_ok=True)
    for carpeta in SCRIPTS:
        copiar_py(carpeta)
    for carpeta, archivos in RESULTADOS.items():
        c = os.path.join(OVC, carpeta, "resultados")
        os.makedirs(c, exist_ok=True)
        for f in archivos:
            shutil.copyfile(os.path.join(OVO, carpeta, "resultados", f), os.path.join(c, f))
    # src/ (h29_comun importa src.process.volcat_colorbar): sólo los .py
    for raiz, _, fs in os.walk(os.path.join(REPO, "src")):
        if "__pycache__" in raiz:
            continue
        dest = os.path.join(COPIA, os.path.relpath(raiz, REPO))
        os.makedirs(dest, exist_ok=True)
        for f in fs:
            if f.endswith(".py"):
                shutil.copyfile(os.path.join(raiz, f), os.path.join(dest, f))
    # parche de s23b_confirmar.py
    fn = os.path.join(OVC, "s23_fondo_2025", "scripts", "s23b_confirmar.py")
    orig = open(os.path.join(OVO, "s23_fondo_2025", "scripts", "s23b_confirmar.py"), encoding="utf-8").read()
    nuevo = orig
    for a, b in PARCHES:
        assert nuevo.count(a) == 1, (a, nuevo.count(a))
        nuevo = nuevo.replace(a, b)
    open(fn, "w", encoding="utf-8", newline="").write(nuevo)
    print("".join(difflib.unified_diff(orig.splitlines(True), nuevo.splitlines(True), "original", "copia", n=0)))
    # los demás scripts de la copia son idénticos byte a byte a los del repo
    dif = []
    for carpeta in SCRIPTS:
        o, c = os.path.join(OVO, carpeta, "scripts"), os.path.join(OVC, carpeta, "scripts")
        for f in os.listdir(c):
            if f.endswith(".py") and open(os.path.join(o, f), "rb").read() != open(os.path.join(c, f), "rb").read():
                dif.append(f"{carpeta}/{f}")
    print("scripts de la copia que difieren del repo:", dif)
    # carpeta de datos base: cuadros por archivo de 07 a 11-11 (ya vistos) y copia del estat congelado
    base = os.path.join(V, "trab_base")
    for k in ("l1b", "acm"):
        os.makedirs(os.path.join(base, k), exist_ok=True)
        n = 0
        for f in os.listdir(os.path.join(H23, k)):
            if f[:8] in DIAS and f.endswith(".npz") and ".tmp" not in f:
                d = os.path.join(base, k, f)
                if not os.path.exists(d):
                    shutil.copyfile(os.path.join(H23, k, f), d)
                n += 1
        print(k, "cuadros en la base de ensayo:", n)
    shutil.copyfile(ESTAT, os.path.join(base, "estat_2026.npy"))
    print("estat copiado; sha256 del archivo",
          hashlib.sha256(open(os.path.join(base, "estat_2026.npy"), "rb").read()).hexdigest()[:16])
    # clases reales de 08 a 11-11 en el formato del CSV de la confirmación
    filas = []
    with open(os.path.join(OVO, "calor_rayos", "resultados", "frames_calor.csv"), encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if "2026-11-08" <= r["dt"][:10] <= "2026-11-11":
                filas.append([r["dt"][:16], r["clase"]])
    for nombre, hasta in (("clases_08a11.csv", "2026-11-11"), ("clases_08a10.csv", "2026-11-10"),
                          ("clases_08a09.csv", "2026-11-09")):
        with open(os.path.join(V, nombre), "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(["dt", "clase"])
            w.writerows([x for x in filas if x[0][:10] <= hasta])
        sub = [x for x in filas if x[0][:10] <= hasta]
        print(nombre, len(sub), "filas;", sum(1 for x in sub if x[1] == "P"), "P en",
              len({x[0][:10] for x in sub if x[1] == "P"}), "días")


if __name__ == "__main__":
    main()
