"""Caché en memoria para objetos remotos INMUTABLES: tiles RAMMB y gránulos FDCF.

QUÉ: guarda los bytes crudos de un objeto remoto bajo una clave que lo
identifica para siempre, y los devuelve sin salir a la red mientras quepan en
el techo de memoria. Si dos hilos piden la misma clave a la vez, baja uno solo
y el otro espera ese resultado.

POR QUÉ: un scan GOES-19 Full Disk se publica una vez y no cambia. La URL de un
tile RAMMB lleva el timestamp del scan; la key S3 de un FDCF lleva el inicio del
scan en el nombre. Volver a bajarlos no trae información nueva. Medido en
nov-2026, sin este caché Modo Guardia hacía ~850 peticiones por ciclo de 10 min
y Modo Sala bajaba el mismo FDCF una vez por zona y otra por volcán.

QUÉ NO GUARDA, a propósito: las fallas. Si `bajar()` devuelve None (404, error
de red, cuerpo vacío) no se memoriza nada y el próximo pedido vuelve a
intentar. Memorizar una falla convertiría un tropiezo de RAMMB o S3 en un panel
congelado en el scan anterior durante toda la vida del caché: ausencia de dato
presentada como si fuera el dato.

Vive a nivel de proceso (no `st.cache_data`) porque lo usan `src/fetch`, que no
depende de Streamlit, y los hilos del productor de la sala. Es compartido entre
sesiones, igual que `st.cache_data`.
"""
from __future__ import annotations

import threading
from collections import OrderedDict
from typing import Callable, Hashable, Optional

_REGISTRO: list["CacheInmutable"] = []


class CacheInmutable:
    """LRU por bytes con deduplicación de descargas simultáneas."""

    def __init__(self, nombre: str, max_bytes: int):
        self.nombre = nombre
        self.max_bytes = int(max_bytes)
        self._datos: "OrderedDict[Hashable, bytes]" = OrderedDict()
        self._bytes = 0
        self._lock = threading.Lock()
        # Un lock por clave EN VUELO: el segundo hilo espera al primero en vez
        # de bajar lo mismo en paralelo (productor de sala + fragment en frío).
        self._en_vuelo: dict[Hashable, threading.Lock] = {}
        self._aciertos = 0
        self._descargas = 0
        _REGISTRO.append(self)

    def obtener(self, clave: Hashable,
                bajar: Callable[[], Optional[bytes]]) -> Optional[bytes]:
        """Bytes de `clave`; si no están, llama a `bajar()` una sola vez."""
        with self._lock:
            if clave in self._datos:
                self._datos.move_to_end(clave)
                self._aciertos += 1
                return self._datos[clave]
            lock_clave = self._en_vuelo.setdefault(clave, threading.Lock())
        with lock_clave:
            # Otro hilo pudo haberlo bajado mientras esperábamos el lock.
            with self._lock:
                if clave in self._datos:
                    self._datos.move_to_end(clave)
                    self._aciertos += 1
                    return self._datos[clave]
            try:
                datos = bajar()
                with self._lock:
                    self._descargas += 1
                    if datos:  # None o b"" = falla: no se memoriza
                        self._guardar(clave, datos)
                return datos
            finally:
                with self._lock:
                    self._en_vuelo.pop(clave, None)

    def _guardar(self, clave: Hashable, datos: bytes) -> None:
        if len(datos) > self.max_bytes:
            return  # no cabe ni solo: no desalojar todo por un objeto
        self._datos[clave] = datos
        self._bytes += len(datos)
        while self._bytes > self.max_bytes:
            _, viejo = self._datos.popitem(last=False)
            self._bytes -= len(viejo)

    def limpiar(self) -> None:
        with self._lock:
            self._datos.clear()
            self._bytes = 0
            self._aciertos = 0
            self._descargas = 0

    def stats(self) -> dict:
        with self._lock:
            return {"nombre": self.nombre, "entradas": len(self._datos),
                    "bytes": self._bytes, "aciertos": self._aciertos,
                    "descargas": self._descargas}


def limpiar_todas() -> None:
    """Vacía todos los cachés del proceso (las pruebas parten en frío)."""
    for c in _REGISTRO:
        c.limpiar()
