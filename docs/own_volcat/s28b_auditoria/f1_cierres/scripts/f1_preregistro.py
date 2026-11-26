"""F1 (S28b): orden temporal criterio -> medida, con git y con el reflog de las ramas remotas (empuje).

Para cada medida: primer commit que trae el criterio, primer commit que trae resultados/*.json de esa medida,
fechas de autor y de commit, hora de empuje (reflog 'update by push' de refs/remotes/origin/claude/*, que queda en el
.git compartido por los worktrees), y git diff del criterio entre su commit y el de la medida y entre su commit y la
base auditada 8894722. Sólo lee git; no toca nada.
"""
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8")
BASE = "8894722"
OV = "docs/own_volcat/"
# (medida, criterio, resultado que la trae, rama de la sesión)
MEDIDAS = [
    ("S23a", "s23_fondo_2025/criterio_2026-11-24.md", "s23_fondo_2025/resultados/s23a_resultado.json", "s23-fondo-2025-68f1e1"),
    ("S23b candidata (post hoc)", "s23_fondo_2025/criterio_S23b_2026-11-25.md",
     "s23_fondo_2025/resultados/sensibilidad_costumbre_2026.json", "s23-fondo-2025-68f1e1"),
    ("S24 A y B", "s24_dia14_noche/criterio_2026-11-25.md", "s24_dia14_noche/resultados/s24_resultado.json",
     "s24-confirmar-s23b-11fe53"),
    ("S24c", "s24_dia14_noche/criterio_S24c_2026-11-25.md", "s24_dia14_noche/resultados/s24c_calibracion.json",
     "s24-confirmar-s23b-11fe53"),
    ("S25a", "s25a_crater/criterio_2026-11-25.md", "s25a_crater/resultados/s25a_resultado.json", "s25a-crater-s23b-92d67e"),
    ("S25b", "s25b_fondo_2024/criterio_2026-11-25.md", "s25b_fondo_2024/resultados/s25b_resultado.json",
     "s25b-fondo-2024-73846a"),
    ("S26a", "s26a_combinado/criterio_2026-11-25.md", "s26a_combinado/resultados/s26a_desarrollo.json",
     "s26a-combinado-cceab0"),
    ("S26b", "s26b_noche_crater/criterio_2026-11-25.md", "s26b_noche_crater/resultados/s26b_resultado.json",
     "s26b-noche-crater-d9afef"),
    ("S27a", "s27a_noche_causa/criterio_2026-11-25.md", "s27a_noche_causa/resultados/s27a_resultado.json",
     "s27a-noche-viento-9d839d"),
    ("S27b", "s27b_altura_desfase/criterio_2026-11-25.md", "s27b_altura_desfase/resultados/s27b_resultado.json",
     "s27b-altura-desfase-04d8dd"),
    ("S28a", "s28a_vecinas/criterio_2026-11-25.md", "s28a_vecinas/resultados/s28a_resultado.json",
     "s28a-vecinas-falsa-alarma-7791f2"),
]


def git(*a):
    return subprocess.run(["git", *a], capture_output=True, text=True, encoding="utf-8").stdout.strip()


def primer(path):
    out = git("log", "--all", "--diff-filter=A", "--format=%h|%ad|%cd", "--date=iso", "--", OV + path).splitlines()
    return out[-1].split("|") if out else (None, None, None)


def todos(path):
    return [x.split("|")[0] for x in git("log", "--all", "--format=%h|%cd", "--date=iso", "--", OV + path).splitlines()]


def empuje(rama, commit):
    """Hora del primer empuje (el más antiguo del reflog) cuyo tip ya contiene al commit."""
    filas = git("reflog", "show", "--date=iso", f"refs/remotes/origin/claude/{rama}").splitlines()[::-1]
    for linea in filas:
        h = linea.split()[0]
        if subprocess.run(["git", "merge-base", "--is-ancestor", commit, h]).returncode == 0:
            return linea.split("@{")[1].split("}")[0]
    return "SIN DATO"


print("medida | criterio (commit, fecha) | empuje del criterio | resultado (commit, fecha) | empuje del resultado | "
      "commits del criterio | diff criterio..medida | diff criterio..base")
for nom, cri, res, rama in MEDIDAS:
    hc, ac, cc = primer(cri)
    hr, ar, cr = primer(res)
    pc = empuje(rama, hc) if hc else "SIN DATO"
    pr = empuje(rama, hr) if hr else "SIN DATO"
    d1 = git("diff", "--stat", hc, hr, "--", OV + cri) if hc and hr else "?"
    d2 = git("diff", "--stat", hc, BASE, "--", OV + cri) if hc else "?"
    print(f"{nom} | {hc} {cc} | {pc} | {hr} {cr} | {pr} | {','.join(todos(cri))} | "
          f"{'vacío' if not d1 else d1.splitlines()[-1].strip()} | {'vacío' if not d2 else d2.splitlines()[-1].strip()} | "
          f"autor==commit {ac == cc and ar == cr} | criterio antes {cc < cr if cc and cr else '?'}")
