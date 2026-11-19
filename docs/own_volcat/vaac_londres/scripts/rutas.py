"""Rutas de datos de la prueba London VAAC (Chillan, nov-2026). Todo absoluto, sin adivinar desde donde corre.

Datos de entrada (de solo lectura, del detector previo del 17-11-2026):
- CACHE_PREV: ventana 83 x 94 px ABI alrededor de Chillan con C11, C14, C15 en K (un .npz por scan).
- SNAPSHOT: foto fija de los scans que uso el detector previo (mismos conjuntos, comparables).
- HUELLAS / HUELLAS_DIL: huellas VOLCAT en la grilla ABI (sin dilatar y dilatadas 1 px).
- CUADROS: tabla de cuadros VOLCAT de 10 min (01 a 16-11).
Datos nuevos de esta prueba (TRABAJO): C13 por scan y resultados intermedios.
"""
import os

PREV = r"C:\Users\nmend\AppData\Local\Temp\claude\d6ea8719dcf88502\536a0873-47fb-4b33-9ee5-de0197c3f321\scratchpad\det"
CACHE_PREV = os.path.join(PREV, "cache")
SNAPSHOT = os.path.join(PREV, "resultados", "snapshot_cache.txt")
WINDOW = os.path.join(PREV, "window.json")
PLANCK_PREV = os.path.join(PREV, "planck.json")
LATLON = os.path.join(PREV, "latlon.npz")
HUELLAS = os.path.join(PREV, "volcat", "huellas.npz")
HUELLAS_DIL = os.path.join(PREV, "volcat", "huellas_dil.npz")
CUADROS = os.path.join(PREV, "volcat", "cuadros_10min.csv")

TRABAJO = os.environ.get(
    "VAAC_TRABAJO",
    r"C:\Users\nmend\AppData\Local\Temp\claude\470cdb238f003f8e\1985b7fb-c655-4e72-b95c-8d201d1a842a\scratchpad\vaac")
CACHE13 = os.path.join(TRABAJO, "cache13")
PLANCK13 = os.path.join(TRABAJO, "planck_c13.json")
RESULTADOS = os.path.join(TRABAJO, "resultados")

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", ".."))
