"""Fixtures compartidos. Todos sintéticos: ningún test depende de los CSV reales de
STEG, que no se pueden versionar ni distribuir con el repositorio."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import pytest


@dataclass(frozen=True)
class FakeRawFilePaths:
    client_train: Path
    client_test: Path
    invoice_train: Path
    invoice_test: Path


def _write_valid_raw_csvs(base_dir: Path) -> FakeRawFilePaths:
    client_train = pd.DataFrame(
        {
            "disrict": [60, 69, 62],
            "client_id": ["train_Client_0", "train_Client_1", "train_Client_2"],
            "client_catg": [11, 11, 51],
            "region": [101, 107, 103],
            "creation_date": ["31/12/1994", "29/05/2002", "13/03/1986"],
            "target": [0.0, 1.0, 0.0],
        }
    )
    client_test = pd.DataFrame(
        {
            "disrict": [62, 69],
            "client_id": ["test_Client_0", "test_Client_1"],
            "client_catg": [11, 11],
            "region": [307, 103],
            "creation_date": ["28/05/2002", "06/08/2009"],
        }
    )

    def _invoice_rows(client_ids: list[str]) -> pd.DataFrame:
        n = len(client_ids)
        return pd.DataFrame(
            {
                "client_id": client_ids,
                "invoice_date": ["2014-03-24"] * n,
                "tarif_type": [11] * n,
                "counter_number": list(range(1000, 1000 + n)),
                "counter_statue": ["0"] * n,
                "counter_code": [203] * n,
                "reading_remarque": [8] * n,
                "counter_coefficient": [1] * n,
                "consommation_level_1": [82] * n,
                "consommation_level_2": [0] * n,
                "consommation_level_3": [0] * n,
                "consommation_level_4": [0] * n,
                "old_index": [14302] * n,
                "new_index": [14384] * n,
                "months_number": [4] * n,
                "counter_type": ["ELEC"] * n,
            }
        )

    invoice_train = _invoice_rows(list(client_train["client_id"]))
    invoice_test = _invoice_rows(list(client_test["client_id"]))

    paths = FakeRawFilePaths(
        client_train=base_dir / "client_train.csv",
        client_test=base_dir / "client_test.csv",
        invoice_train=base_dir / "invoice_train.csv",
        invoice_test=base_dir / "invoice_test.csv",
    )
    client_train.to_csv(paths.client_train, index=False)
    client_test.to_csv(paths.client_test, index=False)
    invoice_train.to_csv(paths.invoice_train, index=False)
    invoice_test.to_csv(paths.invoice_test, index=False)
    return paths


@pytest.fixture
def valid_raw_paths(tmp_path: Path) -> FakeRawFilePaths:
    """Cuatro CSV mínimos y válidos según el contrato, en un directorio temporal."""
    return _write_valid_raw_csvs(tmp_path)


def make_invoice_df(rows: list[dict]) -> pd.DataFrame:
    """Construye un DataFrame de facturas con las columnas del contrato, rellenando
    con valores válidos por defecto lo que cada fila no especifique."""
    defaults = {
        "client_id": "train_Client_0",
        "invoice_date": pd.Timestamp("2014-03-24"),
        "tarif_type": 11,
        "counter_number": 1000,
        "counter_statue": "0",
        "counter_code": 203,
        "reading_remarque": 8,
        "counter_coefficient": 1,
        "consommation_level_1": 82,
        "consommation_level_2": 0,
        "consommation_level_3": 0,
        "consommation_level_4": 0,
        "old_index": 14302,
        "new_index": 14384,
        "months_number": 4,
        "counter_type": "ELEC",
    }
    full_rows = [{**defaults, **row} for row in rows]
    return pd.DataFrame(full_rows)
