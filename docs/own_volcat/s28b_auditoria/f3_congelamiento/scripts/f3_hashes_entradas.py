r"""F3 (S28b): SHA-256 y mtime de todo lo que las tres confirmaciones congeladas leen y que su código NO verifica.

Por qué: s23b_confirmar.py y s26a_medir.py sólo comprueban el hash de estat_2026.npy. La base, el umbral, el nublado de
costumbre de 2025, el azar r25, el de la unión y p* se recalculan en el momento de la medida desde estos archivos. Si
alguno cambia antes de la medida única, la confirmación usa otra regla sin avisar. Esta tabla deja la línea base de hoy.
Sólo lee. Salida: D:\goes_notas\s28\s28b\f3\hashes_entradas.json
"""
import hashlib
import json
import os
import sys
from datetime import datetime, timezone

sys.stdout.reconfigure(encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
OV = os.path.abspath(os.path.join(AQUI, "..", "..", ".."))
ARCH = [
    r"D:\goes_notas\s23\s23b\estat_2026.npy",
    r"D:\goes_notas\s23\s23a\r25_acm.npy", r"D:\goes_notas\s23\s23a\r25_m1.npy", r"D:\goes_notas\s23\s23a\r25_bt11.npy",
    r"D:\goes_notas\s25\s25a\r25_acm.npy", r"D:\goes_notas\s25\s25a\r25_btd.npy", r"D:\goes_notas\s25\s25a\n26_btd.npy",
    r"D:\goes_notas\s22\s22b\dev_acm.npy", r"D:\goes_notas\s22\s22b\dev_bt11.npy", r"D:\goes_notas\s22\s22b\dev_btd.npy",
    r"D:\goes_notas\s22\s22b\dev_co.npy", r"D:\goes_notas\s22\s22b\dev_m1.npy",
    r"D:\goes_notas\s22\s22b\nuevo_acm.npy", r"D:\goes_notas\s22\s22b\nuevo_bt11.npy", r"D:\goes_notas\s22\s22b\nuevo_m1.npy",
    r"D:\goes_notas\local_f3a7d295\cache_rescatada\reproducir_volcat\latlon.npz",
    r"D:\goes_cache\etapa3_chillan\dem_ventana.npz",
    os.path.join(OV, "s26a_combinado", "resultados", "s26a_seco.json"),
    os.path.join(OV, "calor_rayos", "resultados", "frames_calor.csv"),
    os.path.join(OV, "s22b_pluma_vs_nubes", "resultados", "volcat_clases_22a24nov.csv"),
    os.path.join(OV, "s22b_pluma_vs_nubes", "resultados", "seco.json"),
]


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(2**22), b""):
            h.update(b)
    return h.hexdigest()


if __name__ == "__main__":
    out = []
    for p in ARCH:
        if not os.path.exists(p):
            out.append({"archivo": p, "existe": False})
            continue
        st = os.stat(p)
        out.append({"archivo": p, "existe": True, "bytes": st.st_size, "sha256": sha(p),
                    "mtime_utc": datetime.fromtimestamp(st.st_mtime, timezone.utc).strftime("%Y-%m-%d %H:%M:%S")})
        print(out[-1]["mtime_utc"], out[-1]["sha256"][:16], st.st_size, p, flush=True)
    json.dump(out, open(r"D:\goes_notas\s28\s28b\f3\hashes_entradas.json", "w", encoding="utf-8"), indent=1)
