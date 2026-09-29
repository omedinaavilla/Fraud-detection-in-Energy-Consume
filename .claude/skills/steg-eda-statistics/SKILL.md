---
name: steg-eda-statistics
description: Cataloga qué herramienta estadística usar para cada par de tipos de variable en el proyecto STEG — asociación categórica-categórica (Cramér's V, chi-cuadrado con su advertencia de tamaño muestral), numérica-binaria (Mann-Whitney, tamaño de efecto, punto biserial), información mutua, correlaciones robustas, detección de atípicos, y pruebas de diferencia de distribución entre train y test — y cuándo un p-valor no significa nada por el tamaño de la muestra. Úsala al elegir qué prueba aplicar en el análisis bivariado o multivariado, o al interpretar un resultado estadístico antes de escribirlo en un reporte.
---

# Estadística para el EDA — STEG

Con 135.493 clientes en train, casi cualquier prueba de hipótesis da p < 0,001 aunque el
efecto sea trivial. El tamaño muestral aquí es una razón para reportar **tamaño de
efecto e intervalo**, no el p-valor solo. Un p-valor sin tamaño de efecto no se escribe
en ningún reporte de este proyecto.

## Categórica × categórica

Ejemplos en este dataset: `disrict` × `client_catg`, `region` × `counter_type`.

- **Cramér's V** como tamaño de efecto (0 = sin asociación, 1 = asociación perfecta).
  Reportarlo siempre junto al chi-cuadrado, nunca solo.
- **Chi-cuadrado de independencia**: válido solo si ninguna celda esperada cae por
  debajo de 5. Con `region` (25 categorías) cruzada con otra variable de alta
  cardinalidad, verificar las celdas antes de confiar en el estadístico; si fallan,
  agrupar categorías raras primero o usar el test exacto de Fisher extendido si el
  software lo soporta.

## Numérica × binaria (la relación central: cualquier variable de consumo vs. `target`)

- **Mann-Whitney U**, no t-test: los consumos tienen colas extremas y la normalidad no
  se sostiene (`consommation_level_1` llega a 999.910). Mann-Whitney no asume
  normalidad y es robusto a esos atípicos.
- **Tamaño de efecto**: `rank-biserial correlation` (se deriva directamente del
  estadístico U) o `Cliff's delta`. Reportarlo con intervalo por bootstrap (ver
  `steg-validation-protocol` para el procedimiento de remuestreo agrupado por
  cliente — el bootstrap aquí también debe respetar la unidad cliente).
- **Punto biserial** como complemento si se quiere una medida tipo correlación, con la
  advertencia de que asume relación lineal con el rango, que puede no sostenerse en
  variables tan sesgadas.
- Con 7.566 positivos, la prueba tiene potencia de sobra: un Mann-Whitney
  significativo con tamaño de efecto minúsculo no es un hallazgo, es ruido de muestra
  grande. El umbral de "vale la pena reportar" lo da el tamaño de efecto, se define en
  este catálogo como |rank-biserial| > 0,1 salvo que el eda-analyst justifique otro
  corte con evidencia.

## Información mutua

Útil para relaciones no monótonas que Mann-Whitney o Cramér's V no capturan (p. ej.
`target` con una variable derivada que combina meses sin factura y nivel de consumo).
Usar `sklearn.feature_selection.mutual_info_classif` con la semilla del proyecto
(`steg.config.SEED`). La información mutua no da significancia por sí sola: acompañarla
de permutación (recalcular con `target` barajado) para saber si el valor observado
podría salir del azar.

## Correlaciones entre numéricas

- **Spearman**, no Pearson, por defecto: las variables de consumo no son lineales entre
  sí ni normales. Pearson solo si un scatter confirma relación lineal.
- Matriz de correlación entre `consommation_level_1..4`, `old_index`, `new_index`:
  esperable alta colinealidad porque `sum(levels) ≈ new_index - old_index` en el 99,6 %
  de las filas (ver `steg-data-contract`). Repórtala explícitamente antes de decidir
  qué variables derivadas construir en Fase 3 — no tiene sentido usar los cuatro
  niveles y los dos índices como si fueran independientes sin decir que no lo son.

## Detección de atípicos

- **IQR robusto** (basado en percentiles 25/75) como primer filtro, no z-score: la
  media y desviación están dominadas por la cola en columnas como
  `consommation_level_1`.
- Todo atípico se reporta con su tasa de `target` asociada antes de decidir si se
  recorta, se transforma o se deja: un consumo extremo puede ser exactamente la señal
  de fraude que se busca, no ruido a limpiar.

## Diferencia de distribución train vs. test

Antes de construir cualquier variable, verificar que su distribución no difiera
sistemáticamente entre `client_train`/`invoice_train` y `client_test`/`invoice_test`
(más allá de lo esperable por muestreo aleatorio):

- **Kolmogorov-Smirnov de dos muestras** para numéricas.
- **Chi-cuadrado** o **Cramér's V** para categóricas (con la misma advertencia de
  celdas esperadas).
- Si una variable difiere fuerte entre train y test, documentarlo: puede indicar que
  la partición de Zindi no es tan aleatoria como sugiere la evidencia temporal (ver
  `steg-data-contract`), o que la variable no es estable para producción.

## Regla general de reporte

Ninguna cifra estadística se escribe en `reports/EDA/` sin: (1) el tamaño de efecto,
(2) el tamaño de muestra sobre el que se calculó, (3) si aplica, el intervalo. El
p-valor solo se incluye como información adicional, nunca como el único criterio de
"esto importa".
