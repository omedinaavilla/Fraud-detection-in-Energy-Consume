"""Prueba anti-fuga estructural: ningún client_id aparece en dos folds ni a la vez en
train y valid. Esta garantía sostiene todo el protocolo de evaluación (sección 2 de
contextPrompt.md), por eso se implementa y se prueba ya en la Fase 0."""

from __future__ import annotations

import pandas as pd

from steg.data.split import (
    assert_no_group_leakage,
    grouped_kfold_splits,
    grouped_train_valid_split,
)


def _synthetic_invoices(n_clients: int = 40, invoices_per_client: int = 5) -> pd.DataFrame:
    rows = []
    for i in range(n_clients):
        for _ in range(invoices_per_client):
            rows.append({"client_id": f"client_{i}", "value": i})
    return pd.DataFrame(rows)


def test_train_valid_split_has_no_shared_client_id():
    df = _synthetic_invoices()
    train_idx, valid_idx = grouped_train_valid_split(df, valid_size=0.25)

    train_clients = set(df.iloc[train_idx]["client_id"])
    valid_clients = set(df.iloc[valid_idx]["client_id"])

    assert train_clients.isdisjoint(valid_clients)
    assert_no_group_leakage(df, train_idx, valid_idx)  # no debe lanzar
    # cada cliente conserva todas sus facturas en el mismo lado del split
    for client_id, group in df.groupby("client_id"):
        idx_set = set(group.index)
        assert idx_set.issubset(set(train_idx)) or idx_set.issubset(set(valid_idx))


def test_kfold_splits_never_place_a_client_in_two_folds():
    df = _synthetic_invoices(n_clients=50, invoices_per_client=4)

    fold_client_sets = []
    for train_idx, valid_idx in grouped_kfold_splits(df, n_splits=5):
        assert_no_group_leakage(df, train_idx, valid_idx)
        fold_client_sets.append(set(df.iloc[valid_idx]["client_id"]))

    # cada cliente aparece como "validación" en exactamente un fold
    all_clients = set(df["client_id"])
    seen = set()
    for fold_clients in fold_client_sets:
        assert fold_clients.isdisjoint(seen)
        seen |= fold_clients
    assert seen == all_clients


def test_assert_no_group_leakage_detects_a_violation():
    df = _synthetic_invoices(n_clients=4, invoices_per_client=2)
    # fuerza una fuga a mano: mismo client_id en "train" y en "valid"
    train_idx = df.index[df["client_id"] == "client_0"].to_numpy()
    valid_idx = df.index[df["client_id"].isin(["client_0", "client_1"])].to_numpy()

    try:
        assert_no_group_leakage(df, train_idx, valid_idx)
    except AssertionError:
        pass
    else:
        raise AssertionError("se esperaba que assert_no_group_leakage detectara la fuga")
