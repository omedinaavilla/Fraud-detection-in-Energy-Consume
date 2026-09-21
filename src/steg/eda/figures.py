"""Estilo visual único del proyecto (compartido por el EDA y el artículo).

Implementa la gramática visual de ``.claude/skills/steg-eda-visuals/SKILL.md``: una
sola hoja de estilo aplicada antes de cualquier figura, paleta fija de dos colores para
fraude/no-fraude, colormap perceptualmente uniforme para lo secuencial, y guardado en
PNG a 300 dpi para revisión rápida en ``reports/figures/`` (el paso a vectorial para
``paper/figuras/`` lo hace ``src/steg/reporting/`` en la Fase 9, sobre las mismas
figuras).

Los ayudantes de trazado que viven aquí son los únicos que debe usar
``notebooks/01_eda.ipynb``: si una figura necesita un tipo de gráfico nuevo, se añade
aquí con su estilo, no se configura ``matplotlib`` en la celda que llama.

El módulo no fija backend a propósito: el notebook usa el backend inline para mostrar
la figura y :func:`save_figure` la escribe además en ``reports/figures/``. Las dos
cosas conviven —``fig.savefig`` funciona con cualquier backend—, de modo que la figura
queda tanto a la vista de quien lee el notebook como en disco para el manuscrito.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

# Paleta fija: se reutiliza en cualquier figura que distinga por target, nunca se
# reasignan colores entre figuras (steg-eda-visuals).
COLOR_NO_FRAUD = "#3A6EA5"
COLOR_FRAUD = "#C0392B"
COLOR_NEUTRAL = "#5B5B5B"
SEQUENTIAL_CMAP = "viridis"

# Colores para la comparación train vs. test. No distinguen target (test no lo tiene),
# así que reutilizan el neutro y una variante clara del mismo para no competir con la
# pareja fraude/no-fraude.
COLOR_TRAIN = COLOR_NEUTRAL
COLOR_TEST = "#9E9E9E"

FIGSIZE_DEFAULT = (6.0, 4.0)
FIGSIZE_WIDE = (8.0, 4.0)
FIGSIZE_TALL = (6.0, 6.0)
FIGSIZE_GRID = (8.0, 6.0)
DPI = 300

# Año a partir del cual el volumen de facturación es real (ver 00_data_audit.md y
# steg-eda-protocol). Toda figura temporal que incluya años anteriores lo marca.
VOLUME_BREAK_YEAR = 2005


def apply_style() -> None:
    """Aplica la hoja de estilo del proyecto. Llamar una vez antes de graficar."""
    plt.rcParams.update(
        {
            "font.family": "serif",
            "font.size": 10,
            "axes.titlesize": 11,
            "axes.labelsize": 10,
            "legend.fontsize": 9,
            "xtick.labelsize": 9,
            "ytick.labelsize": 9,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "grid.alpha": 0.25,
            "grid.linewidth": 0.5,
            "figure.dpi": 100,
            "savefig.dpi": DPI,
            "savefig.bbox": "tight",
            # El notebook deja abiertas ~20 figuras para que el backend inline las
            # muestre; la advertencia de matplotlib al pasar de 20 no aporta nada aquí.
            "figure.max_open_warning": 0,
        }
    )


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
    fig.savefig(path)
    if close:
        plt.close(fig)


def add_caption(fig: plt.Figure, text: str) -> None:
    """Añade el pie de figura. Se usa para declarar supuestos (unidad, filas excluidas,
    escala logarítmica) que la skill de visuales exige no ocultar."""
    fig.text(0.0, -0.04, text, fontsize=8, color=COLOR_NEUTRAL, ha="left", va="top", wrap=True)


def log10_1p(values: np.ndarray) -> np.ndarray:
    """log10(1 + x) para variables de consumo con muchos ceros y cola extrema.

    Se usa +1 en vez de descartar ceros porque el consumo cero es informativo en este
    dataset (factura emitida sin consumo registrado), no un faltante.
    """
    arr = np.asarray(values, dtype="float64")
    return np.log10(1.0 + np.clip(arr, 0.0, None))


def plot_log_histogram(
    ax: plt.Axes,
    values: np.ndarray,
    color: str = COLOR_NEUTRAL,
    bins: int = 60,
    label: str | None = None,
) -> None:
    """Histograma en escala log10(1+x) del eje x. El eje se etiqueta fuera."""
    ax.hist(log10_1p(values), bins=bins, color=color, alpha=0.85, label=label)
    ax.set_ylabel("facturas")


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
    ax.step(arr, y, where="post", color=color, label=label, linewidth=1.2)
    ax.set_ylabel("proporción acumulada de clientes")


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
    ax.barh(y, values[order], color=color)
    ax.set_yticks(y)
    ax.set_yticklabels([str(labels[i]) for i in order])
    ax.set_xlabel(xlabel)
    ax.grid(axis="y", visible=False)
    if annotate_values is not None:
        xmax = float(values.max()) if values.size else 1.0
        for i, v in enumerate(values[order]):
            ax.annotate(
                annotate_values.format(v).replace(".", ","),
                xy=(v + xmax * 0.02, i),
                fontsize=8,
                color=COLOR_NEUTRAL,
                va="center",
            )
        ax.set_xlim(0, xmax * 1.18)


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
    ax.barh(y, rate, color=color, alpha=0.85)
    ax.errorbar(rate, y, xerr=err, fmt="none", ecolor=COLOR_NEUTRAL, elinewidth=1.0, capsize=2.5)
    ax.set_yticks(y)
    ax.set_yticklabels([str(lab) for lab in labels])
    ax.set_xlabel(xlabel)
    ax.grid(axis="y", visible=False)
    if baseline is not None:
        ax.axvline(baseline, color=COLOR_NO_FRAUD, linestyle="--", linewidth=1.0)
        ax.annotate(
            f"tasa global {baseline:.2f} %",
            xy=(baseline, len(labels) - 0.4),
            fontsize=8,
            color=COLOR_NO_FRAUD,
            ha="left",
            va="center",
        )
    if annotate_n:
        xmax = float(np.nanmax(hi)) if len(hi) else 1.0
        for i, ni in enumerate(n):
            ax.annotate(
                f"n={int(ni):,}".replace(",", "."),
                xy=(xmax * 1.02, i),
                fontsize=7,
                color=COLOR_NEUTRAL,
                va="center",
            )
        ax.set_xlim(0, xmax * 1.25)


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
        ax.plot([lo[i], hi[i]], [i, i], color=colors[i], linewidth=1.6, alpha=0.8)
    ax.scatter(point, y, color=colors, s=18, zorder=3)
    ax.axvline(0.0, color=COLOR_NEUTRAL, linewidth=0.8)
    if threshold is not None:
        for sign in (-1.0, 1.0):
            ax.axvline(sign * threshold, color=COLOR_NEUTRAL, linestyle=":", linewidth=0.8)
    ax.set_yticks(y)
    ax.set_yticklabels([str(lab) for lab in labels])
    ax.set_xlabel(xlabel)
    ax.grid(axis="y", visible=False)


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
        medianprops={"color": "black", "linewidth": 1.2},
    )
    for patch, color in zip(bp["boxes"], [COLOR_NO_FRAUD, COLOR_FRAUD], strict=False):
        patch.set_facecolor(color)
        patch.set_alpha(0.85)
    ax.set_ylabel(ylabel)
    ax.grid(axis="x", visible=False)


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
) -> None:
    """Heatmap con colorbar. Anota los valores solo si la matriz es pequeña (<=10x10),
    como pide la skill de visuales."""
    if annotate is None:
        annotate = matrix.shape[0] <= 10 and matrix.shape[1] <= 10
    im = ax.imshow(matrix, cmap=cmap, aspect="auto", vmin=vmin, vmax=vmax)
    ax.set_xticks(np.arange(len(col_labels)))
    ax.set_xticklabels([str(c) for c in col_labels], rotation=45, ha="right")
    ax.set_yticks(np.arange(len(row_labels)))
    ax.set_yticklabels([str(r) for r in row_labels])
    ax.grid(visible=False)
    cbar = ax.figure.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label(cbar_label)
    if annotate:
        finite = matrix[np.isfinite(matrix)]
        mid = (finite.min() + finite.max()) / 2 if finite.size else 0.0
        for i in range(matrix.shape[0]):
            for j in range(matrix.shape[1]):
                val = matrix[i, j]
                if not np.isfinite(val):
                    continue
                ax.text(
                    j,
                    i,
                    fmt.format(val),
                    ha="center",
                    va="center",
                    fontsize=7,
                    color="white" if val < mid else "black",
                )


def plot_month_profile(
    ax: plt.Axes,
    months: Sequence[int],
    counts: Sequence[float],
    color: str = COLOR_NEUTRAL,
    ylabel: str = "facturas",
) -> None:
    """Perfil por mes del año (estacionalidad). Barras verticales en orden de calendario."""
    etiquetas = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
    ax.bar(list(months), list(counts), color=color, alpha=0.85)
    ax.set_xticks(list(range(1, 13)))
    ax.set_xticklabels(etiquetas)
    ax.set_xlabel("mes de la factura")
    ax.set_ylabel(ylabel)
    ax.grid(axis="x", visible=False)


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
    ax.fill_between(x, np.asarray(lo), np.asarray(hi), color=color, alpha=0.18, linewidth=0)
    ax.plot(x, np.asarray(rate), color=color, marker="o", markersize=3.5, linewidth=1.4,
            label=label)
    if baseline is not None:
        ax.axhline(baseline, color=COLOR_NO_FRAUD, linestyle="--", linewidth=1.0)
        ax.annotate(
            f"tasa global {baseline:.2f} %".replace(".", ","),
            xy=(x[0], baseline),
            xytext=(0, 4),
            textcoords="offset points",
            fontsize=8,
            color=COLOR_NO_FRAUD,
        )
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)


def plot_year_series(
    ax: plt.Axes,
    years: Sequence[int],
    counts: Sequence[float],
    color: str = COLOR_NEUTRAL,
    label: str | None = None,
    mark_break: bool = True,
    ylabel: str = "facturas",
) -> None:
    """Serie anual con el quiebre de volumen de 2005 marcado (steg-eda-visuals)."""
    ax.plot(list(years), list(counts), color=color, marker="o", markersize=2.5, linewidth=1.2,
            label=label)
    ax.set_xlabel("año de la factura")
    ax.set_ylabel(ylabel)
    if mark_break and len(years) and min(years) < VOLUME_BREAK_YEAR:
        ax.axvline(VOLUME_BREAK_YEAR, color=COLOR_FRAUD, linestyle="--", linewidth=1.0)
        ax.annotate(
            f"{VOLUME_BREAK_YEAR}: inicio del volumen real",
            xy=(VOLUME_BREAK_YEAR, ax.get_ylim()[1] * 0.92),
            fontsize=8,
            color=COLOR_FRAUD,
            ha="left",
        )
