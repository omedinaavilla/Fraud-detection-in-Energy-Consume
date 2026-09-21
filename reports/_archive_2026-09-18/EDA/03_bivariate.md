# EDA Fase 1 — Bivariado y multivariado

El análisis completo, con su código y sus salidas intermedias, está documentado en `notebooks/01_eda.ipynb`; este informe recoge en texto plano lo que allí se calcula e interpreta. Las cifras corresponden a la ejecución del 2026-09-18 sobre `data/interim/*.parquet`, las tablas limpias con las banderas de anomalía de `src/steg/data/clean.py`.

**Regla de higiene.** Todo este informe sale de `client_train` e `invoice_train` o de
agregados derivados de ellas. `client_test` e `invoice_test` no se tocan: mirar la
etiqueta contra test es imposible porque no existe, y mirar variables explicativas de
test contra la etiqueta de train sería fuga.

**Regla de reporte.** Ningún p-valor aparece sin su tamaño de efecto. Con
135.493 clientes y 7.566 positivos, p < 0,001 no es una noticia.
El umbral de "vale la pena reportar" se fija en
|rank-biserial| ≥ 0.1.

## 1. El agregado exploratorio

Las variables numéricas de este informe salen de una tabla a nivel cliente construida
desde `invoice_train`, documentada en
`reports/tables/bivariate_exploratory_feature_dictionary.csv`
(40 variables con nombre, unidad y definición).

**No es el conjunto de variables de modelado.** Se calcula una sola vez sobre todo
`invoice_train`, fuera de cualquier fold; usa el historial completo sin decidir ventana
temporal; e incluye a propósito variables que aquí se descartan. El conjunto oficial se
construye en la Fase 3, dentro de un `Pipeline` por fold, y el prefijo `exp_` marca la
diferencia en cada columna.

## 2. Categóricas del cliente

| variable | n_categories | cramers_v_bias_corrected | chi2 | dof | p_value | n | min_expected | pct_cells_expected_lt5 |
|---|---|---|---|---|---|---|---|---|
| region | 13 | 0.08186 | 920 | 12 | 2.869e-189 | 135493 | 213.8 | 0 |
| counter_type_mix | 3 | 0.06615 | 595 | 2 | 6.367e-130 | 135493 | 37.86 | 0 |
| disrict | 4 | 0.05824 | 462.6 | 3 | 6.108e-100 | 135493 | 1619 | 0 |
| client_catg | 3 | 0.05554 | 419.9 | 2 | 6.507e-92 | 135493 | 93.7 | 0 |
| tarif_type_mode | 13 | 0.03741 | 201.6 | 12 | 1.492e-36 | 135493 | 0.05584 | 30.77 |

Tabla: `reports/tables/bivariate_categorical_target.csv`. Tasas por categoría con
intervalo de Wilson en `reports/tables/bivariate_category_rates.csv`. Figuras:
`fig_biv_target_rate_categorical.png` y `fig_biv_target_rate_region.png`.

La asociación más fuerte es `region` con V corregida de
0.0819. Ninguna categórica separa por sí
sola: todas quedan por debajo de 0,1, en el terreno de lo detectable con 135.000 filas e
inservible para decidir a quién inspeccionar.

Lo que sí tiene lectura operativa son los extremos. Entre las regiones con n suficiente,
la tasa va de 3.30 % a 10.30 %
frente a una tasa global de 5.58 %, con *lift* de hasta
1.84. Un modelo va a explotar esa diferencia, y por eso
el análisis por subgrupo de la Fase 6 tiene que reportar desempeño desagregado por región:
si el modelo concentra las inspecciones en dos regiones, el hallazgo es sobre a quién se le
manda el inspector.

## 3. Banderas de anomalía contra la etiqueta

| variable | n_flagged | rate_flagged_pct | flagged_wilson_lo_pct | flagged_wilson_hi_pct | rate_not_flagged_pct | risk_ratio | rr_ci95_lo | rr_ci95_hi |
|---|---|---|---|---|---|---|---|---|
| tiene al menos un logical_duplicate | 2191 | 11.82 | 10.54 | 13.24 | 5.481 | 2.156 | 1.919 | 2.423 |
| tiene al menos un index_regression | 1816 | 11.34 | 9.966 | 12.88 | 5.506 | 2.06 | 1.808 | 2.348 |
| tiene contador ELEC y GAZ | 61376 | 7.236 | 7.033 | 7.443 | 4.216 | 1.716 | 1.641 | 1.794 |
| tiene al menos un months_number_invalid | 14944 | 6.411 | 6.029 | 6.815 | 5.482 | 1.169 | 1.095 | 1.249 |
| primera factura anterior al alta | 8748 | 5.304 | 4.854 | 5.794 | 5.603 | 0.9466 | 0.8639 | 1.037 |
| tres facturas o menos | 15269 | 0.6353 | 0.5211 | 0.7743 | 6.213 | 0.1023 | 0.0838 | 0.1248 |
| tiene al menos un counter_statue_invalid | 6 | 0 | 0 | 39.03 | 5.584 | — | — | — |
| tiene al menos un reading_remarque_invalid | 5 | 0 | 0 | 43.45 | 5.584 | — | — | — |

Tabla: `reports/tables/bivariate_flags_target.csv`. Figura:
`reports/figures/fig_biv_flags_target.png`.

El protocolo pide tratar estas anomalías como candidatas a variable y no solo como
defectos de captura. El resultado es mixto y conviene leerlo con el `n` delante.

Las banderas con mayor riesgo relativo son `counter_statue_invalid` y
`reading_remarque_invalid`, que afectan a 6 y 5 clientes. Un riesgo relativo calculado
sobre esa base arrastra un intervalo que abarca casi un orden de magnitud, y
`01_univariate.md` ya mostró que ninguna de las dos existe en test. Quedan descartadas como
candidatas, porque no serían reproducibles fuera de este train.

`index_regression` y `months_number_invalid` sí tienen n suficiente y aparecen en las dos
particiones. Son las candidatas serias del grupo, y `index_regression` tiene además una
historia física detrás: un contador cuyo índice retrocede es exactamente lo que deja una
manipulación del medidor.

## 4. Numéricas: Mann-Whitney con rank-biserial e intervalo

| variable | n | median_neg | median_pos | rank_biserial | ci95_lo | ci95_hi | above_threshold | p_value |
|---|---|---|---|---|---|---|---|---|
| exp_n_counters | 135493 | 2 | 2 | 0.4148 | 0.4037 | 0.4246 | True | 0 |
| exp_n_invoices | 135493 | 29 | 41 | 0.3246 | 0.3149 | 0.3346 | True | 0 |
| exp_cons_total_max | 135493 | 1280 | 2016 | 0.3227 | 0.311 | 0.334 | True | 0 |
| exp_span_years | 135493 | 8.988 | 12.94 | 0.3067 | 0.2959 | 0.318 | True | 0 |
| exp_cons_l2_mean | 135493 | 3.808 | 32.4 | 0.268 | 0.2567 | 0.2802 | True | 0 |
| exp_cons_total_std | 131281 | 320.1 | 452.5 | 0.2646 | 0.2521 | 0.2772 | True | 0 |
| exp_n_counter_codes | 135493 | 1 | 2 | 0.2636 | 0.2525 | 0.2751 | True | 0 |
| exp_client_age_years | 135493 | 10.97 | 17.21 | 0.2599 | 0.2469 | 0.2718 | True | 0 |
| exp_cons_l3_mean | 135493 | 0 | 1.26 | 0.2554 | 0.2442 | 0.2673 | True | 0 |
| exp_rate_above_level_1 | 135493 | 0.02857 | 0.1111 | 0.2423 | 0.2317 | 0.2534 | True | 1.566e-299 |
| exp_rate_rr_8 | 135493 | 0.1429 | 0.1944 | 0.2111 | 0.2007 | 0.2216 | True | 3.196e-215 |
| exp_cons_l1_std | 131281 | 276.9 | 331.5 | 0.2013 | 0.1902 | 0.2133 | True | 1.288e-189 |

Tabla completa: `reports/tables/bivariate_numeric_target.csv`. Figuras:
`fig_biv_effect_sizes.png` y `fig_biv_boxplots_top.png`. Intervalo por bootstrap de
400 remuestreos **de clientes**, no de facturas: cada fila del agregado es un
cliente, y remuestrear facturas devolvería intervalos artificialmente estrechos, por
tratar como independientes las treinta observaciones de una misma persona.

35 de 39 variables salen
significativas al 0,1 %, y solo 24 superan
|rank-biserial| ≥ 0.1. Ese contraste es el argumento entero: con
7.566 positivos la significancia no informa, el tamaño de efecto sí.

La variable con más señal es `exp_n_counters` con rank-biserial de
0.415 (IC 95 %
[0.404, 0.425]), mediana
2.0 en no fraude contra
2.0 en fraude.

Las que encabezan la lista son de cantidad de historial y de cadencia de facturación, no
de nivel de consumo. Resulta contraintuitivo frente a la literatura de fraude eléctrico,
donde el consumo anómalo es la señal canónica.

**Limitación que el EDA no puede resolver.** La etiqueta no trae fecha de fraude. Si a un
cliente detectado se le interviene el suministro o se le cambia el régimen de lectura, su
historial posterior queda alterado por la propia detección, y una variable como "número
de facturas" podría estar recogiendo la consecuencia administrativa del fraude en vez de
su causa. La auditoría de fuga de la Fase 8 tiene que mirar esto específicamente, y la
ventana temporal que se decida en la Fase 3 es la herramienta para acotarlo.

## 5. Información mutua

| variable | mutual_info | null_mean | null_max | excess_over_null | above_null_max |
|---|---|---|---|---|---|
| exp_n_counters | 0.01945 | 0.003363 | 0.005022 | 0.01608 | True |
| exp_span_years | 0.01403 | 0.000384 | 0.001053 | 0.01364 | True |
| exp_n_invoices | 0.012 | 0.000726 | 0.002006 | 0.01127 | True |
| exp_cons_total_max | 0.01011 | 6.7e-05 | 0.000334 | 0.01005 | True |
| exp_rate_rr_6 | 0.01036 | 0.000482 | 0.002076 | 0.009877 | True |
| exp_last_invoice_year | 0.0133 | 0.00384 | 0.004615 | 0.009456 | True |
| exp_cons_total_std | 0.009097 | 0.000244 | 0.000971 | 0.008853 | True |
| exp_rate_zero_consumption | 0.008823 | 0.000191 | 0.000656 | 0.008633 | True |
| exp_rate_above_level_1 | 0.009157 | 0.000909 | 0.00184 | 0.008247 | True |
| exp_cons_l3_mean | 0.008363 | 0.000417 | 0.001471 | 0.007946 | True |
| exp_client_age_years | 0.007819 | 0.000203 | 0.000867 | 0.007616 | True |
| exp_rate_rr_9 | 0.008336 | 0.000817 | 0.001993 | 0.007519 | True |

Tabla: `reports/tables/bivariate_mutual_information.csv`. Figura:
`reports/figures/fig_biv_mutual_information.png`. Calculada sobre una submuestra de
40.000 clientes con SEED=42, contra un nulo de
5 permutaciones de la etiqueta.

32 de 39 variables superan el máximo
del nulo. El orden coincide a grandes rasgos con el del rank-biserial, lo que significa
que no hay relaciones fuertemente no monótonas escondidas: un modelo lineal regularizado
no queda estructuralmente ciego frente a un árbol, y la comparación de la Fase 4 entre
regresión logística y LightGBM medirá capacidad de combinar variables, no de representar
una forma funcional que la logística no puede.

## 6. Correlación entre explicativas

| var_a | var_b | spearman |
|---|---|---|
| exp_cons_l2_mean | exp_rate_above_level_1 | 0.9783 |
| exp_cons_total_mean | exp_index_delta_mean | 0.9539 |
| exp_cons_total_std | exp_cons_total_max | 0.9447 |
| exp_n_tarif_types | exp_n_counter_codes | 0.9389 |
| exp_cons_total_mean | exp_cons_l1_mean | 0.9358 |
| exp_n_tarif_types | exp_n_counter_types | 0.9333 |
| exp_prop_gaz | exp_n_counter_types | 0.9259 |
| exp_n_counter_codes | exp_n_counter_types | 0.9167 |
| exp_rate_counter_statue_invalid | exp_rate_reading_remarque_invalid | 0.9129 |

Tablas: `reports/tables/bivariate_spearman_invoice.csv`,
`bivariate_spearman_exploratory.csv` y `bivariate_redundant_pairs.csv`. Figura:
`reports/figures/fig_biv_spearman_invoice.png`.

Los cuatro niveles de consumo y los dos índices aportan en buena medida la misma
información: el contrato de datos ya advertía que `sum(levels)` reproduce
`new_index − old_index` en el 99,58 % de las filas. De cada par con |rho| ≥ 0,9 la Fase 3
tiene que justificar por qué entran los dos, o entra uno.

## 7. Multivariado

Figuras: `fig_multi_region_disrict.png` y `fig_multi_region_countertype.png`. Tablas:
`multivariate_region_x_disrict.csv` y `multivariate_region_x_countertype.csv`. Las celdas
con menos de 100 clientes se dejan en blanco porque su tasa no es leíble.

El patrón por región se mantiene dentro de cada distrito y dentro de cada perfil de
contador. No aparece ninguna interacción que invierta el signo, que es lo que justificaría
construir una variable cruzada explícita. Tener contador de gas además del eléctrico sí va
asociado a una tasa distinta, y de forma consistente entre regiones.
