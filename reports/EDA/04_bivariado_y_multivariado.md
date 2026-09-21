# Relación con la etiqueta — Fase 1

Exportado desde `notebooks/01_eda.ipynb`, que es la fuente de estos resultados. Ejecución del 2026-09-18. Las cifras proceden de `reports/tables/` y las figuras de `reports/figures/`; regenerar el informe exige volver a ejecutar el cuaderno, no editar este archivo.

Todo lo que sigue corre exclusivamente sobre la partición de entrenamiento. Los agregados
por cliente que aparecen aquí son instrumentos para medir cuánta señal hay y dónde está; no
son las variables del modelo, que se construyen en la fase siguiente con su propio
diccionario. La lista completa está en `exploratory_aggregate_dictionary.csv`.

## Variables del cliente

| variable | n_categories | cramers_v_bias_corrected | n |
|---|---|---|---|
| disrict | 4 | 0,05824 | 135.493 |
| client_catg | 3 | 0,05554 | 135.493 |
| region | 13 | 0,08186 | 135.493 |

La categoría de cliente 51 tiene una tasa de fraude del 16,87 % sobre
1.678 clientes, frente al 5,58 % global. Entre las regiones con al menos 100 clientes la tasa recorre de
0,57 % a 10,3 %; las 2 regiones por debajo de ese tamaño
quedan fuera de la comparación porque su intervalo es demasiado ancho para sostener
una conclusión. La Cramér's V corregida no supera
0,082 en ninguna de las tres variables: la asociación existe y explica poco
por sí sola (`bivariate_category_rates.csv`, `fig_biv_tasas_categoricas.png`,
`fig_biv_tasas_region.png`).

## Historial de facturación

| variable | median_neg | median_pos | rank_biserial | ci95_lo | ci95_hi |
|---|---|---|---|---|---|
| exp_n_counters | 2 | 2 | 0,4148 | 0,4034 | 0,4257 |
| exp_n_invoices | 29 | 41 | 0,3246 | 0,314 | 0,335 |
| exp_cons_total_max | 1.280 | 2.016 | 0,3227 | 0,311 | 0,334 |
| exp_span_days | 3.283 | 4.727 | 0,3067 | 0,2965 | 0,318 |
| exp_new_index_max | 18.218 | 28.463 | 0,3053 | 0,2947 | 0,3164 |
| exp_cons2_mean | 3,808 | 32,4 | 0,268 | 0,2566 | 0,2802 |
| exp_cons_total_std | 320,1 | 452,5 | 0,2646 | 0,2523 | 0,2768 |
| exp_n_counter_codes | 1 | 2 | 0,2636 | 0,2523 | 0,275 |
| exp_antiguedad_dias | 4.008 | 6.285 | 0,2599 | 0,2483 | 0,2716 |
| exp_cons3_mean | 0 | 1,26 | 0,2554 | 0,244 | 0,2673 |

20 de 34 agregados superan el umbral de
|rank-biserial| = 0,1 por debajo del cual el efecto se considera ruido de muestra grande.
El máximo es 0,415 para `exp_n_counters`, que equivale a un ROC-AUC de
70,7 % usando esa sola variable. Los primeros puestos los ocupan medidas
del tamaño del historial antes que del comportamiento de consumo, resultado que motiva la
sección siguiente.

Dos de las cinco banderas de anomalía parecen discriminar: al menos una factura duplicada
por clave lógica da un riesgo relativo de 2,16 (IC 95 %
[1,92, 2,42]) y al menos un retroceso de
índice 2,06 (`bivariate_flags_target.csv`). La sección siguiente
muestra que ese riesgo se confunde en buena parte con la longitud del historial.

## La longitud del historial confunde la relación

La tasa de fraude pasa del 0,642 % en el decil de clientes con menos facturas
al 9,756 % en el de más, un factor de 15,2
(`confounding_history_length.csv`, `fig_confusion_historial.png`). Como la etiqueta registra
fraude detectado y la detección exige haber sido inspeccionado, un historial largo significa
más ocasiones de inspección y no necesariamente más propensión a defraudar.

El análisis dentro de estratos de longitud comparable separa los dos efectos
(`confounding_conditional_effects.csv`, `fig_confusion_condicional.png`). `exp_new_index_max`
pierde casi todo su efecto al condicionar, así que medía acumulación de lecturas.
`exp_n_counters` lo conserva entre 0,22 y 0,40 en todos los quintiles, de modo que el número
de contadores dice algo propio. El consumo máximo queda en posición intermedia, con un
efecto que se reduce a la mitad sin desaparecer.

La misma comprobación recorta el riesgo doble de las banderas
(`confounding_flags.csv`). Expresadas como proporción de las facturas del cliente, la
duplicación por clave lógica da 0,019 de rank-biserial y el
retroceso de índice 0,015, frente al umbral de 0,1. La marca
binaria sigue elevando el riesgo dentro de cada estrato, de 2,31 en el
quintil de historial más corto a 1,26 en el más largo: parte de lo que
mide es la oportunidad de acumular una anomalía, no la anomalía misma.

Esto obliga a tres cautelas en lo que sigue: mirar con sospecha cualquier variable de
volumen acumulado, distinguir señal de exposición al interpretar importancias, y reportar el
desempeño desagregado por longitud de historial como control obligatorio.

`old_index` y `new_index` correlacionan a
0,99 en Spearman
(`multivariate_spearman_consumo.csv`), así que usar ambos como variables independientes sería
redundante. El cruce entre distrito y categoría muestra que el exceso de riesgo de la
categoría 51 se mantiene en los cuatro distritos (`fig_multi_disrict_catg.png`), con lo que
no es un artefacto geográfico.
