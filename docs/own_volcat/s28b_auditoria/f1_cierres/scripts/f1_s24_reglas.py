"""F1 (S28b): aplica la regla escrita del criterio de S24 (criterio_2026-11-25.md, 5c83319) al JSON de
resultados, sin leer el INFORME. Linea base roja: el control positivo A (08-11) debe salir INVALIDO.

Regla (criterio §2): por banda, minimo 5 cuadros (si no SIN DATO); SENAL si mediana q <= 0,05 y al menos la
mitad con q <= 0,10; DEBIL si mediana q <= 0,20; SIN SENAL lo demas. Control positivo: si el 08-11 no da SENAL
en 'todo el anillo', la medida es INVALIDA. Control negativo: giro con SENAL igual que la huella -> NO ESPECIFICA.
Regla B1 (§3): EPISODICO si top5 >= 0,60 y Fisher comunes vs 2026 p > 0,05.
"""
import json, statistics, sys
from pathlib import Path
from scipy.stats import fisher_exact

sys.stdout.reconfigure(encoding="utf-8")

R = Path(__file__).resolve().parents[3] / 's24_dia14_noche' / 'resultados' / 's24_resultado.json'
d = json.loads(R.read_text(encoding='utf-8'))

def regla(qs):
    qs = [q for q in qs if q is not None]
    if len(qs) < 5:
        return 'SIN DATO', len(qs), None
    med = statistics.median(qs)
    frac = sum(q <= 0.10 for q in qs) / len(qs)
    if med <= 0.05 and frac >= 0.5:
        v = 'SENAL'
    elif med <= 0.20:
        v = 'DEBIL'
    else:
        v = 'SIN SENAL'
    return v, len(qs), round(med, 4)

for clave in ('A_14-11', 'A_control_08-11'):
    bloque = d[clave]
    print('==', clave, 'cuadros P con compuerta', bloque['cuadros_P_con_compuerta'], 'filas', len(bloque['cuadros']))
    for banda in ('huella 4-8 km', 'huella 8-15 km', 'huella 15-40 km', 'huella anillo',
                  'giro 4-8 km', 'giro 8-15 km', 'giro 15-40 km', 'giro anillo'):
        qs = [c[banda]['q'] for c in bloque['cuadros'] if c.get(banda)]
        v, n, med = regla(qs)
        guardado = bloque['veredictos'][banda]
        print(f'  {banda:16s} recomputado {v:9s} n={n:2d} med={med}  | json {guardado["veredicto"]} n={guardado["cuadros"]} med={guardado["mediana_q"]}')

ctrl = regla([c['huella anillo']['q'] for c in d['A_control_08-11']['cuadros']])
print('CONTROL POSITIVO 08-11 todo el anillo:', ctrl[0], '-> A', 'VALIDA' if ctrl[0] == 'SENAL' else 'INVALIDA',
      '| json A_valida =', d['A_valida'])

b1 = d['B']['B1']
_, p = fisher_exact([[b1['disparos_comunes'], b1['evaluados_comunes'] - b1['disparos_comunes']],
                     [b1['disparos_noche_2026'], b1['evaluados_noche_2026'] - b1['disparos_noche_2026']]])
epi = b1['frac_top5'] >= 0.60 and p > 0.05
print('B1 recomputado: p_fisher', p, 'top5', b1['frac_top5'], '->', 'EPISODICO' if epi else 'NO EPISODICO',
      '| json', b1['veredicto'])
top = sorted(b1['top_noches_2025'], key=lambda r: -r['disparos'])[:5]
print('B1 top5 suma', sum(r['disparos'] for r in top), 'de', b1['disparos_noche_2025'],
      '=', round(sum(r['disparos'] for r in top) / b1['disparos_noche_2025'], 4))
print('B1 tasa 2026/comunes', round(b1['tasa_2026'] / b1['tasa_comunes_2025'], 2))
