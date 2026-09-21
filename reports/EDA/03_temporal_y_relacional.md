# Estructura temporal y relación entre tablas — Fase 1

Exportado desde `notebooks/01_eda.ipynb`, que es la fuente de estos resultados. Ejecución del 2026-09-18. Las cifras proceden de `reports/tables/` y las figuras de `reports/figures/`; regenerar el informe exige volver a ejecutar el cuaderno, no editar este archivo.

## Cobertura temporal

El historial va de 1977 a
2019, pero el volumen anterior a 2005 es residual:
22.112 facturas en 28 años (0,49 % del total), frente a una media de
296.975 al año desde 2005
(`temporal_invoices_per_year.csv`, `fig_temporal_invoices_per_year.png`). Ese tramo no
sostiene ningún estadístico anual, aunque alarga la ventana de los clientes antiguos.

Dentro del año, la facturación se reparte en tres picos separados por cuatro meses
(`fig_temporal_seasonality.png`), coherente con la cadencia cuatrimestral que ya indicaba
`months_number`. La diferencia entre el mes más cargado y el más flojo es de pocos puntos
porcentuales, de modo que no hay estacionalidad de consumo que corregir.

## La partición de Zindi no es temporal

Comparando el año de la última factura de cada cliente entre las dos particiones, las
cuotas coinciden hasta décimas de punto porcentual en todos los años
(`temporal_train_test_last_year.csv`). La separación entre entrenamiento y prueba es
aleatoria por cliente, no cronológica.

Esto fija dos cosas. La validación interna debe imitar esa separación, agrupando por cliente
sin corte temporal. Y el desempeño que se mida no responde a si el modelo detecta fraude
futuro, limitación que corresponde declarar de forma explícita en el manuscrito.

## Heterogeneidad del historial

| tramo | clientes | pct |
|---|---|---|
| 1 | 4.212 | 3,11 |
| 2-3 | 11.057 | 8,16 |
| 4-10 | 18.662 | 13,77 |
| 11-30 | 35.508 | 26,21 |
| 31-60 | 42.592 | 31,43 |
| >60 | 23.462 | 17,32 |

La mediana es de 30 facturas por cliente, con
4.212 clientes de una sola factura,
15.269 con tres o menos y un máximo de
439. Un resumen calculado sobre una factura y otro calculado
sobre cuatrocientas no son estadísticos comparables aunque ocupen la misma columna, lo que
convierte el tratamiento de los historiales cortos en una decisión de diseño y no en un
detalle de implementación.

El 45 % de los clientes
tiene contador eléctrico y de gas a la vez, así que los intervalos entre lecturas se
calculan dentro de cada tipo de contador; medidos así la mediana es de
121
días.

La fecha de alta es inconsistente con el historial en 8.748 clientes, cuya
primera factura antecede a su propia alta en una mediana de
75 días. Conviene medir la antigüedad desde la primera factura
observada en vez de desde `creation_date`.

## Comparabilidad entre particiones

La mayor diferencia de cuota entre entrenamiento y prueba en las categóricas es de
0,22 puntos porcentuales (`traintest_comparison.csv`,
`fig_traintest_ks.png`). Varios estadísticos de Kolmogorov-Smirnov superan su valor crítico,
lo previsible con muestras de este tamaño, con magnitudes en torno a 0,01. La única
asimetría con consecuencias es de categorías raras: la región 199, la tarifa 18 y tres
códigos de contador aparecen solo en entrenamiento, lo que obliga a que la codificación de
categóricas resuelva el caso de una categoría no vista.
