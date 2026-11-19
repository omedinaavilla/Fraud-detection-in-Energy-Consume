"""Figuras Plotly con una sola gramática visual.

Paleta: azul, aqua y violeta del orden categórico de referencia (validados en modo
claro y oscuro; pares adyacentes ΔE ≥ 17 con daltonismo simulado). Se evita rojo,
naranja y amarillo por la guía de sustentación. El gris marca líneas base y lo que no
es protagonista. El texto, la cuadrícula y el fondo los pone el tema de Streamlit
(``theme="streamlit"``), así que las figuras se leen igual en modo claro y oscuro.
"""

from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

PALETAS = {
    "light": {
        "s1": "#2a78d6",
        "s2": "#1baf7a",
        "s3": "#6250d6",
        "gris": "#a9a8a1",
        "ref": "#898781",
        "fondo": "#fcfcfb",
    },
    "dark": {
        "s1": "#3987e5",
        "s2": "#199e70",
        "s3": "#9085e9",
        "gris": "#5c5b56",
        "ref": "#898781",
        "fondo": "#1a1a19",
    },
}

FUENTE = "system-ui, -apple-system, 'Segoe UI', sans-serif"


def es(valor: float, formato: str) -> str:
    """Formato numérico en español: 1.234,5."""
    return format(valor, formato).translate(str.maketrans({",": ".", ".": ","}))


def paleta() -> dict:
    try:
        tipo = st.context.theme.type
    except Exception:  # fuera de una sesión (pruebas) no hay contexto de tema
        tipo = None
    return PALETAS["dark" if tipo == "dark" else "light"]


def color_modelo(modelo: str) -> str:
    """El color sigue a la entidad en todo el dashboard, nunca a su posición."""
    p = paleta()
    return {
        "lgbm_comportamiento": p["s1"],
        "solo_exposicion": p["s2"],
        "lgbm_historial_completo": p["s3"],
        "prevalencia": p["ref"],
    }.get(modelo, p["gris"])


SIMBOLO = {
    "lgbm_comportamiento": "circle",
    "solo_exposicion": "square",
    "lgbm_historial_completo": "diamond",
    "prevalencia": "circle",
}


def _base(fig: go.Figure, alto: int = 360, leyenda: bool = True) -> go.Figure:
    fig.update_layout(
        height=alto,
        margin=dict(l=8, r=24, t=16, b=8),
        font=dict(family=FUENTE, size=14),
        separators=",.",
        showlegend=leyenda,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, title=None),
        hoverlabel=dict(font=dict(family=FUENTE, size=13)),
        bargap=0.45,
        bargroupgap=0.08,
        barcornerradius=4,
    )
    fig.update_xaxes(showgrid=False, zeroline=False, ticks="")
    fig.update_yaxes(gridwidth=1, zeroline=False, ticks="")
    return fig


def mostrar(fig: go.Figure, key: str) -> None:
    st.plotly_chart(
        fig,
        theme="streamlit",
        key=key,
        config={"displayModeBar": False, "locale": "es"},
    )


# --------------------------------------------------------------------------- columnas


def columnas_con_ic(x, y, lo, hi, nombre_x: str, nombre_y: str, alto: int = 340) -> go.Figure:
    """Una serie de columnas con intervalo de confianza (Wilson)."""
    p = paleta()
    fig = go.Figure(
        go.Bar(
            x=x,
            y=y,
            marker=dict(color=p["s1"]),
            error_y=dict(
                type="data",
                symmetric=False,
                array=[h - v for h, v in zip(hi, y, strict=True)],
                arrayminus=[v - lo_ for v, lo_ in zip(y, lo, strict=True)],
                thickness=1.5,
                width=4,
                color=p["ref"],
            ),
            hovertemplate=f"{nombre_x}: %{{x}}<br><b>%{{y:.2f}} %</b> {nombre_y}<extra></extra>",
        )
    )
    fig.update_xaxes(title=nombre_x, type="category")
    fig.update_yaxes(title=f"{nombre_y} (%)", rangemode="tozero")
    return _base(fig, alto, leyenda=False)


def barras_horizontales(
    etiquetas,
    valores,
    nombre_valor: str,
    formato: str = ".3f",
    sufijo: str = "",
    resaltar: list[bool] | None = None,
    colores: list[str] | None = None,
    error=None,
    referencia: float | None = None,
    nombre_referencia: str = "",
    hover_extra=None,
    alto: int | None = None,
) -> go.Figure:
    """Barras ordenadas de arriba abajo; énfasis opcional (una barra en azul, el resto gris)."""
    p = paleta()
    if colores is None:
        colores = p["s1"] if resaltar is None else [p["s1"] if r else p["gris"] for r in resaltar]
    custom = hover_extra if hover_extra is not None else [""] * len(etiquetas)
    textos = [f"{es(v, formato)}{sufijo}" for v in valores]
    if error is not None:
        # El bigote ocuparía el sitio del valor: el valor pasa a la etiqueta del eje.
        etiquetas = [f"{e}  ·  {t}" for e, t in zip(etiquetas, textos, strict=True)]
        textos = None
    fig = go.Figure(
        go.Bar(
            y=etiquetas,
            x=valores,
            orientation="h",
            marker=dict(color=colores),
            error_x=(
                dict(type="data", array=error, thickness=1.5, width=4, color=p["ref"])
                if error is not None
                else None
            ),
            text=textos,
            textposition="outside",
            cliponaxis=False,
            customdata=custom,
            hovertemplate=f"%{{y}}<br><b>%{{x:{formato}}}{sufijo}</b> {nombre_valor}"
            "%{customdata}<extra></extra>",
        )
    )
    if referencia is not None:
        fig.add_vline(x=referencia, line=dict(color=p["ref"], width=1.5))
        fig.add_annotation(
            x=referencia,
            y=1.0,
            yref="paper",
            text=nombre_referencia,
            showarrow=False,
            xanchor="left",
            yanchor="bottom",
            xshift=4,
            font=dict(size=12),
        )
    fig.update_yaxes(autorange="reversed", showgrid=False)
    tope = max(valores) + (max(error) if error is not None else 0)
    fig.update_xaxes(title=nombre_valor, showgrid=True, gridwidth=1, range=[0, tope * 1.15])
    alto = alto or max(220, 44 * len(etiquetas) + 80)
    _base(fig, alto, leyenda=False)
    fig.update_layout(margin=dict(r=64))
    # Grosor ~22 px: banda de 44 px por barra con la mitad de aire.
    fig.update_layout(bargap=max(0.3, 1 - 22 * len(etiquetas) / max(alto - 80, 1)))
    return fig


def barras_agrupadas(
    categorias,
    series: list[tuple[str, list, str]],
    nombre_valor: str,
    formato: str = ".1f",
    sufijo: str = "",
    errores: list | None = None,
    alto: int = 360,
    ancho_px: int = 560,
    con_texto: bool = True,
) -> go.Figure:
    """Columnas agrupadas; ``series`` = [(nombre, valores, color)]. Valor en la punta.

    ``ancho_px`` es el ancho aproximado del área de trazado; con él se fija el hueco
    entre grupos para que cada columna mida unos 22 px. Con intervalos (``errores``) el
    valor no se imprime en la punta, porque chocaría con el bigote: queda en el tooltip
    y en la tabla.
    """
    p = paleta()
    fig = go.Figure()
    for i, (nombre, valores, color) in enumerate(series):
        err = errores[i] if errores else None
        fig.add_bar(
            name=nombre,
            x=categorias,
            y=valores,
            marker=dict(color=color),
            error_y=(
                dict(
                    type="data",
                    symmetric=False,
                    array=err[0],
                    arrayminus=err[1],
                    thickness=1.5,
                    width=4,
                    color=p["ref"],
                )
                if err
                else None
            ),
            text=None if (err or not con_texto) else [f"{es(v, formato)}{sufijo}" for v in valores],
            textposition="outside",
            textfont=dict(size=11),
            constraintext="none",
            cliponaxis=False,
            hovertemplate=f"%{{x}}<br><b>%{{y:{formato}}}{sufijo}</b> {nombre}<extra></extra>",
        )
    fig.update_layout(barmode="group")
    fig.update_xaxes(type="category")
    tope = max(max(v) for _, v, _ in series)
    if errores:
        tope = max(
            tope,
            max(
                max(m + e for m, e in zip(v, er[0], strict=True))
                for (_, v, _), er in zip(series, errores, strict=True)
            ),
        )
    # Aire sobre la barra más alta para que el valor no se encoja al tocar el borde.
    fig.update_yaxes(title=nombre_valor, range=[0, tope * 1.15])
    _base(fig, alto)
    banda = ancho_px / max(len(categorias), 1)
    hueco = 1 - 22 * len(series) * 1.08 / banda
    fig.update_layout(bargap=min(0.85, max(0.2, hueco)), bargroupgap=0.08)
    return fig


# --------------------------------------------------------------------------- líneas


def lineas(
    x,
    series: list[tuple[str, str, list]],
    titulo_x: str,
    titulo_y: str,
    formato: str = ".3f",
    sufijo: str = "",
    x_log: bool = False,
    etiquetas_x=None,
    marca_x=None,
    alto: int = 360,
    y_rango=None,
) -> go.Figure:
    """Líneas de 2 px con marcadores de 8 px y anillo; ``series`` = [(modelo, nombre, valores)].

    La identidad se lee por color, símbolo y etiqueta directa al final de cada línea.
    """
    p = paleta()
    fig = go.Figure()
    for modelo, nombre, valores in series:
        color = color_modelo(modelo)
        es_ref = modelo == "prevalencia"
        fig.add_scatter(
            x=x,
            y=valores,
            name=nombre,
            mode="lines+markers",
            line=dict(color=color, width=1.5 if es_ref else 2, shape="linear"),
            marker=dict(
                size=6 if es_ref else 9,
                symbol=SIMBOLO.get(modelo, "circle"),
                color=color,
                line=dict(width=2, color=p["fondo"]),
            ),
            hovertemplate=f"<b>%{{y:{formato}}}{sufijo}</b> {nombre}<extra></extra>",
        )
        fig.add_annotation(
            x=x[-1] if not x_log else _log10(x[-1]),
            y=valores[-1],
            text=nombre,
            showarrow=False,
            xanchor="left",
            xshift=10,
            font=dict(size=12),
        )
    if marca_x is not None:
        todos = [v for _, _, vals in series for v in vals]
        tope = y_rango[1] if y_rango else max(todos) * 1.05
        fig.add_scatter(
            x=[marca_x, marca_x],
            y=[y_rango[0] if y_rango else 0, tope],
            mode="lines",
            line=dict(color=p["ref"], width=1),
            showlegend=False,
            hoverinfo="skip",
        )
    fig.update_xaxes(
        title=titulo_x,
        type="log" if x_log else None,
        tickvals=x if etiquetas_x is not None else None,
        ticktext=etiquetas_x,
        showgrid=False,
    )
    fig.update_yaxes(title=titulo_y, range=y_rango)
    fig.update_layout(hovermode="x unified")
    _base(fig, alto)
    fig.update_layout(margin=dict(r=190))
    return fig


def _log10(v: float) -> float:
    import math

    return math.log10(v)


def calibracion(prob, obs) -> go.Figure:
    p = paleta()
    tope = max(max(prob), max(obs)) * 1.08
    fig = go.Figure()
    fig.add_scatter(
        x=[0, tope],
        y=[0, tope],
        mode="lines",
        name="Calibración perfecta",
        line=dict(color=p["ref"], width=1.5),
        hoverinfo="skip",
    )
    fig.add_scatter(
        x=prob,
        y=obs,
        mode="lines+markers",
        name="Modelo final",
        line=dict(color=p["s1"], width=2),
        marker=dict(size=9, color=p["s1"], line=dict(width=2, color=p["fondo"])),
        hovertemplate="Predicha %{x:.1%}<br><b>Observada %{y:.1%}</b><extra></extra>",
    )
    fig.update_xaxes(title="Probabilidad media predicha (decil)", tickformat=".0%", range=[0, tope])
    fig.update_yaxes(title="Tasa de fraude observada", tickformat=".0%", range=[0, tope])
    return _base(fig, 360)
