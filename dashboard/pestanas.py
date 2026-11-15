"""Pestañas que sólo ejecutan lo que se está mirando.

QUÉ: un `st.tabs` con estado y un `visible(pestaña)` para saltar el contenido
de las pestañas ocultas.

POR QUÉ: por defecto `st.tabs` no difiere nada. Todas las pestañas corren en
cada rerun y sus fragments con `run_every` siguen refrescando aunque nadie las
vea. Medido en nov-2026 en Modo Guardia: los seis sub-tabs refrescaban mapas,
mosaico de 15 celdas y VOLCAT cada minuto, con ~850 peticiones por ciclo de
10 min; con sólo la pestaña visible el régimen bajaba a 11 peticiones y 0
tiles. El costo es que cambiar de pestaña ahora pide un rerun al servidor (la
pestaña nueva tarda lo que tarda su primera carga), a cambio de que lo que no
se mira no consuma red ni CPU.

LA ELECCIÓN SE GUARDA APARTE, por dos razones medidas:

1. Defecto de Streamlit 1.56: un `st.rerun(scope="app")` llamado desde un
   fragment corre con las pestañas con estado VUELTAS a la primera. Vista
   Operacional lo hace en `_health_banner` con cada scan nuevo, así que el
   turno que miraba "Volcán" caía a "Nacional" cada 10 minutos, o veía la
   pestaña elegida en blanco (el navegador la mostraba elegida y el servidor
   corría otra). Reproducido en una app mínima: sin memoria, cada rerun del
   fragment perdía la pestaña; con memoria, 0 de 30.
2. Pestañas ANIDADAS: si la madre está oculta, las hijas ni se crean y
   Streamlit olvida cuál estaba elegida. El turno que dejó "Ash RGB" abierto
   en Nacional lo encuentra igual al volver de Zona.

La memoria es una clave de `session_state` que NO es de widget (sobrevive a
que el widget no se cree), escrita por el callback del clic, y vuelve como
`default`.
"""
from __future__ import annotations

from typing import Sequence

import streamlit as st


def _clave_memoria(key: str) -> str:
    return f"_pestana_elegida_{key}"


def pestanas_perezosas(etiquetas: Sequence[str], key: str):
    """`st.tabs` con estado: cada pestaña trae `.open` True/False.

    Usar siempre con `visible()` al entrar a cada pestaña; sin esa guardia la
    pestaña oculta corre igual y sólo se agrega un rerun por clic.
    """
    etiquetas = list(etiquetas)
    memoria = _clave_memoria(key)

    def _guardar():
        valor = st.session_state.get(key)
        if valor in etiquetas:
            st.session_state[memoria] = valor

    default = st.session_state.get(memoria)
    if default not in etiquetas:
        # Rótulo que cambió (o nada guardado): Streamlit lanza excepción con
        # un default que no está en la lista; se vuelve a la primera.
        default = None
    return st.tabs(etiquetas, key=key, on_change=_guardar, default=default)


def visible(pestana) -> bool:
    """¿Hay que ejecutar el contenido de esta pestaña?

    `.open` es True/False sólo si las pestañas llevan estado. Si viene None
    (pestañas sin estado), se ejecuta: ante la duda se muestra, nunca se
    esconde contenido por error.
    """
    return getattr(pestana, "open", None) is not False
