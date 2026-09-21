"""Esquema y carga de las cuatro tablas, e integridad referencial."""

from __future__ import annotations

import pandas as pd
import pytest

from steg.data import load as load_module
from steg.data.load import SchemaValidationError, load_raw_data


def test_load_valid_raw_data_succeeds(monkeypatch, valid_raw_paths):
    monkeypatch.setattr(load_module, "RAW_FILES", valid_raw_paths)
    dataset = load_raw_data()

    assert dataset.client_train.shape == (3, 6)
    assert dataset.client_test.shape == (2, 5)
    assert pd.api.types.is_datetime64_any_dtype(dataset.client_train["creation_date"])
    assert pd.api.types.is_datetime64_any_dtype(dataset.invoice_train["invoice_date"])


def test_duplicate_client_id_is_rejected(monkeypatch, valid_raw_paths):
    df = pd.read_csv(valid_raw_paths.client_train)
    df.loc[len(df)] = df.iloc[0]  # duplica el primer client_id
    df.to_csv(valid_raw_paths.client_train, index=False)

    monkeypatch.setattr(load_module, "RAW_FILES", valid_raw_paths)
    with pytest.raises(SchemaValidationError, match="duplicados"):
        load_raw_data()


def test_missing_column_is_rejected(monkeypatch, valid_raw_paths):
    df = pd.read_csv(valid_raw_paths.client_train)
    df = df.drop(columns=["region"])
    df.to_csv(valid_raw_paths.client_train, index=False)

    monkeypatch.setattr(load_module, "RAW_FILES", valid_raw_paths)
    with pytest.raises(SchemaValidationError, match="faltan columnas"):
        load_raw_data()


def test_extra_column_is_rejected(monkeypatch, valid_raw_paths):
    df = pd.read_csv(valid_raw_paths.invoice_train)
    df["columna_inesperada"] = 1
    df.to_csv(valid_raw_paths.invoice_train, index=False)

    monkeypatch.setattr(load_module, "RAW_FILES", valid_raw_paths)
    with pytest.raises(SchemaValidationError, match="no esperadas"):
        load_raw_data()


def test_invoice_client_id_without_client_row_is_rejected(monkeypatch, valid_raw_paths):
    df = pd.read_csv(valid_raw_paths.invoice_train)
    df.loc[len(df)] = df.iloc[0]
    df.loc[df.index[-1], "client_id"] = "train_Client_no_existe"
    df.to_csv(valid_raw_paths.invoice_train, index=False)

    monkeypatch.setattr(load_module, "RAW_FILES", valid_raw_paths)
    with pytest.raises(SchemaValidationError, match="sin fila en client"):
        load_raw_data()


def test_overlapping_client_ids_between_train_and_test_is_rejected(monkeypatch, valid_raw_paths):
    client_train = pd.read_csv(valid_raw_paths.client_train)
    client_test = pd.read_csv(valid_raw_paths.client_test)
    client_test.loc[0, "client_id"] = client_train.loc[0, "client_id"]
    client_test.to_csv(valid_raw_paths.client_test, index=False)

    invoice_test = pd.read_csv(valid_raw_paths.invoice_test)
    invoice_test.loc[0, "client_id"] = client_train.loc[0, "client_id"]
    invoice_test.to_csv(valid_raw_paths.invoice_test, index=False)

    monkeypatch.setattr(load_module, "RAW_FILES", valid_raw_paths)
    with pytest.raises(SchemaValidationError, match="tanto en client_train"):
        load_raw_data()
