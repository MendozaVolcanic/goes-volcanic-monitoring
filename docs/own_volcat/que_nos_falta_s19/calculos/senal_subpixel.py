"""Senal IR esperada de una pluma que llena solo una fraccion del pixel. S19i, 23-11-2026.

Fenomeno: en 11 y 12 um el satelite mide la mezcla de lo que emite el suelo y lo que
emite la pluma. La pluma solo cambia la medida si (1) tapa una parte apreciable del
pixel, (2) no es transparente y (3) esta a otra temperatura que el suelo que tapa.
Este script multiplica esos tres factores para decir cuantos kelvin se mueve el pixel.

Modelo (deliberadamente simple; es para decidir plausibilidad, no para medir):
- Pixel = fraccion f cubierta por una capa de emisividad e11 a temperatura Tc, y
  fraccion (1 - f) de suelo despejado a temperatura de brillo Ts.
- Radiancia = (1 - f*e) * B(Ts) + f*e * B(Tc). Sin atmosfera encima ni debajo de la capa
  (la absorcion del vapor entre la capa y el satelite achicaria todavia mas la senal).
- Monocromatico en la longitud de onda central de C14 (11,2 um) y C15 (12,3 um).
- e12 sale de beta = ln(1 - e12) / ln(1 - e11) (definicion de Pavolonis 2010);
  beta 0,70 es el de H23 para ceniza "tipica"; beta 1,0 es una pluma gris (gruesa, o
  agua y gas), que no mueve la diferencia 11 - 12.
- Temperaturas: las de docs/own_volcat/h23_inyeccion/INFORME.md seccion 1: aire a 3, 4 y
  5 km = 269, 263 y 257 K; suelo de la cumbre despejado 264 a 274 K; terreno bajo mas tibio.
- El caso de 285 K lo agrego el verificador de S19i: de tarde la huella esta mucho mas tibia
  que la nieve de la manana, y ahi "pluma angosta" ya no alcanza para explicar que no se vea.

Uso: python senal_subpixel.py
"""
from __future__ import annotations

import math

C1 = 1.191042e-5   # mW m-2 sr-1 (cm-1)-4
C2 = 1.4387752     # K cm
NU11 = 1e4 / 11.2  # cm-1
NU12 = 1e4 / 12.3


def planck(nu: float, t: float) -> float:
    return C1 * nu ** 3 / (math.exp(C2 * nu / t) - 1.0)


def bt(nu: float, rad: float) -> float:
    return C2 * nu / math.log(C1 * nu ** 3 / rad + 1.0)


def senal(f: float, e11: float, beta: float, ts: float, tc: float) -> tuple[float, float]:
    """Devuelve (cambio de BT11, cambio de BT11 - BT12) en K respecto del suelo despejado."""
    e12 = 1.0 - (1.0 - e11) ** beta
    r11 = (1 - f * e11) * planck(NU11, ts) + f * e11 * planck(NU11, tc)
    r12 = (1 - f * e12) * planck(NU12, ts) + f * e12 * planck(NU12, tc)
    b11, b12 = bt(NU11, r11), bt(NU12, r12)
    return b11 - ts, (b11 - b12)   # el suelo despejado tiene BTD 0 en este modelo


def tabla(titulo: str, ts: float, capas: list[tuple[str, float]]) -> None:
    print(f"\n{titulo} (suelo despejado a {ts:.0f} K)")
    print("  capa            e11   beta   f=1,00          f=0,35          f=0,15")
    print("                               dBT11   dBTD    dBT11   dBTD    dBT11   dBTD")
    for nombre, tc in capas:
        for e11 in (0.15, 0.30, 0.60, 0.95):
            for beta in (0.70, 1.00):
                fila = f"  {nombre:<14} {e11:4.2f}   {beta:4.2f}  "
                for f in (1.0, 0.35, 0.15):
                    d11, dbtd = senal(f, e11, beta, ts, tc)
                    fila += f" {d11:+6.2f} {dbtd:+6.2f}  "
                print(fila)


def main() -> None:
    capas = [("3 km (269 K)", 269.0), ("4 km (263 K)", 263.0), ("5 km (257 K)", 257.0)]
    tabla("CUMBRE, suelo frio (nieve, madrugada)", 264.0, capas)
    tabla("CUMBRE, suelo tibio (media manana despejada)", 274.0, capas)
    tabla("CUMBRE DE TARDE (BT11 de las huellas VOLCAT de tarde: 280 a 288 K, h3_resultado.txt)", 285.0, capas)
    tabla("TERRENO BAJO (bajo 1.300 m, de dia)", 290.0, capas)
    print("\nPara comparar: el fondo sin pluma de la diferencia 11 - 12 um en los pixeles de cumbre "
          "va de -0,3 a +0,4 K\n(docs/own_volcat/h23_inyeccion/INFORME.md seccion 1), y la BT11 del suelo "
          "despejado cambia varios K de un dia a otro.")
    print("f = 0,35 es una pluma de 1 km de ancho que cruza el pixel de este a oeste; "
          "f = 0,15 es una de 0,4 km (geometria_pixel.py).")


if __name__ == "__main__":
    main()
