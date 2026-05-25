# MCI506 - F1 Data Pipeline

Un pipeline de **Ingeniería de Datos** para la extracción, transformación y carga de datos de Fórmula 1 hacia Google Cloud Storage (GCS). Diseñado como proyecto educativo para la asignatura MCI506 en la Universidad Católica Boliviana.

## 📊 Descripción General

Este proyecto implementa un pipeline **ELT (Extract-Load-Transform)** completamente automatizado que:

- **Extrae** datos históricos y actuales de carreras de Fórmula 1 usando la API de [FastF1](https://docs.fastf1.dev/)
- **Carga** los datos en formato Parquet hacia Google Cloud Storage con particionamiento Hive
- **Automatiza** el proceso mediante GitHub Actions con soporte para desarrollo local y producción
- **Analiza** los datos mediante notebooks Jupyter

### Datos Disponibles

El pipeline captura múltiples tipos de datos para cada carrera:

| Tipo | Descripción |
|------|-------------|
| **schedule** | Calendario de la temporada con fechas y ubicaciones de eventos |
| **results** | Resultados finales: posiciones, puntos, tiempo total por piloto |
| **laps** | Datos detallados por vuelta: tiempos de sector, estado de pits, posición, etc. |

**Temporadas cubiertas:** 2025, 2026  
**Rounds extraídos:** 3 primeras carreras de cada temporada

---

## 🏗️ Arquitectura

```
mci506-f1/
├── scripts/                    # Scripts principales del pipeline
│   ├── extract.py             # Extrae datos de FastF1 → data/raw/*.parquet
│   └── load.py                # Carga parquets → Google Cloud Storage
├── utils.py                   # Funciones compartidas (GCS, paths, slugs)
├── notebook.ipynb             # Análisis exploratorio de datos
├── data/
│   ├── raw/                   # Parquets descargados (no versionado)
│   └── cache/                 # Cache local de FastF1 (acelera recargas)
├── .github/
│   └── workflows/
│       └── pipeline.yml       # CI/CD automatizado con GitHub Actions
└── README.md                  # Este archivo
```

### Flujo de Datos

```
FastF1 API
    ↓
extract.py → Parquet files (data/raw/)
    ↓
load.py → Google Cloud Storage
    ↓
gs://mci506-f1-analysis/
  ├── raw/
  │   ├── schedule/year={year}/
  │   ├── results/year={year}/eventname={eventname}/
  │   └── laps/year={year}/eventname={eventname}/
  └── dev_raw/ (en branches que no sean main)
```

---

## 📋 Esquema de Datos

### Schedule
Calendario de eventos de la temporada.

```
schedule_{year}.parquet
├── Date              → Fecha del evento
├── EventName         → Nombre del Gran Premio
├── Location          → Ubicación (país/ciudad)
├── Country           → País
├── Circuit           → Nombre del circuito
└── ... (otras columnas de FastF1)
```

### Results
Resultados finales de cada carrera.

```
results_{year}_{event_slug}.parquet
├── Driver            → Código de piloto (3 letras: VER, HAM, etc.)
├── DriverNumber      → Número de dorsal
├── Position          → Posición final (1-20)
├── Points            → Puntos obtenidos
├── Time              → Tiempo total de carrera
├── Status            → Estado (Finished, DNF, etc.)
├── year              → [AÑADIDO] Año de la carrera
├── EventName         → [AÑADIDO] Nombre del evento
└── ... (otras columnas de FastF1)
```

### Laps
Datos granulares por vuelta de cada piloto.

```
laps_{year}_{event_slug}.parquet
├── Driver            → Código de piloto
├── DriverNumber      → Número de dorsal
├── LapNumber         → Número de vuelta
├── LapTime           → Tiempo de vuelta completo
├── Sector1Time       → Tiempo Sector 1
├── Sector2Time       → Tiempo Sector 2
├── Sector3Time       → Tiempo Sector 3
├── Stint             → Número de parada en pits
├── PitOutTime        → Hora salida de pits (NaT si no paró)
├── PitInTime         → Hora entrada a pits
├── TrackStatus       → Estado de pista (1=green, 4=yellow, 124=red, etc.)
├── Position          → Posición en esa vuelta
├── year              → [AÑADIDO] Año de la carrera
├── EventName         → [AÑADIDO] Nombre del evento
└── ... (otras columnas de FastF1)
```

---

## 🚀 Guía de Instalación

### Requisitos Previos

- **Python 3.13+**
- **Git**
- Acceso a Google Cloud Platform (para cargar datos)

### 1. Clonar el repositorio

```bash
git clone https://github.com/auzaluis/mci506-f1.git
cd mci506-f1
```

### 2. Crear entorno virtual

```bash
# En Windows (PowerShell)
python -m venv venv
.\venv\Scripts\Activate.ps1

# En macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

Las dependencias principales son:
- **fastf1**: API para datos de F1
- **pandas**: Manipulación de datos
- **google-cloud-storage**: Cliente de GCS
- **python-dotenv**: Gestión de variables de entorno

### 4. Configurar credenciales GCP (opcional)

Para cargar datos a Google Cloud Storage:

1. Descarga el JSON de tu service account desde [Google Cloud Console](https://console.cloud.google.com/iam-admin/serviceaccounts)
2. Crea un archivo `.env` en la raíz del proyecto:

```env
GCP_SA_KEY='{"type": "service_account", "project_id": "...", ...}'
```

---

## 📝 Uso

### Extracción de Datos

```bash
python scripts/extract.py
```

**Qué hace:**
- Descarga el calendario de las temporadas 2025 y 2026
- Para los 3 primeros rounds de cada año:
  - Descarga resultados y vueltas de la sesión de carrera (SESSION = "R")
  - Guarda en `data/raw/*.parquet`
  - Cachea datos en `data/cache/` para futuras ejecuciones

**Modo Desarrollo:**
- Si ejecutas desde una rama diferente a `main` (o si `DEV_MODE=true`), solo descarga 10 filas
- Los archivos se suben a `gs://mci506-f1-analysis/dev_raw/` en lugar de `raw/`

```bash
# Forzar modo desarrollo
DEV_MODE=true python scripts/extract.py
```

### Carga a Google Cloud Storage

```bash
python scripts/load.py
```

**Qué hace:**
- Lee todos los archivos `.parquet` de `data/raw/`
- Sube a GCS con estructura Hive-style: `{RAW_PREFIX}/{dataset}/year={year}[/eventname={eventname}]/`
- Sobrescribe archivos existentes (para capturar correcciones de FastF1)

**Requiere:** Variable de entorno `GCP_SA_KEY`

### Ejecutar Ambos Pasos

```bash
python scripts/extract.py && python scripts/load.py
```

---

## 🔄 CI/CD Automatizado

El repositorio incluye un workflow de GitHub Actions que ejecuta automáticamente el pipeline.

### Cuándo Se Ejecuta

- **En cada push** a cualquier rama
- **Manualmente** desde la pestaña "Actions" de GitHub

### Comportamiento por Rama

| Rama | Modo | Destino en GCS |
|------|------|---|
| `main` | Producción | `raw/` |
| Otra rama | Desarrollo | `dev_raw/` |

### Caché de FastF1

El workflow cachea los datos descargados de FastF1 para acelerar futuras ejecuciones. El caché se reutiliza entre ejecuciones si el contenido no ha cambiado.

---

## 🤝 Guía para Contribuidores

### Estructura de Commits

1. **Extracción:** Cambios en `scripts/extract.py`
2. **Carga:** Cambios en `scripts/load.py`
3. **Utilidades:** Cambios en `utils.py`
4. **CI/CD:** Cambios en `.github/workflows/`
5. **Análisis:** Cambios en `notebook.ipynb`

### Pasos para Contribuir

#### 1. Crear una rama de desarrollo

```bash
git checkout -b feature/descripcion-corta
```

Por ejemplo:
```bash
git checkout -b feature/agregar-sesiones-practica
git checkout -b fix/manejo-errores-laps
```

#### 2. Hacer cambios locales

- Edita los scripts según sea necesario
- Prueba localmente:

```bash
# Modo desarrollo (10 filas)
DEV_MODE=true python scripts/extract.py

# O sin cargar a GCS (si no tienes credenciales)
python scripts/extract.py
python scripts/load.py  # Requiere GCP_SA_KEY
```

#### 3. Validar datos

Usa el notebook para explorar:
```bash
jupyter notebook notebook.ipynb
```

Carga los parquets generados y verifica su estructura:
```python
import pandas as pd
df = pd.read_parquet('data/raw/schedule_2025.parquet')
df.head()
```

#### 4. Commit y Push

```bash
git add scripts/ utils.py .github/
git commit -m "Descripción clara del cambio"
git push origin feature/descripcion-corta
```

#### 5. Crear un Pull Request

En GitHub:
1. Ve a "Pull Requests"
2. Haz clic en "New Pull Request"
3. Selecciona tu rama como "compare"
4. Describe los cambios
5. Solicita revisión

### Mejoras Sugeridas

Algunos cambios que podrían ser útiles:

- **Agregar más rounds:** Modificar `ROUNDS = [1, 2, 3]` en `extract.py`
- **Agregar temporadas:** Agregar años a `YEARS = [2025, 2026]`
- **Agregar sesiones:** Cambiar `SESSION = "R"` por otras (P, Q, SQ1, SQ2, SQ3, etc.)
- **Transformaciones:** Agregar un `scripts/transform.py` para limpiar/enriquecer datos en GCS
- **Análisis:** Expandir `notebook.ipynb` con visualizaciones y análisis comparativos

### Consideraciones Técnicas

#### Variables de Entorno

- `DEV_MODE`: `true` para modo desarrollo (10 filas), `false` para producción
- `GCP_SA_KEY`: JSON de service account para autenticación en GCS

#### Paths

- `RAW_DIR`: `{root}/data/raw/` - donde se guardan los parquets locales
- `CACHE_DIR`: `{root}/data/cache/` - caché de FastF1 para no recargar

#### Manejo de Errores

- Las vueltas (`laps`) pueden no estar disponibles para algunas sesiones → Se captura la excepción y se continúa
- FastF1 puede tardar o fallar → El caché acelera recargas

---

## 📚 Recursos

- **FastF1 Documentation:** https://docs.fastf1.dev/
- **Google Cloud Storage Client:** https://cloud.google.com/python/docs/reference/storage/latest
- **Pandas Documentation:** https://pandas.pydata.org/docs/
- **GitHub Actions:** https://docs.github.com/en/actions

---

## 📝 Licencia

Proyecto educativo para UCB MCI506.

---

## ✉️ Contacto

Creado por Luis Auza (luis.auza@gmail.com)

Para reportar bugs o sugerencias, abre un issue en GitHub.