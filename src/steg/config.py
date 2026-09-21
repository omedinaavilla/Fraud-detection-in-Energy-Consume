"""Configuración centralizada del proyecto: rutas, semilla y parámetros.

Ninguna ruta ni número mágico debe aparecer fuera de este módulo (sección 9 de
``contextPrompt.md``). Se usa una ``dataclass`` congelada en vez de pydantic: no hay
entrada externa (API, CLI de terceros) que requiera validación de tipos en el borde,
así que la dependencia adicional no se justifica.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

# Semilla única del proyecto. Se importa desde aquí en todo el código que necesite
# aleatoriedad controlada (splits, inicialización de modelos, remuestreo, etc.).
SEED: int = 42

# Número de folds para la validación cruzada agrupada por cliente. Se fija aquí como
# valor por defecto; el protocolo definitivo se congela en la Fase 2 y puede ajustar
# este valor en reports/DECISIONS.md, no en el código de modelado.
N_FOLDS: int = 5

# Prefijo que identifica a un cliente de la partición de entrenamiento de Zindi
# (``train_Client_*``; ver .claude/skills/steg-data-contract/SKILL.md). Lo usa
# src/steg/data/guards.py para impedir que un análisis que mira ``target`` corra
# sobre filas de client_test. Sensible a mayúsculas y sin normalizar espacios.
TRAIN_ID_PREFIX: str = "train_"

PROJECT_ROOT: Path =Path(__file__).resolve().parents[2]

DATA_RAW_DIR: Path = PROJECT_ROOT / "data" / "raw"
DATA_INTERIM_DIR: Path = PROJECT_ROOT / "data" / "interim"
DATA_PROCESSED_DIR: Path = PROJECT_ROOT / "data" / "processed"

REPORTS_DIR: Path = PROJECT_ROOT / "reports"
REPORTS_EDA_DIR: Path = REPORTS_DIR / "EDA"
REPORTS_FIGURES_DIR: Path = REPORTS_DIR / "figures"
REPORTS_TABLES_DIR: Path = REPORTS_DIR / "tables"
REPORTS_METRICS_DIR: Path = REPORTS_DIR / "metrics"

DECISIONS_PATH: Path = REPORTS_DIR / "DECISIONS.md"
LEAKAGE_AUDIT_PATH: Path = REPORTS_DIR / "LEAKAGE_AUDIT.md"
RESULTS_PATH: Path = REPORTS_DIR / "RESULTS.md"
DATA_CHECKSUMS_PATH: Path = REPORTS_DIR / "data_checksums.json"


@dataclass(frozen=True)
class RawFilePaths:
    """Rutas a los cuatro CSV originales del reto, tal como los entrega Zindi."""

    client_train: Path = DATA_RAW_DIR / "client_train.csv"
    client_test: Path = DATA_RAW_DIR / "client_test.csv"
    invoice_train: Path = DATA_RAW_DIR / "invoice_train.csv"
    invoice_test: Path = DATA_RAW_DIR / "invoice_test.csv"


RAW_FILES = RawFilePaths()

# Rutas de las tablas limpias (Fase 0), en parquet, con banderas de anomalía añadidas
# por src/steg/data/clean.py. No se sobrescriben los CSV crudos.
INTERIM_FILES = {
    "client_train": DATA_INTERIM_DIR / "client_train.parquet",
    "client_test": DATA_INTERIM_DIR / "client_test.parquet",
    "invoice_train": DATA_INTERIM_DIR / "invoice_train.parquet",
    "invoice_test": DATA_INTERIM_DIR / "invoice_test.parquet",
}


@dataclass(frozen=True)
class DataContract:
    """Valores centinela y reglas de validación derivados de la auditoría de Fase 0.

    Estas cifras son evidencia empírica sobre ``data/raw/*.csv`` (ver
    ``reports/EDA/00_data_audit.md`` y ``.claude/skills/steg-data-contract/SKILL.md``),
    no supuestos de diseño. Si una nueva versión de los datos cambia estos valores,
    el contrato y la skill deben actualizarse juntos.
    """

    # counter_statue es texto, no numérico: el README dice "hasta 5 valores" y test
    # respeta {0,1,2,3,4,5}, pero train trae además basura de captura.
    counter_statue_valid: frozenset[str] = field(
        default_factory=lambda: frozenset({"0", "1", "2", "3", "4", "5"})
    )
    # reading_remarque es numérico (int64) en el CSV. Válido según lo que aparece en
    # test; en train se filtran valores de counter_code que quedaron mezclados
    # (203, 207, 413, 5) — evidencia de columnas corridas en captura.
    reading_remarque_valid: frozenset[int] = field(
        default_factory=lambda: frozenset({6, 7, 8, 9})
    )
    months_number_min: int = 1
    months_number_max: int = 12
    creation_date_format: str = "%d/%m/%Y"
    invoice_date_format: str = "%Y-%m-%d"


DATA_CONTRACT = DataContract()
