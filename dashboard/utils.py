"""Utilidades de tiempo y formato para el dashboard.

Manejo de zonas horarias:
  UTC → America/Santiago (CLT/CLST)
  - Invierno (abril-septiembre): UTC-4 (CLT)
  - Verano (octubre-marzo):      UTC-3 (CLST)
  La conversion es automatica via zoneinfo.
"""

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

CHILE_TZ = ZoneInfo("America/Santiago")


def now_utc() -> datetime:
    """Datetime actual en UTC."""
    return datetime.now(timezone.utc)


def utc_to_chile(dt: datetime) -> datetime:
    """Convertir datetime UTC a hora local de Chile."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(CHILE_TZ)


def fmt_utc(dt: datetime) -> str:
    """Formato legible solo UTC: '2026-04-15 14:30 UTC'"""
    return dt.strftime("%Y-%m-%d %H:%M UTC")


def fmt_chile(dt: datetime) -> str:
    """Formato hora local Chile: '10:30 CLT'"""
    dt_ch = utc_to_chile(dt)
    tz_name = dt_ch.strftime("%Z")   # CLT o CLST segun temporada
    return dt_ch.strftime(f"%H:%M {tz_name}")


def fmt_both(dt: datetime) -> str:
    """UTC + hora local: '14:30 UTC (10:30 CLT)'"""
    utc_str = dt.strftime("%H:%M UTC")
    ch_str = fmt_chile(dt)
    return f"{utc_str}  ({ch_str})"


def fmt_both_long(dt: datetime) -> str:
    """Version larga con fecha: '2026-04-15 14:30 UTC (10:30 CLT)'"""
    utc_str = dt.strftime("%Y-%m-%d %H:%M UTC")
    ch_str = fmt_chile(dt)
    return f"{utc_str}  ({ch_str})"


def parse_rammb_ts(ts: str) -> datetime:
    """Convertir timestamp RAMMB (14 digitos YYYYMMDDHHmmss) a datetime UTC."""
    return datetime(
        int(ts[:4]), int(ts[4:6]), int(ts[6:8]),
        int(ts[8:10]), int(ts[10:12]), int(ts[12:14]),
        tzinfo=timezone.utc,
    )


def ts14_to_display(ts: str) -> str:
    """Timestamp 14 digitos → 'HH:MM UTC (HH:MM CLT)'"""
    dt = parse_rammb_ts(ts)
    return fmt_both(dt)


def ts14_to_display_long(ts: str) -> str:
    """Timestamp 14 digitos → 'YYYY-MM-DD HH:MM UTC (HH:MM CLT)'"""
    dt = parse_rammb_ts(ts)
    return fmt_both_long(dt)
