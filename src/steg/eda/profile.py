"""Perfilado automático de columnas y auditoría de calidad (Fase 0).

Describe cada columna de las cuatro tablas crudas (tipo, faltantes, cardinalidad,
valores más frecuentes, estadísticos robustos) y ejecuta el catálogo de verificaciones
de calidad: faltantes, duplicados, valores imposibles, incoherencias internas de una
fila, incoherencias entre la tabla de clientes y la de facturas, y desajustes de
categorías entre train y test.

Ninguna verificación mira la relación de una columna con ``target`` más allá de la
prevalencia global: eso es análisis bivariado, pertenece a la Fase 1
(``src/steg/eda/bivariate.py``) y solo puede correr sobre la partición de entrenamiento
(regla de higiene, ``.claude/skills/steg-eda-protocol/SKILL.md``).

La auditoría detecta y cuantifica; no repara. Cada anomalía se marca en
``src/steg/data/clean.py`` con una columna booleana para que la Fase 1 pueda estudiar
si es defecto de captura o señal, y la decisión de qué hacer con ella se registra en
``reports/DECISIONS.md``.

Salidas:
    - ``reports/tables/profile_<tabla>.csv``: una fila por columna.
    - ``reports/tables/quality_checks.csv``: una fila por verificación, con el número
      de filas afectadas y su porcentaje.
    - ``reports/tables/schema_vs_readme.csv``: columna real contra lo que documenta
      ``data/raw/README.md``.
    - ``reports/EDA/00_data_audit.md``: informe legible con todo lo anterior.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime

import numpy as np
import pandas as pd

from steg.config import (
    DATA_CHECKSUMS_PATH,
    DATA_CONTRACT,
    REPORTS_EDA_DIR,
    REPORTS_TABLES_DIR,
)
from steg.data.clean import clean_all
from steg.data.load import compute_and_save_checksums, load_raw_data

logger = logging.getLogger(__name__)

NUMERIC_PERCENTILES = [0.01, 0.25, 0.5, 0.75, 0.99]

CONSUMPTION_COLS = [
    "consommation_level_1",
    "consommation_level_2",
    "consommation_level_3",
    "consommation_level_4",
]

#: Año a partir del cual el volumen de facturación deja de ser residual. Se verifica en
#: la auditoría (``invoice_date_before_volume_break``), no se asume.
VOLUME_BREAK_YEAR = 2005

#: Columnas que el README oficial (``data/raw/README.md``) documenta, con el nombre
#: real en el CSV. Un valor ``False`` significa que la columna existe en el archivo
#: pero el README no la define (la deja con la etiqueta vacía).
README_DOCUMENTED: dict[str, bool] = {
    "client_id": True,
    "disrict": True,
    "client_catg": True,
    "region": True,
    "creation_date": True,
    "target": True,
    "invoice_date": True,
    "tarif_type": True,
    "counter_number": False,
    "counter_statue": True,
    "counter_code": False,
    "reading_remarque": True,
    "counter_coefficient": True,
    "consommation_level_1": True,
    "consommation_level_2": True,
    "consommation_level_3": True,
    "consommation_level_4": True,
    "old_index": True,
    "new_index": True,
    "months_number": True,
    "counter_type": True,
}

#: Nombre con el que el README se refiere a cada columna. Donde difiere del nombre real
#: hay un desajuste que se reporta en ``schema_vs_readme.csv``.
README_NAME: dict[str, str] = {
    "disrict": "District",
    "client_catg": "Client_catg",
    "client_id": "Client_id",
    "region": "Region",
    "creation_date": "Creation_date",
    "target": "Target",
    "invoice_date": "Invoice_date",
    "tarif_type": "Tarif_type",
    "counter_number": "Counter_number",
    "counter_statue": "Counter_statue",
    "counter_code": "Counter_code",
    "reading_remarque": "Reading_remarque",
    "counter_coefficient": "Counter_coefficient",
    "consommation_level_1": "Consommation_level_1",
    "consommation_level_2": "Consommation_level_2",
    "consommation_level_3": "Consommation_level_3",
    "consommation_level_4": "Consommation_level_4",
    "old_index": "Old_index",
    "new_index": "New_index",
    "months_number": "Months_number",
    "counter_type": "Counter_type",
}


def profile_dataframe(df: pd.DataFrame, name: str) -> pd.DataFrame:
    """Perfila cada columna de ``df``. Devuelve un DataFrame con una fila por columna."""
    n = len(df)
    rows = []
    for col in df.columns:
        s = df[col]
        row: dict[str, object] = {
            "table": name,
            "column": col,
            "dtype": str(s.dtype),
            "n_missing": int(s.isna().sum()),
            "pct_missing": round(100 * s.isna().sum() / n, 4) if n else 0.0,
            "n_unique": int(s.nunique(dropna=True)),
            "is_constant": bool(s.nunique(dropna=True) <= 1),
        }
        if pd.api.types.is_numeric_dtype(s):
            desc = s.describe(percentiles=NUMERIC_PERCENTILES)
            row.update(
                {
                    "min": desc.get("min"),
                    "p01": desc.get("1%"),
                    "p25": desc.get("25%"),
                    "median": desc.get("50%"),
                    "p75": desc.get("75%"),
                    "p99": desc.get("99%"),
                    "max": desc.get("max"),
                    "mean": desc.get("mean"),
                    "std": desc.get("std"),
                    "top_value": np.nan,
                    "top_value_freq": np.nan,
                }
            )
        elif pd.api.types.is_datetime64_any_dtype(s):
            row.update(
                {
                    "min": s.min(),
                    "max": s.max(),
                    "p01": np.nan,
                    "p25": np.nan,
                    "median": np.nan,
                    "p75": np.nan,
                    "p99": np.nan,
                    "mean": np.nan,
                    "std": np.nan,
                    "top_value": np.nan,
                    "top_value_freq": np.nan,
                }
            )
        else:
            vc = s.value_counts(dropna=True)
            top_value = vc.index[0] if len(vc) else np.nan
            top_freq = int(vc.iloc[0]) if len(vc) else 0
            row.update(
                {
                    "min": np.nan,
                    "p01": np.nan,
                    "p25": np.nan,
                    "median": np.nan,
                    "p75": np.nan,
                    "p99": np.nan,
                    "max": np.nan,
                    "mean": np.nan,
                    "std": np.nan,
                    "top_value": top_value,
                    "top_value_freq": top_freq,
                }
            )
        rows.append(row)
    return pd.DataFrame(rows)


# --- Catálogo de verificaciones de calidad -----------------------------------------


def _check(
    table: str,
    column: str,
    check: str,
    n_affected: int,
    n_total: int,
    detail: str,
) -> dict[str, object]:
    """Una fila del catálogo de verificaciones. ``detail`` explica qué se encontró."""
    return {
        "table": table,
        "column": column,
        "check": check,
        "n_affected": int(n_affected),
        "n_total": int(n_total),
        "pct_affected": round(100.0 * n_affected / n_total, 6) if n_total else np.nan,
        "detail": detail,
    }


def _client_checks(df: pd.DataFrame, name: str) -> list[dict[str, object]]:
    n = len(df)
    rows = [
        _check(name, "(todas)", "filas_con_algun_nulo", int(df.isna().any(axis=1).sum()), n, ""),
        _check(name, "(todas)", "filas_exactamente_duplicadas", int(df.duplicated().sum()), n, ""),
        _check(
            name,
            "client_id",
            "client_id_duplicado",
            int(df["client_id"].duplicated().sum()),
            n,
            f"{df['client_id'].nunique()} ids únicos",
        ),
    ]
    fecha = df["creation_date"]
    fuera_de_rango = (fecha < pd.Timestamp("1960-01-01")) | (fecha > pd.Timestamp("2020-12-31"))
    rows.append(
        _check(
            name,
            "creation_date",
            "creation_date_fuera_de_rango_plausible",
            int(fuera_de_rango.sum()),
            n,
            f"rango observado {fecha.min():%Y-%m-%d} a {fecha.max():%Y-%m-%d}",
        )
    )
    for col in ("disrict", "client_catg", "region"):
        rows.append(
            _check(
                name,
                col,
                "cardinalidad",
                int(df[col].nunique()),
                n,
                f"valores: {sorted(df[col].unique())[:8]}{'...' if df[col].nunique() > 8 else ''}",
            )
        )
    return rows


def _invoice_checks(df: pd.DataFrame, name: str) -> list[dict[str, object]]:
    n = len(df)
    rows: list[dict[str, object]] = []
    rows.append(
        _check(name, "(todas)", "filas_con_algun_nulo", int(df.isna().any(axis=1).sum()), n, "")
    )
    rows.append(
        _check(name, "(todas)", "filas_exactamente_duplicadas", int(df.duplicated().sum()), n, "")
    )
    dup_key = df.duplicated(subset=["client_id", "invoice_date", "counter_number"], keep="first")
    rows.append(
        _check(
            name,
            "client_id+invoice_date+counter_number",
            "duplicado_por_clave_logica",
            int(dup_key.sum()),
            n,
            "misma clave con contenido potencialmente distinto; no se elimina",
        )
    )

    statue_invalid = ~df["counter_statue"].isin(DATA_CONTRACT.counter_statue_valid)
    valores_raros = sorted(df.loc[statue_invalid, "counter_statue"].unique().tolist())
    rows.append(
        _check(
            name,
            "counter_statue",
            "valor_fuera_del_dominio_documentado",
            int(statue_invalid.sum()),
            n,
            f"valores inesperados: {valores_raros}" if valores_raros else "ninguno",
        )
    )

    rr_invalid = ~df["reading_remarque"].isin(DATA_CONTRACT.reading_remarque_valid)
    rr_raros = sorted(df.loc[rr_invalid, "reading_remarque"].unique().tolist())
    rows.append(
        _check(
            name,
            "reading_remarque",
            "valor_fuera_del_dominio_observado_en_test",
            int(rr_invalid.sum()),
            n,
            f"valores inesperados: {rr_raros}" if rr_raros else "ninguno",
        )
    )

    mn = df["months_number"]
    rows.append(
        _check(name, "months_number", "igual_a_cero", int((mn == 0).sum()), n, "período nulo")
    )
    rows.append(
        _check(
            name,
            "months_number",
            "mayor_que_12",
            int((mn > DATA_CONTRACT.months_number_max).sum()),
            n,
            f"máximo observado {int(mn.max())}",
        )
    )
    rows.append(
        _check(name, "months_number", "negativo", int((mn < 0).sum()), n, "")
    )

    rows.append(
        _check(
            name,
            "old_index/new_index",
            "new_index_menor_que_old_index",
            int((df["new_index"] < df["old_index"]).sum()),
            n,
            "el contador retrocede: cambio de equipo no señalizado o error de captura",
        )
    )
    rows.append(
        _check(
            name,
            "old_index/new_index",
            "indice_negativo",
            int(((df["old_index"] < 0) | (df["new_index"] < 0)).sum()),
            n,
            "",
        )
    )

    niveles = df[CONSUMPTION_COLS].sum(axis=1)
    delta = df["new_index"] - df["old_index"]
    desajuste = niveles != delta
    rows.append(
        _check(
            name,
            "consommation_level_1..4",
            "suma_niveles_distinta_de_new_menos_old",
            int(desajuste.sum()),
            n,
            "la descomposición por nivel tarifario no reconstruye el diferencial de índice",
        )
    )
    rows.append(
        _check(
            name,
            "consommation_level_1..4",
            "consumo_negativo",
            int((df[CONSUMPTION_COLS] < 0).any(axis=1).sum()),
            n,
            "",
        )
    )
    rows.append(
        _check(
            name,
            "consommation_level_1..4",
            "consumo_total_cero",
            int((niveles == 0).sum()),
            n,
            "factura emitida sin consumo registrado",
        )
    )

    rows.append(
        _check(
            name,
            "counter_number",
            "igual_a_cero",
            int((df["counter_number"] == 0).sum()),
            n,
            "valor centinela: no identifica ningún contador",
        )
    )
    compartidos = df.groupby("counter_number", observed=True)["client_id"].nunique()
    n_compartidos = int((compartidos > 1).sum())
    rows.append(
        _check(
            name,
            "counter_number",
            "valor_compartido_por_varios_clientes",
            n_compartidos,
            int(compartidos.size),
            f"máximo {int(compartidos.max())} clientes con el mismo valor; "
            f"el denominador son valores distintos, no filas",
        )
    )

    rows.append(
        _check(
            name,
            "counter_coefficient",
            "igual_a_cero",
            int((df["counter_coefficient"] == 0).sum()),
            n,
            f"máximo observado {int(df['counter_coefficient'].max())}",
        )
    )

    fechas = df["invoice_date"]
    rows.append(
        _check(
            name,
            "invoice_date",
            "anterior_al_quiebre_de_volumen",
            int((fechas.dt.year < VOLUME_BREAK_YEAR).sum()),
            n,
            f"el README declara cobertura {VOLUME_BREAK_YEAR}-2019; rango real "
            f"{fechas.min():%Y-%m-%d} a {fechas.max():%Y-%m-%d}",
        )
    )
    return rows


def _cross_table_checks(
    client: pd.DataFrame, invoice: pd.DataFrame, particion: str
) -> list[dict[str, object]]:
    """Consistencia entre la tabla de clientes y la de facturas de la misma partición."""
    n_clients = len(client)
    client_ids = set(client["client_id"])
    invoice_ids = set(invoice["client_id"])
    rows = [
        _check(
            f"{particion}",
            "client_id",
            "cliente_sin_ninguna_factura",
            len(client_ids - invoice_ids),
            n_clients,
            "sin historial no hay variables agregadas",
        ),
        _check(
            f"{particion}",
            "client_id",
            "factura_sin_cliente",
            len(invoice_ids - client_ids),
            len(invoice_ids),
            "rompería la integridad referencial",
        ),
    ]
    primera = invoice.groupby("client_id", observed=True)["invoice_date"].min()
    comparable = client.set_index("client_id")["creation_date"].reindex(primera.index)
    anterior = primera < comparable
    dias = (comparable - primera).dt.days
    rows.append(
        _check(
            f"{particion}",
            "creation_date vs. min(invoice_date)",
            "primera_factura_anterior_al_alta",
            int(anterior.sum()),
            int(primera.size),
            f"mediana del adelanto {float(dias[anterior].median()):.0f} días, "
            f"máximo {int(dias[anterior].max())} días"
            if int(anterior.sum())
            else "ninguno",
        )
    )
    return rows


def _train_test_checks(
    client_train: pd.DataFrame,
    client_test: pd.DataFrame,
    invoice_train: pd.DataFrame,
    invoice_test: pd.DataFrame,
) -> list[dict[str, object]]:
    """Desajustes entre las dos particiones de Zindi que afectarían a un modelo."""
    rows = [
        _check(
            "train vs. test",
            "client_id",
            "clientes_en_ambas_particiones",
            len(set(client_train["client_id"]) & set(client_test["client_id"])),
            len(client_train),
            "un solapamiento invalidaría cualquier evaluación",
        )
    ]
    for col, izq, der in (
        ("region", client_train, client_test),
        ("disrict", client_train, client_test),
        ("client_catg", client_train, client_test),
        ("tarif_type", invoice_train, invoice_test),
        ("counter_code", invoice_train, invoice_test),
    ):
        solo_train = sorted(set(izq[col].unique()) - set(der[col].unique()))
        solo_test = sorted(set(der[col].unique()) - set(izq[col].unique()))
        rows.append(
            _check(
                "train vs. test",
                col,
                "categorias_presentes_en_una_sola_particion",
                len(solo_train) + len(solo_test),
                int(izq[col].nunique()),
                f"solo en train: {solo_train}; solo en test: {solo_test}",
            )
        )
    return rows


def build_quality_checks(
    client_train: pd.DataFrame,
    client_test: pd.DataFrame,
    invoice_train: pd.DataFrame,
    invoice_test: pd.DataFrame,
) -> pd.DataFrame:
    """Ejecuta el catálogo completo de verificaciones de calidad sobre las cuatro tablas."""
    rows: list[dict[str, object]] = []
    rows += _client_checks(client_train, "client_train")
    rows += _client_checks(client_test, "client_test")
    rows += _invoice_checks(invoice_train, "invoice_train")
    rows += _invoice_checks(invoice_test, "invoice_test")
    rows += _cross_table_checks(client_train, invoice_train, "train")
    rows += _cross_table_checks(client_test, invoice_test, "test")
    rows += _train_test_checks(client_train, client_test, invoice_train, invoice_test)
    return pd.DataFrame(rows)


def build_schema_vs_readme(dataset_by_name: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Compara las columnas reales de cada tabla con lo que documenta el README oficial."""
    rows = []
    for table, df in dataset_by_name.items():
        for col in df.columns:
            rows.append(
                {
                    "table": table,
                    "column_real": col,
                    "dtype_real": str(df[col].dtype),
                    "readme_name": README_NAME.get(col, "(ausente)"),
                    "readme_documenta_significado": README_DOCUMENTED.get(col, False),
                    "nombre_coincide_ignorando_mayusculas": README_NAME.get(col, "").lower()
                    == col.lower(),
                }
            )
    return pd.DataFrame(rows)


# --- Informe -----------------------------------------------------------------------


def _mil(value: float | int) -> str:
    """Entero con separador de millar español ('135.493')."""
    return f"{int(round(float(value))):,}".replace(",", ".")


def _md_table(df: pd.DataFrame, cols: list[str], int_cols: tuple[str, ...] = ()) -> str:
    lines = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for _, row in df[cols].iterrows():
        cells = []
        for col, v in zip(cols, row, strict=True):
            if col in int_cols and isinstance(v, int | float | np.integer | np.floating):
                cells.append(_mil(v))
            elif isinstance(v, float | np.floating):
                cells.append(f"{v:.4g}".replace(".", ",") if np.isfinite(v) else "—")
            else:
                cells.append(str(v))
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def _write_profile_tables(dataset_by_name: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    REPORTS_TABLES_DIR.mkdir(parents=True, exist_ok=True)
    profiles = {}
    for name, df in dataset_by_name.items():
        profile = profile_dataframe(df, name)
        out_path = REPORTS_TABLES_DIR / f"profile_{name}.csv"
        profile.to_csv(out_path, index=False)
        logger.info("Perfil de %s escrito en %s (%s columnas)", name, out_path, len(profile))
        profiles[name] = profile
    return profiles


def _render_markdown_report(
    dataset_by_name: dict[str, pd.DataFrame],
    cleaning_reports: dict[str, object],
    checks: pd.DataFrame,
    schema: pd.DataFrame,
) -> str:
    lines: list[str] = []
    lines.append("# Auditoría de calidad de datos — Fase 0")
    lines.append("")
    lines.append(
        "Informe reproducible: lo genera `src/steg/eda/profile.py` (`make audit`) a partir "
        f"de `data/raw/*.csv`. Última ejecución: "
        f"{datetime.now(UTC).strftime('%Y-%m-%d %H:%M UTC')}. Los hashes SHA-256 de "
        f"los cuatro CSV están en `{DATA_CHECKSUMS_PATH.name}`, y cada cifra de aquí sale de "
        "`reports/tables/quality_checks.csv`, `reports/tables/profile_<tabla>.csv` o "
        "`reports/tables/schema_vs_readme.csv`."
    )
    lines.append("")
    lines.append(
        "El alcance de esta fase es detectar y cuantificar. Ninguna anomalía se corrige "
        "aquí: `src/steg/data/clean.py` la marca con una columna booleana y la Fase 1 "
        "estudia si es defecto de captura o señal, antes de que la Fase 3 decida qué hacer."
    )
    lines.append("")

    lines.append("## 1. Qué contiene cada archivo")
    lines.append("")
    lines.append("| Tabla | Filas | Columnas | Unidad de observación |")
    lines.append("|---|---|---|---|")
    unidades = {
        "client_train": "un cliente con etiqueta",
        "client_test": "un cliente sin etiqueta",
        "invoice_train": "una factura de un cliente de train",
        "invoice_test": "una factura de un cliente de test",
    }
    for name, df in dataset_by_name.items():
        lines.append(f"| {name} | {_mil(df.shape[0])} | {df.shape[1]} | {unidades[name]} |")
    lines.append("")
    lines.append(
        "Las dos tablas se relacionan por `client_id` en una cardinalidad uno a muchos: "
        "un cliente tiene tantas facturas como lecturas se le hayan tomado, y la etiqueta "
        "vive en la tabla de clientes. La unidad de análisis del proyecto es el cliente."
    )
    lines.append("")

    if "client_train" in dataset_by_name and "target" in dataset_by_name["client_train"].columns:
        target = dataset_by_name["client_train"]["target"]
        n_pos = int((target == 1).sum())
        n_total = len(target)
        lines.append("## 2. Distribución de la etiqueta (solo train)")
        lines.append("")
        pct_pos = f"{100 * n_pos / n_total:.2f}".replace(".", ",")
        ratio = f"{(n_total - n_pos) / n_pos:.1f}".replace(".", ",")
        lines.append(
            f"{_mil(n_pos)} clientes fraudulentos de {_mil(n_total)} ({pct_pos} %), "
            f"es decir {ratio} negativos por positivo. La etiqueta "
            f"toma {int(target.nunique())} valores distintos y no tiene fecha asociada: no se "
            "sabe cuándo se detectó el fraude, lo que impide construir un corte temporal "
            "honesto entre historial y etiqueta. La relación de la etiqueta con el resto de "
            "las variables pertenece a la Fase 1."
        )
        lines.append("")

    lines.append("## 3. Esquema real contra el README oficial")
    lines.append("")
    no_doc = schema.loc[~schema["readme_documenta_significado"], "column_real"].unique()
    desajuste = schema.loc[~schema["nombre_coincide_ignorando_mayusculas"], "column_real"].unique()
    lines.append(
        f"Las {schema['column_real'].nunique()} columnas distintas de los cuatro archivos "
        f"aparecen en `data/raw/README.md` salvo en dos puntos. El README lista "
        f"{', '.join(f'`{c}`' for c in no_doc)} sin definición, de modo que su significado no "
        "está documentado por la fuente y cualquier interpretación es una hipótesis del "
        "análisis. Y el nombre de "
        f"{', '.join(f'`{c}`' for c in desajuste)} no coincide con el del README "
        f"(`{README_NAME.get(desajuste[0], '')}`): el archivo trae una errata que se respeta "
        "tal cual en la carga, porque renombrar rompería la trazabilidad con el original."
    )
    lines.append("")
    lines.append("Detalle columna por columna en `reports/tables/schema_vs_readme.csv`.")
    lines.append("")

    lines.append("## 4. Faltantes, duplicados y claves")
    lines.append("")
    claves = checks[
        checks["check"].isin(
            [
                "filas_con_algun_nulo",
                "filas_exactamente_duplicadas",
                "client_id_duplicado",
                "duplicado_por_clave_logica",
                "cliente_sin_ninguna_factura",
                "factura_sin_cliente",
                "clientes_en_ambas_particiones",
            ]
        )
    ]
    lines.append(
        _md_table(
            claves,
            ["table", "column", "check", "n_affected", "pct_affected"],
            int_cols=("n_affected",),
        )
    )
    lines.append("")
    lines.append(
        "Ninguna de las cuatro tablas declara un solo valor faltante, lo que no significa "
        "que no haya información ausente: las columnas que la codifican con valores "
        "imposibles aparecen en el apartado siguiente. Los duplicados exactos son un "
        "puñado de filas y se eliminan; los duplicados por la clave lógica "
        "(`client_id`, `invoice_date`, `counter_number`) son dos órdenes de magnitud más "
        "frecuentes y no se eliminan, porque esas filas difieren en consumo o en índices y "
        "esa diferencia puede ser refacturación en vez de error."
    )
    lines.append("")

    lines.append("## 5. Valores imposibles o fuera del dominio declarado")
    lines.append("")
    imposibles = checks[
        checks["check"].isin(
            [
                "valor_fuera_del_dominio_documentado",
                "valor_fuera_del_dominio_observado_en_test",
                "igual_a_cero",
                "mayor_que_12",
                "negativo",
                "new_index_menor_que_old_index",
                "indice_negativo",
                "suma_niveles_distinta_de_new_menos_old",
                "consumo_negativo",
                "consumo_total_cero",
                "creation_date_fuera_de_rango_plausible",
                "anterior_al_quiebre_de_volumen",
            ]
        )
    ]
    lines.append(
        _md_table(
            imposibles,
            ["table", "column", "check", "n_affected", "pct_affected", "detail"],
            int_cols=("n_affected",),
        )
    )
    lines.append("")
    lines.append(
        "`months_number` fuera de `[1, 12]` y `counter_statue` con letras o con números de "
        "seis cifras no son valores mal medidos: son celdas que se llenaron con otra cosa. "
        "El caso de `reading_remarque` lo muestra sin ambigüedad, porque los cuatro valores "
        "inesperados que aparecen ahí (5, 203, 207, 413) son valores propios de "
        "`counter_code`, lo que apunta a filas con las columnas corridas en la captura "
        "original. Son el equivalente de un faltante en un archivo que no declara ninguno, "
        "y por eso se marcan en vez de imputarse."
    )
    lines.append("")

    lines.append("## 6. Incoherencias de identidad y de fecha entre tablas")
    lines.append("")
    cruce = checks[
        checks["check"].isin(
            ["primera_factura_anterior_al_alta", "valor_compartido_por_varios_clientes"]
        )
    ]
    lines.append(
        _md_table(
            cruce,
            ["table", "column", "check", "n_affected", "n_total", "detail"],
            int_cols=("n_affected", "n_total"),
        )
    )
    lines.append("")
    lines.append(
        "Una factura anterior a la fecha de alta del cliente contradice la definición del "
        "README (`Creation_date: Date client joined`). Cualquier variable de antigüedad "
        "construida como diferencia contra `creation_date` hereda ese defecto y saldrá "
        "negativa para esos clientes. Y `counter_number` no identifica un contador: el "
        "mismo valor aparece en clientes distintos, así que usarlo como identificador de "
        "equipo sin verificarlo produciría agregaciones sin sentido."
    )
    lines.append("")

    lines.append("## 7. Comparabilidad entre train y test")
    lines.append("")
    tt = checks[checks["table"] == "train vs. test"]
    lines.append(_md_table(tt, ["column", "check", "n_affected", "detail"]))
    lines.append("")
    lines.append(
        "Ningún cliente aparece en las dos particiones, así que la separación de Zindi es "
        "limpia a nivel de cliente. Las categorías exclusivas de train son de frecuencia "
        "marginal y afectan a la codificación de categóricas de la Fase 3: un esquema que "
        "aprenda una columna por categoría producirá columnas que en test valen cero "
        "siempre. La comparación de distribuciones entre las dos particiones, que es lo "
        "que decide si el modelo puede extrapolar, corresponde a la Fase 1."
    )
    lines.append("")

    lines.append("## 8. Reglas de limpieza aplicadas (`src/steg/data/clean.py`)")
    lines.append("")
    lines.append("| Tabla | Regla | Filas afectadas |")
    lines.append("|---|---|---|")
    for table_name, report in cleaning_reports.items():
        if not report.counts:
            lines.append(f"| {table_name} | (sin reglas aplicables) | 0 |")
        for rule, count in report.counts.items():
            lines.append(f"| {table_name} | {rule} | {_mil(count)} |")
    lines.append("")
    lines.append(
        "Solo `exact_duplicates_dropped` elimina filas. El resto añade una columna booleana "
        "a `data/interim/*.parquet` y deja la decisión para más adelante."
    )
    lines.append("")

    lines.append("## 9. Qué queda abierto al terminar la Fase 0")
    lines.append("")
    lines.append(
        "El significado de `counter_number` y `counter_code` no está documentado, y el de "
        "los códigos de `counter_statue` y `reading_remarque` se describe en el README de "
        "forma genérica, sin la tabla de correspondencias. Ninguna de las cuatro tablas "
        "declara la unidad de medida del consumo. Estas lagunas no se resuelven con los "
        "datos disponibles, así que el análisis las trata como categóricas sin semántica "
        "en vez de atribuirles un significado por el nombre."
    )
    lines.append("")
    lines.append(
        "El perfil columna por columna de las cuatro tablas está en "
        "`reports/tables/profile_<tabla>.csv`; el catálogo completo de verificaciones, con "
        "las que no dieron ningún hallazgo, en `reports/tables/quality_checks.csv`."
    )
    lines.append("")

    return "\n".join(lines)


def run_audit() -> None:
    """Ejecuta el perfilado y la auditoría de calidad, y escribe el informe de Fase 0."""
    dataset = load_raw_data()
    dataset_by_name = {
        "client_train": dataset.client_train,
        "client_test": dataset.client_test,
        "invoice_train": dataset.invoice_train,
        "invoice_test": dataset.invoice_test,
    }
    _write_profile_tables(dataset_by_name)
    compute_and_save_checksums()

    checks = build_quality_checks(
        dataset.client_train, dataset.client_test, dataset.invoice_train, dataset.invoice_test
    )
    checks.to_csv(REPORTS_TABLES_DIR / "quality_checks.csv", index=False)
    logger.info("Catálogo de verificaciones escrito: %s filas", len(checks))

    schema = build_schema_vs_readme(dataset_by_name)
    schema.to_csv(REPORTS_TABLES_DIR / "schema_vs_readme.csv", index=False)

    cleaning_reports = clean_all()

    REPORTS_EDA_DIR.mkdir(parents=True, exist_ok=True)
    report_md = _render_markdown_report(dataset_by_name, cleaning_reports, checks, schema)
    out_path = REPORTS_EDA_DIR / "00_data_audit.md"
    out_path.write_text(report_md, encoding="utf-8")
    logger.info("Informe de auditoría escrito en %s", out_path)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    run_audit()


if __name__ == "__main__":
    main()
