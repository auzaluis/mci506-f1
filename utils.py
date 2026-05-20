import json
import os
import subprocess
from pathlib import Path

import pandas as pd
from google.cloud import storage
from google.oauth2 import service_account

ROOT = Path(__file__).resolve().parent
RAW_DIR = ROOT / "data/raw"
CACHE_DIR = ROOT / "data/cache"

GCS_BUCKET = "mci506-f1-analysis"


def _is_dev_mode() -> bool:
    """Detecta si estamos en dev: rama distinta a main, o env var DEV_MODE=true."""
    if os.environ.get("DEV_MODE") == "true":
        return True
    try:
        branch = subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=ROOT, text=True
        ).strip()
        return branch != "main"
    except Exception:
        return False


DEV_MODE = _is_dev_mode()
RAW_PREFIX = "dev_raw" if DEV_MODE else "raw"


def slug(text: str) -> str:
    """Convierte un nombre de evento en algo apto para un nombre de archivo."""
    return "_".join(str(text).split())


def to_parquet(df: pd.DataFrame, path: Path) -> None:
    """Guarda un DataFrame en parquet (descartando subclases de FastF1)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(df).to_parquet(path, index=False)
    print(f"  guardado: {path}  ({len(df)} filas)")


def gcs_client() -> storage.Client:
    """Autentica y retorna un cliente de Google Cloud Storage.

    Lee la service account del JSON en la variable de entorno GCP_SA_KEY.
    Reutilizable para cualquier operación en GCS (upload, download, etc.).
    """
    sa_key = os.environ.get("GCP_SA_KEY")
    if not sa_key:
        raise EnvironmentError("GCP_SA_KEY no está definida")
    info = json.loads(sa_key)
    creds = service_account.Credentials.from_service_account_info(
        info, scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )
    return storage.Client(credentials=creds, project=info["project_id"])