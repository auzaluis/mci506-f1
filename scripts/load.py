"""Sube los parquet de data/raw/ a GCS.

Estructura en el bucket:
  {RAW_PREFIX}/{dataset}/year={year}/{filename}.parquet

Requiere la variable de entorno GCP_SA_KEY con el JSON de la service account.
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

from utils import GCS_BUCKET, RAW_DIR, RAW_PREFIX, gcs_client

load_dotenv()

# Patrón: {dataset}_{year}_{slug}.parquet  o  {dataset}_{year}.parquet
_FILENAME_RE = re.compile(r"^(?P<dataset>[a-z]+)_(?P<year>\d{4})")


def _gcs_path(filename: str) -> str:
    """Extrae dataset y year del nombre de archivo y arma el path Hive-style.

    Ejemplo: results_2026_Bahrain.parquet → raw/results/year=2026/results_2026_Bahrain.parquet
    """
    m = _FILENAME_RE.match(filename)
    if not m:
        raise ValueError(f"Nombre de archivo inesperado: {filename}")
    dataset = m.group("dataset")
    year = m.group("year")
    return f"{RAW_PREFIX}/{dataset}/year={year}/{filename}"


def upload_raw() -> None:
    """Sube todos los parquets de data/raw/ a GCS con prefijos Hive-style.

    Sobrescribe los archivos si ya existen (para capturar correcciones en FastF1).
    """
    parquets = sorted(RAW_DIR.glob("*.parquet"))
    if not parquets:
        print("No hay archivos parquet en data/raw/")
        return

    client = gcs_client()
    bucket = client.bucket(GCS_BUCKET)

    for path in parquets:
        gcs_path = _gcs_path(path.name)
        blob = bucket.blob(gcs_path)
        blob.upload_from_filename(str(path))
        print(f"  subido: gs://{GCS_BUCKET}/{gcs_path}")

    print(f"\n{len(parquets)} archivo(s) subido(s).")


if __name__ == "__main__":
    upload_raw()
