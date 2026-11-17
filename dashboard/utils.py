"""Utilidades de tiempo y formato para el dashboard.

Manejo de zonas horarias:
  UTC -> America/Santiago, conversion automatica via zoneinfo.
  - Invierno: UTC-4
  - Verano:   UTC-3
  (Las fechas de cambio las fija decreto y se han movido; la base tz las sigue.)

Por que el desfase va en numeros y no como sigla: la base tz de IANA saco en
2017 las siglas CLT/CLST de America/Santiago, asi que el codigo de zona de
strftime imprime "-03". En pantalla eso quedaba "10:10 -03", que nadie lee
como hora de Chile.
El rotulo es "10:10 Chile (UTC-3)": dice de donde es la hora y cuanto se
separa de UTC, que es lo que se compara contra la hora del scan.
"""

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

CHILE_TZ = ZoneInfo("America/Santiago")


def now_utc() -> datetime:
    """Datetime actual en UTC."""
    return datetime.now(timezone.utc)


def _a_utc(dt: datetime) -> datetime:
    """Datetime en UTC; uno sin zona se lee como UTC (asi vienen de RAMMB)."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def utc_to_chile(dt: datetime) -> datetime:
    """Convertir datetime UTC a hora local de Chile."""
    return _a_utc(dt).astimezone(CHILE_TZ)


def fmt_utc(dt: datetime) -> str:
    """Formato legible solo UTC: '2026-04-15 14:30 UTC'"""
    return dt.strftime("%Y-%m-%d %H:%M UTC")


def desfase_chile(dt: datetime) -> str:
    """Desfase de Chile respecto de UTC en esa fecha: 'UTC-3' o 'UTC-4'."""
    off_h = int(utc_to_chile(dt).utcoffset().total_seconds() // 3600)
    return f"UTC{off_h:+d}"


def fmt_chile(dt: datetime) -> str:
    """Hora local de Chile con su desfase: '10:10 Chile (UTC-3)'.

    Solo HH:MM: quien necesite la fecha usa fmt_both_long, que la agrega
    cuando el dia local no es el dia UTC.
    """
    return f"{utc_to_chile(dt):%H:%M} Chile ({desfase_chile(dt)})"


def fmt_both(dt: datetime) -> str:
    """UTC + hora local: '13:10 UTC · 10:10 Chile (UTC-3)'."""
    return f"{_a_utc(dt):%H:%M} UTC · {fmt_chile(dt)}"


def fmt_both_long(dt: datetime) -> str:
    """Con fecha: '2026-11-15 13:10 UTC · 10:10 Chile (UTC-3)'.

    De 21 a 24 h en Chile ya es el dia siguiente en UTC; ahi la hora local
    lleva su propia fecha ('2026-11-16 01:10 UTC · 2026-11-15 22:10 Chile
    (UTC-3)'), porque una hora sin fecha al lado de otra fecha se lee mal.
    """
    dt = _a_utc(dt)
    local = utc_to_chile(dt)
    hora_local = (f"{local:%H:%M}" if local.date() == dt.date()
                  else f"{local:%Y-%m-%d %H:%M}")
    return (f"{dt:%Y-%m-%d %H:%M} UTC · "
            f"{hora_local} Chile ({desfase_chile(dt)})")


def parse_rammb_ts(ts: str) -> datetime:
    """Convertir timestamp RAMMB (14 digitos YYYYMMDDHHmmss) a datetime UTC."""
    return datetime(
        int(ts[:4]), int(ts[4:6]), int(ts[6:8]),
        int(ts[8:10]), int(ts[10:12]), int(ts[12:14]),
        tzinfo=timezone.utc,
    )


def ts14_to_display(ts: str) -> str:
    """Timestamp 14 digitos -> 'HH:MM UTC · HH:MM Chile (UTC-3)'"""
    dt = parse_rammb_ts(ts)
    return fmt_both(dt)


def ts14_to_display_long(ts: str) -> str:
    """Timestamp 14 digitos -> 'YYYY-MM-DD HH:MM UTC · HH:MM Chile (UTC-3)'"""
    dt = parse_rammb_ts(ts)
    return fmt_both_long(dt)
