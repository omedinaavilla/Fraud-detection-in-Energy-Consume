"""Limpieza documentada de las tablas crudas.

Cada regla es una función independiente que:

1. Tiene nombre y docstring explícitos.
2. Nunca borra información en silencio: marca la anomalía con una columna booleana
   para que el EDA pueda estudiar si es señal (por ejemplo, ¿los clientes fraudulentos
   tienen más `counter_statue` inválidos?) antes de decidir qué hacer con ella.
3. Devuelve el número de filas afectadas, para que quede en el reporte de limpieza y
   se pueda verificar contra las cifras de la auditoría (``reports/EDA/00_data_audit.md``).

La única regla que sí elimina filas es ``drop_exact_duplicates``: una fila
completamente duplicada no es una anomalía a estudiar, es el mismo registro capturado
dos veces.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

import pandas as pd

from steg.config import DATA_CONTRACT, INTERIM_FILES
from steg.data.load import load_raw_data

logger = logging.getLogger(__name__)


@dataclass
class CleaningReport:
    """Cuenta de filas afectadas por cada regla, por tabla."""

    table: str
    counts: dict[str, int] = field(default_factory=dict)

    def add(self, rule: str, n: int) -> None:
        self.counts[rule] = n
        logger.info("%s.%s: %s filas afectadas", self.table, rule, n)


def mark_counter_statue_invalid(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Marca counter_statue fuera de {0..5} (basura de captura: 'A', '618', '46', ...)."""
    invalid = ~df["counter_statue"].isin(DATA_CONTRACT.counter_statue_valid)
    df = df.copy()
    df["counter_statue_invalid"] = invalid
    return df, int(invalid.sum())


def mark_reading_remarque_invalid(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Marca reading_remarque fuera de {6,7,8,9}: valores propios de counter_code
    que aparecen mezclados en train (203, 207, 413, 5), evidencia de columnas
    corridas en la captura original."""
    invalid = ~df["reading_remarque"].isin(DATA_CONTRACT.reading_remarque_valid)
    df = df.copy()
    df["reading_remarque_invalid"] = invalid
    return df, int(invalid.sum())


def mark_months_number_invalid(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Marca months_number fuera de [1, 12]. El máximo observado en train es 636624,
    imposible para un período de facturación."""
    invalid = (df["months_number"] < DATA_CONTRACT.months_number_min) | (
        df["months_number"] > DATA_CONTRACT.months_number_max
    )
    df = df.copy()
    df["months_number_invalid"] = invalid
    return df, int(invalid.sum())


def mark_index_regression(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Marca facturas donde new_index < old_index: el contador retrocedió, lo cual
    solo tiene sentido si hubo cambio de contador (no verificable con estas columnas
    solas) o es un error de captura."""
    invalid = df["new_index"] < df["old_index"]
    df = df.copy()
    df["index_regression"] = invalid
    return df, int(invalid.sum())


def drop_exact_duplicates(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Elimina filas completamente duplicadas (todas las columnas iguales). A
    diferencia de las demás reglas, esta sí elimina: no hay nada que estudiar en un
    registro capturado dos veces de forma idéntica."""
    dup_mask = df.duplicated(keep="first")
    n = int(dup_mask.sum())
    return df.loc[~dup_mask].copy(), n


def mark_logical_duplicates(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Marca (sin eliminar) filas duplicadas por la clave lógica
    (client_id, invoice_date, counter_number). No se eliminan porque, a diferencia
    del duplicado exacto, estas filas pueden diferir en consumo o índices y esa
    diferencia podría ser señal (p.ej. refacturación) en vez de puro error."""
    dup_mask = df.duplicated(subset=["client_id", "invoice_date", "counter_number"], keep="first")
    df = df.copy()
    df["logical_duplicate"] = dup_mask
    return df, int(dup_mask.sum())


def clean_invoice(df: pd.DataFrame, table_name: str) -> tuple[pd.DataFrame, CleaningReport]:
    """Aplica todas las reglas de limpieza a una tabla de facturas, en orden."""
    report = CleaningReport(table=table_name)

    df, n = drop_exact_duplicates(df)
    report.add("exact_duplicates_dropped", n)

    df, n = mark_logical_duplicates(df)
    report.add("logical_duplicate", n)

    df, n = mark_counter_statue_invalid(df)
    report.add("counter_statue_invalid", n)

    df, n = mark_reading_remarque_invalid(df)
    report.add("reading_remarque_invalid", n)

    df, n = mark_months_number_invalid(df)
    report.add("months_number_invalid", n)

    df, n = mark_index_regression(df)
    report.add("index_regression", n)

    return df, report


def clean_client(df: pd.DataFrame, table_name: str) -> tuple[pd.DataFrame, CleaningReport]:
    """Limpieza de la tabla de clientes. La auditoría de Fase 0 no encontró
    duplicados, nulos ni valores fuera de rango en client_train/client_test, así que
    esta función no aplica reglas todavía; queda como punto de extensión si una
    versión futura de los datos los introduce."""
    return df.copy(), CleaningReport(table=table_name)


def clean_all() -> dict[str, CleaningReport]:
    """Carga las cuatro tablas crudas, las limpia y escribe data/interim/*.parquet."""
    dataset = load_raw_data()
    INTERIM_FILES["client_train"].parent.mkdir(parents=True, exist_ok=True)

    client_train, report_ct = clean_client(dataset.client_train, "client_train")
    client_test, report_cte = clean_client(dataset.client_test, "client_test")
    invoice_train, report_it = clean_invoice(dataset.invoice_train, "invoice_train")
    invoice_test, report_ite = clean_invoice(dataset.invoice_test, "invoice_test")

    client_train.to_parquet(INTERIM_FILES["client_train"], index=False)
    client_test.to_parquet(INTERIM_FILES["client_test"], index=False)
    invoice_train.to_parquet(INTERIM_FILES["invoice_train"], index=False)
    invoice_test.to_parquet(INTERIM_FILES["invoice_test"], index=False)

    return {
        "client_train": report_ct,
        "client_test": report_cte,
        "invoice_train": report_it,
        "invoice_test": report_ite,
    }


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    reports = clean_all()
    for name, report in reports.items():
        logger.info("Reporte de limpieza %s: %s", name, report.counts)


if __name__ == "__main__":
    main()
