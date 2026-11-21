"""H3: transferencia radiativa de cielo despejado por pixel (version M del criterio).

Por que asi: lo que VOLCAT compara contra la observacion es la radiancia que veria el ABI si no hubiera
nube ni ceniza. Se arma con el perfil GFS del lugar (temperatura, vapor de agua, ozono), la temperatura de
piel y la presion de superficie del GFS interpoladas al pixel (la columna se corta en esa presion), y un
calculo linea por linea (lbl.py) convolucionado con la SRF de cada banda.

Supuestos declarados:
- Capas entre los 33 niveles isobaricos del GFS (1000 a 1 hPa) mas una capa 1050-1000 hPa por si la
  superficie queda bajo 1000 hPa. Capa isoterma a la media de sus dos niveles; la capa que contiene la
  superficie se corta a la fraccion de presion (T y q en la superficie interpolados en ln p).
- Coeficientes de absorcion precalculados (LUT) en la presion media de cada capa y en una rejilla de T por
  capa, interpolados linealmente en T.
- Gases de mezcla fija (fraccion molar en aire seco, supuesto declarado): CO2 425 ppm, CH4 1,93 ppm,
  N2O 0,338 ppm. H2O y O3 del GFS.
- Camino oblicuo plano-paralelo: tau_vertical * sec(cenit satelital). Superficie lambertiana: termino
  reflejado = (1 - eps_sfc) * radiancia descendente con angulo de difusividad (sec = 1,66).
- Emisividad de superficie fija por banda (sin CAMEL, que pide cuenta): ver EMIS.
"""
import os
import numpy as np
import lbl

HERE = os.path.dirname(os.path.abspath(__file__))
# Tabla de coeficientes (lut.npz, lineas.npz): por defecto en ./lbl; H3_RT_LBL apunta a otra carpeta (C2, 21-11-2026).
# El continuo MT_CKD se busca en lbl.DL (variable H3_RT_DL).
LBL = os.environ.get("H3_RT_LBL", os.path.join(HERE, "lbl"))
G = 9.80665; NA = 6.02214076e23; MD = 28.9647e-3; MW = 18.01528e-3; MO3 = 47.9982e-3
VMR_FIJO = {2: 425e-6, 6: 1.93e-6, 4: 0.338e-6}
NCOL = {1: 3e22, 2: 9e21, 3: 8e18, 4: 7e18, 6: 4e19}   # columnas tipicas (molec/cm2) para el corte de lineas
EMIS = {10: 0.97, 11: 0.95, 14: 0.97, 15: 0.97}         # supuesto declarado, ver informe (sensibilidad)
BANDS = (10, 11, 14, 15)
LEVELS = np.array([1050.0, 1000, 975, 950, 925, 900, 850, 800, 750, 700, 650, 600, 550, 500, 450, 400, 350,
                   300, 250, 200, 150, 100, 70, 50, 40, 30, 20, 15, 10, 7, 5, 3, 2, 1])
PBOT, PTOP = LEVELS[:-1], LEVELS[1:]
PMID = 0.5 * (PBOT + PTOP)
NL = len(PMID)


def construir_lut(tmin, tmax, nT=7, out=os.path.join(LBL, "lut.npz")):
    """k por molecula (H2O, O3) y por molecula de aire seco (gases fijos), en (capa, T, nu)."""
    import hapi
    L = dict(np.load(os.path.join(LBL, "lineas.npz")))
    nu = lbl.rejilla()
    keep = np.zeros(len(L["nu"]), bool)
    for M, N in NCOL.items():
        keep |= (L["M"] == M) & (L["sw"] * N >= 1e-5)
    TG = np.stack([np.linspace(a, b, nT) for a, b in zip(tmin, tmax)])     # (NL, nT)
    ps = np.repeat(PMID, nT); Ts = TG.ravel()
    kh = lbl.kabs(nu, ps, Ts, L, keep & (L["M"] == 1), True, hapi.partitionSum).astype("float32")
    ko = lbl.kabs(nu, ps, Ts, L, keep & (L["M"] == 3), False, hapi.partitionSum).astype("float32")
    kf = np.zeros_like(kh)
    for M, v in VMR_FIJO.items():
        kf += v * lbl.kabs(nu, ps, Ts, L, keep & (L["M"] == M), False, hapi.partitionSum).astype("float32")
    np.savez(out, nu=nu, TG=TG, kh=kh.reshape(NL, nT, -1), ko=ko.reshape(NL, nT, -1),
             kf=kf.reshape(NL, nT, -1), nlin=np.array([(keep & (L["M"] == M)).sum() for M in (1, 2, 3, 4, 6)]))
    return out


class Modelo:
    def __init__(self, lut=os.path.join(LBL, "lut.npz")):
        z = np.load(lut)
        self.nu = z["nu"]; self.TG = z["TG"]; self.kh = z["kh"]; self.ko = z["ko"]; self.kf = z["kf"]
        import netCDF4
        d = netCDF4.Dataset(os.path.join(lbl.DL, "mtckd", "absco-ref_wv-mt-ckd.nc"))
        w = d["wavenumbers"][:].data
        self.c_s = np.interp(self.nu, w, d["self_absco_ref"][:].data)
        self.c_f = np.interp(self.nu, w, d["for_absco_ref"][:].data)
        self.c_x = np.interp(self.nu, w, d["self_texp"][:].data)
        self.P0 = float(d["ref_press"][...]); self.T0 = float(d["ref_temp"][...]); d.close()
        self.srf = {b: lbl.srf(b, self.nu) for b in BANDS}

    def _k(self, arr, l, T):
        tg = self.TG[l]
        if T < tg[0] or T > tg[-1]:
            self.recortes = getattr(self, "recortes", 0) + 1
        T = np.clip(T, tg[0], tg[-1])
        j = min(int(np.searchsorted(tg, T)) - 1, len(tg) - 2); j = max(j, 0)
        w = (T - tg[j]) / (tg[j + 1] - tg[j])
        return (1 - w) * arr[l, j] + w * arr[l, j + 1]

    def capas(self, plev, T, q, o3, psfc):
        """Perfil GFS (niveles 1000..1 hPa) -> capas recortadas en psfc: (indices, T capa, W_h2o, N_seco, W_o3, p)."""
        lp = np.log(plev)
        f = lambda x, p: np.interp(np.log(p), lp[::-1], x[::-1])   # noqa: E731
        Pl = LEVELS.copy()
        Tl = f(T, Pl); ql = f(q, Pl); ol = f(o3, Pl)                   # 1050 -> extrapolacion constante
        res = []
        for l in range(NL):
            pb, pt = PBOT[l], PTOP[l]
            if pt >= psfc:
                continue
            if pb > psfc:
                pb = psfc; tb, qb, ob = f(T, psfc), f(q, psfc), f(o3, psfc)
            else:
                tb, qb, ob = Tl[l], ql[l], ol[l]
            tt, qq, oo = 0.5 * (tb + Tl[l + 1]), 0.5 * (qb + ql[l + 1]), 0.5 * (ob + ol[l + 1])
            dp = (pb - pt) * 100.0
            n_seco = dp * (1 - qq) / (G * MD / NA) / 1e4      # molec/cm2
            w = dp * qq / (G * MW / NA) / 1e4
            wo = dp * oo / (G * MO3 / NA) / 1e4
            res.append((l, tt, w, n_seco, wo, 0.5 * (pb + pt)))
        return res

    def tau_capas(self, capas):
        out = []
        for l, tt, w, ns, wo, pm in capas:
            vmr = w / (w + ns)
            rho = (pm / self.P0) * (self.T0 / tt)
            x = self.nu * lbl.C2 / tt
            rad = self.nu * (1 - np.exp(-x)) / (1 + np.exp(-x))
            kc = (self.c_s * (self.T0 / tt) ** self.c_x * vmr + self.c_f * (1 - vmr)) * rho * rad
            tau = (self._k(self.kh, l, tt) + kc) * w + self._k(self.kf, l, tt) * ns + self._k(self.ko, l, tt) * wo
            out.append((tau, tt))
        return out   # de abajo hacia arriba

    def radiancia(self, plev, T, q, o3, psfc, tskin, sec, emis=EMIS):
        """Radiancias de banda (mW m-2 sr-1 (cm-1)-1) de cielo despejado al tope, para C10, C11, C14, C15."""
        tc = self.tau_capas(self.capas(plev, T, q, o3, psfc))
        # hacia arriba (camino oblicuo): transmitancia desde la base de cada capa al tope
        tau_up = np.cumsum([t for t, _ in tc][::-1], axis=0)[::-1] * sec       # tau del tope a la base de capa
        tr_base = np.exp(-tau_up)
        tr_top = np.vstack([tr_base[1:], np.ones((1, len(self.nu)))])
        Bl = lbl.planck(self.nu, np.array([tt for _, tt in tc]))
        L_atm = (Bl * (tr_top - tr_base)).sum(0)
        tr_sfc = tr_base[0]
        # descendente difusa al nivel de superficie
        td = np.cumsum([t for t, _ in tc], axis=0) * 1.66      # tau desde la superficie hasta el tope de capa
        tr_dtop = np.exp(-td); tr_dbase = np.vstack([np.ones((1, len(self.nu))), tr_dtop[:-1]])
        L_down = (Bl * (tr_dbase - tr_dtop)).sum(0)
        Bs = lbl.planck(self.nu, np.array(tskin))
        out = {}
        for b in BANDS:
            e = emis[b]
            Lnu = L_atm + tr_sfc * (e * Bs + (1 - e) * L_down)
            s = self.srf[b]
            out[b] = float((s * Lnu).sum() / s.sum())
        return out


def bt_de_rad(R, co):
    fk1, fk2, bc1, bc2 = co
    return (fk2 / np.log(fk1 / np.asarray(R) + 1) - bc1) / bc2


def rad_de_bt(T, co):
    fk1, fk2, bc1, bc2 = co
    return fk1 / np.expm1(fk2 / (bc1 + bc2 * np.asarray(T, float)))


def cenit_satelital(lat, lon, sat_lon=-75.0, H=35786.023, R=6371.0):  # sat_lon y H del atributo goes_imager_projection del L1b
    la, lo, ls = np.radians(lat), np.radians(lon), np.radians(sat_lon)
    P = R * np.stack([np.cos(la) * np.cos(lo), np.cos(la) * np.sin(lo), np.sin(la)])
    S = (R + H) * np.array([np.cos(ls), np.sin(ls), 0.0]).reshape(3, *([1] * np.ndim(lat)))
    v = S - P
    c = (P * v).sum(0) / (np.linalg.norm(P, axis=0) * np.linalg.norm(v, axis=0))
    return np.degrees(np.arccos(c))
