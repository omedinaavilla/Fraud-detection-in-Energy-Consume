"""Estilo visual único del proyecto (compartido por el EDA y el artículo).

Implementa la gramática visual de ``.claude/skills/steg-eda-visuals/SKILL.md``: una
sola hoja de estilo aplicada antes de cualquier figura, paleta fija de dos colores para
fraude/no-fraude, un color neutro para todo lo que no distingue la etiqueta, una rampa
secuencial de un solo tono para lo ordenado, y guardado en PNG a 300 dpi para revisión
rápida en ``reports/figures/`` (el paso a vectorial para ``paper/figuras/`` lo hace
``src/steg/reporting/`` en la Fase 9, sobre las mismas figuras).

Los ayudantes de trazado que viven aquí son los únicos que debe usar
``notebooks/01_eda.ipynb``: si una figura necesita un tipo de gráfico nuevo, se añade
aquí con su estilo, no se configura ``matplotlib`` en la celda que llama.

Reglas de la hoja de estilo, para que cualquier figura nueva se parezca a las demás:

* Texto en tinta (negro, gris oscuro o gris medio), nunca en el color de la serie. El
  color va en la marca (barra, línea, punto), no en la etiqueta.
* Rejilla de línea fina, continua y clara, solo en el eje que lleva la magnitud; sin
  marcas de tick; sin recuadro superior ni derecho.
* Ejes de conteo con miles abreviados (``400 k``, ``1,5 M``) y coma decimal, en
  convención española.
* Título en negrita alineado a la izquierda y, cuando hace falta, un subtítulo en gris
  con la unidad o la condición que el título no dice (:func:`set_title`).
* Los valores extremos no se ocultan: si una figura recorta, submuestrea o usa escala
  logarítmica, lo declara en el pie (:func:`add_caption`).

El módulo no fija backend a propósito: el notebook usa el backend inline para mostrar
la figura y :func:`save_figure` la escribe además en ``reports/figures/``. Las dos
cosas conviven —``fig.savefig`` funciona con cualquier backend—, de modo que la figura
queda tanto a la vista de quien lee el notebook como en disco para el manuscrito.
"""

from __future__ import annotations

import math
from collections.abc import Callable, Sequence
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.ticker import FixedLocator, FuncFormatter, MaxNLocator

# --- Paleta ------------------------------------------------------------------------
#
# Pareja fija fraude / no-fraude: se reutiliza en cualquier figura que distinga por
# target y nunca se reasignan colores entre figuras (steg-eda-visuals). Los dos tonos
# pasan las seis comprobaciones del validador de paleta (banda de luminosidad, croma,
# separación bajo daltonismo, contraste >= 3:1 sobre blanco).
COLOR_NO_FRAUD = "#2A78D6"
COLOR_FRAUD = "#D03B3B"

# Color neutro: toda marca que no distingue la etiqueta (histogramas, barras de
# frecuencia, series temporales). Es un verde azulado apagado, distinto del azul de
# «no fraude» para que un lector no confunda una figura univariada con una por clase.
COLOR_NEUTRAL = "#0E9594"
COLOR_NEUTRAL_LIGHT = "#A9D3D3"

# Colores para la comparación train vs. test. No distinguen target (test no lo tiene),
# así que reutilizan el neutro y un gris claro para no competir con la pareja
# fraude/no-fraude.
COLOR_TRAIN = COLOR_NEUTRAL
COLOR_TEST = "#9E9E9E"

# Tinta: texto y elementos de referencia. Nunca lleva el color de una serie.
INK = "#1F1F1F"
INK_SECONDARY = "#52514E"
INK_MUTED = "#898781"
COLOR_GRID = "#E4E3DC"
COLOR_AXIS = "#C3C2B7"

# Rampa secuencial de un solo tono (claro = poco, oscuro = mucho), derivada del neutro.
# Se registra en matplotlib para poder pasarla por nombre a ``imshow``.
_SEQ_STOPS = ["#EEF4F5", "#B9DCDC", "#7FBFBF", "#3FA3A3", "#0E9594", "#0B6667", "#063F40"]
SEQUENTIAL_CMAP = "steg_seq"
try:
    mpl.colormaps.register(LinearSegmentedColormap.from_list(SEQUENTIAL_CMAP, _SEQ_STOPS))
except ValueError:
    # Ya registrada (el notebook reimportó el módulo). El mapa no cambia entre importaciones.
    pass

# Rampa divergente para matrices centradas en cero (correlaciones, efectos con signo):
# azul <-> rojo con gris neutro en el centro, la misma pareja que fraude/no-fraude.
DIVERGING_CMAP = "RdBu_r"

FIGSIZE_DEFAULT = (6.0, 4.0)
FIGSIZE_WIDE = (8.0, 4.0)
FIGSIZE_TALL = (6.0, 6.0)
FIGSIZE_GRID = (8.0, 6.0)
DPI = 300

# Año a partir del cual el volumen de facturación es real (ver 00_data_audit.md y
# steg-eda-protocol). Toda figura temporal que incluya años anteriores lo marca.
VOLUME_BREAK_YEAR = 2005

MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]


def apply_style() -> None:
    """Aplica la hoja de estilo del proyecto. Llamar una vez antes de graficar."""
    plt.rcParams.update(
        {
            # Tipografía: la sans del sistema; cae a DejaVu Sans donde no exista.
            "font.family": "sans-serif",
            "font.sans-serif": [
                "Segoe UI",
                "Source Sans 3",
                "Helvetica Neue",
                "Arial",
                "Liberation Sans",
                "DejaVu Sans",
            ],
            "font.size": 10,
            "text.color": INK,
            # Títulos: negrita, a la izquierda, con aire.
            "axes.titlesize": 11.5,
            "axes.titleweight": "bold",
            "axes.titlelocation": "left",
            "axes.titlepad": 10,
            "axes.titlecolor": INK,
            "figure.titlesize": 12.5,
            "figure.titleweight": "bold",
            # Etiquetas y ticks en tinta secundaria, sin marcas de tick.
            "axes.labelsize": 9.5,
            "axes.labelcolor": INK_SECONDARY,
            "axes.labelpad": 6,
            "xtick.labelsize": 9,
            "ytick.labelsize": 9,
            "xtick.color": COLOR_AXIS,
            "ytick.color": COLOR_AXIS,
            "xtick.labelcolor": INK_SECONDARY,
            "ytick.labelcolor": INK_SECONDARY,
            "xtick.major.size": 0,
            "ytick.major.size": 0,
            "xtick.minor.size": 0,
            "ytick.minor.size": 0,
            "xtick.major.pad": 5,
            "ytick.major.pad": 5,
            # Recuadro: solo los ejes izquierdo e inferior, finos y claros.
            "axes.edgecolor": COLOR_AXIS,
            "axes.linewidth": 0.8,
            "axes.spines.top": False,
            "axes.spines.right": False,
            # Rejilla: línea fina, continua, un paso por encima del fondo, detrás de las marcas.
            "axes.grid": True,
            "axes.grid.axis": "both",
            "axes.axisbelow": True,
            "grid.color": COLOR_GRID,
            "grid.linewidth": 0.6,
            "grid.linestyle": "-",
            "grid.alpha": 1.0,
            # Marcas.
            "lines.linewidth": 1.8,
            "lines.markersize": 5,
            "lines.solid_capstyle": "round",
            "lines.solid_joinstyle": "round",
            "patch.linewidth": 0.5,
            "legend.fontsize": 9,
            "legend.frameon": False,
            "legend.handlelength": 1.4,
            "legend.labelcolor": INK_SECONDARY,
            # Lienzo y guardado.
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "figure.dpi": 100,
            "savefig.dpi": DPI,
            "savefig.bbox": "tight",
            "savefig.pad_inches": 0.12,
            "savefig.facecolor": "white",
            # El notebook deja abiertas ~20 figuras para que el backend inline las
            # muestre; la advertencia de matplotlib al pasar de 20 no aporta nada aquí.
            "figure.max_open_warning": 0,
        }
    )


# --- Formato numérico --------------------------------------------------------------


def es_number(value: float, decimals: int | None = None) -> str:
    """Número en convención española: punto de millar y coma decimal.

    ``decimals=None`` deja el número como viene (enteros sin decimales, el resto con
    los que hagan falta hasta dos). Se usa en etiquetas de figuras, no en tablas.
    """
    v = float(value)
    if decimals is None:
        decimals = 0 if v.is_integer() else 2
    s = f"{v:,.{decimals}f}"
    return s.replace(",", " ").replace(".", ",").replace(" ", ".")


def sig_number(value: float, digits: int = 3) -> str:
    """Número con ``digits`` cifras significativas, sin notación científica y con coma
    decimal: 10,444 → '10,4'; 0,000045 → '0,0000447'. Para etiquetas en escala
    logarítmica, donde los valores se reparten en varios órdenes de magnitud."""
    v = float(value)
    if v == 0:
        return "0"
    s = np.format_float_positional(v, precision=digits, unique=False, fractional=False, trim="-")
    return s.replace(".", ",")


def _unit_for(magnitude: float) -> str:
    """Unidad de miles para una magnitud: '' (entero), 'k' o 'M'. El umbral de 'M' se
    adelanta a 999.500 para que un valor que redondea a un millón no salga '1000 k'."""
    a = abs(float(magnitude))
    if a >= 999_500:
        return "M"
    if a >= 1e4:
        return "k"
    return ""


def _trim(value: float, decimals: int) -> str:
    """``f'{value:.{decimals}f}'`` sin ceros de cola ('12.50' → '12.5', '5.0' → '5')."""
    s = f"{value:.{decimals}f}"
    return s.rstrip("0").rstrip(".") if "." in s else s


def compact_number(value: float, unit: str | None = None) -> str:
    """Miles abreviados para ejes de conteo: 2.500 → '2.500', 12.500 → '12,5 k',
    400.000 → '400 k', 1.500.000 → '1,5 M'.

    ``unit`` fuerza la unidad ('', 'k' o 'M'); se usa para que todos los ticks de un
    mismo eje compartan unidad (:func:`format_axis_thousands` la decide una vez por eje
    a partir de su valor máximo). Sin ``unit``, cada valor elige la suya.
    """
    v = float(value)
    if v == 0:
        return "0"
    if unit is None:
        unit = _unit_for(v)
    if unit == "M":
        s = _trim(v / 1e6, 2) + " M"
    elif unit == "k":
        s = _trim(v / 1e3, 1) + " k"
    elif v.is_integer():
        s = f"{v:,.0f}"
    else:
        s = _trim(v, 2)
    return s.replace(",", " ").replace(".", ",").replace(" ", ".")


def _thousands_formatter(axis_obj) -> FuncFormatter:
    """Formateador que elige la unidad una vez por eje, según el máximo visible, para que
    un eje que cruza los 10.000 no mezcle '5.000' con '10 k'."""

    def _fmt(x: float, _pos: int) -> str:
        lo, hi = axis_obj.get_view_interval()
        return compact_number(x, _unit_for(max(abs(lo), abs(hi))))

    return FuncFormatter(_fmt)


def format_axis_thousands(ax: plt.Axes, axis: str = "y") -> None:
    """Ticks de conteo en miles abreviados (``400 k``, ``1,5 M``) en vez de ``4e5``.
    Todos los ticks del eje comparten la unidad, decidida por el máximo del eje."""
    target = ax.yaxis if axis == "y" else ax.xaxis
    target.set_major_formatter(_thousands_formatter(target))


def format_axis_percent(ax: plt.Axes, axis: str = "y", decimals: int | None = None) -> None:
    """Ticks en porcentaje con coma decimal (``8,3 %``)."""
    formatter = FuncFormatter(lambda x, _pos: f"{es_number(x, decimals)} %")
    (ax.yaxis if axis == "y" else ax.xaxis).set_major_formatter(formatter)


def format_axis_log10_1p(ax: plt.Axes, axis: str = "x") -> None:
    """Ticks legibles para un eje en escala log10(1 + x): 0, 10, 100, 1 k, 10 k, ...

    La marca ``k`` corresponde a 10^k − 1 (9, 99, 999...), que en escala logarítmica es
    indistinguible de 10^k para el lector; el pie de figura declara la transformación.
    """
    target = ax.xaxis if axis == "x" else ax.yaxis
    # En un panel estrecho (rejilla de 2x3) siete etiquetas se solapan: se limita el
    # número de ticks según el ancho que el eje ocupa en la figura.
    size = ax.figure.get_size_inches()[0 if axis == "x" else 1]
    extent = ax.get_position().width if axis == "x" else ax.get_position().height
    nbins = 8 if size * extent >= 4.0 else 4
    target.set_major_locator(MaxNLocator(integer=True, nbins=nbins))

    def _label(k: float, _pos: int) -> str:
        k = int(round(k))
        if k <= 0:
            return "0"
        if k == 3:
            return "1 k"
        return compact_number(10**k)

    target.set_major_formatter(FuncFormatter(_label))


# --- Anatomía común -----------------------------------------------------------------


def save_figure(fig: plt.Figure, path: Path, close: bool = False) -> None:
    """Guarda la figura en ``path`` (PNG, 300 dpi) creando el directorio si hace falta.

    ``close`` es ``False`` por defecto porque el consumidor principal es el notebook:
    cerrar la figura antes de que termine la celda impide que el backend inline la
    muestre.

    No devuelve la figura a propósito. El backend inline ya la dibuja al terminar la
    celda; si además se devolviera, Jupyter dibujaría el valor de retorno y la figura
    saldría dos veces en toda celda que termine en esta llamada.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, facecolor="white")
    if close:
        plt.close(fig)


def add_caption(fig: plt.Figure, text: str) -> None:
    """Añade el pie de figura. Se usa para declarar supuestos (unidad, filas excluidas,
    escala logarítmica) que la skill de visuales exige no ocultar."""
    fig.text(0.0, -0.035, text, fontsize=8, color=INK_MUTED, ha="left", va="top", wrap=True)


def set_title(
    ax: plt.Axes, title: str, subtitle: str | None = None, size: float | None = None
) -> None:
    """Título en negrita a la izquierda y, opcionalmente, un subtítulo en gris debajo.

    El subtítulo lleva lo que el título no dice y la figura necesita para leerse sola:
    la unidad, el filtro aplicado o la condición («% de facturas en cero», «desde 2005»).
    """
    ax.set_title(title, loc="left", pad=(20 if subtitle else 8), fontsize=size)
    if subtitle:
        ax.annotate(
            subtitle,
            xy=(0.0, 1.0),
            xycoords="axes fraction",
            xytext=(0, 5),
            textcoords="offset points",
            ha="left",
            va="bottom",
            fontsize=8.5,
            color=INK_MUTED,
        )


#: Fondo blanco semitransparente detrás de las etiquetas de referencia, para que sigan
#: legibles cuando la línea cruza barras o puntos.
_LABEL_BBOX = {"boxstyle": "round,pad=0.15", "facecolor": "white", "edgecolor": "none",
               "alpha": 0.85}


def _reference_line(
    ax: plt.Axes,
    value: float,
    label: str,
    orientation: str = "h",
    y_text: float | None = None,
    label_x: float = 0.0,
) -> None:
    """Línea de referencia (tasa global, reparto uniforme) en tinta secundaria.

    Es una referencia, no una serie: va discontinua y sin color de datos. Para una
    línea horizontal, ``label_x`` es la posición de la etiqueta en fracción del eje
    (0 = izquierda, 1 = derecha); la etiqueta lleva fondo blanco por si cae sobre marcas.
    """
    style = {"color": INK_SECONDARY, "linestyle": (0, (4, 3)), "linewidth": 1.0, "zorder": 2}
    if orientation == "h":
        ax.axhline(value, **style)
        ax.annotate(
            label,
            xy=(label_x, value),
            xycoords=("axes fraction", "data"),
            xytext=(4 if label_x < 0.5 else -4, 4),
            textcoords="offset points",
            fontsize=8,
            color=INK_SECONDARY,
            ha="left" if label_x < 0.5 else "right",
            va="bottom",
            bbox=_LABEL_BBOX,
            zorder=5,
        )
    else:
        ax.axvline(value, **style)
        ax.annotate(
            label,
            xy=(value, 1.0 if y_text is None else y_text),
            xycoords=("data", "axes fraction"),
            xytext=(4, -2),
            textcoords="offset points",
            fontsize=8,
            color=INK_SECONDARY,
            ha="left",
            va="top",
            bbox=_LABEL_BBOX,
            zorder=5,
        )


def log10_1p(values: np.ndarray) -> np.ndarray:
    """log10(1 + x) para variables de consumo con muchos ceros y cola extrema.

    Se usa +1 en vez de descartar ceros porque el consumo cero es informativo en este
    dataset (factura emitida sin consumo registrado), no un faltante.
    """
    arr = np.asarray(values, dtype="float64")
    return np.log10(1.0 + np.clip(arr, 0.0, None))


# --- Distribuciones ----------------------------------------------------------------


def plot_log_histogram(
    ax: plt.Axes,
    values: np.ndarray,
    color: str = COLOR_NEUTRAL,
    bins: int = 60,
    label: str | None = None,
) -> None:
    """Histograma en escala log10(1+x) del eje x, con ticks legibles (0, 10, 100, 1 k...).

    El eje x se etiqueta fuera (``ax.set_xlabel``); el pie de figura declara la escala.
    """
    ax.hist(
        log10_1p(values),
        bins=bins,
        color=color,
        alpha=0.92,
        label=label,
        edgecolor="white",
        linewidth=0.3,
    )
    ax.set_ylabel("facturas")
    ax.grid(axis="x", visible=False)
    format_axis_thousands(ax, "y")
    format_axis_log10_1p(ax, "x")


def plot_ecdf(
    ax: plt.Axes,
    values: np.ndarray,
    color: str = COLOR_NEUTRAL,
    label: str | None = None,
    max_points: int = 20000,
    seed: int = 42,
) -> None:
    """ECDF. Si hay más de ``max_points`` valores, submuestrea con semilla fija para que
    el PNG no pese de más; la forma de la curva no cambia a esa escala."""
    arr = np.asarray(values, dtype="float64")
    arr = arr[np.isfinite(arr)]
    arr = np.sort(arr)
    if arr.size > max_points:
        idx = np.linspace(0, arr.size - 1, max_points).astype(int)
        arr = arr[idx]
        y = (idx + 1) / (np.asarray(values, dtype="float64").size)
    else:
        y = np.arange(1, arr.size + 1) / arr.size
    ax.step(arr, y, where="post", color=color, label=label, linewidth=1.8)
    ax.set_ylabel("proporción acumulada de clientes")
    ax.set_ylim(0, 1.02)


def boxplot_stats(values: np.ndarray, label: str) -> dict[str, object]:
    """Estadísticos de un diagrama de caja, calculados una vez sobre la escala original.

    Devuelve cuartiles, cercas de Tukey (1,5 × RIC) y extremos de los bigotes (el dato
    más extremo que queda dentro de cada cerca), junto con el conteo y el porcentaje de
    valores por encima de la cerca superior. Son las mismas definiciones que usa
    :func:`steg.eda.univariate.describe_numeric` para ``iqr_upper_fence`` y
    ``n_outliers_high_iqr``, de modo que la figura y la tabla de atípicos cuadran.

    Se precalcula en vez de pasar millones de valores a ``ax.boxplot`` porque el dibujo
    no necesita los datos, solo estos números, y así la figura se traza en milisegundos.
    """
    arr = np.asarray(values, dtype="float64")
    arr = arr[np.isfinite(arr)]
    n = int(arr.size)
    if n == 0:
        return {"label": label, "n": 0}
    q1, med, q3 = (float(v) for v in np.percentile(arr, [25, 50, 75]))
    iqr = q3 - q1
    lo_fence, hi_fence = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    inside = arr[(arr >= lo_fence) & (arr <= hi_fence)]
    n_hi = int((arr > hi_fence).sum())
    n_lo = int((arr < lo_fence).sum())
    return {
        "label": label,
        "n": n,
        "min": float(arr.min()),
        "q1": q1,
        "med": med,
        "q3": q3,
        "iqr": iqr,
        "iqr_lower_fence": lo_fence,
        "iqr_upper_fence": hi_fence,
        "whislo": float(inside.min()) if inside.size else q1,
        "whishi": float(inside.max()) if inside.size else q3,
        "n_outliers_low": n_lo,
        "n_outliers_high": n_hi,
        "pct_outliers_high": round(100.0 * n_hi / n, 4),
        "p99": float(np.percentile(arr, 99)),
        "max": float(arr.max()),
    }


def plot_boxplots(
    ax: plt.Axes,
    stats: Sequence[dict[str, object]],
    log: bool = True,
    color: str = COLOR_NEUTRAL,
    annotate: str | None = "outliers",
    show_max: bool = True,
) -> None:
    """Diagramas de caja horizontales, uno por variable, a partir de :func:`boxplot_stats`.

    * La caja va del primer al tercer cuartil con la mediana en tinta; los bigotes
      terminan en el dato más extremo dentro de las cercas de Tukey; los valores por
      fuera no se dibujan uno a uno (serían cientos de miles de puntos superpuestos).
    * ``show_max`` dibuja el máximo observado como rombo hueco, para que la cola quede
      declarada aunque no se pinte.
    * ``annotate="outliers"`` escribe a la derecha el porcentaje de valores por encima
      del bigote superior; ``annotate="n"`` escribe el número de valores; ``None`` no
      anota.
    * Con ``log=True`` la escala es log10(1 + x) y los ticks se etiquetan como valores
      (0, 10, 100, 1 k...). Una caja colapsada en 0 significa que al menos tres cuartas
      partes de los valores son cero: es información, no un defecto del dibujo.
    """
    tf = log10_1p if log else (lambda v: np.asarray(v, dtype="float64"))
    stats = [s for s in stats if s.get("n", 0)]
    positions = np.arange(len(stats))[::-1]
    bxp_stats = []
    for s in stats:
        bxp_stats.append(
            {
                "label": str(s["label"]),
                "q1": float(tf(s["q1"])),
                "med": float(tf(s["med"])),
                "q3": float(tf(s["q3"])),
                "whislo": float(tf(s["whislo"])),
                "whishi": float(tf(s["whishi"])),
                "fliers": [],
            }
        )
    orient = (
        {"orientation": "horizontal"}
        if mpl.__version_info__ >= (3, 10)
        else {"vert": False}
    )
    ax.bxp(
        bxp_stats,
        positions=positions,
        widths=0.55,
        patch_artist=True,
        showfliers=False,
        boxprops={"facecolor": color, "edgecolor": "white", "linewidth": 0.8, "alpha": 0.92},
        medianprops={"color": INK, "linewidth": 1.6},
        whiskerprops={"color": INK_SECONDARY, "linewidth": 1.2},
        capprops={"color": INK_SECONDARY, "linewidth": 1.2},
        **orient,
    )
    ax.set_yticks(positions)
    ax.set_yticklabels([str(s["label"]) for s in stats])
    ax.grid(axis="y", visible=False)
    ax.spines["left"].set_visible(False)
    if log:
        # Si ningún bigote llega a cero (p. ej. solo valores positivos), el eje arranca
        # justo por debajo del bigote más bajo, para no mostrar un tick en «0».
        lowest = min(float(tf(s["whislo"])) for s in stats) if stats else 0.0
        if lowest > 0:
            ax.set_xlim(left=max(0.05, lowest - 0.25))
        format_axis_log10_1p(ax, "x")
    if show_max:
        ax.scatter(
            [float(tf(s["max"])) for s in stats],
            positions,
            marker="D",
            s=26,
            facecolor="white",
            edgecolor=INK_SECONDARY,
            linewidth=1.1,
            zorder=4,
        )
    if annotate:
        for s, y in zip(stats, positions, strict=True):
            if annotate == "outliers":
                text = f"{es_number(s['pct_outliers_high'], 1)} % por encima del bigote"
            else:
                text = f"n = {es_number(s['n'])}"
            ax.annotate(
                text,
                xy=(1.0, y),
                xycoords=("axes fraction", "data"),
                xytext=(6, 0),
                textcoords="offset points",
                fontsize=8,
                color=INK_MUTED,
                ha="left",
                va="center",
                annotation_clip=False,
            )


# --- Frecuencias y tasas -----------------------------------------------------------


def _format_value(spec: str | Callable[[float], str], value: float) -> str:
    """Etiqueta de un valor: ``spec`` es un formato (``"{:.2f} %"``, con coma decimal
    aplicada después) o una función que recibe el valor y devuelve el texto."""
    if callable(spec):
        return spec(float(value))
    return spec.format(value).replace(".", ",")


def plot_bars(
    ax: plt.Axes,
    x: Sequence[float],
    heights: Sequence[float],
    color: str = COLOR_NEUTRAL,
    xlabel: str = "",
    ylabel: str = "",
    annotate_values: str | None = None,
    width: float = 0.72,
) -> None:
    """Barras verticales sobre un eje x numérico o categórico ordenado.

    ``annotate_values`` es un formato (p. ej. ``"{:.0f} %"``) que escribe el valor
    sobre cada barra; se usa cuando hay pocas barras y una domina tanto que el resto
    queda ilegible sin el número.
    """
    x = list(x)
    h = np.asarray(heights, dtype="float64")
    ax.bar(x, h, color=color, width=width, edgecolor="white", linewidth=0.5)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.grid(axis="x", visible=False)
    if h.size and float(np.nanmax(h)) >= 1e4:
        format_axis_thousands(ax, "y")
    if annotate_values is not None:
        for xi, v in zip(x, h, strict=True):
            ax.annotate(
                _format_value(annotate_values, v),
                xy=(xi, v),
                xytext=(0, 3),
                textcoords="offset points",
                fontsize=8,
                color=INK_SECONDARY,
                ha="center",
                va="bottom",
            )
        ax.set_ylim(0, float(np.nanmax(h)) * 1.12)


def plot_barh_frequency(
    ax: plt.Axes,
    labels: Sequence[str],
    counts: Sequence[float],
    color: str = COLOR_NEUTRAL,
    xlabel: str = "filas",
    annotate_values: str | None = None,
) -> None:
    """Barras horizontales ordenadas por frecuencia (la de mayor conteo arriba).

    ``annotate_values`` es un formato (p. ej. ``"{:.2f} %"``) que escribe el valor al
    final de cada barra. Se usa cuando el reparto es tan desigual que las categorías
    minoritarias quedan como barras de pocos píxeles y solo el número las hace legibles.
    """
    # ``order`` son posiciones: si ``labels`` llega como Series con índice propio,
    # ``labels[i]`` buscaría la etiqueta i y no la posición i.
    labels = list(labels)
    values = np.asarray(counts, dtype="float64")
    order = np.argsort(values)
    y = np.arange(len(labels))
    ax.barh(y, values[order], color=color, height=0.68, edgecolor="white", linewidth=0.5)
    ax.set_yticks(y)
    ax.set_yticklabels([str(labels[i]) for i in order])
    ax.set_xlabel(xlabel)
    ax.grid(axis="y", visible=False)
    ax.spines["left"].set_visible(False)
    if values.size and float(values.max()) >= 1e4:
        format_axis_thousands(ax, "x")
    if annotate_values is not None:
        xmax = float(values.max()) if values.size else 1.0
        for i, v in enumerate(values[order]):
            ax.annotate(
                _format_value(annotate_values, v),
                xy=(v, i),
                xytext=(4, 0),
                textcoords="offset points",
                fontsize=8,
                color=INK_SECONDARY,
                va="center",
            )
        ax.set_xlim(0, xmax * 1.2)


def plot_lollipop(
    ax: plt.Axes,
    labels: Sequence[str],
    values: Sequence[float],
    counts: Sequence[int] | None = None,
    color: str = COLOR_NEUTRAL,
    xlabel: str = "% de filas afectadas",
    log: bool = True,
    value_fmt: str = "{} %",
) -> None:
    """Gráfico de puntos con tallo, una fila por elemento, ordenado de mayor a menor.

    Pensado para magnitudes que se reparten en varios órdenes de magnitud (frecuencia
    de anomalías: de dos filas a una de cada diez). Una barra en escala logarítmica
    engañaría, porque su longitud dejaría de ser proporcional al valor; el punto no.
    Cada valor se escribe a su derecha, con el conteo entre paréntesis si se pasa
    ``counts``, de modo que la escala no es la única forma de leerlo.
    """
    labels = list(labels)
    v = np.asarray(values, dtype="float64")
    # ``counts`` puede llegar como Series con índice propio: se pasa a posiciones.
    counts_arr = None if counts is None else np.asarray(list(counts))
    order = np.argsort(v)
    y = np.arange(len(labels))
    positive = v[v > 0]
    if log:
        # Una década por debajo del mínimo dividido entre tres: así el punto más bajo
        # conserva un tallo visible aunque caiga justo encima de una potencia de diez.
        xmin = 10 ** math.floor(math.log10(float(positive.min()) / 3)) if positive.size else 1e-3
    else:
        xmin = 0.0
    ax.hlines(y, xmin, v[order], color=COLOR_NEUTRAL_LIGHT, linewidth=1.8, zorder=2)
    ax.scatter(v[order], y, s=52, color=color, edgecolor="white", linewidth=1.3, zorder=3)
    ax.set_yticks(y)
    ax.set_yticklabels([str(labels[i]) for i in order])
    ax.set_xlabel(xlabel)
    ax.grid(axis="y", visible=False)
    ax.spines["left"].set_visible(False)
    if log:
        ax.set_xscale("log")
        # El margen derecho aloja las etiquetas; los ticks se detienen en la década que
        # cubre el máximo, para que ese margen no se lea como rango de datos.
        vmax = float(v.max())
        ax.set_xlim(xmin, vmax * 40)
        k_lo = math.floor(math.log10(xmin))
        k_hi = math.ceil(math.log10(vmax)) if vmax > 0 else k_lo
        ax.xaxis.set_major_locator(FixedLocator([10.0**k for k in range(k_lo, k_hi + 1)]))
        ax.xaxis.set_major_formatter(FuncFormatter(lambda x, _p: sig_number(x, 1)))
        ax.xaxis.set_minor_formatter(FuncFormatter(lambda x, _p: ""))
    else:
        ax.set_xlim(0, float(v.max()) * 1.35)
    for i, idx in enumerate(order):
        text = value_fmt.format(sig_number(v[idx], 3))
        if counts_arr is not None:
            text += f"  (n = {es_number(counts_arr[idx])})"
        ax.annotate(
            text,
            xy=(v[idx], i),
            xytext=(8, 0),
            textcoords="offset points",
            fontsize=8,
            color=INK_SECONDARY,
            va="center",
        )


def plot_rate_with_ci(
    ax: plt.Axes,
    labels: Sequence[str],
    rate: Sequence[float],
    lo: Sequence[float],
    hi: Sequence[float],
    n: Sequence[int],
    baseline: float | None = None,
    color: str = COLOR_FRAUD,
    xlabel: str = "tasa de fraude (%)",
    annotate_n: bool = True,
) -> None:
    """Tasa de positivos por categoría con intervalo de Wilson y ``n`` anotado.

    La skill de visuales prohíbe reportar la tasa por categoría como un punto suelto:
    varias categorías de ``region`` tienen pocos clientes y su intervalo es ancho.
    """
    rate = np.asarray(rate, dtype="float64")
    lo = np.asarray(lo, dtype="float64")
    hi = np.asarray(hi, dtype="float64")
    y = np.arange(len(labels))
    err = np.vstack([rate - lo, hi - rate])
    ax.barh(y, rate, color=color, alpha=0.9, height=0.68, edgecolor="white", linewidth=0.5)
    ax.errorbar(
        rate, y, xerr=err, fmt="none", ecolor=INK_SECONDARY, elinewidth=1.0, capsize=2.5, zorder=3
    )
    ax.set_yticks(y)
    ax.set_yticklabels([str(lab) for lab in labels])
    ax.set_xlabel(xlabel)
    ax.grid(axis="y", visible=False)
    ax.spines["left"].set_visible(False)
    if baseline is not None:
        _reference_line(ax, baseline, f"tasa global {es_number(baseline, 2)} %", orientation="v")
    if annotate_n:
        xmax = float(np.nanmax(hi)) if len(hi) else 1.0
        for i, ni in enumerate(n):
            ax.annotate(
                f"n = {es_number(int(ni))}",
                xy=(xmax * 1.03, i),
                fontsize=7.5,
                color=INK_MUTED,
                va="center",
            )
        ax.set_xlim(0, xmax * 1.28)


def plot_forest(
    ax: plt.Axes,
    labels: Sequence[str],
    point: Sequence[float],
    lo: Sequence[float],
    hi: Sequence[float],
    xlabel: str,
    threshold: float | None = None,
) -> None:
    """Gráfico de bosque: tamaño de efecto con intervalo, una fila por variable.

    El color de cada fila se asigna por el signo del efecto usando la pareja fija
    fraude/no-fraude, no por una escala arbitraria.
    """
    point = np.asarray(point, dtype="float64")
    lo = np.asarray(lo, dtype="float64")
    hi = np.asarray(hi, dtype="float64")
    y = np.arange(len(labels))
    colors = [COLOR_FRAUD if p > 0 else COLOR_NO_FRAUD for p in point]
    for i in y:
        ax.plot([lo[i], hi[i]], [i, i], color=colors[i], linewidth=2.0, alpha=0.85, zorder=2)
    ax.scatter(point, y, color=colors, s=42, edgecolor="white", linewidth=1.2, zorder=3)
    ax.axvline(0.0, color=INK_SECONDARY, linewidth=0.9, zorder=1)
    if threshold is not None:
        for sign in (-1.0, 1.0):
            ax.axvline(sign * threshold, color=INK_MUTED, linestyle=(0, (1, 3)), linewidth=0.9)
    ax.set_yticks(y)
    ax.set_yticklabels([str(lab) for lab in labels])
    ax.set_xlabel(xlabel)
    ax.grid(axis="y", visible=False)
    ax.spines["left"].set_visible(False)


def plot_boxplot_by_target(
    ax: plt.Axes,
    values_neg: np.ndarray,
    values_pos: np.ndarray,
    ylabel: str,
    log: bool = True,
) -> None:
    """Caja por clase con escala log10(1+x) opcional, para numéricas muy sesgadas."""
    a = log10_1p(values_neg) if log else np.asarray(values_neg, dtype="float64")
    b = log10_1p(values_pos) if log else np.asarray(values_pos, dtype="float64")
    a = a[np.isfinite(a)]
    b = b[np.isfinite(b)]
    bp = ax.boxplot(
        [a, b],
        tick_labels=["no fraude", "fraude"],
        patch_artist=True,
        showfliers=False,
        widths=0.55,
        medianprops={"color": INK, "linewidth": 1.6},
        whiskerprops={"color": INK_SECONDARY, "linewidth": 1.2},
        capprops={"color": INK_SECONDARY, "linewidth": 1.2},
        boxprops={"edgecolor": "white", "linewidth": 0.8},
    )
    for patch, color in zip(bp["boxes"], [COLOR_NO_FRAUD, COLOR_FRAUD], strict=False):
        patch.set_facecolor(color)
        patch.set_alpha(0.9)
    ax.set_ylabel(ylabel)
    ax.grid(axis="x", visible=False)
    if log:
        format_axis_log10_1p(ax, "y")


def plot_heatmap(
    ax: plt.Axes,
    matrix: np.ndarray,
    row_labels: Sequence[str],
    col_labels: Sequence[str],
    cbar_label: str,
    annotate: bool | None = None,
    fmt: str = "{:.2f}",
    cmap: str = SEQUENTIAL_CMAP,
    vmin: float | None = None,
    vmax: float | None = None,
    rotate_xlabels: int = 45,
    cbar_thousands: bool = False,
) -> None:
    """Heatmap con colorbar y separación blanca entre celdas.

    Anota los valores solo si la matriz es pequeña (<=10x10), como pide la skill de
    visuales; el color del texto se elige por la luminosidad de cada celda, así que
    funciona con cualquier mapa de color. ``cbar_thousands`` formatea la barra de color
    en miles abreviados cuando la magnitud es un conteo.
    """
    matrix = np.asarray(matrix, dtype="float64")
    if annotate is None:
        annotate = matrix.shape[0] <= 10 and matrix.shape[1] <= 10
    im = ax.imshow(matrix, cmap=cmap, aspect="auto", vmin=vmin, vmax=vmax)
    ax.set_xticks(np.arange(len(col_labels)))
    ax.set_xticklabels(
        [str(c) for c in col_labels],
        rotation=rotate_xlabels,
        ha="right" if rotate_xlabels else "center",
    )
    ax.set_yticks(np.arange(len(row_labels)))
    ax.set_yticklabels([str(r) for r in row_labels])
    # Rejilla blanca fina entre celdas (el «hueco de superficie» que separa marcas).
    ax.set_xticks(np.arange(-0.5, len(col_labels), 1), minor=True)
    ax.set_yticks(np.arange(-0.5, len(row_labels), 1), minor=True)
    ax.grid(which="major", visible=False)
    ax.grid(which="minor", color="white", linewidth=1.2)
    ax.tick_params(which="minor", length=0)
    for side in ("left", "bottom"):
        ax.spines[side].set_visible(False)
    cbar = ax.figure.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label(cbar_label)
    cbar.outline.set_visible(False)
    if cbar_thousands:
        cbar.ax.yaxis.set_major_formatter(_thousands_formatter(cbar.ax.yaxis))
    if annotate:
        for i in range(matrix.shape[0]):
            for j in range(matrix.shape[1]):
                val = matrix[i, j]
                if not np.isfinite(val):
                    continue
                r, g, b, _ = im.cmap(im.norm(val))
                luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b
                ax.text(
                    j,
                    i,
                    fmt.format(val).replace(".", ","),
                    ha="center",
                    va="center",
                    fontsize=7.5,
                    color="white" if luminance < 0.55 else INK,
                )


# --- Series temporales -------------------------------------------------------------


def plot_month_profile(
    ax: plt.Axes,
    months: Sequence[int],
    counts: Sequence[float],
    color: str = COLOR_NEUTRAL,
    ylabel: str = "facturas",
    reference: float | None = None,
    reference_label: str = "reparto uniforme",
    annotate_values: str | Callable[[float], str] | None = None,
) -> None:
    """Perfil por mes del año (estacionalidad). Barras verticales en orden de calendario.

    ``reference`` dibuja una línea horizontal de referencia (p. ej. ``100 / 12`` cuando
    las barras son porcentajes): la estacionalidad es la distancia a esa línea. Como esa
    distancia suele ser de pocos puntos sobre barras casi iguales, ``annotate_values``
    escribe el valor sobre cada barra para que la diferencia se pueda leer.
    """
    months = list(months)
    h = np.asarray(list(counts), dtype="float64")
    ax.bar(months, h, color=color, width=0.72, edgecolor="white", linewidth=0.5)
    ax.set_xticks(list(range(1, 13)))
    ax.set_xticklabels(MESES)
    ax.set_xlabel("mes de la factura")
    ax.set_ylabel(ylabel)
    ax.grid(axis="x", visible=False)
    if h.size and float(np.nanmax(h)) >= 1e4:
        format_axis_thousands(ax, "y")
    if annotate_values is not None:
        # Las etiquetas van dentro de la barra, junto a su borde superior, en blanco: así
        # no chocan con la línea de referencia cuando todas las barras la rozan. Una
        # barra demasiado corta para alojar el texto lo lleva encima, en tinta.
        top = float(np.nanmax(h)) if h.size else 1.0
        for xi, v in zip(months, h, strict=True):
            inside = v >= 0.25 * top
            ax.annotate(
                _format_value(annotate_values, v),
                xy=(xi, v),
                xytext=(0, -3 if inside else 3),
                textcoords="offset points",
                fontsize=7.5,
                color="white" if inside else INK_SECONDARY,
                ha="center",
                va="top" if inside else "bottom",
                rotation=90 if inside else 0,
            )
        ax.set_ylim(0, top * 1.12)
    if reference is not None:
        # Etiqueta a la derecha: en este calendario el último mes es de los más bajos,
        # así que ahí la etiqueta no pisa las barras.
        _reference_line(
            ax,
            reference,
            f"{reference_label} ({es_number(reference, 1)} %)",
            orientation="h",
            label_x=1.0,
        )


def plot_rate_by_bin(
    ax: plt.Axes,
    x: Sequence[float],
    rate: Sequence[float],
    lo: Sequence[float],
    hi: Sequence[float],
    xlabel: str,
    baseline: float | None = None,
    color: str = COLOR_FRAUD,
    label: str | None = None,
    ylabel: str = "tasa de fraude (%)",
) -> None:
    """Tasa de positivos a lo largo de una variable ordenada, con banda de intervalo.

    Responde si el riesgo crece de forma monótona con una variable continua, que es lo
    que una tabla de tasas por categoría no deja ver cuando los tramos tienen un orden
    natural (deciles de historial, tramos de antigüedad).
    """
    x = np.asarray(x, dtype="float64")
    ax.fill_between(x, np.asarray(lo), np.asarray(hi), color=color, alpha=0.14, linewidth=0)
    ax.plot(
        x,
        np.asarray(rate),
        color=color,
        marker="o",
        markersize=5.5,
        markeredgecolor="white",
        markeredgewidth=1.0,
        linewidth=1.8,
        label=label,
        zorder=3,
    )
    if baseline is not None:
        _reference_line(ax, baseline, f"tasa global {es_number(baseline, 2)} %", orientation="h")
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.grid(axis="x", visible=False)
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))


def plot_year_series(
    ax: plt.Axes,
    years: Sequence[int],
    counts: Sequence[float],
    color: str = COLOR_NEUTRAL,
    label: str | None = None,
    mark_break: bool = True,
    ylabel: str = "facturas",
) -> None:
    """Serie anual con el quiebre de volumen de 2005 marcado (steg-eda-visuals).

    El tramo anterior al quiebre se sombrea en gris para que se lea como residual sin
    necesidad de leer el pie de figura.
    """
    years = list(years)
    ax.plot(
        years,
        list(counts),
        color=color,
        marker="o",
        markersize=4.5,
        markeredgecolor="white",
        markeredgewidth=0.8,
        linewidth=1.8,
        label=label,
        zorder=3,
    )
    ax.set_xlabel("año de la factura")
    ax.set_ylabel(ylabel)
    ax.grid(axis="x", visible=False)
    ax.margins(x=0.015)
    if counts is not None and len(counts) and float(np.nanmax(np.asarray(counts))) >= 1e4:
        format_axis_thousands(ax, "y")
    if mark_break and len(years) and min(years) < VOLUME_BREAK_YEAR:
        ax.axvspan(
            min(years) - 0.5, VOLUME_BREAK_YEAR, color=COLOR_GRID, alpha=0.55, linewidth=0, zorder=0
        )
        _reference_line(
            ax,
            VOLUME_BREAK_YEAR,
            f"desde {VOLUME_BREAK_YEAR}: volumen real",
            orientation="v",
        )
