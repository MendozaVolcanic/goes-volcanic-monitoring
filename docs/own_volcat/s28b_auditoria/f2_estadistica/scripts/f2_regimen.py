r"""F2 (S28b): régimen del instrumento dentro de cada ventana (2024, 2025, 2026).

Por qué: una ventana que cruza un cambio de satélite, de modo de escaneo o de versión del producto de nubes mezcla dos
sistemas (§3b fila 10 de la guía). Se lee el nombre del archivo NOAA guardado en cada npz (key14, key15 y, si está, la
del ACM): satélite (G16/G19), modo (M3/M4/M6) y, para el ACM, el nombre del producto. Se cuenta por día.
Sólo lee D: (cachés de S22b, S22d/S23 y S25b); no abre días posteriores al 24-11-2026.
Uso: python -I f2_regimen.py
"""
import glob
import json
import os
import re
import sys
from collections import Counter, defaultdict

import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
CARP = {"2025": r"D:\goes_notas\s22\s22d_2025", "2024": r"D:\goes_notas\s25\s25b_2024",
        "2026_22a24": r"D:\goes_notas\s22\s22b"}
PAT = re.compile(r"OR_ABI-(L\w+?)-(\w+?)-(M\d)(C\d\d)?_(G\d\d)_s(\d{7})")


def main():
    out = {}
    for año, c in CARP.items():
        for sub in ("l1b", "acm"):
            fs = sorted(glob.glob(os.path.join(c, sub, "*.npz")))
            fs = [f for f in fs if os.path.basename(f)[:8] <= "20261124"]
            cnt, por_dia, claves = Counter(), defaultdict(Counter), set()
            for f in fs:
                try:
                    with np.load(f) as z:
                        claves.update(z.files)
                        ks = [str(z[k]) for k in z.files if k.startswith("key") or k in ("key", "archivo", "fn")]
                except Exception as e:  # noqa: BLE001
                    cnt[f"error:{type(e).__name__}"] += 1
                    continue
                if not ks:
                    cnt["sin_nombre"] += 1
                    continue
                for k in ks:
                    m = PAT.search(os.path.basename(k))
                    tag = f"{m.group(1)}-{m.group(2)}-{m.group(3)}-{m.group(5)}" if m else "no_parsea:" + k[-60:]
                    cnt[tag] += 1
                    por_dia[os.path.basename(f)[:8]][tag] += 1
            dias_mixtos = {d: dict(v) for d, v in por_dia.items() if len(v) > 1}
            out[f"{año}_{sub}"] = {"archivos": len(fs), "campos_npz": sorted(claves), "regimenes": dict(cnt),
                                   "dias_con_mas_de_un_regimen": dias_mixtos}
            print(año, sub, len(fs), sorted(claves), dict(cnt), "dias mixtos:", len(dias_mixtos), flush=True)
    json.dump(out, open(r"D:\goes_notas\s28\s28b\f2\regimen.json", "w", encoding="utf-8"), indent=1)


if __name__ == "__main__":
    main()
