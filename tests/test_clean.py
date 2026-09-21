"""Cada regla de limpieza contra un fixture sintético con el caso patológico exacto."""

from __future__ import annotations

from steg.data.clean import (
    clean_invoice,
    drop_exact_duplicates,
    mark_counter_statue_invalid,
    mark_index_regression,
    mark_logical_duplicates,
    mark_months_number_invalid,
    mark_reading_remarque_invalid,
)
from tests.conftest import make_invoice_df


def test_mark_counter_statue_invalid_flags_garbage_values():
    df = make_invoice_df(
        [
            {"counter_statue": "0"},
            {"counter_statue": "5"},
            {"counter_statue": "A"},
            {"counter_statue": "618"},
        ]
    )
    out, n = mark_counter_statue_invalid(df)
    assert n == 2
    assert out["counter_statue_invalid"].tolist() == [False, False, True, True]


def test_mark_reading_remarque_invalid_flags_counter_code_leftovers():
    df = make_invoice_df(
        [
            {"reading_remarque": 6},
            {"reading_remarque": 9},
            {"reading_remarque": 203},  # valor propio de counter_code
        ]
    )
    out, n = mark_reading_remarque_invalid(df)
    assert n == 1
    assert out["reading_remarque_invalid"].tolist() == [False, False, True]


def test_mark_months_number_invalid_flags_out_of_range():
    df = make_invoice_df(
        [
            {"months_number": 1},
            {"months_number": 12},
            {"months_number": 0},
            {"months_number": 636624},
        ]
    )
    out, n = mark_months_number_invalid(df)
    assert n == 2
    assert out["months_number_invalid"].tolist() == [False, False, True, True]


def test_mark_index_regression_flags_new_below_old():
    df = make_invoice_df(
        [
            {"old_index": 100, "new_index": 200},
            {"old_index": 200, "new_index": 100},
        ]
    )
    out, n = mark_index_regression(df)
    assert n == 1
    assert out["index_regression"].tolist() == [False, True]


def test_drop_exact_duplicates_removes_only_identical_rows():
    df = make_invoice_df(
        [
            {"client_id": "a", "counter_number": 1},
            {"client_id": "a", "counter_number": 1},  # duplicado exacto
            {"client_id": "b", "counter_number": 2},
        ]
    )
    out, n = drop_exact_duplicates(df)
    assert n == 1
    assert len(out) == 2


def test_mark_logical_duplicates_flags_same_key_different_values():
    df = make_invoice_df(
        [
            {
                "client_id": "a",
                "invoice_date": "2014-03-24",
                "counter_number": 1,
                "consommation_level_1": 82,
            },
            {
                "client_id": "a",
                "invoice_date": "2014-03-24",
                "counter_number": 1,
                "consommation_level_1": 999,  # misma clave lógica, distinto consumo
            },
            {"client_id": "b", "invoice_date": "2014-03-24", "counter_number": 2},
        ]
    )
    out, n = mark_logical_duplicates(df)
    assert n == 1
    assert out["logical_duplicate"].tolist() == [False, True, False]


def test_clean_invoice_report_matches_individual_rule_counts():
    df = make_invoice_df(
        [
            {"counter_statue": "A", "months_number": 0},
            {"counter_statue": "0", "months_number": 4},
            {"counter_statue": "0", "months_number": 4},  # exacto duplicado de la fila anterior
        ]
    )
    cleaned, report = clean_invoice(df, table_name="invoice_test_synth")
    assert report.counts["exact_duplicates_dropped"] == 1
    assert report.counts["months_number_invalid"] == 1
    assert report.counts["counter_statue_invalid"] == 1
    assert len(cleaned) == 2
