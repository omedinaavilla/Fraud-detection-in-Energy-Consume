"""Ayudantes de cómputo para la relación de una variable con la etiqueta.

Como ``univariate.py``, este módulo es una **librería sin opinión de negocio**:
funciones puras que reciben una columna y un vector binario y devuelven un tamaño de
efecto con su intervalo. No decide qué variables construir ni interpreta resultados;
eso ocurre en `notebooks/01_eda.ipynb`.

**Regla de higiene (`.claude/skills/steg-eda-protocol/SKILL.md`).** Todo lo que hay
aquí recibe una etiqueta, así que solo puede aplicarse a la partición de
entrenamiento. Mirar variables explicativas de test contra la etiqueta de train sería
fuga, y mirar la etiqueta en test es imposible porque no existe.

**Contrato (lo hace cumplir cada función, no quien llama).** Las 7 funciones públicas
que reciben etiqueta (``numeric_vs_target``, ``numeric_table_vs_target``,
``categorical_vs_target``, ``target_rate_by_category``, ``binary_flag_vs_target``,
``mutual_information_ranking`` y ``fold_prevalence``), antes de cualquier filtro o
máscara:

1. llaman a :func:`steg.data.guards.assert_train_partition` sobre el índice de la
   etiqueta (``target.index`` o ``y.index``): tiene que ser un índice de ``client_id``
   con todos los ids ``train_*``; un ``RangeIndex`` posicional se rechaza;
2. exigen que ese índice sea **único** (una fila por cliente);
3. exigen alineación estricta por firma: el índice de la variable explicativa
   (``values``, ``flag``, ``df`` o ``X``) tiene que ser *igual* (``Index.equals``: mismos
   ids en el mismo orden) al de la etiqueta. No se realinea ni se reordena nada;
4. ``fold_prevalence`` además materializa ``splits`` una sola vez (acepta generadores
   como ``GroupKFold.split``), exige al menos un fold y que todo ``valid_idx`` sea un
   array de enteros en ``[0, len(target))``, para que ``iloc`` no envuelva índices
   negativos; una máscara booleana se rechaza (hay que pasar posiciones).

Cualquier incumplimiento lanza :class:`steg.data.guards.PartitionLeakError`. No hay
parámetro, variable de entorno ni flag que desactive la verificación.

Límites (lo que el contrato NO garantiza): no distingue train de una partición de
validación interna, porque ambas tienen ids ``train_*`` — separarlas es trabajo del
split agrupado por cliente; y solo inspecciona índices, no el origen de los valores:
unas features calculadas desde ``client_test`` y reindexadas a mano con ids ``train_*``
pasarían. Lo segundo exige manipulación deliberada; la alineación por firma sí impide
que una serie con otro índice (o posicional) se cuele por alineación implícita.

**Regla de reporte (`.claude/skills/steg-eda-statistics/SKILL.md`).** Ninguna función
devuelve un p-valor sin su tamaño de efecto. Con 135.493 clientes y 7.566 positivos,
p < 0,001 no es una noticia; el criterio de "vale la pena reportar" lo da el tamaño de
efecto.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.feature_selection import mutual_info_classif

from steg.config import SEED
from steg.data.guards import PartitionLeakError, assert_train_partition
from steg.eda.univariate import cramers_v, maybe_group, wilson_interval

#: Corte por debajo del cual un rank-biserial se considera ruido de muestra grande y
#: no un hallazgo (``steg-eda-statistics``). Quien llame puede justificar otro.
EFFECT_SIZE_THRESHOLD: float = 0.1

#: Remuestreos por defecto del bootstrap. 1.000 da tres cifras estables en el intervalo
#: sin que el cálculo de ~40 variables tarde minutos.
N_BOOTSTRAP: int = 1000


# --- Contrato de partición ---------------------------------------------------------


def _check_label(target: pd.Series, label_name: str = "target") -> None:
    """Guardia de partición + unicidad sobre el índice de la etiqueta."""
    if not isinstance(target, pd.Series):
        raise PartitionLeakError(
            f"{label_name} debe ser una pd.Series indexada por client_id; se recibió "
            f"{type(target).__name__}."
        )
    assert_train_partition(target.index)
    if not target.index.is_unique:
        dup = target.index[target.index.duplicated()].unique().tolist()
        raise PartitionLeakError(
            f"el índice de {label_name} tiene {len(dup)} client_id duplicados "
            f"(ejemplos: {dup[:5]!r}); se exige una fila por cliente."
        )


def _check_aligned(
    features: pd.Series | pd.DataFrame,
    target: pd.Series,
    feat_name: str,
    label_name: str = "target",
) -> None:
    """Alineación estricta: el índice de las explicativas es igual al de la etiqueta."""
    if not isinstance(features, (pd.Series, pd.DataFrame)):
        raise PartitionLeakError(
            f"{feat_name} debe ser pd.Series o pd.DataFrame indexado por client_id; se "
            f"recibió {type(features).__name__}."
        )
    if not features.index.equals(target.index):
        raise PartitionLeakError(
            f"{feat_name}.index no es igual a {label_name}.index (mismos client_id en el "
            f"mismo orden): {len(features.index)} vs {len(target.index)} filas. No se "
            f"realinea implícitamente."
        )


# --- Numérica × binaria ------------------------------------------------------------


def _rank_biserial(values: np.ndarray, target: np.ndarray) -> float:
    """Correlación rank-biserial a partir del estadístico U de Mann-Whitney.

    Equivale a ``2 * AUC - 1``: 0 significa que las dos clases son indistinguibles por
    esta variable, +1 que todo positivo tiene un valor mayor que cualquier negativo.
    Se deriva del U, así que hereda su robustez a las colas extremas del consumo.

    Se implementa sobre ``scipy.stats.rankdata`` en vez de llamar a ``mannwhitneyu``
    porque el bootstrap la ejecuta miles de veces y esta versión no recalcula el
    p-valor, que ahí no se usa.
    """
    pos = target == 1
    n1 = int(pos.sum())
    n0 = int(target.size - n1)
    if n1 == 0 or n0 == 0:
        return float("nan")
    ranks = stats.rankdata(values)
    u1 = ranks[pos].sum() - n1 * (n1 + 1) / 2.0
    return float(2.0 * u1 / (n1 * n0) - 1.0)


def numeric_vs_target(
    values: pd.Series,
    target: pd.Series,
    name: str,
    n_boot: int = N_BOOTSTRAP,
    seed: int = SEED,
) -> dict[str, object]:
    """Mann-Whitney U + rank-biserial + intervalo por bootstrap, para una numérica.

    Se usa Mann-Whitney y no un t-test porque las variables de consumo tienen colas
    extremas y la normalidad no se sostiene.

    **Unidad del bootstrap.** Cada fila de ``values`` tiene que ser un cliente, no una
    factura: el remuestreo sortea filas con reemplazo, y si las filas fueran facturas
    el intervalo saldría artificialmente estrecho por tratar como independientes varias
    observaciones del mismo cliente (``steg-validation-protocol``). Quien llama es
    responsable de pasar una tabla agregada a nivel cliente.

    También devuelve las medianas por clase, porque un tamaño de efecto sin la dirección
    ni la magnitud original no se puede leer.
    """
    _check_label(target)
    _check_aligned(values, target, "values")
    mask = values.notna()
    x = pd.to_numeric(values[mask], errors="coerce").to_numpy(dtype="float64")
    y = target[mask].to_numpy(dtype="int8")
    n1 = int((y == 1).sum())
    n0 = int((y == 0).sum())
    if n1 == 0 or n0 == 0 or x.size == 0:
        return {"variable": name, "n": int(x.size), "n_pos": n1, "n_neg": n0}

    mw = stats.mannwhitneyu(x[y == 1], x[y == 0], alternative="two-sided")
    point = _rank_biserial(x, y)

    rng = np.random.default_rng(seed)
    boot = np.empty(n_boot, dtype="float64")
    n = x.size
    for i in range(n_boot):
        idx = rng.integers(0, n, size=n)
        boot[i] = _rank_biserial(x[idx], y[idx])
    lo, hi = np.nanpercentile(boot, [2.5, 97.5])

    return {
        "variable": name,
        "n": int(n),
        "n_pos": n1,
        "n_neg": n0,
        "median_neg": float(np.median(x[y == 0])),
        "median_pos": float(np.median(x[y == 1])),
        "mean_neg": float(np.mean(x[y == 0])),
        "mean_pos": float(np.mean(x[y == 1])),
        "rank_biserial": round(point, 5),
        "ci95_lo": round(float(lo), 5),
        "ci95_hi": round(float(hi), 5),
        "abs_effect": round(abs(point), 5),
        "above_threshold": bool(abs(point) >= EFFECT_SIZE_THRESHOLD),
        "mannwhitney_u": float(mw.statistic),
        "p_value": float(mw.pvalue),
        "n_bootstrap": n_boot,
    }


def numeric_table_vs_target(
    df: pd.DataFrame,
    target: pd.Series,
    cols: Sequence[str],
    n_boot: int = N_BOOTSTRAP,
    seed: int = SEED,
) -> pd.DataFrame:
    """Aplica :func:`numeric_vs_target` a varias columnas, ordenado por efecto absoluto."""
    _check_label(target)
    _check_aligned(df, target, "df")
    rows = [numeric_vs_target(df[c], target, c, n_boot=n_boot, seed=seed) for c in cols]
    out = pd.DataFrame(rows)
    return out.sort_values("abs_effect", ascending=False).reset_index(drop=True)


# --- Categórica × binaria ----------------------------------------------------------


def categorical_vs_target(
    values: pd.Series, target: pd.Series, name: str, top_k: int | None = None
) -> dict[str, object]:
    """Cramér's V corregida + chi-cuadrado entre una categórica y la etiqueta.

    Si ``top_k`` se indica, las categorías raras se agrupan antes de construir la tabla
    de contingencia: con 25 categorías y una tasa de positivos de 5,58 %, hay celdas
    esperadas por debajo de 5 y el chi-cuadrado deja de ser válido. El resultado
    incluye ``pct_cells_expected_lt5`` para que eso quede visible en el reporte.
    """
    _check_label(target)
    _check_aligned(values, target, "values")
    v = values if top_k is None else maybe_group(values, top_k=top_k)[0]
    table = pd.crosstab(v, target)
    res = cramers_v(table.to_numpy())
    res.update(
        {
            "variable": name,
            "n_categories": int(table.shape[0]),
            "grouped": top_k is not None and values.nunique(dropna=False) > top_k,
        }
    )
    return res


def target_rate_by_category(
    values: pd.Series, target: pd.Series, name: str, top_k: int | None = None
) -> pd.DataFrame:
    """Tasa de positivos por categoría con intervalo de Wilson y ``n``.

    El protocolo prohíbe reportar la tasa por categoría como un punto suelto: algunas
    categorías tienen pocos clientes y su intervalo es ancho. Se devuelve también el
    ``lift`` frente a la tasa global, que es lo que hace comparables dos categorías de
    tamaño muy distinto.
    """
    _check_label(target)
    _check_aligned(values, target, "values")
    v = values if top_k is None else maybe_group(values, top_k=top_k)[0]
    base = float(target.mean())
    rows = []
    for category, idx in v.groupby(v, observed=True).groups.items():
        t = target.loc[idx]
        n, k = int(t.size), int(t.sum())
        lo, hi = wilson_interval(k, n)
        rows.append(
            {
                "variable": name,
                "category": str(category),
                "n": n,
                "n_pos": k,
                "rate_pct": round(100.0 * k / n, 4) if n else np.nan,
                "wilson_lo_pct": round(100.0 * lo, 4),
                "wilson_hi_pct": round(100.0 * hi, 4),
                "lift_vs_base": round((k / n) / base, 4) if n and base else np.nan,
                "base_rate_pct": round(100.0 * base, 4),
            }
        )
    return pd.DataFrame(rows).sort_values("rate_pct", ascending=False).reset_index(drop=True)


def binary_flag_vs_target(flag: pd.Series, target: pd.Series, name: str) -> dict[str, object]:
    """Tasa de positivos con y sin la bandera, más riesgo relativo con intervalo.

    Para una anomalía de captura, el riesgo relativo dice directamente lo que interesa:
    cuántas veces más frecuente es el fraude entre los clientes marcados. El intervalo
    es el logarítmico estándar (Katz), que es el adecuado para una razón.
    """
    _check_label(target)
    _check_aligned(flag, target, "flag")
    f = flag.astype(bool)
    n1, k1 = int(f.sum()), int(target[f].sum())
    n0, k0 = int((~f).sum()), int(target[~f].sum())
    lo1, hi1 = wilson_interval(k1, n1)
    lo0, hi0 = wilson_interval(k0, n0)
    if n1 == 0 or n0 == 0 or k1 == 0 or k0 == 0:
        rr = rr_lo = rr_hi = float("nan")
    else:
        p1, p0 = k1 / n1, k0 / n0
        rr = p1 / p0
        se = np.sqrt(1 / k1 - 1 / n1 + 1 / k0 - 1 / n0)
        rr_lo, rr_hi = float(np.exp(np.log(rr) - 1.96 * se)), float(np.exp(np.log(rr) + 1.96 * se))
    return {
        "variable": name,
        "n_flagged": n1,
        "n_not_flagged": n0,
        "rate_flagged_pct": round(100.0 * k1 / n1, 4) if n1 else np.nan,
        "flagged_wilson_lo_pct": round(100.0 * lo1, 4),
        "flagged_wilson_hi_pct": round(100.0 * hi1, 4),
        "rate_not_flagged_pct": round(100.0 * k0 / n0, 4) if n0 else np.nan,
        "not_flagged_wilson_lo_pct": round(100.0 * lo0, 4),
        "not_flagged_wilson_hi_pct": round(100.0 * hi0, 4),
        "risk_ratio": round(rr, 4) if np.isfinite(rr) else np.nan,
        "rr_ci95_lo": round(rr_lo, 4) if np.isfinite(rr_lo) else np.nan,
        "rr_ci95_hi": round(rr_hi, 4) if np.isfinite(rr_hi) else np.nan,
    }


# --- Información mutua -------------------------------------------------------------


def mutual_information_ranking(
    X: pd.DataFrame,
    y: pd.Series,
    n_permutations: int = 10,
    seed: int = SEED,
    discrete_features: Sequence[bool] | bool = False,
) -> pd.DataFrame:
    """Información mutua de cada columna con la etiqueta, contra un nulo de permutación.

    La información mutua capta relaciones no monótonas que ni Mann-Whitney ni Cramér's
    V ven, pero no trae significancia por sí sola: un estimador de MI sobre 135.493
    filas devuelve valores positivos incluso para ruido puro. Por eso se recalcula con
    la etiqueta barajada ``n_permutations`` veces y se reporta el exceso sobre ese nulo,
    que es la cifra interpretable.
    """
    _check_label(y, "y")
    _check_aligned(X, y, "X", "y")
    X_filled = X.astype("float64").fillna(X.astype("float64").median())
    observed = mutual_info_classif(
        X_filled, y, random_state=seed, discrete_features=discrete_features
    )
    rng = np.random.default_rng(seed)
    null = np.empty((n_permutations, X.shape[1]), dtype="float64")
    for i in range(n_permutations):
        null[i] = mutual_info_classif(
            X_filled,
            rng.permutation(y.to_numpy()),
            random_state=seed + i + 1,
            discrete_features=discrete_features,
        )
    null_mean = null.mean(axis=0)
    null_max = null.max(axis=0)
    return (
        pd.DataFrame(
            {
                "variable": list(X.columns),
                "mutual_info": np.round(observed, 6),
                "null_mean": np.round(null_mean, 6),
                "null_max": np.round(null_max, 6),
                "excess_over_null": np.round(observed - null_mean, 6),
                "above_null_max": observed > null_max,
                "n": int(len(y)),
                "n_permutations": n_permutations,
            }
        )
        .sort_values("excess_over_null", ascending=False)
        .reset_index(drop=True)
    )


# --- Correlación entre explicativas ------------------------------------------------


def spearman_matrix(
    df: pd.DataFrame, cols: Sequence[str], sample: int | None = None, seed: int = SEED
) -> pd.DataFrame:
    """Matriz de correlación de Spearman.

    Spearman y no Pearson por defecto: las variables de consumo no son lineales entre
    sí ni normales (``steg-eda-statistics``). ``sample`` submuestrea con semilla fija
    cuando la tabla tiene millones de filas.
    """
    data = df[list(cols)]
    if sample is not None and len(data) > sample:
        data = data.sample(n=sample, random_state=seed)
    return data.corr(method="spearman")


# --- Evidencia para el protocolo de evaluación -------------------------------------


def fold_prevalence(
    target: pd.Series, splits: Iterable[tuple[np.ndarray, np.ndarray]]
) -> pd.DataFrame:
    """Tasa de positivos y número de positivos en el pliegue de validación de cada fold.

    Es la evidencia directa de la decisión sobre estratificación: si la dispersión de
    la prevalencia entre folds sin estratificar ya está dentro de lo que se espera por
    azar binomial, estratificar no compra nada.

    ``splits`` puede ser cualquier iterable de ``(train_idx, valid_idx)``, incluido un
    generador (``GroupKFold.split``, ``steg.data.split.grouped_kfold_splits``): se
    materializa una sola vez con ``list`` antes de validar y computar, para que la
    validación no lo agote. Cero folds lanza ``PartitionLeakError`` en vez de devolver
    un DataFrame vacío en silencio.

    ``valid_idx`` son posiciones (``iloc``) sobre ``target``; cada una tiene que ser un
    entero en ``[0, len(target))``. Un negativo se rechaza en vez de dejar que ``iloc``
    lo interprete desde el final. Una máscara booleana también se rechaza (dtype no
    entero): hay que pasar posiciones, p. ej. ``np.flatnonzero(mask)``.
    """
    _check_label(target)
    splits = list(splits)
    if not splits:
        raise PartitionLeakError("fold_prevalence: splits no contiene ningún fold.")
    n_target = len(target)
    for i, (_, valid_idx) in enumerate(splits, start=1):
        v = np.asarray(valid_idx)
        if v.size and not np.issubdtype(v.dtype, np.integer):
            raise PartitionLeakError(
                f"fold {i}: valid_idx debe ser entero (posiciones iloc); dtype {v.dtype}."
            )
        if v.size and (int(v.min()) < 0 or int(v.max()) >= n_target):
            raise PartitionLeakError(
                f"fold {i}: valid_idx fuera de [0, {n_target}) "
                f"(min={int(v.min())}, max={int(v.max())})."
            )
    rows = []
    for i, (_, valid_idx) in enumerate(splits, start=1):
        t = target.iloc[valid_idx]
        n, k = int(t.size), int(t.sum())
        lo, hi = wilson_interval(k, n)
        rows.append(
            {
                "fold": i,
                "n_valid": n,
                "n_pos": k,
                "prevalence_pct": round(100.0 * k / n, 4),
                "wilson_lo_pct": round(100.0 * lo, 4),
                "wilson_hi_pct": round(100.0 * hi, 4),
            }
        )
    return pd.DataFrame(rows)


def binomial_sd_pct(p: float, n: int) -> float:
    """Desviación estándar esperada de una prevalencia muestral, en puntos porcentuales.

    Es la referencia contra la que se compara la dispersión observada entre folds: una
    dispersión de ese orden es lo que produce el azar, no un defecto de la partición.
    """
    return float(100.0 * np.sqrt(p * (1 - p) / n))
