r"""V308: qué protege la guarda de `estat_2026.npy` (`hashlib.sha256(estat.tobytes()).hexdigest()[:16] == SHA`).

Todo sobre COPIAS en D:\goes_notas\s28\s28b\v301\mut (el original sólo se lee).
  0. Los dos hashes del original: el del archivo (lo que da `sha256sum`) y el del arreglo (`tobytes`).
  1. Mutación de un elemento: la guarda tiene que fallar (línea base roja del instrumento).
  2. Mismos bytes con otro dtype (uint8): ¿pasa la guarda? ¿cambia la nube dinámica de un cuadro real ya visto?
  3. Mismos bytes con otra forma (7802 x 144): ¿pasa la guarda? ¿el código falla con ruido después?

Uso: python -I -B v308_hash.py
"""
import hashlib
import os
import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
V = r"D:\goes_notas\s28\s28b\v301"
ORIG = r"D:\goes_notas\s23\s23b\estat_2026.npy"
MUT = os.path.join(V, "mut")
SHA = "e0f093eb6e441cc4"
sys.path.insert(0, os.path.join(V, "repo", "docs", "own_volcat", "s22b_pluma_vs_nubes", "scripts"))


def guarda(fn):
    e = np.load(fn)
    return hashlib.sha256(e.tobytes()).hexdigest()[:16] == SHA, e


def main():
    os.makedirs(MUT, exist_ok=True)
    b = open(ORIG, "rb").read()
    e = np.load(ORIG)
    print("0. original:", e.shape, e.dtype, "suma", int(e.sum()))
    print("   sha256 del archivo :", hashlib.sha256(b).hexdigest())
    print("   sha256 de tobytes():", hashlib.sha256(e.tobytes()).hexdigest())
    print("   declarado (16 hex) :", SHA, "| coincide con archivo:", hashlib.sha256(b).hexdigest()[:16] == SHA,
          "| con tobytes:", hashlib.sha256(e.tobytes()).hexdigest()[:16] == SHA)
    # 1
    m = e.copy()
    m[0, 0] = ~m[0, 0]
    np.save(os.path.join(MUT, "estat_un_elemento.npy"), m)
    print("1. un elemento cambiado: guarda pasa =", guarda(os.path.join(MUT, "estat_un_elemento.npy"))[0])
    # 2
    np.save(os.path.join(MUT, "estat_uint8.npy"), e.view(np.uint8))
    ok, u = guarda(os.path.join(MUT, "estat_uint8.npy"))
    print("2. mismos bytes como uint8: guarda pasa =", ok, "| dtype", u.dtype, "| sha del archivo",
          hashlib.sha256(open(os.path.join(MUT, "estat_uint8.npy"), "rb").read()).hexdigest()[:16])
    import s22b_medir as B
    M = B.M
    dif = n = 0
    for nom in ("20261108_1800", "20261108_0600", "20261110_2000", "20261111_1200"):
        a = np.load(os.path.join(V, "trab_base", "acm", nom + ".npz"))["acm"].ravel()
        s = M.slot(f"{nom[9:11]}:{nom[11:13]}")
        nd_b, nd_u = B.dinamica(a, e[s]), B.dinamica(a, u[s])
        igual = (np.array_equal(nd_b.astype(bool), nd_u.astype(bool))
                 and np.array_equal(B.borde(nd_b), B.borde(nd_u)) and nd_b[M.AP].mean() == nd_u[M.AP].mean())
        n += 1
        dif += not igual
    print(f"   nube dinámica, borde y fracción del anillo con uint8 contra bool: {n - dif} de {n} cuadros iguales")
    # 3
    np.save(os.path.join(MUT, "estat_otra_forma.npy"), e.reshape(e.shape[1], e.shape[0]))
    ok, r = guarda(os.path.join(MUT, "estat_otra_forma.npy"))
    print("3. mismos bytes con forma", r.shape, ": guarda pasa =", ok)
    try:
        a = np.load(os.path.join(V, "trab_base", "acm", "20261108_1800.npz"))["acm"].ravel()
        B.dinamica(a, r[M.slot("18:00")])
        print("   el código sigue sin error (malo)")
    except Exception as x:  # noqa: BLE001
        print("   el código falla después con ruido:", repr(x)[:120])


if __name__ == "__main__":
    main()
