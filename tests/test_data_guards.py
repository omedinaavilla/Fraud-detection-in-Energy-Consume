"""Tests de ``steg.data.guards.assert_train_partition`` (T001, requirement 002).

Los tests sintéticos cubren AC1-AC3. El último test corre sobre la carga real
(``load.py`` + ``clean.py``) y se salta con motivo explícito si falta ``data/raw/``,
que no se versiona (los datos son propiedad de STEG/Zindi).
"""

from __future__ import annotations

import inspect
import re

import numpy as np
import pandas as pd
import pytest

from steg.config import RAW_FILES, TRAIN_ID_PREFIX
from steg.data import guards
from steg.data.guards import PartitionLeakError, assert_train_partition

TRAIN_IDS = [f"train_Client_{i}" for i in range(10)]


def _failed_count(message: str) -> int:
    match = re.search(r"(\d+) de (\d+) filas fallaron", message)
    assert match, f"el mensaje no informa el conteo de filas fallidas: {message}"
    return int(match.group(1))


# --------------------------------------------------------------------------- AC1


def test_prefix_constant_matches_data_contract():
    assert TRAIN_ID_PREFIX == "train_"


def test_error_is_a_value_error():
    assert issubclass(PartitionLeakError, ValueError)


@pytest.mark.parametrize(
    "index",
    [
        pd.Index(TRAIN_IDS),
        pd.Index(TRAIN_IDS, dtype="string"),
        pd.Index(["train_Client_0"], name="client_id"),
    ],
    ids=["object", "string_dtype", "single_named"],
)
def test_accepts_pure_train_string_index(index):
    assert assert_train_partition(index) is None


def test_rejects_range_index():
    with pytest.raises(PartitionLeakError, match="RangeIndex"):
        assert_train_partition(pd.RangeIndex(10))


@pytest.mark.parametrize(
    "index",
    [
        pd.Index([0, 1, 2]),
        pd.Index([0.5, 1.5]),
        pd.Index(pd.to_datetime(["2014-01-01", "2015-01-01"])),
        pd.MultiIndex.from_tuples([("train_Client_0", 1), ("train_Client_1", 2)]),
    ],
    ids=["int", "float", "datetime", "multiindex"],
)
def test_rejects_non_string_index(index):
    with pytest.raises(PartitionLeakError):
        assert_train_partition(index)


@pytest.mark.parametrize(
    "not_an_index",
    [TRAIN_IDS, pd.Series(TRAIN_IDS), np.array(TRAIN_IDS)],
    ids=["list", "series", "ndarray"],
)
def test_rejects_objects_that_are_not_an_index(not_an_index):
    with pytest.raises(PartitionLeakError, match="pd.Index"):
        assert_train_partition(not_an_index)


def test_rejects_all_test_ids():
    index = pd.Index([f"test_Client_{i}" for i in range(7)])
    with pytest.raises(PartitionLeakError) as exc:
        assert_train_partition(index)
    assert _failed_count(str(exc.value)) == 7


def test_rejects_single_test_id_among_many_train():
    index = pd.Index([f"train_Client_{i}" for i in range(1000)] + ["test_Client_42"])
    with pytest.raises(PartitionLeakError) as exc:
        assert_train_partition(index)
    assert _failed_count(str(exc.value)) == 1
    assert "'test_Client_42'" in str(exc.value)


@pytest.mark.parametrize(
    "missing", [np.nan, None, pd.NA], ids=["nan", "none", "pd_na"]
)
def test_rejects_missing_values(missing):
    index = pd.Index([*TRAIN_IDS, missing], dtype=object)
    with pytest.raises(PartitionLeakError) as exc:
        assert_train_partition(index)
    assert _failed_count(str(exc.value)) == 1


def test_rejects_missing_value_in_string_dtype():
    index = pd.Index([*TRAIN_IDS, None], dtype="string")
    with pytest.raises(PartitionLeakError) as exc:
        assert_train_partition(index)
    assert _failed_count(str(exc.value)) == 1


@pytest.mark.parametrize(
    "index",
    [pd.Index([], dtype=object), pd.Index([], dtype="string")],
    ids=["object", "string_dtype"],
)
def test_rejects_empty_index(index):
    with pytest.raises(PartitionLeakError, match="vacío"):
        assert_train_partition(index)


@pytest.mark.parametrize(
    "bad_id",
    ["Train_Client_0", " train_Client_0", "trainClient_0", "train", "TRAIN_Client_0", "train_"],
    ids=["capital_T", "leading_space", "no_underscore", "bare_train", "upper", "prefix_only"],
)
def test_rejects_near_miss_prefixes_without_normalizing(bad_id):
    index = pd.Index([*TRAIN_IDS, bad_id])
    with pytest.raises(PartitionLeakError) as exc:
        assert_train_partition(index)
    assert _failed_count(str(exc.value)) == 1
    # repr del id tal cual: prueba que no se normalizó (espacio y mayúscula visibles).
    assert repr(bad_id) in str(exc.value)


# --------------------------------------------------------------------------- AC2


def test_message_reports_count_and_at_most_five_examples():
    bad = [f"test_Client_{i}" for i in range(12)]
    index = pd.Index(TRAIN_IDS + bad)
    with pytest.raises(PartitionLeakError) as exc:
        assert_train_partition(index)
    message = str(exc.value)
    assert _failed_count(message) == 12
    assert f"de {len(index)} filas" in message
    shown = [b for b in bad if repr(b) in message]
    assert shown == bad[:5]


def test_message_with_fewer_than_five_failures_shows_all():
    bad = ["test_Client_1", "test_Client_2"]
    with pytest.raises(PartitionLeakError) as exc:
        assert_train_partition(pd.Index(TRAIN_IDS + bad))
    assert all(repr(b) in str(exc.value) for b in bad)


# --------------------------------------------------------------------------- AC3


def test_has_no_parameter_to_disable_it():
    params = list(inspect.signature(assert_train_partition).parameters)
    assert params == ["index"]
    with pytest.raises(TypeError):
        assert_train_partition(pd.Index(["test_Client_0"]), strict=False)  # type: ignore[call-arg]


def test_has_no_environment_switch(monkeypatch):
    source = inspect.getsource(guards)
    assert "environ" not in source and "getenv" not in source
    for var in ("STEG_DISABLE_GUARDS", "STEG_SKIP_PARTITION_CHECK", "DISABLE_GUARDS"):
        monkeypatch.setenv(var, "1")
    with pytest.raises(PartitionLeakError):
        assert_train_partition(pd.Index(["test_Client_0"]))


# --------------------------------------------------------------------------- AC4


def test_docstring_declares_both_limits():
    doc = assert_train_partition.__doc__ or ""
    assert "valid interno" in doc
    assert "reindexadas con ids de train" in doc


# --------------------------------------------------------------------------- AC5 (datos reales)

_RAW_PATHS = [
    RAW_FILES.client_train,
    RAW_FILES.client_test,
    RAW_FILES.invoice_train,
    RAW_FILES.invoice_test,
]


@pytest.mark.skipif(
    not all(p.exists() for p in _RAW_PATHS),
    reason=(
        "faltan los CSV de data/raw/ (no se versionan: propiedad de STEG/Zindi); "
        "el test sobre la carga real solo corre donde están los datos"
    ),
)
def test_real_load_train_ids_pass_and_test_ids_fail():
    from steg.data.clean import clean_client
    from steg.data.load import load_raw_data

    dataset = load_raw_data()
    client_train, _ = clean_client(dataset.client_train, "client_train")
    client_test, _ = clean_client(dataset.client_test, "client_test")

    train_index = pd.Index(client_train["client_id"])
    test_index = pd.Index(client_test["client_id"])

    # El 100 % de los client_id de train pasa, también como índice del DataFrame y
    # sobre los client_id únicos de invoice_train.
    assert_train_partition(train_index)
    assert_train_partition(client_train.set_index("client_id").index)
    assert_train_partition(pd.Index(dataset.invoice_train["client_id"].unique()))

    # Todos los de test fallan, uno por uno contados en el mensaje.
    with pytest.raises(PartitionLeakError) as exc:
        assert_train_partition(test_index)
    assert _failed_count(str(exc.value)) == len(test_index)

    with pytest.raises(PartitionLeakError):
        assert_train_partition(pd.Index(dataset.invoice_test["client_id"].unique()))

    # Una mezcla train + un solo id de test también falla.
    mixed = train_index.append(test_index[:1])
    with pytest.raises(PartitionLeakError) as exc:
        assert_train_partition(mixed)
    assert _failed_count(str(exc.value)) == 1
