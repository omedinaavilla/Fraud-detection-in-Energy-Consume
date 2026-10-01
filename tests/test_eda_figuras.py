"""Humo de los ayudantes de ``steg.eda.figures`` que añaden opciones nuevas.

Comprueba que dibujan sin error con datos sintéticos y que las opciones nuevas hacen lo que
prometen. Las opciones por defecto deben dejar el dibujo como estaba, porque el notebook
las usa en secciones que no se tocan.
"""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pytest  # noqa: E402

from steg.eda import figures as fg  # noqa: E402


@pytest.fixture(autouse=True)
def _cerrar_figuras():
    fg.apply_style()
    yield
    plt.close("all")


def _textos(ax: plt.Axes) -> list[str]:
    return [t.get_text() for t in ax.texts]


def test_plot_qq_dibuja_cuantiles_y_nota():
    fig, ax = plt.subplots()
    x = np.random.default_rng(0).lognormal(size=10_000)
    fg.plot_qq(ax, x, n_quantiles=50, note="D = 0,10")
    puntos = ax.collections[0].get_offsets()
    assert len(puntos) == 50
    assert np.all(np.diff(puntos[:, 1]) >= 0)
    assert "D = 0,10" in _textos(ax)


def test_plot_month_deviation_rotula_los_extremos():
    fig, ax = plt.subplots()
    cuotas = [8.0, 9.5, 8.5, 8.4, 8.3, 8.2, 8.1, 8.0, 7.9, 8.3, 8.4, 8.4]
    fg.plot_month_deviation(ax, list(range(1, 13)), cuotas)
    alturas = [p.get_height() for p in ax.patches]
    assert alturas == pytest.approx([c - 100 / 12 for c in cuotas])
    textos = _textos(ax)
    assert "9,50 %" in textos and "7,90 %" in textos


def test_plot_boxplots_nube_y_caja_colapsada():
    rng = np.random.default_rng(1)
    con_ceros = np.where(rng.random(5_000) < 0.9, 0.0, rng.lognormal(5, 1, 5_000))
    positivos = rng.lognormal(5, 1, 5_000)
    stats = [fg.boxplot_stats(con_ceros, "a"), fg.boxplot_stats(positivos, "b")]
    assert stats[0]["pct_zero"] == pytest.approx(100 * float((con_ceros == 0).mean()), abs=1e-3)
    fig, ax = plt.subplots()
    fg.plot_boxplots(ax, stats, samples=[con_ceros[:300], positivos[:300]])
    assert any(t.startswith("caja colapsada en 0") for t in _textos(ax))
    # Una nube de 300 puntos por variable, más el rombo de los máximos.
    tamanos = sorted(len(c.get_offsets()) for c in ax.collections)
    assert tamanos == [2, 300, 300]


def test_plot_boxplots_sin_opciones_nuevas_no_dibuja_nube():
    fig, ax = plt.subplots()
    x = np.random.default_rng(2).lognormal(5, 1, 2_000)
    fg.plot_boxplots(ax, [fg.boxplot_stats(x, "x")])
    assert [len(c.get_offsets()) for c in ax.collections] == [1]


def test_plot_boxplot_by_target_con_nube_y_anotaciones():
    rng = np.random.default_rng(3)
    neg, pos = rng.lognormal(6, 1, 4_000), rng.lognormal(7, 0.8, 300)
    fig, ax = plt.subplots()
    fg.plot_boxplot_by_target(ax, neg, pos, ylabel="consumo", n_points=200, annotate=True)
    tamanos = sorted(len(c.get_offsets()) for c in ax.collections)
    assert tamanos == [200, 200]
    assert sum(t.startswith("mediana") for t in _textos(ax)) == 2
    etiquetas = [t.get_text() for t in ax.get_xticklabels()]
    assert etiquetas[0].startswith("no fraude\nn = 4.000")


def test_plot_barh_frequency_otras_al_final_y_filas_reservadas():
    fig, ax = plt.subplots()
    fg.plot_barh_frequency(ax, ["x", "otras", "y"], [50.0, 30.0, 20.0], other_label="otras",
                           min_slots=6)
    etiquetas = [t.get_text() for t in ax.get_yticklabels()]
    assert etiquetas == ["otras", "y", "x"]
    assert ax.get_ylim() == pytest.approx((-3.5, 2.5))


def test_plot_log_histogram_marca_la_mediana_sin_rotulo():
    fig, ax = plt.subplots()
    x = np.random.default_rng(4).lognormal(5, 1, 3_000)
    fg.plot_log_histogram(ax, x, median=True)
    assert len(ax.lines) == 1
    assert ax.lines[0].get_xdata()[0] == pytest.approx(float(fg.log10_1p(np.median(x))))
    assert _textos(ax) == []
