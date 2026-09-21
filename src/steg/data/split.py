"""Utilidades de partición agrupada por cliente.

La unidad de análisis es el cliente, no la factura (sección 2 de ``contextPrompt.md``):
ninguna partición train/valid/test ni ningún fold de validación cruzada puede separar
facturas del mismo ``client_id`` entre conjuntos. Este módulo centraliza esa regla para
que ningún otro módulo tenga que reimplementarla.

Se implementa ya en la Fase 0, antes de que exista modelado, porque es la garantía
estructural sobre la que se apoya todo el protocolo de evaluación (congelado en la
Fase 2) y porque ``tests/test_split_anti_leakage.py`` la ejercita como prueba de
higiene, no como feature del pipeline de modelos.
"""

from __future__ import annotations

from collections.abc import Iterator

import numpy as np
import pandas as pd
from sklearn.model_selection import GroupKFold, GroupShuffleSplit

from steg.config import N_FOLDS, SEED


def grouped_train_valid_split(
    df: pd.DataFrame,
    group_col: str = "client_id",
    valid_size: float = 0.2,
    seed: int = SEED,
) -> tuple[np.ndarray, np.ndarray]:
    """Devuelve (train_idx, valid_idx) sin que ningún group_col se reparta entre ambos."""
    splitter = GroupShuffleSplit(n_splits=1, test_size=valid_size, random_state=seed)
    train_idx, valid_idx = next(splitter.split(df, groups=df[group_col]))
    return train_idx, valid_idx


def grouped_kfold_splits(
    df: pd.DataFrame,
    group_col: str = "client_id",
    n_splits: int = N_FOLDS,
) -> Iterator[tuple[np.ndarray, np.ndarray]]:
    """Genera (train_idx, valid_idx) por fold, agrupado por group_col.

    ``GroupKFold`` de scikit-learn no acepta ``random_state`` (no baraja los grupos);
    la asignación de grupos a folds es determinista dado el orden de entrada. Si el
    protocolo congelado en la Fase 2 exige estratificación además de agrupación, se
    sustituye aquí por ``StratifiedGroupKFold`` sin tocar el resto del pipeline.
    """
    splitter = GroupKFold(n_splits=n_splits)
    yield from splitter.split(df, groups=df[group_col])


def assert_no_group_leakage(
    df: pd.DataFrame, train_idx: np.ndarray, valid_idx: np.ndarray, group_col: str = "client_id"
) -> None:
    """Lanza AssertionError si algún group_col aparece a la vez en train y en valid."""
    train_groups = set(df.iloc[train_idx][group_col])
    valid_groups = set(df.iloc[valid_idx][group_col])
    overlap = train_groups & valid_groups
    if overlap:
        raise AssertionError(
            f"{len(overlap)} valores de {group_col} aparecen en train y en valid: "
            f"{sorted(overlap)[:5]}..."
        )
