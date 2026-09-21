"""Tests de la guardia de partición de ``steg.eda.bivariate`` (T003, requirement 002).

Objetivo: que ninguna función pública que reciba la etiqueta pueda entrar al módulo sin
la guardia sin que falle este archivo.

- AC1: descubrimiento por ``inspect`` de las funciones con ``target``, ``y`` o ``X``+``y``
  en la firma, comparado **por igualdad** con la lista esperada de 7.
- AC2: cada función lanza ``PartitionLeakError`` con ids 100 % test, con 1 fila ``test_``
  entre N, con ``RangeIndex``, con índice duplicado y con índices desalineados.
- AC3: cada función funciona con un fixture válido de solo train.
- AC4: regresión: con train válido, cada función devuelve exactamente lo mismo que la
  implementación previa a la guardia. Los valores de referencia se calcularon con esa
  versión previa (sin guardia) sobre este mismo fixture y se fijan aquí como literales.
- AC5: caso con ids reales de ``client_test`` vía ``load.py``; se salta con motivo
  explícito si falta ``data/raw/``.
- AC7: ``fold_prevalence`` con ``splits`` como generador da lo mismo que con lista; una
  máscara booleana como ``valid_idx`` se rechaza (rechazo documentado, no regresión).

Todo lo sintético vive en este archivo; no depende de los CSV reales de STEG. La columna
categórica se llama ``disrict`` (errata de origen del contrato de datos).
"""

from __future__ import annotations

import inspect
import re
from collections.abc import Callable

import numpy as np
import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from steg.config import RAW_FILES
from steg.data.guards import PartitionLeakError
from steg.data.split import grouped_kfold_splits
from steg.eda import bivariate

# Lista cerrada de funciones públicas que reciben etiqueta. Añadir una función nueva con
# ``target``/``y`` en la firma obliga a actualizar esta lista y ``_CALLS`` (y por tanto
# a pasar por los casos adversariales de AC2).
EXPECTED_LABEL_FUNCTIONS: frozenset[str] = frozenset(
    {
        "numeric_vs_target",
        "numeric_table_vs_target",
        "categorical_vs_target",
        "target_rate_by_category",
        "binary_flag_vs_target",
        "mutual_information_ranking",
        "fold_prevalence",
    }
)

N = 60
N_BOOT = 200
N_PERM = 3
N_SPLITS = 5


# --------------------------------------------------------------------------- fixture


def make_train_frame() -> pd.DataFrame:
    """60 clientes de train, deterministas, con ids en orden no lexicográfico.

    ``x`` tiene dos NaN (clientes 3 y 44) para ejercitar la máscara de
    ``numeric_vs_target``; ``disrict`` es categórica con 5 niveles; ``flag`` es booleana.
    """
    order = [(7 * i) % N for i in range(N)]
    ids = [f"train_Client_{k}" for k in order]
    target = [1.0 if k % 5 == 0 else 0.0 for k in order]
    x = [float((k * 37) % 61) + (15.0 if k % 5 == 0 else 0.0) for k in order]
    z = [float((k * 13) % 17) + (4.0 if k % 5 == 0 else 0.0) for k in order]
    x = [np.nan if k in (3, 44) else v for k, v in zip(order, x, strict=True)]
    cat = [["A", "B", "C", "D", "E"][(k * 3 + k // 7) % 5] for k in order]
    flag = [bool(k % 3 == 0 or k % 10 == 0) for k in order]
    return pd.DataFrame(
        {"client_id": ids, "target": target, "x": x, "z": z, "disrict": cat, "flag": flag}
    )


def _indexed() -> tuple[pd.DataFrame, pd.Series]:
    t = make_train_frame().set_index("client_id")
    return t, t["target"]


def _splits_for(n_rows: int) -> list[tuple[np.ndarray, np.ndarray]]:
    """Folds agrupados por posición sobre ``n_rows`` filas (una fila por cliente)."""
    frame = pd.DataFrame({"client_id": [f"g{i}" for i in range(n_rows)]})
    return list(grouped_kfold_splits(frame, n_splits=N_SPLITS))


# Cada función con etiqueta, invocada con (tabla de explicativas, etiqueta). La tabla y la
# etiqueta comparten índice salvo en los casos de desalineación.
_CALLS: dict[str, Callable[[pd.DataFrame, pd.Series], object]] = {
    "numeric_vs_target": lambda f, t: bivariate.numeric_vs_target(
        f["x"], t, "x", n_boot=N_BOOT
    ),
    "numeric_table_vs_target": lambda f, t: bivariate.numeric_table_vs_target(
        f, t, ["x", "z"], n_boot=N_BOOT
    ),
    "categorical_vs_target": lambda f, t: bivariate.categorical_vs_target(
        f["disrict"], t, "disrict"
    ),
    "target_rate_by_category": lambda f, t: bivariate.target_rate_by_category(
        f["disrict"], t, "disrict"
    ),
    "binary_flag_vs_target": lambda f, t: bivariate.binary_flag_vs_target(
        f["flag"], t, "flag"
    ),
    "mutual_information_ranking": lambda f, t: bivariate.mutual_information_ranking(
        f[["x", "z"]], t, n_permutations=N_PERM
    ),
    "fold_prevalence": lambda f, t: bivariate.fold_prevalence(t, _splits_for(len(t))),
}

FUNCTIONS = sorted(EXPECTED_LABEL_FUNCTIONS)


# --------------------------------------------------------------------------- AC1


def _discover_label_functions() -> set[str]:
    found = set()
    for name, fn in inspect.getmembers(bivariate, inspect.isfunction):
        if name.startswith("_") or fn.__module__ != bivariate.__name__:
            continue
        params = set(inspect.signature(fn).parameters)
        if "target" in params or "y" in params or {"X", "y"} <= params:
            found.add(name)
    return found


def test_discovered_label_functions_equal_expected_list():
    assert _discover_label_functions() == EXPECTED_LABEL_FUNCTIONS


def test_every_label_function_has_an_adversarial_caller():
    # Si alguien añade una función a la lista sin cubrirla en _CALLS, AC2/AC3 no la
    # ejercitarían: este test lo impide.
    assert set(_CALLS) == EXPECTED_LABEL_FUNCTIONS


def test_discovery_excludes_functions_without_label():
    discovered = _discover_label_functions()
    assert "spearman_matrix" not in discovered
    assert "binomial_sd_pct" not in discovered


# --------------------------------------------------------------------------- AC2


def _raises(name: str, feats: pd.DataFrame, target: pd.Series, pattern: str) -> None:
    with pytest.raises(PartitionLeakError, match=pattern):
        _CALLS[name](feats, target)


@pytest.mark.parametrize("name", FUNCTIONS)
def test_all_test_ids_raise(name):
    feats, target = _indexed()
    test_index = pd.Index([f"test_Client_{i}" for i in range(N)], name="client_id")
    feats = feats.set_axis(test_index)
    target = target.set_axis(test_index)
    _raises(name, feats, target, rf"{N} de {N} filas fallaron")


@pytest.mark.parametrize("name", FUNCTIONS)
def test_single_test_id_among_train_raises(name):
    # El id contaminado es el cliente 3, cuyo ``x`` es NaN: la guardia tiene que
    # dispararse antes de la máscara de nulos, no después.
    feats, target = _indexed()
    pos = feats.index.get_loc("train_Client_3")
    assert np.isnan(feats["x"].iloc[pos])
    ids = feats.index.tolist()
    ids[pos] = "test_Client_3"
    mixed = pd.Index(ids, name="client_id")
    _raises(name, feats.set_axis(mixed), target.set_axis(mixed), rf"1 de {N} filas fallaron")


@pytest.mark.parametrize("name", FUNCTIONS)
def test_range_index_raises(name):
    feats, target = _indexed()
    _raises(name, feats.reset_index(drop=True), target.reset_index(drop=True), "RangeIndex")


@pytest.mark.parametrize("name", FUNCTIONS)
def test_duplicated_index_raises(name):
    feats, target = _indexed()
    ids = feats.index.tolist()
    ids[-1] = ids[0]
    dup = pd.Index(ids, name="client_id")
    _raises(name, feats.set_axis(dup), target.set_axis(dup), "duplicados")


# Variantes de desalineación de las explicativas respecto de una etiqueta válida.
_MISALIGNMENTS: dict[str, Callable[[pd.DataFrame], pd.DataFrame]] = {
    "reordered": lambda f: f.iloc[::-1],
    "one_row_dropped": lambda f: f.iloc[1:],
    "range_index": lambda f: f.reset_index(drop=True),
    "features_with_test_id": lambda f: f.rename(index={f.index[0]: "test_Client_0"}),
}


@pytest.mark.parametrize("variant", sorted(_MISALIGNMENTS))
@pytest.mark.parametrize("name", sorted(EXPECTED_LABEL_FUNCTIONS - {"fold_prevalence"}))
def test_misaligned_features_raise(name, variant):
    feats, target = _indexed()
    _raises(name, _MISALIGNMENTS[variant](feats), target, "no es igual a")


# ``fold_prevalence`` no recibe explicativas: su desalineación posible es que ``splits``
# se haya generado sobre otra tabla (posiciones que no existen en ``target``).
@pytest.mark.parametrize(
    "bad_splits",
    [
        pytest.param(lambda n: _splits_for(n + 5), id="splits_from_larger_table"),
        pytest.param(lambda n: [(np.arange(1, n), np.array([-1]))], id="negative_position"),
        pytest.param(lambda n: [], id="no_folds"),
    ],
)
def test_fold_prevalence_misaligned_splits_raise(bad_splits):
    _, target = _indexed()
    with pytest.raises(PartitionLeakError):
        bivariate.fold_prevalence(target, bad_splits(len(target)))


@pytest.mark.parametrize("name", FUNCTIONS)
@pytest.mark.parametrize(
    "as_type",
    [pytest.param(lambda s: s.to_numpy(), id="ndarray"), pytest.param(list, id="list")],
)
def test_label_that_is_not_a_series_raises(name, as_type):
    feats, target = _indexed()
    with pytest.raises(PartitionLeakError, match="pd.Series"):
        _CALLS[name](feats, as_type(target))


# --------------------------------------------------------------------------- AC3


@pytest.mark.parametrize("name", FUNCTIONS)
def test_valid_train_fixture_runs(name):
    feats, target = _indexed()
    result = _CALLS[name](feats, target)
    assert isinstance(result, (dict, pd.DataFrame))
    assert len(result) > 0


# --------------------------------------------------------------------------- AC4
#
# Referencias generadas con la implementación previa a T002 (sin guardia), sobre
# ``make_train_frame`` y los mismos argumentos de ``_CALLS``. La igualdad es exacta.

REF_NUMERIC_VS_TARGET = {
    "variable": "x",
    "n": 58,
    "n_pos": 12,
    "n_neg": 46,
    "median_neg": 35.5,
    "median_pos": 26.0,
    "mean_neg": 34.391304347826086,
    "mean_pos": 26.0,
    "rank_biserial": -0.3587,
    "ci95_lo": -0.59562,
    "ci95_hi": -0.05595,
    "abs_effect": 0.3587,
    "above_threshold": True,
    "mannwhitney_u": 177.0,
    "p_value": 0.05861274918103702,
    "n_bootstrap": 200,
}

REF_NUMERIC_TABLE_VS_TARGET = {
    "variable": ["z", "x"],
    "n": [60, 58],
    "n_pos": [12, 12],
    "n_neg": [48, 46],
    "median_neg": [8.0, 35.5],
    "median_pos": [11.5, 26.0],
    "mean_neg": [7.854166666666667, 34.391304347826086],
    "mean_pos": [11.583333333333334, 26.0],
    "rank_biserial": [0.37847, -0.3587],
    "ci95_lo": [0.07173, -0.59562],
    "ci95_hi": [0.66959, -0.05595],
    "abs_effect": [0.37847, 0.3587],
    "above_threshold": [True, True],
    "mannwhitney_u": [397.0, 177.0],
    "p_value": [0.04459730827728798, 0.05861274918103702],
    "n_bootstrap": [200, 200],
}

REF_CATEGORICAL_VS_TARGET = {
    "cramers_v": 0.24987856413525514,
    "cramers_v_bias_corrected": 0.0,
    "chi2": 3.7463578088578084,
    "p_value": 0.4414193910111054,
    "dof": 4,
    "n": 60,
    "min_expected": 2.2,
    "pct_cells_expected_lt5": 50.0,
    "variable": "disrict",
    "n_categories": 5,
    "grouped": False,
}

REF_CATEGORICAL_VS_TARGET_TOP2 = {
    "cramers_v": 0.23543547789870936,
    "cramers_v_bias_corrected": 0.14799592206347342,
    "chi2": 3.32579185520362,
    "p_value": 0.1895891479022448,
    "dof": 2,
    "n": 60,
    "min_expected": 2.6,
    "pct_cells_expected_lt5": 33.33333333333333,
    "variable": "disrict",
    "n_categories": 3,
    "grouped": True,
}

REF_TARGET_RATE_BY_CATEGORY = {
    "variable": ["disrict"] * 5,
    "category": ["A", "C", "B", "D", "E"],
    "n": [13, 13, 11, 11, 12],
    "n_pos": [4, 4, 2, 1, 1],
    "rate_pct": [30.7692, 30.7692, 18.1818, 9.0909, 8.3333],
    "wilson_lo_pct": [12.6807, 12.6807, 5.1368, 1.6232, 1.4865],
    "wilson_hi_pct": [57.6307, 57.6307, 47.6981, 37.7358, 35.388],
    "lift_vs_base": [1.5385, 1.5385, 0.9091, 0.4545, 0.4167],
    "base_rate_pct": [20.0, 20.0, 20.0, 20.0, 20.0],
}

REF_BINARY_FLAG_VS_TARGET = {
    "variable": "flag",
    "n_flagged": 24,
    "n_not_flagged": 36,
    "rate_flagged_pct": 33.3333,
    "flagged_wilson_lo_pct": 17.9722,
    "flagged_wilson_hi_pct": 53.2937,
    "rate_not_flagged_pct": 11.1111,
    "not_flagged_wilson_lo_pct": 4.4066,
    "not_flagged_wilson_hi_pct": 25.3148,
    "risk_ratio": 3.0,
    "rr_ci95_lo": 1.0153,
    "rr_ci95_hi": 8.8644,
}

REF_MUTUAL_INFORMATION_RANKING = {
    "variable": ["z", "x"],
    "mutual_info": [0.0, 0.056597],
    "null_mean": [0.023346, 0.111572],
    "null_max": [0.070037, 0.150893],
    "excess_over_null": [-0.023346, -0.054975],
    "above_null_max": [False, False],
    "n": [60, 60],
    "n_permutations": [3, 3],
}

REF_FOLD_PREVALENCE = {
    "fold": [1, 2, 3, 4, 5],
    "n_valid": [12, 12, 12, 12, 12],
    "n_pos": [4, 2, 3, 0, 3],
    "prevalence_pct": [33.3333, 16.6667, 25.0, 0.0, 25.0],
    "wilson_lo_pct": [13.812, 4.6965, 8.8942, 0.0, 8.8942],
    "wilson_hi_pct": [60.9378, 44.8031, 53.2305, 24.2494, 53.2305],
}

_REF_BY_FUNCTION: dict[str, dict] = {
    "numeric_vs_target": REF_NUMERIC_VS_TARGET,
    "numeric_table_vs_target": REF_NUMERIC_TABLE_VS_TARGET,
    "categorical_vs_target": REF_CATEGORICAL_VS_TARGET,
    "target_rate_by_category": REF_TARGET_RATE_BY_CATEGORY,
    "binary_flag_vs_target": REF_BINARY_FLAG_VS_TARGET,
    "mutual_information_ranking": REF_MUTUAL_INFORMATION_RANKING,
    "fold_prevalence": REF_FOLD_PREVALENCE,
}


def _assert_same(result: object, reference: dict) -> None:
    if isinstance(result, pd.DataFrame):
        assert_frame_equal(result, pd.DataFrame(reference), check_exact=True)
    else:
        assert isinstance(result, dict)
        # Mismas claves, mismo orden y mismos valores exactos.
        assert list(result) == list(reference)
        for key, expected in reference.items():
            assert result[key] == expected, key


def test_reference_covers_every_label_function():
    assert set(_REF_BY_FUNCTION) == EXPECTED_LABEL_FUNCTIONS


@pytest.mark.parametrize("name", FUNCTIONS)
def test_regression_against_pre_guard_implementation(name):
    feats, target = _indexed()
    _assert_same(_CALLS[name](feats, target), _REF_BY_FUNCTION[name])


def test_regression_categorical_grouped_top_k():
    feats, target = _indexed()
    result = bivariate.categorical_vs_target(feats["disrict"], target, "disrict", top_k=2)
    _assert_same(result, REF_CATEGORICAL_VS_TARGET_TOP2)


def test_regression_fold_prevalence_with_client_id_splits():
    # Mismo uso que el notebook: splits de ``grouped_kfold_splits`` sobre la tabla de
    # clientes, en el mismo orden que ``target``.
    frame = make_train_frame()
    target = frame.set_index("client_id")["target"]
    result = bivariate.fold_prevalence(
        target, list(grouped_kfold_splits(frame, n_splits=N_SPLITS))
    )
    _assert_same(result, REF_FOLD_PREVALENCE)


# --------------------------------------------------------------------------- AC7


def test_fold_prevalence_generator_equals_list():
    frame = make_train_frame()
    target = frame.set_index("client_id")["target"]
    from_list = bivariate.fold_prevalence(
        target, list(grouped_kfold_splits(frame, n_splits=N_SPLITS))
    )
    from_gen = bivariate.fold_prevalence(target, grouped_kfold_splits(frame, n_splits=N_SPLITS))
    assert_frame_equal(from_gen, from_list, check_exact=True)
    _assert_same(from_gen, REF_FOLD_PREVALENCE)
    assert len(from_gen) == N_SPLITS


def test_fold_prevalence_boolean_mask_is_rejected():
    # Rechazo documentado (no regresión): la versión previa aceptaba una máscara
    # booleana vía iloc; el contrato actual exige posiciones enteras.
    frame = make_train_frame()
    target = frame.set_index("client_id")["target"]
    splits = []
    for train_idx, valid_idx in grouped_kfold_splits(frame, n_splits=N_SPLITS):
        mask = np.zeros(len(target), dtype=bool)
        mask[valid_idx] = True
        splits.append((train_idx, mask))
    with pytest.raises(PartitionLeakError, match="entero"):
        bivariate.fold_prevalence(target, splits)
    # Y la alternativa documentada (posiciones) reproduce la referencia.
    positions = [(tr, np.flatnonzero(m)) for tr, m in splits]
    _assert_same(bivariate.fold_prevalence(target, positions), REF_FOLD_PREVALENCE)


# --------------------------------------------------------------------------- AC5 (datos reales)

_RAW_PATHS = [
    RAW_FILES.client_train,
    RAW_FILES.client_test,
    RAW_FILES.invoice_train,
    RAW_FILES.invoice_test,
]

_SKIP_REAL = pytest.mark.skipif(
    not all(p.exists() for p in _RAW_PATHS),
    reason=(
        "faltan los CSV de data/raw/ (no se versionan: propiedad de STEG/Zindi); "
        "el caso con ids reales de client_test solo corre donde están los datos"
    ),
)


@pytest.fixture(scope="module")
def real_clients() -> tuple[pd.DataFrame, pd.DataFrame]:
    from steg.data.load import load_raw_data

    dataset = load_raw_data()
    return (
        dataset.client_train.set_index("client_id"),
        dataset.client_test.set_index("client_id"),
    )


def _real_frame(clients: pd.DataFrame) -> pd.DataFrame:
    """Explicativas reales con los nombres que usa ``_CALLS``."""
    return pd.DataFrame(
        {
            "x": clients["region"].astype("float64"),
            "z": clients["client_catg"].astype("float64"),
            "disrict": clients["disrict"].astype(str),
            "flag": clients["client_catg"] == 11,
        },
        index=clients.index,
    )


@_SKIP_REAL
@pytest.mark.parametrize("name", FUNCTIONS)
def test_real_client_test_ids_raise(name, real_clients):
    _, client_test = real_clients
    feats = _real_frame(client_test)
    # client_test no tiene etiqueta: se fabrica una de ceros con sus ids. Lo que se
    # prueba es que la guardia rechaza el índice, no el valor.
    fake_target = pd.Series(0.0, index=client_test.index, name="target")
    n_test = len(client_test)
    with pytest.raises(PartitionLeakError, match=rf"{n_test} de {n_test} filas fallaron"):
        _CALLS[name](feats, fake_target)


@_SKIP_REAL
def test_real_train_passes_and_one_real_test_id_fails(real_clients):
    client_train, client_test = real_clients
    feats = _real_frame(client_train)
    target = client_train["target"]
    rate = bivariate.target_rate_by_category(feats["disrict"], target, "disrict")
    assert int(rate["n"].sum()) == len(client_train)
    flag = bivariate.binary_flag_vs_target(feats["flag"], target, "flag")
    assert flag["n_flagged"] + flag["n_not_flagged"] == len(client_train)

    # Un solo id real de client_test entre todo train basta para fallar.
    mixed = pd.concat([feats, _real_frame(client_test).iloc[:1]])
    mixed_target = pd.concat(
        [target, pd.Series(0.0, index=client_test.index[:1], name="target")]
    )
    with pytest.raises(PartitionLeakError, match=r"\b1 de \d+ filas fallaron"):
        bivariate.binary_flag_vs_target(mixed["flag"], mixed_target, "flag")


def test_skip_reason_is_explicit():
    reason = _SKIP_REAL.kwargs["reason"]
    assert re.search(r"data/raw/", reason)
