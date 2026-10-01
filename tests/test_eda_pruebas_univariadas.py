"""Pruebas de normalidad, homogeneidad de varianzas y uniformidad de ``steg.eda.univariate``.

Todo sintético y con semilla fija: no depende de los CSV reales de STEG.
"""

from __future__ import annotations

import numpy as np
import pytest
from scipy import stats

from steg.eda import univariate as uni
from steg.eda.bivariate import _rank_biserial


def test_normality_tests_no_rechaza_una_normal():
    x = np.random.default_rng(0).normal(10.0, 2.0, size=20_000)
    r = uni.normality_tests(x, "x")
    assert r["n"] == 20_000
    assert r["shapiro_n"] == uni.SHAPIRO_MAX_N
    assert abs(r["skew"]) < 0.1
    assert abs(r["excess_kurtosis"]) < 0.2
    assert r["shapiro_w"] > 0.99
    assert r["lilliefors_d"] < r["lilliefors_d_critical_05"]
    assert not r["normal_rejected_05"]


def test_normality_tests_rechaza_una_lognormal_y_el_log_la_acerca():
    x = np.random.default_rng(1).lognormal(5.0, 1.0, size=20_000)
    bruto = uni.normality_tests(x, "x", "original")
    en_log = uni.normality_tests(np.log(x), "x", "log")
    assert bruto["normal_rejected_05"]
    assert bruto["skew"] > 2
    assert en_log["lilliefors_d"] < bruto["lilliefors_d"]
    assert en_log["scale"] == "log"


def test_normality_tests_d_coincide_con_kolmogorov_smirnov():
    x = np.random.default_rng(2).exponential(size=3_000)
    r = uni.normality_tests(x, "x")
    esperado = stats.kstest(x, stats.norm(loc=x.mean(), scale=x.std(ddof=1)).cdf).statistic
    assert r["lilliefors_d"] == pytest.approx(esperado, rel=1e-9)
    assert r["lilliefors_d_critical_05"] == pytest.approx(uni.LILLIEFORS_COEF_05 / np.sqrt(3_000))


def test_normality_tests_es_reproducible_y_descarta_faltantes():
    x = np.random.default_rng(3).gamma(2.0, size=12_000)
    x[:10] = np.nan
    a, b = uni.normality_tests(x, "x"), uni.normality_tests(x, "x")
    assert a == b
    assert a["n"] == 11_990


def test_normality_tests_con_muy_pocos_datos_no_calcula():
    assert uni.normality_tests([1.0, 2.0, 3.0], "x") == {"column": "x", "scale": "original", "n": 3}


def test_variance_homogeneity_detecta_dispersion_distinta():
    rng = np.random.default_rng(4)
    a, b = rng.normal(0, 1, 5_000), rng.normal(0, 2, 5_000)
    r = uni.variance_homogeneity(a, b)
    assert r["n_a"] == r["n_b"] == 5_000
    assert r["brown_forsythe_p"] < 1e-6
    assert r["fligner_killeen_p"] < 1e-6
    assert r["mad_ratio"] == pytest.approx(2.0, rel=0.1)
    assert r["iqr_ratio"] == pytest.approx(2.0, rel=0.1)
    assert abs(r["rank_biserial"]) < 0.05


def test_variance_homogeneity_misma_dispersion_con_posicion_desplazada():
    rng = np.random.default_rng(5)
    a, b = rng.normal(0, 1, 5_000), rng.normal(1, 1, 5_000)
    r = uni.variance_homogeneity(a, b)
    assert r["brown_forsythe_p"] > 0.01
    assert r["mad_ratio"] == pytest.approx(1.0, abs=0.1)
    # P(b > a) = Phi(1 / sqrt(2)), así que el rank-biserial esperado es 2 * Phi(0,707) - 1.
    esperado = 2 * stats.norm.cdf(1 / np.sqrt(2)) - 1
    assert r["rank_biserial"] == pytest.approx(esperado, abs=0.03)


def test_variance_homogeneity_usa_el_rank_biserial_de_bivariate():
    rng = np.random.default_rng(6)
    a, b = rng.exponential(1.0, 800), rng.exponential(1.5, 200)
    valores = np.concatenate([a, b])
    etiqueta = np.concatenate([np.zeros(a.size), np.ones(b.size)]).astype("int8")
    r = uni.variance_homogeneity(a, b)
    assert r["rank_biserial"] == pytest.approx(_rank_biserial(valores, etiqueta))


def test_uniformity_test():
    plano = uni.uniformity_test([100] * 12)
    assert plano["chi2"] == 0
    assert plano["cohen_w"] == 0
    assert plano["max_abs_dev_pp"] == pytest.approx(0)
    sesgado = uni.uniformity_test([200] + [100] * 11)
    esperado = stats.chisquare([200] + [100] * 11)
    assert sesgado["n"] == 1_300
    assert sesgado["dof"] == 11
    assert sesgado["chi2"] == pytest.approx(esperado.statistic)
    assert sesgado["cohen_w"] == pytest.approx(np.sqrt(esperado.statistic / 1_300))
    assert sesgado["max_share_pct"] == pytest.approx(100 * 200 / 1_300)
