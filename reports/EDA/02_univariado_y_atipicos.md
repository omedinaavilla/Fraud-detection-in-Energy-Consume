# Distribuciones y valores atípicos — Fase 1

Exportado desde `notebooks/01_eda.ipynb`, que es la fuente de estos resultados. Ejecución del 2026-09-18. Las cifras proceden de `reports/tables/` y las figuras de `reports/figures/`; regenerar el informe exige volver a ejecutar el cuaderno, no editar este archivo.

## Consumo e índices

Las cuatro columnas de consumo y los dos índices comparten forma: masa concentrada en
valores bajos y cola extrema. `consommation_level_1` tiene mediana
274 y máximo
999.910, con un
sesgo que llega a 526 en la columna más extrema del grupo. Cualquier
estadístico basado en la media está dominado por la cola, así que se reportan percentiles.
La figura `fig_univ_consumo_indices.png` muestra las seis distribuciones en escala
logarítmica, y las cifras están en `univariate_numeric_invoice.csv`.

## Categóricas

`counter_statue` reparte el 97,8 % de las filas en un solo código y `counter_coefficient`
vale 1 en el 99,97 %, de modo que ninguna de las dos aporta variación aprovechable tal
cual. `counter_type` reparte entre electricidad y gas. Las de alta cardinalidad se reportan
en tabla (`univariate_high_cardinality.csv`) en vez de en un gráfico de cuarenta barras:
`counter_code` tiene 42 valores y `region` 25, con una cola de categorías por debajo del
1 % que condiciona su codificación en la fase de variables.

## Atípicos: cuantificación y decisión

Entre el 3 % y el 12 % de las facturas caen fuera del bigote superior del criterio
intercuartílico según la columna (`outliers_iqr.csv`), con máximos tres órdenes de magnitud
por encima del percentil 99. La pregunta relevante no es cuántos son sino qué son.

Agrupando a los clientes por decil de consumo máximo, la tasa de fraude crece con el
consumo a lo largo de casi todo el recorrido (`outliers_target_rate.csv`,
`fig_outliers_target_rate.png`). Un recorte automático por percentil habría eliminado
justamente el tramo con más señal.

La propuesta para la fase de variables es transformar la escala y no truncar el rango: una
transformación logarítmica conserva el orden y hace manejable la cola, mientras que la
winsorización destruiría información útil. Los valores imposibles de `months_number` son un
caso distinto, porque ahí sí hay valores que no admiten lectura como período de
facturación; esos siguen tratados como anomalía marcada, no como atípico de una
distribución.
