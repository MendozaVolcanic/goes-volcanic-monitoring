r"""S21b, antes de medir: fraccion despejada E1 de H23 (>= 80 % del terreno bajo, 10 a 30 km del crater, ACMF 0 o 1)
por dia y cuadro, de los cubos infrarrojos de H23 y H24 (solo lectura). Sirve para elegir los dias de control y para
dejar escrito de donde salen (S20c: los dias despejados no son una muestra cualquiera).
Uso: python -I s21b_desp_e1.py > ../resultados/desp_e1.txt
"""
import os, numpy as np
from datetime import datetime, timedelta
H23 = r"D:\goes_notas\s17\h23"; H24 = r"D:\goes_notas\s18\h24"
T0 = datetime(2026, 9, 21); NDIAS = 62
LL = np.load(r"D:\goes_notas\local_f3a7d295\cache_rescatada\reproducir_volcat\latlon.npz")
LAT, LON = LL["lat"].ravel(), LL["lon"].ravel()
Z = np.load(r"D:\goes_cache\etapa3_chillan\dem_ventana.npz")["zdem"].ravel()
acm = np.full((NDIAS*144, LAT.size), 255, "uint8")
for fc, fa in [(f"{H23}/cubo_oct.npz", f"{H23}/acm_oct.npz"), (f"{H24}/cubo_oct.npz", f"{H24}/acm_oct.npz"), (f"{H23}/cubo_nov.npz", f"{H23}/acm_nov.npz")]:
    t0 = datetime.strptime(str(np.load(fc)["t0"]), "%Y-%m-%d"); a = np.load(fa)["acm"]
    i0 = (t0-T0).days*144; acm[i0:i0+a.shape[0]] = a.reshape(a.shape[0], -1)
acm = acm.reshape(NDIAS,144,-1)
def hav(la,lo,a,b):
    p1,p2=np.radians(la),np.radians(a); x=np.sin((p2-p1)/2)**2+np.cos(p1)*np.cos(p2)*np.sin(np.radians(b-lo)/2)**2
    return 2*6371*np.arcsin(np.sqrt(x))
la,lo,h=-36.86,-71.38,3212
d = hav(LAT,LON,la-0.93*h/1000/111.2,lo)
bajo = np.where((d>=10)&(d<=30)&(Z<1300))[0]
cerca = np.where(d<=12)[0]   # incluye cumbre (ACM marca nieve como nube a veces)
fr = (acm[:,:,bajo]<=1).mean(2); frc=(acm[:,:,cerca]<=1).mean(2)
np.savez("D:/goes_notas/s21/b/desp_e1.npz", fr=fr, frc=frc)
slots = {"14:30":87,"14:20":86}
for s in range(102, 134): slots[f"{s//6:02d}:{s%6*10:02d}"]=s
print("dia      ", " ".join(k for k in ["14:20","14:30","17:20","17:30","17:40","20:20","20:30","20:40","21:30","21:40","21:50","22:00"]))
for di in range(NDIAS):
    dd = T0+timedelta(days=di)
    row=[f"{fr[di,slots[k]]:.2f}" for k in ["14:20","14:30","17:20","17:30","17:40","20:20","20:30","20:40","21:30","21:40","21:50","22:00"]]
    print(dd.strftime("%m-%d"), " ".join(row))
