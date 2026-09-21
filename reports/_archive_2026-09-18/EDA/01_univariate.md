# EDA Fase 1 — Univariado

El análisis completo, con su código y sus salidas intermedias, está documentado en `notebooks/01_eda.ipynb`; este informe recoge en texto plano lo que allí se calcula e interpreta. Las cifras corresponden a la ejecución del 2026-09-18 sobre `data/interim/*.parquet`, las tablas limpias con las banderas de anomalía de `src/steg/data/clean.py`.

Ninguna cifra de este informe mira `target`: la relación con la etiqueta se examina en
`03_bivariate.md`, y allí solo sobre la partición de entrenamiento.

## 1. Variables de consumo: la cola manda

| column | pct_zero | p25 | p50 | p75 | p99 | max | mean | std | skew | pct_outliers_high_iqr |
|---|---|---|---|---|---|---|---|---|---|---|
| consommation_level_1 | 10.44 | 79 | 274 | 600 | 2192 | 9.999e+05 | 411 | 757.3 | 526 | 2.783 |
| consommation_level_2 | 85.24 | 0 | 0 | 0 | 2069 | 9.991e+05 | 109.3 | 1220 | 338.9 | 14.76 |
| consommation_level_3 | 95.9 | 0 | 0 | 0 | 800 | 6.449e+04 | 20.31 | 157.4 | 75.31 | 4.096 |
| consommation_level_4 | 97.92 | 0 | 0 | 0 | 1222 | 5.479e+05 | 52.93 | 875.5 | 118.6 | 2.076 |
| old_index | 6.431 | 1791 | 7690 | 2.166e+04 | 1.51e+05 | 2.8e+06 | 1.777e+04 | 4.037e+04 | 11.09 | 6 |
| new_index | 4.377 | 2056 | 8192 | 2.234e+04 | 1.557e+05 | 2.871e+06 | 1.835e+04 | 4.095e+04 | 10.99 | 5.963 |
| months_number | 0 | 4 | 4 | 4 | 12 | 6.366e+05 | 44.83 | 3128 | 105.3 | 9.043 |
| counter_coefficient | 0.001 | 1 | 1 | 1 | 1 | 50 | 1.003 | 0.3083 | 116.8 | 0.0358 |
| consommation_total (derivada) | 10.44 | 80 | 309 | 657 | 5046 | 9.999e+05 | 593.5 | 1775 | 166.5 | 7.378 |

Tabla completa (train y test): `reports/tables/univariate_numeric.csv`. Figura:
`reports/figures/fig_univ_consumption_log_hist.png`.

`consommation_level_1` tiene mediana 274 y máximo 999910, es decir
3649 veces la mediana, con sesgo 526 y curtosis
678682. Ninguna prueba que asuma normalidad tiene sentido sobre una
columna así, y de ahí que el bivariado recurra a Mann-Whitney.

Los niveles 2 a 4 están vacíos en el 85.2 %,
95.9 % y
97.9 % de las facturas.
Ninguno de los tres se comporta como una medición continua comparable con la del primer
nivel: funcionan como indicadores de que la factura superó un escalón tarifario, y así
habría que construirlos en la Fase 3.

## 2. months_number: el faltante que no se declara como faltante

`months_number` debería vivir en [1, 12]. Su máximo en train es 636624, y
24.043 facturas
(0.54 %) caen fuera del rango,
repartidas entre 14.944
clientes. En test la tasa es 0.54 %.

Que las dos tasas coincidan con dos decimales descarta un artefacto de la partición: el
defecto está en el sistema de facturación y atraviesa toda la base. Figura:
`reports/figures/fig_univ_months_number.png`.

## 3. Banderas de anomalía: tasa base

| table | flag | n_flagged | pct_flagged | wilson_lo_pct | wilson_hi_pct | n_clients_affected |
|---|---|---|---|---|---|---|
| invoice_train | logical_duplicate | 29278 | 0.654 | 0.6466 | 0.6615 | 2191 |
| invoice_train | counter_statue_invalid | 47 | 0.001 | 0.0008 | 0.0014 | 6 |
| invoice_train | reading_remarque_invalid | 34 | 0.0008 | 0.0005 | 0.0011 | 5 |
| invoice_train | months_number_invalid | 24043 | 0.5371 | 0.5303 | 0.5439 | 14944 |
| invoice_train | index_regression | 2264 | 0.0506 | 0.0485 | 0.0527 | 1816 |
| invoice_test | logical_duplicate | 14136 | 0.7288 | 0.7169 | 0.7408 | 964 |
| invoice_test | counter_statue_invalid | 0 | 0 | 0 | 0.0002 | 0 |
| invoice_test | reading_remarque_invalid | 0 | 0 | 0 | 0.0002 | 0 |
| invoice_test | months_number_invalid | 10401 | 0.5362 | 0.526 | 0.5466 | 6296 |
| invoice_test | index_regression | 1054 | 0.0543 | 0.0512 | 0.0577 | 811 |

Tabla: `reports/tables/univariate_anomaly_rates.csv`. Figura:
`reports/figures/fig_univ_anomaly_rates.png`.

`counter_statue_invalid` (47 filas,
6 clientes) y
`reading_remarque_invalid` (34 filas,
5 clientes) tienen tasa
exactamente cero en test. Bajo una partición aleatoria por cliente en proporción 70/30,
esas cifras en train deberían venir acompañadas de unas veinte filas en test. Que no
aparezca ninguna apunta a un lote de registros de captura defectuosa que quedó entero de un
lado. La consecuencia es directa: aunque `03_bivariate.md` les encuentre asociación con
`target`, quedan fuera de las candidatas a variable, porque no serían reproducibles fuera
de este train.

## 4. Categóricas

Frecuencias completas en `reports/tables/univariate_categorical.csv`, con las categorías
raras agrupadas cuando la columna supera 12 valores. Figuras:
`fig_univ_categorical_freq.png` y `fig_univ_region_freq.png`.

- `client_catg`: 3 valores, y el 11 cubre el 97,05 % de los clientes. Tan concentrada que
  apenas funciona como variable.
- `disrict`: 4 valores, el más frecuente con el 29,78 %.
- `region`: 25 valores; las 12 más
  frecuentes cubren el 86.3 % de los clientes. Esa cola larga es el caso
  que tendrá que resolver la decisión sobre codificación de categóricas de alta
  cardinalidad (Fase 3).
- `counter_type`: 2 valores, ELEC en el 68,79 % de las facturas.
- `counter_coefficient`: vale 1 en el 99,97 % de las filas.

## 5. Train vs. test

La comparación no mira `target`, que no existe en test, y por eso puede tocar las
cuatro tablas. Con 135.493 y 58.069 clientes el p-valor rechaza por diferencias irrelevantes, así
que lo que se lee es el tamaño del efecto contra su referencia. `max_abs_share_diff_pp`
traduce Cramér's V a puntos porcentuales, tomando la mayor diferencia de cuota entre las
categorías de esa columna.

| level | column | effect_size_name | effect_size | reference_name | reference | max_abs_share_diff_pp | p_value | n_train | n_test |
|---|---|---|---|---|---|---|---|---|---|
| factura | counter_code | Cramér's V (corregida) | 0.05607 | mínima celda esperada | 1784 | 0.3075 | 0 | 4476738 | 1939722 |
| factura | new_index | D | 0.009095 | D crítico 5 % | 0.004301 | — | 1.298e-07 | 4476738 | 1939722 |
| factura | old_index | D | 0.008985 | D crítico 5 % | 0.004301 | — | 1.933e-07 | 4476738 | 1939722 |
| factura | tarif_type | Cramér's V (corregida) | 0.008659 | mínima celda esperada | 22.07 | 0.123 | 6.615e-98 | 4476738 | 1939722 |
| cliente (agregado) | span_years | D | 0.006545 | D crítico 5 % | 0.006746 | — | 0.06118 | 135493 | 58069 |
| cliente (agregado) | n_invoices | D | 0.005314 | D crítico 5 % | 0.006746 | — | 0.2004 | 135493 | 58069 |
| cliente (agregado) | median_gap_days_within_stream | D | 0.004824 | D crítico 5 % | 0.006872 | — | 0.3208 | 130422 | 55967 |
| cliente | creation_date (año) | D | 0.004232 | D crítico 5 % | 0.006746 | — | 0.4593 | 135493 | 58069 |
| factura | logical_duplicate | Cramér's V (corregida) | 0.00417 | mínima celda esperada | 1.312e+04 | 0.0748 | 2.698e-26 | 4476738 | 1939722 |
| cliente (agregado) | invoices_per_year | D | 0.004028 | D crítico 5 % | 0.006877 | — | 0.5482 | 130246 | 55895 |
| factura | invoice_date (año) | D | 0.00371 | D crítico 5 % | 0.004301 | — | 0.1271 | 4476738 | 1939722 |
| cliente (agregado) | max_gap_days | D | 0.003685 | D crítico 5 % | 0.006851 | — | 0.6569 | 131281 | 56309 |
| factura | months_number | D | 0.00303 | D crítico 5 % | 0.004301 | — | 0.3169 | 4476738 | 1939722 |
| factura | consommation_level_1 | D | 0.002485 | D crítico 5 % | 0.004301 | — | 0.5665 | 4476738 | 1939722 |
| factura | consommation_level_2 | D | 0.001765 | D crítico 5 % | 0.004301 | — | 0.9138 | 4476738 | 1939722 |
| factura | counter_statue_invalid | Cramér's V (corregida) | 0.001737 | mínima celda esperada | 14.21 | 0.001 | 6.4e-06 | 4476738 | 1939722 |
| factura | counter_statue | Cramér's V (corregida) | 0.001684 | mínima celda esperada | 0.3 | 0.0158 | 0.002118 | 4476738 | 1939722 |
| cliente | client_catg | Cramér's V (corregida) | 0.001674 | mínima celda esperada | 716.4 | 0.1021 | 0.2805 | 135493 | 58069 |
| factura | reading_remarque | Cramér's V (corregida) | 0.00162 | mínima celda esperada | 0.3 | 0.1123 | 0.001219 | 4476738 | 1939722 |
| factura | reading_remarque_invalid | Cramér's V (corregida) | 0.001463 | mínima celda esperada | 10.28 | 0.0008 | 0.0001239 | 4476738 | 1939722 |
| factura | consommation_level_3 | D | 0.000915 | D crítico 5 % | 0.004301 | — | 1 | 4476738 | 1939722 |
| factura | counter_type | Cramér's V (corregida) | 0.000668 | mínima celda esperada | 6.05e+05 | 0.0783 | 0.04935 | 4476738 | 1939722 |
| factura | index_regression | Cramér's V (corregida) | 0.00065 | mínima celda esperada | 1003 | 0.0038 | 0.05402 | 4476738 | 1939722 |
| factura | consommation_level_4 | D | 0.000485 | D crítico 5 % | 0.004301 | — | 1 | 4476738 | 1939722 |
| factura | counter_coefficient | D | 0.00017 | D crítico 5 % | 0.004301 | — | 1 | 4476738 | 1939722 |
| factura | months_number_invalid | Cramér's V (corregida) | 0 | mínima celda esperada | 1.041e+04 | 0.0009 | 0.8918 | 4476738 | 1939722 |
| cliente | region | Cramér's V (corregida) | 0 | mínima celda esperada | 1649 | 0.1826 | 0.6577 | 135493 | 58069 |
| cliente | disrict | Cramér's V (corregida) | 0 | mínima celda esperada | 1.238e+04 | 0.2189 | 0.7287 | 135493 | 58069 |

Tabla: `reports/tables/train_test_drift.csv`. Figura:
`reports/figures/fig_traintest_ks.png`.

2 de 15 columnas numéricas
superan su D crítico al 5 %; el mayor es `new_index` con
D = 0.0091 frente a un crítico de
0.0043. En categóricas el mayor efecto es
`counter_code` con V corregida de 0.0561, que se
traduce en 0.31 puntos porcentuales de diferencia
de cuota: detectable sobre 6,4 millones de filas e irrelevante para cualquier decisión.

La partición de Zindi se comporta, por tanto, como un muestreo aleatorio por cliente. Su
única excepción estructural es la de la sección 3, que ninguna de estas pruebas capta.
