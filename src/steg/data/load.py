"""Carga y validación de esquema de los cuatro CSV originales.

Este módulo solo lee y valida: falla ruidosamente ante cualquier desviación del
contrato de datos (columnas, tipos, unicidad, integridad referencial). No repara nada
— eso es responsabilidad de ``src/steg/data/clean.py``. La separación es intencional:
si ``load`` empezara a corregir datos en silencio, un cambio futuro en el CSV crudo
podría colarse sin que nadie lo note.

Ver ``.claude/skills/steg-data-contract/SKILL.md`` para el detalle de cada regla y su
evidencia.
"""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone

import pandas as pd

from steg.config import DATA_CHECKSUMS_PATH, RAW_FILES

logger = logging.getLogger(__name__)

# Esquema esperado. dtype explícito: nunca se infiere, porque columnas como
# counter_statue mezclan dígitos y letras ('A') y pandas infiere object solo por
# accidente de qué valores aparecen primero.
CLIENT_DTYPES: dict[str, str] = {
    "disrict": "int64",
    "client_id": "string",
    "client_catg": "int64",
    "region": "int64",
}
CLIENT_TRAIN_EXTRA_DTYPES: dict[str, str] = {"target": "float64"}

INVOICE_DTYPES: dict[str, str] = {
    "client_id": "string",
    "tarif_type": "int64",
    "counter_number": "int64",
    "counter_statue": "string",
    "counter_code": "int64",
    "reading_remarque": "int64",
    "counter_coefficient": "int64",
    "consommation_level_1": "int64",
    "consommation_level_2": "int64",
    "consommation_level_3": "int64",
    "consommation_level_4": "int64",
    "old_index": "int64",
    "new_index": "int64",
    "months_number": "int64",
    "counter_type": "string",
}

CLIENT_DATE_COL = "creation_date"
CLIENT_DATE_FORMAT = "%d/%m/%Y"
INVOICE_DATE_COL = "invoice_date"
INVOICE_DATE_FORMAT = "%Y-%m-%d"


class SchemaValidationError(Exception):
    """El CSV no cumple el contrato de datos esperado."""


@dataclass
class RawDataset:
    """Las cuatro tablas crudas, ya tipadas y con fechas parseadas."""

    client_train: pd.DataFrame
    client_test: pd.DataFrame
    invoice_train: pd.DataFrame
    invoice_test: pd.DataFrame


def _validate_columns(df: pd.DataFrame, expected: set[str], name: str) -> None:
    actual = set(df.columns)
    missing = expected - actual
    extra = actual - expected
    if missing:
        raise SchemaValidationError(f"{name}: faltan columnas esperadas: {sorted(missing)}")
    if extra:
        raise SchemaValidationError(f"{name}: columnas no esperadas por el contrato: {sorted(extra)}")


def _load_client(path, is_train: bool) -> pd.DataFrame:
    dtypes = dict(CLIENT_DTYPES)
    if is_train:
        dtypes.update(CLIENT_TRAIN_EXTRA_DTYPES)
    name = "client_train" if is_train else "client_test"

    df = pd.read_csv(path, dtype={k: v for k, v in dtypes.items() if k != CLIENT_DATE_COL})
    _validate_columns(df, set(dtypes) | {CLIENT_DATE_COL}, name)

    df[CLIENT_DATE_COL] = pd.to_datetime(df[CLIENT_DATE_COL], format=CLIENT_DATE_FORMAT)

    if df["client_id"].duplicated().any():
        n_dup = int(df["client_id"].duplicated().sum())
        raise SchemaValidationError(f"{name}: {n_dup} client_id duplicados")

    logger.info("%s cargado: %s filas, %s columnas", name, df.shape[0], df.shape[1])
    return df


def _load_invoice(path, name: str) -> pd.DataFrame:
    df = pd.read_csv(path, dtype=INVOICE_DTYPES)
    _validate_columns(df, set(INVOICE_DTYPES) | {INVOICE_DATE_COL}, name)

    df[INVOICE_DATE_COL] = pd.to_datetime(df[INVOICE_DATE_COL], format=INVOICE_DATE_FORMAT)

    logger.info("%s cargado: %s filas, %s columnas", name, df.shape[0], df.shape[1])
    return df


def _validate_referential_integrity(client: pd.DataFrame, invoice: pd.DataFrame, name: str) -> None:
    client_ids = set(client["client_id"])
    invoice_ids = set(invoice["client_id"])

    clients_without_invoices = client_ids - invoice_ids
    invoices_without_client = invoice_ids - client_ids

    if invoices_without_client:
        raise SchemaValidationError(
            f"{name}: {len(invoices_without_client)} client_id en invoice sin fila en client"
        )
    if clients_without_invoices:
        # No es un error de esquema (un cliente sin facturas es posible), pero es
        # relevante para el EDA y para la fase de features (sin historial, no hay
        # variables agregadas). Se registra como advertencia, no se bloquea la carga.
        logger.warning(
            "%s: %s client_id en client sin ninguna factura", name, len(clients_without_invoices)
        )


def load_raw_data() -> RawDataset:
    """Carga y valida los cuatro CSV crudos. Lanza SchemaValidationError si algo no cuadra."""
    client_train = _load_client(RAW_FILES.client_train, is_train=True)
    client_test = _load_client(RAW_FILES.client_test, is_train=False)
    invoice_train = _load_invoice(RAW_FILES.invoice_train, "invoice_train")
    invoice_test = _load_invoice(RAW_FILES.invoice_test, "invoice_test")

    _validate_referential_integrity(client_train, invoice_train, "train")
    _validate_referential_integrity(client_test, invoice_test, "test")

    overlap = set(client_train["client_id"]) & set(client_test["client_id"])
    if overlap:
        raise SchemaValidationError(
            f"{len(overlap)} client_id aparecen tanto en client_train como en client_test"
        )

    return RawDataset(
        client_train=client_train,
        client_test=client_test,
        invoice_train=invoice_train,
        invoice_test=invoice_test,
    )


def _sha256_of_file(path) -> str:
    """Hash SHA-256 en streaming: invoice_train.csv pesa ~340 MB, no se carga entero."""
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def compute_and_save_checksums() -> dict:
    """Calcula el hash SHA-256, tamaño y número de filas de cada CSV crudo.

    Como ``data/`` no se versiona (los datos son propiedad de STEG/Zindi), el hash es
    la única forma de demostrar que un resultado del artículo salió de este archivo
    exacto. Se escribe en ``reports/data_checksums.json``.
    """
    files = {
        "client_train": RAW_FILES.client_train,
        "client_test": RAW_FILES.client_test,
        "invoice_train": RAW_FILES.invoice_train,
        "invoice_test": RAW_FILES.invoice_test,
    }
    entries = {}
    for name, path in files.items():
        with open(path, "rb") as f:
            n_lines = sum(1 for _ in f)
        entries[name] = {
            "path": str(path),
            "sha256": _sha256_of_file(path),
            "size_bytes": path.stat().st_size,
            "n_rows": n_lines - 1,  # descuenta la fila de encabezado
        }

    payload = {
        "computed_at_utc": datetime.now(timezone.utc).isoformat(),
        "files": entries,
    }
    DATA_CHECKSUMS_PATH.parent.mkdir(parents=True, exist_ok=True)
    DATA_CHECKSUMS_PATH.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    logger.info("Checksums de datos crudos escritos en %s", DATA_CHECKSUMS_PATH)
    return payload


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    compute_and_save_checksums()
    dataset = load_raw_data()
    logger.info(
        "Esquema validado sin excepciones. client_train=%s client_test=%s "
        "invoice_train=%s invoice_test=%s",
        dataset.client_train.shape,
        dataset.client_test.shape,
        dataset.invoice_train.shape,
        dataset.invoice_test.shape,
    )


if __name__ == "__main__":
    main()
