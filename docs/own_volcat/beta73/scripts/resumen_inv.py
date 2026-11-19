import json, sys
from collections import defaultdict
res = []
for f in sys.argv[1:]:
    res += json.load(open(f))
por = defaultdict(lambda: dict(n=0, sinbarra=0, manto=0, dia=[], crep=[], noche=[], n50=0))
for r in res:
    d = r["t"][:10]; e = por[d]; e["n"] += 1
    if not r["barra"]:
        e["sinbarra"] += 1; continue
    e["manto"] += bool(r["manto"]); e["n50"] += r["n50"] > 0
    if r["anc"] and not r["manto"]:
        z = r["sza"]; f = "dia" if z < 80 else ("noche" if z >= 90 else "crep")
        e[f].append(r["t"][11:16])
for d, e in sorted(por.items()):
    print(d, f"n={e['n']} sinbarra={e['sinbarra']} manto={e['manto']} con_ceniza_50km={e['n50']} | anc dia {len(e['dia'])} crep {len(e['crep'])} noche {len(e['noche'])}",
          ("noche:" + ",".join(e["noche"])) if e["noche"] else "", ("crep:" + ",".join(e["crep"])) if e["crep"] else "")
