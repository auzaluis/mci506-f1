# Paso 3: Funciones utilitarias
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent
RAW_DIR = ROOT / "data/raw"
CACHE_DIR = ROOT / "data/cache"


def slug(text: str) -> str:
    """Convierte un nombre de evento en algo apto para un nombre de archivo."""
    return "_".join(str(text).split())


def to_parquet(df: pd.DataFrame, path: Path) -> None:
    """Guarda un DataFrame en parquet (descartando subclases de FastF1)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(df).to_parquet(path, index=False)
    print(f"  guardado: {path}  ({len(df)} filas)")