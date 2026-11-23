import sys, numpy as np
sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__)))
sys.argv=['x']
import s20c_medir_v1_pareo as S
Dt = S.Datos(); QQ,_ = S.cuadros("principal")
for gate in (True, False):
    M = S.Motor(Dt, gate=gate)
    for p in S.PRUEBAS:
        dp=[]; dpl=[]; cp=[]; cpl=[]
        for q in QQ[p]:
            c,d = M.control(q["D"], q["s"], q["F"], q["R"]); dp.append(abs(d)); cp.append(Dt.claro[q["D"], q["s"]])
            for j in S.vecinos(q["D"]):
                c,d = M.control(j, q["s"], q["F"], q["R"]); dpl.append(abs(d)); cpl.append(Dt.claro[j, q["s"]])
        dp=np.array(dp); dpl=np.array(dpl)
        print("gate",gate,p,"|dif| pos med %.1f p25 %.1f p75 %.1f | plac med %.1f | pos ACMF claro %.2f plac claro %.2f"%(np.nanmedian(dp),np.nanpercentile(dp,25),np.nanpercentile(dp,75),np.nanmedian(dpl),np.mean(cp),np.mean(cpl)))
# signo de la diferencia en positivos (pozo limpio mas frio o mas tibio?)
M = S.Motor(Dt, gate=False); sg=[]
for q in QQ["H11_H12"]+QQ["paso2"]:
    c,d = M.control(q["D"], q["s"], q["F"], q["R"]); sg.append(d)
print("dif (control - positivo) mediana %.1f K"%np.nanmedian(sg))
