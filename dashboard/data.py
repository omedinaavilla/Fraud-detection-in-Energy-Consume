"""Carga de las tablas versionadas en reports/tables.

El dashboard no lee data/raw ni data/interim: todo sale de los CSV que exportan
notebooks/01_eda.ipynb y notebooks/02_modelado.ipynb, que sí están en el repositorio.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

TABLAS = Path(__file__).resolve().parent.parent / "reports" / "tables"

# Fracciones de lista que existen en modeling_holdout_metricas.csv (no se interpola).
FRACCIONES = [0.005, 0.01, 0.02, 0.05, 0.10]

NOMBRES_MODELO = {
    "lgbm_comportamiento": "Modelo final (LightGBM)",
    "xgb_comportamiento": "XGBoost",
    "lgbm_comportamiento_optuna": "LightGBM con Optuna",
    "lgbm_comportamiento_ponderado": "LightGBM con pesos de clase",
    "logreg_comportamiento": "Regresión logística",
    "solo_exposicion": "Regla de exposición",
    "prevalencia": "Azar (prevalencia)",
    "lgbm_historial_completo": "Historial completo",
    "lgbm_historial_completo_sin_cambio_contador": "Historial completo sin cambio de contador",
    "lgbm_censurado_todas": "Censurado con todas las variables",
    "lgbm_censurado_sin_grupo_B": "Censurado sin grupo B",
    "lgbm_comportamiento_y_exposicion": "Comportamiento + exposición",
}

CANDIDATOS = [
    "lgbm_comportamiento",
    "xgb_comportamiento",
    "lgbm_comportamiento_optuna",
    "lgbm_comportamiento_ponderado",
    "logreg_comportamiento",
    "solo_exposicion",
    "prevalencia",
]
CONTROLES = [
    "lgbm_historial_completo",
    "lgbm_historial_completo_sin_cambio_contador",
    "lgbm_comportamiento_y_exposicion",
    "lgbm_censurado_todas",
    "lgbm_comportamiento",
    "lgbm_censurado_sin_grupo_B",
]

NOMBRES_FAMILIA = {
    "tarifa_contador": "Tarifa y contador",
    "consumo": "Consumo",
    "dinamica": "Dinámica del consumo",
    "lectura": "Regularidad de lectura",
    "cliente": "Atributos del cliente",
    "relativa_pares": "Comparación con pares",
}

# Etiquetas cortas para el gráfico de importancia; el tooltip muestra la definición completa.
ETIQUETAS_VARIABLE = {
    "inv_share_codigo_contador_207": "Facturas con contador código 207",
    "inv_elec_log_cons_p90": "Consumo alto (percentil 90)",
    "cli_region": "Región",
    "inv_elec_pendiente_log_cons_anual": "Tendencia anual del consumo",
    "inv_share_codigo_contador_203": "Facturas con contador código 203",
    "cli_disrict": "Distrito",
    "inv_elec_share_caidas_fuertes": "Caídas fuertes del consumo",
    "inv_share_tarifa_11": "Facturas con tarifa 11",
    "inv_share_facturas_gas": "Proporción de facturas de gas",
    "inv_elec_share_subidas_fuertes": "Subidas fuertes del consumo",
    "inv_elec_ratio_reciente_vs_previo": "Consumo reciente frente al anterior",
    "rel_elec_cons_vs_catg": "Consumo frente a su categoría",
    "inv_elec_log_cons_desv": "Variabilidad del consumo",
    "inv_elec_log_cons_mediana_u12": "Consumo típico (últimas 12 facturas)",
    "rel_elec_cons_vs_region": "Consumo frente a su región",
    "inv_elec_share_cons_cero": "Facturas con consumo cero",
    "inv_share_estado_contador_no_cero": "Estado de contador anómalo",
    "inv_share_codigo_contador_420": "Facturas con contador código 420",
    "inv_elec_share_gap_largo": "Lecturas con intervalo largo",
    "inv_share_index_regression": "Retrocesos del índice",
}

NOMBRES_EVENTO = {
    "cambio_codigo_contador": "Cambio de código de contador",
    "cambio_tarifa": "Cambio de tarifa",
    "reemplazo_contador": "Reemplazo de contador",
    "cualquiera": "Cualquiera de los tres",
}


@st.cache_data
def tabla(nombre: str, **kwargs) -> pd.DataFrame:
    """Lee reports/tables/<nombre>."""
    return pd.read_csv(TABLAS / nombre, **kwargs)


@st.cache_data
def resumen_datos() -> dict:
    """Tamaños y prevalencia del conjunto etiquetado (fuente: tablas de la fase 0)."""
    calidad = tabla("quality_checks.csv")
    base = tabla("evaluation_metric_baselines.csv").set_index("referencia")["valor"]
    clientes = int(
        calidad.query("table == 'client_train' and check == 'filas_con_algun_nulo'")[
            "n_total"
        ].iloc[0]
    )
    facturas = int(
        calidad.query("table == 'invoice_train' and check == 'filas_con_algun_nulo'")[
            "n_total"
        ].iloc[0]
    )
    positivos = int(base["positivos en entrenamiento"])
    return {
        "clientes": clientes,
        "facturas": facturas,
        "positivos": positivos,
        "prevalencia": positivos / clientes,
        "negativos_por_positivo": float(base["negativos por cada positivo"]),
    }


@st.cache_data
def resumen_holdout() -> dict:
    """Tamaño, positivos y métricas del holdout sellado."""
    eventos = tabla("modeling_holdout_por_evento_equipo.csv")
    final = eventos[eventos["modelo"] == "lgbm_comportamiento"]
    metricas = tabla("modeling_holdout_metricas.csv").set_index("modelo")
    m = metricas.loc["lgbm_comportamiento"]
    return {
        "clientes": int(final["clientes"].sum()),
        "positivos": int(final["positivos"].sum()),
        "prevalencia": float(m["prevalencia"]),
        "pr_auc": float(m["pr_auc"]),
        "pr_auc_lo": float(m["pr_auc_ic95_lo"]),
        "pr_auc_hi": float(m["pr_auc_ic95_hi"]),
        "roc_auc": float(m["roc_auc"]),
        "roc_auc_lo": float(m["roc_auc_ic95_lo"]),
        "roc_auc_hi": float(m["roc_auc_ic95_hi"]),
        "brier": float(m["brier"]),
    }


def etiqueta_fraccion(f: float) -> str:
    """0.005 -> '0,5 %'."""
    texto = f"{f * 100:g}".replace(".", ",")
    return f"{texto} %"


@st.cache_data
def campana(fraccion: float) -> pd.DataFrame:
    """Fraudes esperados en una lista del tamaño dado, en el holdout.

    Modelo final y regla de exposición usan la precisión@k medida en el holdout;
    el azar usa la prevalencia (valor esperado de una lista aleatoria).
    """
    metricas = tabla("modeling_holdout_metricas.csv").set_index("modelo")
    curva = tabla("modeling_holdout_curva_k.csv")
    fila = curva.loc[(curva["fraccion"] - fraccion).abs().idxmin()]
    k = int(fila["k"])
    techo = float(fila["techo_recall"])
    positivos = resumen_holdout()["positivos"]
    sufijo = etiqueta_fraccion(fraccion).replace(" ", "").replace(",", ".")
    filas = []
    for modelo in ["lgbm_comportamiento", "solo_exposicion"]:
        precision = float(metricas.loc[modelo, f"precision@{sufijo}"])
        filas.append((modelo, precision))
    filas.append(("prevalencia", float(metricas.loc["lgbm_comportamiento", "prevalencia"])))
    out = pd.DataFrame(filas, columns=["modelo", "precision"])
    out["k"] = k
    out["fraudes"] = out["precision"] * k
    out["recall"] = out["fraudes"] / positivos
    out["techo_recall"] = techo
    out["nombre"] = out["modelo"].map(NOMBRES_MODELO)
    return out


@st.cache_data
def curva_k() -> pd.DataFrame:
    """Precisión y recall @k en el holdout, formato largo, para los puntos existentes."""
    metricas = tabla("modeling_holdout_metricas.csv").set_index("modelo")
    curva = tabla("modeling_holdout_curva_k.csv")
    positivos = resumen_holdout()["positivos"]
    filas = []
    for f in FRACCIONES:
        sufijo = etiqueta_fraccion(f).replace(" ", "").replace(",", ".")
        k = int(curva.loc[(curva["fraccion"] - f).abs().idxmin(), "k"])
        for modelo in ["lgbm_comportamiento", "solo_exposicion"]:
            p = float(metricas.loc[modelo, f"precision@{sufijo}"])
            filas.append((f, k, modelo, p, float(metricas.loc[modelo, f"recall@{sufijo}"])))
        prev = float(metricas.loc["lgbm_comportamiento", "prevalencia"])
        filas.append((f, k, "prevalencia", prev, prev * k / positivos))
    out = pd.DataFrame(filas, columns=["fraccion", "k", "modelo", "precision", "recall"])
    out["nombre"] = out["modelo"].map(NOMBRES_MODELO)
    out["etiqueta"] = out["fraccion"].map(etiqueta_fraccion)
    return out


@st.cache_data
def importancia_shap() -> pd.DataFrame:
    """Importancia SHAP por variable con su definición del diccionario."""
    shap = tabla("modeling_importancia_shap.csv").rename(columns={"Unnamed: 0": "variable"})
    dic = tabla("feature_dictionary.csv").drop_duplicates("column").set_index("column")
    definicion = shap["variable"].map(dic["definicion"]).fillna(shap["variable"])
    # Quita la coletilla sobre la representación del historial, que es la misma en todas.
    shap["definicion"] = definicion.str.replace(
        r"\s*\((contador elec; )?historial censurado o completo.*$", "", regex=True
    ).str.strip()
    shap["etiqueta"] = shap["variable"].map(ETIQUETAS_VARIABLE).fillna(shap["definicion"])
    shap["familia_nombre"] = shap["familia"].map(NOMBRES_FAMILIA).fillna(shap["familia"])
    return shap.sort_values("media_abs_shap", ascending=False).reset_index(drop=True)
