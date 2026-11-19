"""Dashboard del proyecto: detección de fraude eléctrico en clientes de STEG.

Ejecutar desde la raíz del repositorio:

    streamlit run dashboard/app.py

Todas las cifras salen de reports/tables/*.csv (exportadas por los notebooks).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent))

import charts as ch  # noqa: E402

import data as dt  # noqa: E402

st.set_page_config(
    page_title="Fraude eléctrico STEG",
    page_icon="⚡",
    layout="wide",
)


def fuente(*tablas: str) -> None:
    rutas = ", ".join(f"`reports/tables/{t}`" for t in tablas)
    st.caption(f"Fuente: {rutas}")


def ver_tabla(df: pd.DataFrame, key: str) -> None:
    with st.expander("Ver los datos de la figura"):
        st.dataframe(df, hide_index=True, key=key)


def tabla_es(df: pd.DataFrame, formatos: dict[str, str]) -> pd.DataFrame:
    """Copia con las columnas numéricas como texto en formato español.

    ``formatos`` = {columna: "entero" | "pct" | ".3f" ...}; "pct" multiplica por 100.
    """
    out = df.copy()
    for col, f in formatos.items():
        if f == "entero":
            out[col] = out[col].map(entero)
        elif f == "pct":
            out[col] = out[col].map(pct)
        else:
            out[col] = out[col].map(lambda v, f=f: ch.es(v, f))
    return out


def pct(v: float, dec: int = 1) -> str:
    return ch.es(v * 100, f".{dec}f") + " %"


def entero(v: float) -> str:
    return ch.es(round(v), ",.0f")


D = dt.resumen_datos()
H = dt.resumen_holdout()

st.title("Detección de fraude en el consumo de energía")
st.markdown(
    "Modelo de clasificación para priorizar inspecciones a partir del historial de "
    "facturación de los clientes de STEG (Túnez)."
)

tabs = st.tabs(
    [
        "Resumen",
        "Datos y exploración",
        "Huella de la inspección",
        "Modelos",
        "Simulador de campaña",
        "Interpretación",
    ]
)

# =========================================================================== Resumen
with tabs[0]:
    c1 = dt.campana(0.01).set_index("modelo")
    st.subheader("Resumen")
    st.markdown(
        "- Parte de la energía se consume sin pagarse (pérdidas no técnicas) y la empresa "
        "solo puede inspeccionar a una fracción de sus clientes.\n"
        "- La pregunta es **a quién visitar primero**: ordenar a los clientes por su "
        "probabilidad de fraude usando su historial de facturación.\n"
        "- La etiqueta es **fraude detectado** en una inspección, no fraude real, y no trae "
        "fecha de detección."
    )

    fraudes_modelo = c1.loc["lgbm_comportamiento", "fraudes"]
    k1 = int(c1.loc["lgbm_comportamiento", "k"])
    st.markdown(
        f"<div style='margin:1.25rem 0 0.25rem'>"
        f"<div style='font-size:3.5rem;font-weight:600;line-height:1.1'>"
        f"{entero(fraudes_modelo)} fraudes en {entero(k1)} visitas</div>"
        f"<div style='opacity:0.75;font-size:1.05rem;margin-top:0.35rem'>"
        f"Lista del 1 % de los clientes del holdout ordenada por el modelo. "
        f"Con la regla de exposición serían {entero(c1.loc['solo_exposicion', 'fraudes'])} "
        f"y al azar unos {entero(c1.loc['prevalencia', 'fraudes'])}.</div></div>",
        unsafe_allow_html=True,
    )

    k = st.columns(4)
    k[0].metric("Clientes etiquetados", entero(D["clientes"]), border=True)
    k[1].metric("Fraude detectado", pct(D["prevalencia"], 2), border=True)
    k[2].metric(
        "PR-AUC en el holdout",
        ch.es(H["pr_auc"], ".3f"),
        help=f"IC 95 % [{ch.es(H['pr_auc_lo'], '.3f')}, {ch.es(H['pr_auc_hi'], '.3f')}]. "
        f"Azar: {ch.es(H['prevalencia'], '.3f')}.",
        border=True,
    )
    k[3].metric(
        "ROC-AUC en el holdout",
        ch.es(H["roc_auc"], ".3f"),
        help=f"IC 95 % [{ch.es(H['roc_auc_lo'], '.3f')}, {ch.es(H['roc_auc_hi'], '.3f')}].",
        border=True,
    )
    st.caption(
        f"PR-AUC IC 95 % [{ch.es(H['pr_auc_lo'], '.3f')}, {ch.es(H['pr_auc_hi'], '.3f')}] · "
        f"ROC-AUC IC 95 % [{ch.es(H['roc_auc_lo'], '.3f')}, {ch.es(H['roc_auc_hi'], '.3f')}] · "
        f"holdout de {entero(H['clientes'])} clientes evaluado una sola vez."
    )

    izq, der = st.columns([1.1, 1])
    with izq:
        st.markdown("**Fraudes encontrados al visitar el 1 % de los clientes**")
        orden = ["lgbm_comportamiento", "solo_exposicion", "prevalencia"]
        fig = ch.barras_horizontales(
            [dt.NOMBRES_MODELO[m] for m in orden],
            [c1.loc[m, "fraudes"] for m in orden],
            "fraudes encontrados",
            formato=".0f",
            colores=[ch.color_modelo(m) for m in orden],
            alto=230,
        )
        ch.mostrar(fig, "resumen_campana")
    with der:
        st.markdown("**Hallazgo principal**")
        mh = dt.tabla("modeling_holdout_metricas.csv").set_index("modelo")
        st.markdown(
            "Con el historial completo de facturas el mismo modelo llega a un ROC-AUC de "
            f"{ch.es(mh.loc['lgbm_historial_completo', 'roc_auc'], '.3f')} en el holdout, "
            "pero ese desempeño viene de huellas que deja la propia inspección (cambios de "
            "contador o de tarifa posteriores a la detección). Al cortar el historial en el "
            f"primer evento, el modelo queda en {ch.es(H['roc_auc'], '.3f')}: es lo que se "
            "puede esperar de un cliente que todavía no ha sido inspeccionado."
        )
    fuente(
        "modeling_holdout_metricas.csv",
        "modeling_holdout_curva_k.csv",
        "quality_checks.csv",
        "evaluation_metric_baselines.csv",
    )

# =========================================================================== Datos y EDA
with tabs[1]:
    st.subheader("Datos y exploración")
    k = st.columns(4)
    k[0].metric("Clientes etiquetados", entero(D["clientes"]), border=True)
    k[1].metric("Facturas", entero(D["facturas"]), border=True)
    k[2].metric("Con fraude detectado", entero(D["positivos"]), border=True)
    k[3].metric("Negativos por positivo", ch.es(D["negativos_por_positivo"], ".1f"), border=True)

    hist = dt.tabla("confounding_history_length.csv")
    cons = dt.tabla("outliers_target_rate.csv")
    razon = hist["tasa_fraude_pct"].iloc[-1] / hist["tasa_fraude_pct"].iloc[0]
    izq, der = st.columns(2)
    with izq:
        st.markdown("**Tasa de fraude por decil de número de facturas**")
        etiquetas = [
            f"{a}–{b}" for a, b in zip(hist["facturas_min"], hist["facturas_max"], strict=True)
        ]
        fig = ch.columnas_con_ic(
            etiquetas,
            hist["tasa_fraude_pct"],
            hist["wilson_lo_pct"],
            hist["wilson_hi_pct"],
            "Facturas del cliente (decil)",
            "tasa de fraude",
        )
        ch.mostrar(fig, "eda_historial")
        st.markdown(
            f"La tasa pasa de {ch.es(hist['tasa_fraude_pct'].iloc[0], '.2f')} % a "
            f"{ch.es(hist['tasa_fraude_pct'].iloc[-1], '.2f')} %, un factor de "
            f"{ch.es(razon, '.1f')}: un historial largo da más oportunidades de ser "
            "inspeccionado. Por eso la longitud del historial se trata como exposición y no "
            "como señal."
        )
        ver_tabla(hist, "t_hist")
        fuente("confounding_history_length.csv")
    with der:
        st.markdown("**Tasa de fraude por decil de consumo máximo**")
        etiquetas = [
            f"{ch.es(a, ',.0f')}–{ch.es(b, ',.0f')}"
            for a, b in zip(cons["consumo_max_min"], cons["consumo_max_max"], strict=True)
        ]
        fig = ch.columnas_con_ic(
            etiquetas,
            cons["tasa_fraude_pct"],
            cons["wilson_lo_pct"],
            cons["wilson_hi_pct"],
            "Consumo máximo del cliente (decil)",
            "tasa de fraude",
        )
        ch.mostrar(fig, "eda_consumo")
        st.markdown(
            "La tasa crece con el consumo máximo a lo largo de casi todo el recorrido; por eso "
            "los valores extremos de consumo no se recortan ni se winsorizan."
        )
        ver_tabla(cons, "t_cons")
        fuente("outliers_target_rate.csv")

    cat = dt.tabla("bivariate_category_rates.csv")
    base = cat["base_rate_pct"].iloc[0]
    izq, der = st.columns(2)
    for col, var, titulo in [
        (izq, "disrict", "Tasa de fraude por distrito"),
        (der, "client_catg", "Tasa de fraude por categoría de cliente"),
    ]:
        with col:
            st.markdown(f"**{titulo}**")
            sub = cat[cat["variable"] == var].sort_values("rate_pct", ascending=False)
            fig = ch.barras_horizontales(
                [f"{'Distrito' if var == 'disrict' else 'Categoría'} {c}" for c in sub["category"]],
                list(sub["rate_pct"]),
                "tasa de fraude (%)",
                formato=".1f",
                sufijo=" %",
                error=None,
                referencia=base,
                nombre_referencia=f"Promedio {ch.es(base, '.1f')} %",
                hover_extra=[f"<br>{entero(n)} clientes" for n in sub["n"]],
            )
            ch.mostrar(fig, f"eda_{var}")
            ver_tabla(sub, f"t_{var}")
    fuente("bivariate_category_rates.csv")

    st.markdown("**Calidad de los datos**")
    calidad = dt.tabla("quality_checks.csv")
    problemas = calidad[calidad["n_affected"] > 0].copy()
    problemas = problemas[~problemas["check"].isin(["cardinalidad"])]
    problemas = tabla_es(problemas, {"n_affected": "entero", "pct_affected": ".3f"})
    problemas["detail"] = problemas["detail"].fillna("")
    st.markdown(
        "No hay valores nulos ni clientes duplicados. Los problemas encontrados son de captura "
        "y afectan a una fracción pequeña de las facturas; se marcan como variables en lugar "
        "de eliminarse."
    )
    st.dataframe(
        problemas[["table", "column", "check", "n_affected", "pct_affected", "detail"]].rename(
            columns={
                "table": "tabla",
                "column": "columna",
                "check": "verificación",
                "n_affected": "filas afectadas",
                "pct_affected": "% afectado",
                "detail": "detalle",
            }
        ),
        hide_index=True,
        key="t_calidad",
    )
    with st.expander("Investigación de las anomalías"):
        st.dataframe(dt.tabla("quality_deepdive.csv"), hide_index=True, key="t_deep")
    fuente("quality_checks.csv", "quality_deepdive.csv")

# =========================================================================== Huella
with tabs[2]:
    st.subheader("Huella de la inspección")
    st.markdown(
        "Los reemplazos de contador y los cambios de código o de tarifa se concentran al final "
        "del historial de los clientes con fraude: en buena parte son consecuencia de la "
        "inspección. Un modelo que los ve aprende a quién ya se inspeccionó."
    )
    p = ch.paleta()
    ev = dt.tabla("modeling_diagnostico_eventos_equipo.csv")
    ev["evento_nombre"] = ev["evento"].map(dt.NOMBRES_EVENTO)
    izq, der = st.columns(2)
    with izq:
        st.markdown("**Tasa de fraude con y sin el evento**")
        fig = ch.barras_agrupadas(
            ev["evento_nombre"],
            [
                ("Con el evento", list(ev["tasa_fraude_con_evento"] * 100), p["s1"]),
                ("Sin el evento", list(ev["tasa_fraude_sin_evento"] * 100), p["s2"]),
            ],
            "tasa de fraude (%)",
            formato=".1f",
            sufijo=" %",
        )
        ch.mostrar(fig, "huella_tasas")
    with der:
        st.markdown("**Posición mediana del evento en el historial (0 = inicio, 1 = final)**")
        fig = ch.barras_agrupadas(
            ev["evento_nombre"],
            [
                ("Clientes con fraude", list(ev["posicion_mediana_fraude"]), p["s1"]),
                ("Clientes sin fraude", list(ev["posicion_mediana_no_fraude"]), p["s2"]),
            ],
            "posición mediana",
            formato=".2f",
        )
        ch.mostrar(fig, "huella_posicion")
    ver_tabla(ev.drop(columns=["evento"]), "t_eventos")
    fuente("modeling_diagnostico_eventos_equipo.csv")

    st.markdown("**Verificación por mitades del historial (PR-AUC en validación cruzada)**")
    mit = dt.tabla("modeling_verificacion_mitades_historial.csv")
    orden_var = ["historial_entero", "primera_mitad", "segunda_mitad"]
    nombres_var = ["Historial entero", "Primera mitad", "Segunda mitad"]
    series, errores = [], []
    for rep, nombre, color in [
        ("historial_completo", "Historial completo", p["s3"]),
        ("historial_censurado", "Historial censurado (modelo final)", p["s1"]),
    ]:
        sub = mit[mit["representacion"] == rep].set_index("variables").loc[orden_var]
        series.append((nombre, list(sub["pr_auc_media"]), color))
        errores.append(
            (
                list(sub["pr_auc_ic95_hi"] - sub["pr_auc_media"]),
                list(sub["pr_auc_media"] - sub["pr_auc_ic95_lo"]),
            )
        )
    fig = ch.barras_agrupadas(
        nombres_var, series, "PR-AUC (IC 95 %)", formato=".3f", errores=errores, ancho_px=600
    )
    comp = mit[mit["representacion"] == "historial_completo"].set_index("variables")
    cens = mit[mit["representacion"] == "historial_censurado"].set_index("variables")
    izq, der = st.columns([1.3, 1])
    with izq:
        ch.mostrar(fig, "huella_mitades")
    brecha_cens = (
        cens.loc["segunda_mitad", "pr_auc_media"] - cens.loc["primera_mitad", "pr_auc_media"]
    )
    der.markdown(
        "Con el historial completo, la segunda mitad rinde "
        f"{ch.es(comp.loc['segunda_mitad', 'pr_auc_media'], '.2f')} y la primera "
        f"{ch.es(comp.loc['primera_mitad', 'pr_auc_media'], '.2f')}: la señal se concentra donde "
        "ocurren las inspecciones. Con el historial censurado en el primer evento la brecha baja "
        f"a {ch.es(brecha_cens, '.3f')}."
        "\n\nCada modelo se entrena con variables de una sola mitad del historial de los mismos "
        f"{entero(comp.loc['historial_entero', 'clientes'])} clientes; las barras grises marcan "
        "el intervalo de confianza del 95 %."
    )
    ver_tabla(mit, "t_mitades")
    fuente("modeling_verificacion_mitades_historial.csv")

    st.markdown("**¿La señal sobrevive en clientes sin eventos? ROC-AUC en el holdout**")
    pe = dt.tabla("modeling_holdout_por_evento_equipo.csv")
    modelos = ["lgbm_comportamiento", "solo_exposicion", "lgbm_historial_completo"]
    grupos = ["sin_evento", "con_evento"]
    nombres_grupo = ["Sin eventos de equipo", "Con eventos de equipo"]
    series = []
    for m in modelos:
        sub = pe[pe["modelo"] == m].set_index("evento_equipo").loc[grupos]
        series.append((dt.NOMBRES_MODELO[m], list(sub["roc_auc"]), ch.color_modelo(m)))
    fig = ch.barras_agrupadas(
        nombres_grupo, series, "ROC-AUC", formato=".3f", ancho_px=600, con_texto=False
    )
    fig.update_yaxes(range=[0, 1])
    sin = pe[(pe["evento_equipo"] == "sin_evento") & (pe["modelo"] == "lgbm_comportamiento")].iloc[
        0
    ]
    izq, der = st.columns([1.3, 1])
    with izq:
        ch.mostrar(fig, "huella_sin_evento")
    der.markdown(
        f"En los {entero(sin['clientes'])} clientes del holdout sin eventos (prevalencia "
        f"{pct(sin['prevalencia'])}) el modelo final mantiene un ROC-AUC de "
        f"{ch.es(sin['roc_auc'], '.3f')}: ahí no hay corte que delatar, así que esa señal no "
        "viene de la huella. Un orden al azar daría 0,5."
    )
    ver_tabla(pe, "t_por_evento")
    fuente("modeling_holdout_por_evento_equipo.csv")

# =========================================================================== Modelos
with tabs[3]:
    st.subheader("Modelos")
    cv = dt.tabla("model_comparison.csv").set_index("modelo")
    final = cv.loc["lgbm_comportamiento"]
    k = st.columns(4)
    k[0].metric(
        "PR-AUC en validación cruzada",
        ch.es(final["pr_auc_media"], ".3f"),
        help=f"Desviación entre pliegues {ch.es(final['pr_auc_desv'], '.3f')}.",
        border=True,
    )
    k[1].metric("PR-AUC en el holdout", ch.es(H["pr_auc"], ".3f"), border=True)
    k[2].metric("ROC-AUC en el holdout", ch.es(H["roc_auc"], ".3f"), border=True)
    k[3].metric("Brier en el holdout", ch.es(H["brier"], ".3f"), border=True)
    st.markdown(
        "Validación cruzada estratificada de 5 pliegues sobre el 80 % de los clientes; el 20 % "
        "restante (holdout) se evaluó una sola vez al final. El modelo final es LightGBM con "
        "hiperparámetros por defecto: el más simple entre los que no se distinguen del mejor."
    )

    izq, der = st.columns(2)
    for col, lista, titulo, key in [
        (izq, dt.CANDIDATOS, "Candidatos y líneas base", "mod_candidatos"),
        (der, dt.CONTROLES, "Controles de la huella de inspección", "mod_controles"),
    ]:
        with col:
            st.markdown(f"**{titulo}** · PR-AUC medio ± desviación entre pliegues")
            sub = cv.loc[lista].sort_values("pr_auc_media", ascending=False)
            fig = ch.barras_horizontales(
                [dt.NOMBRES_MODELO[m] for m in sub.index],
                list(sub["pr_auc_media"]),
                "PR-AUC",
                formato=".3f",
                colores=[ch.color_modelo(m) for m in sub.index],
                error=list(sub["pr_auc_desv"]),
                hover_extra=[f"<br>ROC-AUC {ch.es(r, '.3f')}" for r in sub["roc_auc_media"]],
            )
            ch.mostrar(fig, key)
    st.markdown(
        "XGBoost y LightGBM empatan; la regresión logística, la ponderación de clases y la "
        "búsqueda con Optuna no superan al modelo por defecto. Los controles de la derecha "
        "rinden más porque ven la huella de la inspección o la longitud del historial, que no "
        "estarían disponibles al puntuar a un cliente todavía no inspeccionado."
    )
    ver_tabla(cv.reset_index(), "t_cv")
    fuente("model_comparison.csv")

    izq, der = st.columns([1.4, 1])
    with izq:
        st.markdown("**ROC-AUC por quintil de longitud del historial**")
        conjunto = st.radio(
            "Conjunto",
            ["Holdout", "Validación cruzada"],
            horizontal=True,
            key="conjunto_quintil",
        )
        nombre_tabla = (
            "modeling_holdout_por_quintil_historial.csv"
            if conjunto == "Holdout"
            else "modeling_dev_por_quintil_historial.csv"
        )
        q = dt.tabla(nombre_tabla)
        quintiles = sorted(q["quintil_historial"].unique())
        series = []
        for m in ["lgbm_comportamiento", "solo_exposicion", "lgbm_historial_completo"]:
            sub = q[q["modelo"] == m].set_index("quintil_historial").loc[quintiles]
            series.append((m, dt.NOMBRES_MODELO[m], list(sub["roc_auc"])))
        fig = ch.lineas(
            [f"Q{i}" for i in quintiles],
            series,
            "Quintil de longitud del historial (Q1 = más corto)",
            "ROC-AUC",
            y_rango=[0.55, 0.95],
        )
        ch.mostrar(fig, "mod_quintiles")
        st.markdown(
            "La regla de exposición solo funciona en los historiales cortos; el modelo final "
            "mantiene su capacidad de ordenar en los cinco quintiles."
        )
        ver_tabla(q, "t_quintiles")
        fuente(nombre_tabla)
    with der:
        st.markdown("**Estabilidad frente a la semilla de partición**")
        sem = dt.tabla("modeling_estabilidad_semillas.csv")
        st.dataframe(
            tabla_es(
                sem,
                {"pr_auc_media": ".3f", "pr_auc_desv_pliegues": ".3f", "roc_auc_media": ".3f"},
            ).rename(
                columns={
                    "semilla": "semilla",
                    "pr_auc_media": "PR-AUC medio",
                    "pr_auc_desv_pliegues": "desv. entre pliegues",
                    "roc_auc_media": "ROC-AUC medio",
                }
            ),
            hide_index=True,
            key="t_semillas",
        )
        st.markdown(
            f"El PR-AUC medio va de {ch.es(sem['pr_auc_media'].min(), '.3f')} a "
            f"{ch.es(sem['pr_auc_media'].max(), '.3f')} entre semillas."
        )
        fuente("modeling_estabilidad_semillas.csv")
        st.markdown("**Holdout sellado**")
        mh = dt.tabla("modeling_holdout_metricas.csv")
        hold = mh[
            ["modelo", "pr_auc", "pr_auc_ic95_lo", "pr_auc_ic95_hi", "roc_auc", "brier"]
        ].copy()
        hold["modelo"] = hold["modelo"].map(dt.NOMBRES_MODELO)
        hold["IC 95 % PR-AUC"] = [
            f"[{ch.es(lo, '.3f')}, {ch.es(hi, '.3f')}]"
            for lo, hi in zip(hold["pr_auc_ic95_lo"], hold["pr_auc_ic95_hi"], strict=True)
        ]
        hold = tabla_es(hold, {"pr_auc": ".3f", "roc_auc": ".3f", "brier": ".3f"})
        hold = hold[["modelo", "pr_auc", "IC 95 % PR-AUC", "roc_auc", "brier"]].rename(
            columns={"pr_auc": "PR-AUC", "roc_auc": "ROC-AUC", "brier": "Brier"}
        )
        st.dataframe(hold, hide_index=True, key="t_holdout")
        fuente("modeling_holdout_metricas.csv")

# =========================================================================== Simulador
with tabs[4]:
    st.subheader("Simulador de campaña")
    st.markdown(
        f"Si la empresa puede visitar una fracción fija de los {entero(H['clientes'])} clientes "
        f"del holdout ({entero(H['positivos'])} con fraude detectado), ¿cuántos fraudes encuentra "
        "con cada criterio? Solo se ofrecen los tamaños de lista medidos en el holdout."
    )
    eleccion = st.radio(
        "Tamaño de la lista de inspección",
        dt.FRACCIONES,
        index=1,
        format_func=lambda f: f"{dt.etiqueta_fraccion(f)} de los clientes",
        horizontal=True,
        key="fraccion",
    )
    camp = dt.campana(eleccion).set_index("modelo")
    kk = int(camp["k"].iloc[0])
    cols = st.columns(4)
    cols[0].metric("Visitas", entero(kk), border=True)
    for col, m in zip(
        cols[1:], ["lgbm_comportamiento", "solo_exposicion", "prevalencia"], strict=True
    ):
        fila = camp.loc[m]
        col.metric(
            f"Fraudes · {dt.NOMBRES_MODELO[m]}",
            entero(fila["fraudes"]),
            help=f"Precisión {pct(fila['precision'])} · recall {pct(fila['recall'])}",
            border=True,
        )
    mf = camp.loc["lgbm_comportamiento"]
    st.markdown(
        f"Con el modelo, **{pct(mf['precision'])}** de las visitas encuentran fraude "
        f"({ch.es(mf['precision'] / camp.loc['prevalencia', 'precision'], '.1f')} veces el azar) y "
        f"se recupera el **{pct(mf['recall'])}** de los fraudes del holdout. El máximo posible "
        f"con {entero(kk)} visitas es {pct(mf['techo_recall'])}."
    )
    tabla_camp = camp.reset_index()[
        ["nombre", "k", "fraudes", "precision", "recall", "techo_recall"]
    ]
    tabla_camp = tabla_camp.rename(
        columns={
            "nombre": "criterio",
            "k": "visitas",
            "fraudes": "fraudes encontrados",
            "precision": "precisión",
            "recall": "recall",
            "techo_recall": "recall máximo posible",
        }
    )
    tabla_camp = tabla_es(
        tabla_camp,
        {
            "visitas": "entero",
            "fraudes encontrados": "entero",
            "precisión": "pct",
            "recall": "pct",
            "recall máximo posible": "pct",
        },
    )
    st.dataframe(tabla_camp, hide_index=True, key="t_campana")
    st.caption("Para el azar, los fraudes son el valor esperado de una lista aleatoria.")

    curva = dt.curva_k()
    xs = list(dt.FRACCIONES)
    etiquetas = [dt.etiqueta_fraccion(f) for f in xs]
    izq, der = st.columns(2)
    with izq:
        st.markdown("**Precisión según el tamaño de la lista**")
        series = []
        for m in ["lgbm_comportamiento", "solo_exposicion", "prevalencia"]:
            sub = curva[curva["modelo"] == m].sort_values("fraccion")
            series.append((m, dt.NOMBRES_MODELO[m], list(sub["precision"] * 100)))
        fig = ch.lineas(
            xs,
            series,
            "Lista de inspección (% de los clientes)",
            "precisión (%)",
            formato=".1f",
            sufijo=" %",
            x_log=True,
            etiquetas_x=etiquetas,
            marca_x=eleccion,
            y_rango=[0, 50],
        )
        ch.mostrar(fig, "sim_precision")
    with der:
        st.markdown("**Calibración por deciles de puntuación**")
        cal = dt.tabla("modeling_holdout_calibracion.csv")
        fig = ch.calibracion(list(cal["prob_media"]), list(cal["tasa_observada"]))
        ch.mostrar(fig, "sim_calibracion")
    st.markdown(
        "La precisión del modelo es más alta en las listas cortas y siempre queda por encima "
        "de la regla de exposición. Las probabilidades están calibradas: en cada decil la tasa "
        "observada coincide con la predicha, así que pueden leerse como riesgo."
    )
    ver_tabla(curva, "t_curva")
    fuente(
        "modeling_holdout_metricas.csv",
        "modeling_holdout_curva_k.csv",
        "modeling_holdout_calibracion.csv",
    )

# =========================================================================== Interpretación
with tabs[5]:
    st.subheader("Interpretación del modelo")
    shap = dt.importancia_shap()
    fam = (
        shap.groupby("familia_nombre", as_index=False)["participacion"]
        .sum()
        .sort_values("participacion", ascending=False)
    )
    top = shap.head(15)
    izq, der = st.columns([1.6, 1])
    with izq:
        st.markdown("**Las 15 variables con más peso (media del |SHAP|)**")
        fig = ch.barras_horizontales(
            list(top["etiqueta"]),
            list(top["media_abs_shap"]),
            "media del |valor SHAP|",
            formato=".3f",
            hover_extra=[
                f"<br>{d}<br>{v} · {f}"
                for d, v, f in zip(
                    top["definicion"], top["variable"], top["familia_nombre"], strict=True
                )
            ],
            alto=640,
        )
        ch.mostrar(fig, "shap_variables")
    with der:
        st.markdown("**Participación por familia de variables**")
        fig = ch.barras_horizontales(
            list(fam["familia_nombre"]),
            list(fam["participacion"] * 100),
            "% de la importancia total",
            formato=".1f",
            sufijo=" %",
            alto=360,
        )
        ch.mostrar(fig, "shap_familias")
    primera = shap.iloc[0]
    cuota = ch.es(fam["participacion"].iloc[0] * 100, ".0f")
    st.markdown(
        f"La familia de tarifa y contador concentra el {cuota} % de la importancia. "
        f"La variable individual más importante es «{primera['etiqueta'].lower()}». "
        "Las variables de consumo y de dinámica (percentil 90, pendiente anual, caídas fuertes) "
        "son las que describen el comportamiento del cliente."
    )
    st.info(
        "Límite de lectura: aun con el historial censurado, las variables predicen si un cliente "
        "tendrá un evento de equipo. Por eso la prueba de que hay señal propia es el desempeño "
        "en los clientes sin eventos (pestaña «Huella de la inspección»)."
    )
    ver_tabla(shap, "t_shap")
    fuente("modeling_importancia_shap.csv", "feature_dictionary.csv")
