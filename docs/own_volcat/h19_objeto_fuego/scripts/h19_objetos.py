"""H19: tabla por objeto (geocatASHOBJ y geocatICEOBJ) con los atributos candidatos a predecir la
pertenencia al grupo de alerta. Funcion comun para exploracion y validacion."""
import numpy as np
from h19_comun import f, PIX, TRK, VCB


def tabla_objetos(d, pre, idk):
    """pre: 'A__' o 'I__'; idk: 'idA' o 'idI'. Devuelve dict de arreglos por objeto."""
    n = len(d[pre + "Object_Id"])
    ido = d[idk]
    ok = ido >= 0
    cnt = np.bincount(ido[ok], minlength=n).astype(float)

    def frac(m):
        return np.bincount(ido[ok], weights=m[ok].astype(float), minlength=n) / np.maximum(cnt, 1)

    ig = d["p__Ice_Group_Id_2d"] > 0
    ag = d["p__Ash_Group_Id_2d"] > 0
    eps = f(d, PIX + "cloud_emissivity_ch14_tot")
    t = {
        "n": cnt,
        "sel": (d[pre + "Mask"] > 0),
        "grupo": d[pre + "Group_Id"],
        "frac_ig": frac(ig),            # solapamiento con el grupo de nube convectiva volcanica actual
        "frac_ag": frac(ag),
        "frac_prev_ag": frac(d["prev__ag"]) if "prev__ag" in d else np.zeros(n),
        "frac_prev_ig": frac(d["prev__ig"]) if "prev__ig" in d else np.zeros(n),
        "frac_Pir_alta": frac(np.nan_to_num(f(d, PIX + "ash_probability_IR"), nan=0) >= 0.5),
        "frac_eps90": frac(np.nan_to_num(eps, nan=0) >= 0.9),
        "frac_iom": frac(d[VCB + "Ice_Object_Mask"] > 0),
        "frac_count_in_ash": frac(np.nan_to_num(f(d, TRK + "count_in_ash"), nan=0) > 0),
    }
    aom = d[PIX + "Ash_Object_Mask"]
    for c in (1, 2, 3, 4, 5, 6, 7):
        t["frac_aom%d" % c] = frac(aom == c)
    for k in ("Feature_Prob", "Feature_Prob_IR", "Feature_Prob_Loose", "Probability_Mean", "Probability_Median",
              "Probability_Subset_Median", "Emiss14_Tot_Median", "Group_Id_Prev_Match", "Object_Id_Match",
              "Time_Trend_Count", "Spectral_Time_Trend_Count", "Robust_Count_L1", "Robust_Count_L4",
              "Dark_Pixel_Count", "Growth_Rate_Anom_Bt14", "Growth_Rate_Anom_Emiss14_Tot", "Cmask", "Status",
              "Total_Area", "Bt14_Min", "Max_Height", "High_Cloud_Count", "Robust_Neighbor_Count",
              "Latitude_Radiative_Center", "Longitude_Radiative_Center", "New_Emission_Count",
              "Btd_Bullseye_Count", "Coherent_Btd_Time_Trend", "Local_Prob_Max_Pixel_Count"):
        if pre + k in d:
            a = d[pre + k].astype(float)
            a[a <= -900] = np.nan
            t[k] = a
    return t
