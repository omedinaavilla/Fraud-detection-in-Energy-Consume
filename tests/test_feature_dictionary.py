"""Toda columna de data/processed/ debe estar documentada en el diccionario de
variables (sección 9 de contextPrompt.md).

``src/steg/features/build.py`` y ``dictionary.py`` son stubs hasta el incremento de la
Fase 3 (ver sus docstrings): todavía no existe ``data/processed/`` ni un diccionario
que verificar. Este test queda escrito ahora, en skip explícito, para que el
incremento de Fase 3 lo active en vez de tener que redescubrir el requisito.
"""

from __future__ import annotations

import pytest

from steg.config import DATA_PROCESSED_DIR, REPORTS_TABLES_DIR

FEATURE_DICTIONARY_PATH = REPORTS_TABLES_DIR / "feature_dictionary.csv"


@pytest.mark.skipif(
    not DATA_PROCESSED_DIR.exists() or not any(DATA_PROCESSED_DIR.glob("*.parquet")),
    reason="data/processed/ aún no existe: pendiente del incremento de la Fase 3",
)
def test_every_processed_column_is_documented():
    import pandas as pd

    dictionary = pd.read_csv(FEATURE_DICTIONARY_PATH)
    documented = set(dictionary["column"])

    for path in DATA_PROCESSED_DIR.glob("*.parquet"):
        df = pd.read_parquet(path)
        undocumented = set(df.columns) - documented
        assert not undocumented, f"{path.name}: columnas sin documentar: {undocumented}"
