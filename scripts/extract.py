# Paso 4: Script de extracción de datos
"""Módulo de extracción de datos de FastF1.

Descarga y guarda en formato parquet:
- El calendario (schedule) de la temporada.
- Para los primeros rounds del calendario: resultados y vueltas (laps) de la
  sesión indicada, agregando las columnas ``year`` y ``EventName`` a cada df.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import fastf1
import pandas as pd

from utils import CACHE_DIR, DEV_MODE, RAW_DIR, slug, to_parquet

# --- Configuración --------------------------------------------------------
YEAR = 2026
ROUNDS = [1, 2, 3]
SESSION = "R"


def extract_schedule(year: int) -> pd.DataFrame:
    print(f"[schedule] Descargando schedule {year}...")
    schedule = fastf1.get_event_schedule(year)
    if DEV_MODE:
        schedule = schedule.head(10)
        print(f"[schedule] DEV MODE — limitado a 10 filas")
    to_parquet(schedule, RAW_DIR / f"schedule_{year}.parquet")
    print(f"[schedule] OK — {len(schedule)} eventos")
    return schedule


def extract_session(year: int, round_number: int, session_id: str = SESSION) -> None:
    print(f"[round {round_number}] Cargando sesión {session_id}...")
    session = fastf1.get_session(year, round_number, session_id)
    session.load(telemetry=False, weather=False, messages=False)

    event_name = session.event["EventName"]

    results = pd.DataFrame(session.results)
    results["year"] = year
    results["EventName"] = event_name
    if DEV_MODE:
        results = results.head(10)
    to_parquet(results, RAW_DIR / f"results_{year}_{slug(event_name)}.parquet")

    try:
        laps = pd.DataFrame(session.laps)
        laps["year"] = year
        laps["EventName"] = event_name
        if DEV_MODE:
            laps = laps.head(10)
        to_parquet(laps, RAW_DIR / f"laps_{year}_{slug(event_name)}.parquet")
        laps_count = len(laps)
    except Exception as e:
        print(f"[round {round_number}] WARNING — laps no disponibles: {e}")
        laps_count = 0

    if DEV_MODE:
        print(f"[round {round_number}] DEV MODE — limitado a 10 filas")
    print(f"[round {round_number}] OK — {event_name}: {len(results)} resultados, {laps_count} vueltas")


def main() -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    fastf1.Cache.enable_cache(CACHE_DIR)

    extract_schedule(YEAR)
    for round_number in ROUNDS:
        extract_session(YEAR, round_number, SESSION)

    print("\nExtracción completada.")


if __name__ == "__main__":
    main()