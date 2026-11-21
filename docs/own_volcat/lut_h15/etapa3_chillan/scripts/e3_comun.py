r"""H15 etapa 3 (Chillán): rutas e insumos comunes.

Por qué existe: la etapa 3 reutiliza, sin editarlos, el modelo radiativo de H3 (vía comun_h11 / h13_comun), la
ventana L1b de 83 × 94 píxeles alrededor de Nevados de Chillán y el motor de tablas de VOLCAT con las reglas de
nube tenue (nt_regla.py, PR 75). Lo nuevo (L1b de las horas de los eventos, GFS, nodos del modelo, modelo de
elevación) va a D:\goes_cache\etapa3_chillan. Los archivos de evento de VOLCAT (acceso restringido) sólo se leen.

Rutas por variable de entorno (defaults = lo que existe en este computador el 21-11-2026):
  E3_DIR       D:\goes_cache\etapa3_chillan
  H14_EVENTOS  D:\goes_notas\busqueda_2026-11-20\volcat_eventos_357070
  H11_H3       carpeta h3 rescatada (trae lbl\ con la tabla línea por línea)
  H11_B73      D:\goes_cache\h13\shim\b73
  H3_RT_DL     D:\goes_cache\rt (MT_CKD y SRF)
"""
import os
import sys

NOTAS_H12 = (r"C:\Users\nmend\AppData\Local\Claude-Data\claude_pzs8sxrjxfjjc\side-session-notes"
             r"\local_f3a7d295-ddde-4b7c-b258-25e760c44266\h12_datos\trabajo")
os.environ.setdefault("H11_H3", os.path.join(NOTAS_H12, "h3"))
os.environ.setdefault("H11_B73", r"D:\goes_cache\h13\shim\b73")
os.environ.setdefault("H3_RT_DL", r"D:\goes_cache\rt")
for _v in ("TMP", "TEMP"):
    os.environ[_v] = r"D:\goes_cache\tmp"

AQUI = os.path.dirname(os.path.abspath(__file__))
E3 = os.path.dirname(AQUI)                                   # .../lut_h15/etapa3_chillan
LUT_H15 = os.path.dirname(E3)
OWN = os.path.dirname(LUT_H15)
RES = os.path.join(E3, "resultados")
sys.path.insert(0, os.path.join(OWN, "temporal_h13", "scripts"))
sys.path.insert(0, os.path.join(LUT_H15, "nube_tenue", "scripts"))
sys.path.insert(0, os.path.join(LUT_H15, "scripts"))

E3DIR = os.environ.get("E3_DIR", r"D:\goes_cache\etapa3_chillan")
EVDIR = os.environ.get("H14_EVENTOS", r"D:\goes_notas\busqueda_2026-11-20\volcat_eventos_357070")
L1B = os.path.join(E3DIR, "l1b")
GFS = os.path.join(E3DIR, "gfs")
RT = os.path.join(E3DIR, "rt")
DEM = os.path.join(E3DIR, "dem")
for _d in (L1B, GFS, RT, DEM):
    os.makedirs(_d, exist_ok=True)

CRATER = (-36.863, -71.377)
