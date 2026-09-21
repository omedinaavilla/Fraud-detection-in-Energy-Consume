"""Ayudantes de cómputo para el análisis univariado, temporal y relacional.

Este módulo es una **librería sin opinión de negocio**: funciones puras que reciben
columnas y devuelven tablas. No decide qué mirar, no interpreta y no escribe informes.
Esa parte —la exploración narrativa de la Fase 1— vive en `notebooks/01_eda.ipynb`,
que es la fuente de verdad del EDA y desde donde se exportan `reports/EDA/*.md`,
`reports/tables/*.csv` y `reports/figures/*.png`.

La división es deliberada y sigue la distinción de fases del proyecto:

* Fase 0 (`profile.py`): pipeline repetible sin intervención humana, corre con
  `make audit`.
* Fase 1 (este módulo + `bivariate.py` + `figures.py`, orquestados desde el notebook):
  exploración que un humano lee y de la que salen decisiones.

Ninguna función de aquí mira `target`. Las que sí lo hacen están en `bivariate.py` y
solo pueden aplicarse a la partición de entrenamiento (regla de higiene de
`.claude/skills/steg-eda-protocol/SKILL.md`).
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
import pandas as pd
from scipy import stats

from steg.config import SEED

#: Percentiles que se reportan para toda numérica. La skill de protocolo exige
#: percentiles y no solo media/desviación: en las columnas de consumo la media está
#: dominada por la cola.
PERCENTILES: tuple[float, ...] = (0.01, 0.05, 0.25, 0.50, 0.75, 0.95, 0.99)

#: Máximo de categorías que se tabulan antes de agrupar el resto en "otras".
TOP_K_CATEGORIES: int = 12

#: Tamaño máximo de submuestra para pruebas costosas (KS sobre millones de filas).
SAMPLE_SIZE: int = 200_000


# --- Proporciones y asociación -----------------------------------------------------


def wilson_interval(k: int, n: int, z: float = 1.959963985) -> tuple[float, float]:
    """Intervalo de Wilson al 95 % para una proporción, en proporción (no en %).

    Se usa en vez del intervalo normal porque varias categorías tienen pocos casos y
    la aproximación normal produce límites fuera de [0, 1] con tasas tan bajas como la
    de este problema.
    """
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    denom = 1.0 + z**2 / n
    center = (p + z**2 / (2 * n)) / denom
    half = (z / denom) * np.sqrt(p * (1 - p) / n + z**2 / (4 * n**2))
    return (max(0.0, center - half), min(1.0, center + half))


def cramers_v(table: np.ndarray | pd.DataFrame) -> dict[str, float]:
    """Cramér's V con corrección de sesgo, chi-cuadrado y su diagnóstico de validez.

    Devuelve también ``min_expected`` y ``pct_cells_expected_lt5``: el chi-cuadrado no
    es válido si demasiadas celdas esperadas caen por debajo de 5
    (``steg-eda-statistics``), y con variables de 25 categorías eso ocurre de verdad.

    La corrección de sesgo (Bergsma, 2013) importa cuando hay muchas categorías y una
    clase rara: la V sin corregir sobreestima la asociación.
    """
    arr = np.asarray(table, dtype="float64")
    n = arr.sum()
    chi2, p, dof, expected = stats.chi2_contingency(arr, correction=False)
    r, c = arr.shape
    phi2 = chi2 / n
    phi2_corr = max(0.0, phi2 - (r - 1) * (c - 1) / (n - 1))
    r_corr = r - (r - 1) ** 2 / (n - 1)
    c_corr = c - (c - 1) ** 2 / (n - 1)
    denom = min(r_corr - 1, c_corr - 1)
    v_corr = float(np.sqrt(phi2_corr / denom)) if denom > 0 else float("nan")
    v_raw = float(np.sqrt(phi2 / min(r - 1, c - 1))) if min(r - 1, c - 1) > 0 else float("nan")
    return {
        "cramers_v": v_raw,
        "cramers_v_bias_corrected": v_corr,
        "chi2": float(chi2),
        "p_value": float(p),
        "dof": int(dof),
        "n": int(n),
        "min_expected": float(expected.min()),
        "pct_cells_expected_lt5": float(100.0 * (expected < 5).mean()),
    }


def group_rare_categories(
    values: pd.Series, top_k: int = TOP_K_CATEGORIES, other_label: str = "otras"
) -> pd.Series:
    """Deja las ``top_k`` categorías más frecuentes y colapsa el resto en ``other_label``.

    Devuelve texto para que el orden no dependa del dtype original.
    """
    counts = values.value_counts(dropna=False)
    keep = set(counts.index[:top_k])
    return values.map(lambda v: str(v) if v in keep else other_label).astype("string")


def maybe_group(values: pd.Series, top_k: int = TOP_K_CATEGORIES) -> tuple[pd.Series, bool]:
    """Agrupa categorías raras solo si la columna supera ``top_k`` valores.

    Devuelve (serie, se_agrupó) para que quien llame pueda declararlo en la figura o la
    tabla, como exige la skill de visuales.
    """
    if values.nunique(dropna=False) > top_k:
        return group_rare_categories(values, top_k=top_k), True
    return values.astype("string"), False


# --- Descripción de una numérica ---------------------------------------------------


def describe_numeric(s: pd.Series, percentiles: Sequence[float] = PERCENTILES) -> dict[str, float]:
    """Forma de la distribución: percentiles, sesgo, curtosis, masa en cero y atípicos.

    Los atípicos se cuentan por IQR robusto (percentiles 25/75), no por z-score: la
    media y la desviación están dominadas por la cola en las columnas de consumo
    (``steg-eda-statistics``).
    """
    arr = pd.to_numeric(s, errors="coerce").dropna()
    n = int(arr.size)
    if n == 0:
        return {}
    q1, q3 = float(arr.quantile(0.25)), float(arr.quantile(0.75))
    iqr = q3 - q1
    lo_fence, hi_fence = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    n_out_hi = int((arr > hi_fence).sum())
    out: dict[str, float] = {
        "n": n,
        "n_zero": int((arr == 0).sum()),
        "pct_zero": round(100.0 * float((arr == 0).mean()), 4),
        "n_negative": int((arr < 0).sum()),
        "min": float(arr.min()),
        "max": float(arr.max()),
        "mean": float(arr.mean()),
        "std": float(arr.std()),
        "skew": float(arr.skew()),
        "kurtosis": float(arr.kurtosis()),
        "iqr": iqr,
        "iqr_upper_fence": hi_fence,
        "n_outliers_high_iqr": n_out_hi,
        "pct_outliers_high_iqr": round(100.0 * n_out_hi / n, 4),
        "n_outliers_low_iqr": int((arr < lo_fence).sum()),
    }
    for q in percentiles:
        out[f"p{int(round(q * 100)):02d}"] = float(arr.quantile(q))
    return out


def numeric_profile(df: pd.DataFrame, cols: Sequence[str], label: str) -> pd.DataFrame:
    """Aplica :func:`describe_numeric` a varias columnas. Una fila por columna."""
    rows = []
    for col in cols:
        row: dict[str, object] = {"table": label, "column": col}
        row.update(describe_numeric(df[col]))
        rows.append(row)
    return pd.DataFrame(rows)


def categorical_profile(
    df: pd.DataFrame, cols: Sequence[str], label: str, top_k: int = TOP_K_CATEGORIES
) -> pd.DataFrame:
    """Frecuencias de varias categóricas, con las raras agrupadas si hace falta."""
    rows = []
    n = len(df)
    for col in cols:
        n_unique = int(df[col].nunique(dropna=False))
        values, grouped = maybe_group(df[col], top_k=top_k)
        for value, count in values.value_counts(dropna=False).items():
            rows.append(
                {
                    "table": label,
                    "column": col,
                    "n_unique_original": n_unique,
                    "rare_grouped": grouped,
                    "value": str(value),
                    "n": int(count),
                    "pct": round(100.0 * count / n, 4),
                }
            )
    return pd.DataFrame(rows)


def flag_rate_table(
    df: pd.DataFrame, flags: Sequence[str], label: str, id_col: str = "client_id"
) -> pd.DataFrame:
    """Tasa base de cada bandera booleana, con intervalo de Wilson y clientes tocados.

    El protocolo trata estas banderas como el equivalente de un faltante informativo:
    interesa su tasa base antes de cualquier cruce con la etiqueta.
    """
    rows = []
    n = len(df)
    for flag in flags:
        k = int(df[flag].sum())
        lo, hi = wilson_interval(k, n)
        rows.append(
            {
                "table": label,
                "flag": flag,
                "n_rows": n,
                "n_flagged": k,
                "pct_flagged": round(100.0 * k / n, 4),
                "wilson_lo_pct": round(100.0 * lo, 4),
                "wilson_hi_pct": round(100.0 * hi, 4),
                "n_clients_affected": int(df.loc[df[flag], id_col].nunique()),
            }
        )
    return pd.DataFrame(rows)


# --- Temporal por cliente ----------------------------------------------------------


def per_client_temporal(
    invoice: pd.DataFrame,
    id_col: str = "client_id",
    date_col: str = "invoice_date",
    stream_col: str = "counter_type",
) -> pd.DataFrame:
    """Cobertura temporal por cliente: ventana, cadencia y huecos entre facturas.

    El hueco se calcula de dos formas porque un cliente puede tener más de una serie de
    facturas en paralelo (en STEG, contador eléctrico y de gas):

    * ``median_gap_days`` / ``max_gap_days``: sobre el flujo completo de facturas del
      cliente. Es la cadencia con la que recibe documentos.
    * ``median_gap_days_within_stream`` / ``max_gap_days_within_stream``: dentro de cada
      valor de ``stream_col`` por separado. Es la cadencia real de lectura de un
      contador.

    Confundir las dos hace que un cliente con dos contadores parezca leído cada pocos
    días. Un hueco puede ser 0 cuando hay facturas duplicadas en la misma fecha.
    """
    inv = invoice[[id_col, stream_col, date_col]].sort_values([id_col, date_col])
    inv = inv.assign(_gap=inv.groupby(id_col, observed=True)[date_col].diff().dt.days)

    by_stream = inv.sort_values([id_col, stream_col, date_col])
    by_stream = by_stream.assign(
        _gap_stream=by_stream.groupby([id_col, stream_col], observed=True)[date_col]
        .diff()
        .dt.days
    )

    agg = inv.groupby(id_col, observed=True).agg(
        n_invoices=(date_col, "size"),
        first_invoice=(date_col, "min"),
        last_invoice=(date_col, "max"),
        n_streams=(stream_col, "nunique"),
        median_gap_days=("_gap", "median"),
        max_gap_days=("_gap", "max"),
        mean_gap_days=("_gap", "mean"),
    )
    agg = agg.join(
        by_stream.groupby(id_col, observed=True).agg(
            median_gap_days_within_stream=("_gap_stream", "median"),
            max_gap_days_within_stream=("_gap_stream", "max"),
        )
    )
    agg["span_days"] = (agg["last_invoice"] - agg["first_invoice"]).dt.days
    agg["span_years"] = agg["span_days"] / 365.25
    agg["invoices_per_year"] = np.where(
        agg["span_years"] > 0, agg["n_invoices"] / agg["span_years"], np.nan
    )
    return agg.reset_index()


def summarize_columns(df: pd.DataFrame, cols: Sequence[str], label: str) -> pd.DataFrame:
    """Alias legible de :func:`numeric_profile` para tablas ya agregadas por cliente."""
    return numeric_profile(df, cols, label)


def counts_per_key(df: pd.DataFrame, key: str, value: str) -> pd.Series:
    """Número de valores distintos de ``value`` por cada ``key``. Útil para responder
    'cuántos clientes comparten este contador' y su simétrica."""
    return df.groupby(key, observed=True)[value].nunique()


# --- Diferencia de distribución train vs. test -------------------------------------


def ks_two_sample(
    a: pd.Series, b: pd.Series, sample_size: int = SAMPLE_SIZE, seed: int = SEED
) -> dict[str, float]:
    """Kolmogorov-Smirnov de dos muestras con el valor crítico explícito.

    Con cientos de miles de filas el p-valor del KS rechaza por diferencias que no
    importan. Se reporta el estadístico D junto al crítico al 5 % para el mismo par de
    tamaños, que es la referencia que permite leer D como grande o trivial. Si una
    muestra excede ``sample_size`` se submuestrea con ``seed`` fija, para que el
    resultado sea regenerable.
    """
    rng = np.random.default_rng(seed)
    x = pd.to_numeric(a, errors="coerce").dropna().to_numpy()
    y = pd.to_numeric(b, errors="coerce").dropna().to_numpy()
    n_x_full, n_y_full = x.size, y.size
    if x.size > sample_size:
        x = rng.choice(x, size=sample_size, replace=False)
    if y.size > sample_size:
        y = rng.choice(y, size=sample_size, replace=False)
    res = stats.ks_2samp(x, y)
    return {
        "ks_d": float(res.statistic),
        "p_value": float(res.pvalue),
        "ks_d_critical_05": float(1.36 * np.sqrt(1.0 / x.size + 1.0 / y.size)),
        "n_train_used": int(x.size),
        "n_test_used": int(y.size),
        "n_train_total": int(n_x_full),
        "n_test_total": int(n_y_full),
    }


def compare_numeric(
    a: pd.Series, b: pd.Series, column: str, level: str, unit: str = ""
) -> dict[str, object]:
    """Una fila de tabla de comparación train/test para una numérica (KS)."""
    res = ks_two_sample(a, b)
    return {
        "level": level,
        "column": column,
        "test": "KS dos muestras",
        "effect_size_name": "D",
        "effect_size": round(res["ks_d"], 6),
        "reference_name": "D crítico 5 %",
        "reference": round(res["ks_d_critical_05"], 6),
        "max_abs_share_diff_pp": np.nan,
        "n_categories_train": np.nan,
        "n_categories_test": np.nan,
        "p_value": res["p_value"],
        "n_train": res["n_train_total"],
        "n_test": res["n_test_total"],
        "n_train_used": res["n_train_used"],
        "n_test_used": res["n_test_used"],
        "unit": unit,
    }


def compare_categorical(
    a: pd.Series, b: pd.Series, column: str, level: str, top_k: int = TOP_K_CATEGORIES
) -> dict[str, object]:
    """Una fila de tabla de comparación train/test para una categórica (Cramér's V).

    Añade ``max_abs_share_diff_pp``: la mayor diferencia de cuota entre las dos
    muestras, en puntos porcentuales. Es la traducción interpretable de la V — una V
    pequeña sobre millones de filas sigue sonando a "algo pasa" si no se dice cuánto.
    """
    a_g, _ = maybe_group(a, top_k=top_k)
    b_g, _ = maybe_group(b, top_k=top_k)
    cats = sorted(set(a_g.dropna().unique()) | set(b_g.dropna().unique()))
    table = np.vstack(
        [
            a_g.value_counts().reindex(cats, fill_value=0).to_numpy(),
            b_g.value_counts().reindex(cats, fill_value=0).to_numpy(),
        ]
    )
    kept = table[:, table.sum(axis=0) > 0]
    res = cramers_v(kept)
    share_a = 100.0 * kept[0] / kept[0].sum()
    share_b = 100.0 * kept[1] / kept[1].sum()
    return {
        "level": level,
        "column": column,
        "test": "chi-cuadrado de homogeneidad",
        "effect_size_name": "Cramér's V (corregida)",
        "effect_size": round(res["cramers_v_bias_corrected"], 6),
        "reference_name": "mínima celda esperada",
        "reference": round(res["min_expected"], 2),
        "max_abs_share_diff_pp": round(float(np.abs(share_a - share_b).max()), 4),
        "n_categories_train": int(a.nunique(dropna=False)),
        "n_categories_test": int(b.nunique(dropna=False)),
        "p_value": res["p_value"],
        "n_train": int(len(a)),
        "n_test": int(len(b)),
        "n_train_used": int(len(a)),
        "n_test_used": int(len(b)),
        "unit": f"{kept.shape[1]} categorías tras agrupar",
    }


# --- Formato de salida -------------------------------------------------------------


def mil(value: float | int) -> str:
    """Entero con separador de millar español ('4.476.738').

    Existe como función en vez de un ``.replace(',', '.')`` sobre la frase completa,
    que convertiría también las comas de la prosa en puntos.
    """
    return f"{int(round(float(value))):,}".replace(",", ".")


def md_table(df: pd.DataFrame, cols: Sequence[str], float_fmt: str = "{:.4g}") -> str:
    """Renderiza un DataFrame como tabla markdown en convención numérica española.

    Los enteros y los flotantes de parte decimal nula llevan punto de millar; el resto
    se redondea a cuatro cifras significativas con coma decimal. La distinción evita que
    ``{:.4g}`` convierta una lectura de contador de 18.220 en ``1.822e+04``, que es
    ilegible en una tabla de un informe. Los valores no definidos salen como '—'.
    """
    lines = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for _, row in df[list(cols)].iterrows():
        cells = []
        for v in row:
            if isinstance(v, bool | np.bool_):
                cells.append("sí" if v else "no")
            elif isinstance(v, int | np.integer):
                cells.append(mil(v))
            elif isinstance(v, float | np.floating):
                if not np.isfinite(v):
                    cells.append("—")
                elif float(v).is_integer() and abs(v) >= 1000:
                    cells.append(mil(v))
                else:
                    cells.append(float_fmt.format(v).replace(".", ","))
            elif v is None or (not isinstance(v, str) and pd.isna(v)):
                cells.append("—")
            else:
                cells.append(str(v))
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)
