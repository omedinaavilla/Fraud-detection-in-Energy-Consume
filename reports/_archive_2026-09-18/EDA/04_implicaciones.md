# EDA Fase 1 — Implicaciones para el modelado

El análisis completo, con su código y sus salidas intermedias, está documentado en `notebooks/01_eda.ipynb`; este informe recoge en texto plano lo que allí se calcula e interpreta. Las cifras corresponden a la ejecución del 2026-09-18 sobre `data/interim/*.parquet`, las tablas limpias con las banderas de anomalía de `src/steg/data/clean.py`.

Las cuatro decisiones que la Fase 2 tiene que cerrar (sección 3 de `contextPrompt.md`),
con la evidencia de este análisis exploratorio y con sus alternativas. **Ninguna está
tomada**: se presentan con su riesgo y la elección corresponde al usuario. Las mismas
cuatro están en `reports/DECISIONS.md` marcadas `PROPUESTA`.

Cifras de referencia, todas en `reports/tables/`:

| Cifra | Valor | Fuente |
|---|---|---|
| clientes en train | 135.493 | `evaluation_metric_baselines.csv` |
| positivos | 7.566 (5.58 %) | `evaluation_metric_baselines.csv` |
| negativos por positivo | 16.9 | derivada |
| exactitud del clasificador trivial | 94.42 % | `evaluation_metric_baselines.csv` |
| línea base de PR-AUC | 5.58 % | `evaluation_metric_baselines.csv` |
| positivos por pliegue (validación agrupada, 5 folds) | 1486–1549 | `evaluation_fold_prevalence.csv` |
| mayor \|rank-biserial\| | 0.415 (`exp_n_counters`) | `bivariate_numeric_target.csv` |
| variables sobre el umbral 0,1 | 24 de 39 | `bivariate_numeric_target.csv` |
| mayor Cramér's V corregida | 0.0819 (`region`) | `bivariate_categorical_target.csv` |
| clientes con ≤ 3 facturas | 15.269 | `relational_invoices_per_client.csv` |

---

## PROPUESTA 1 — Métrica primaria

**Evidencia.** `evaluation_metric_baselines.csv`: predecir "no fraude" a todo el mundo
acierta el 94.42 % de las veces, así que la exactitud queda descartada.
La línea base de PR-AUC es 5.58 % y la de ROC-AUC es 50 % con
independencia de la prevalencia. `bivariate_numeric_target.csv` muestra que la variable
con más señal alcanza |rank-biserial| de 0.415, de modo que el
modelo producirá un ordenamiento con solapamiento fuerte entre clases y no una separación
limpia.

**Opción A — PR-AUC primaria, ROC-AUC secundaria.** Con 5.58 % de
positivos, la curva PR es sensible a la zona de alta precisión, que es donde se juega una
lista de inspección. *Riesgo*: depende de la prevalencia, así que no es comparable con los
números publicados del reto ni entre subgrupos con prevalencias distintas; reportarla por
región sin decir la prevalencia de cada una induce a error.

**Opción B — ROC-AUC primaria, PR-AUC secundaria.** Es la métrica de la competencia
(leaderboard público alrededor de 0,86), lo que da un ancla externa de dificultad y hace
el trabajo comparable con la literatura del dataset. *Riesgo*: promedia sobre todos los
umbrales, incluidos los que ninguna operación de campo usaría; se puede ganar ROC-AUC
mejorando el orden en la mitad inferior del ranking, que es irrelevante para inspeccionar.

**Opción C — una métrica @k primaria, ROC-AUC y PR-AUC secundarias.** Corresponde al uso
real declarado, una lista de inspecciones en campo. *Riesgo*: exige fijar k antes de ver
resultados, y k depende de una capacidad de inspección que el proyecto no conoce.

---

## PROPUESTA 2 — ¿Hay un problema de desbalance?

**Evidencia.** 7.566 positivos sobre 135.493 clientes y
16.9 negativos por positivo (`evaluation_metric_baselines.csv`). Con la
validación cruzada agrupada por cliente de 5 folds, cada pliegue de validación
contiene entre 1486 y 1549 positivos
(`evaluation_fold_prevalence.csv`, que recoge también el esquema estratificado).

El número absoluto importa más que el porcentaje. Un 5.58 % sobre 500
clientes sería escasez seria; sobre 135.493 deja unos 1.500 positivos por
pliegue, suficientes para estimar una proporción con error estándar relativo del
2.6 % incluso en el pliegue más pequeño de los dos esquemas, el de
1442 positivos. Hay desbalance, sin escasez de positivos.

**Opción A — ninguna técnica de balanceo; entrenar con la distribución real y ajustar el
umbral al final.** *Riesgo*: algunos algoritmos con regularización fuerte pueden converger
a soluciones que ignoran la clase minoritaria; hay que verificarlo en la Fase 4, no
asumirlo.

**Opción B — `class_weight='balanced'` o `scale_pos_weight`.** Cuesta una línea y no
altera los datos. *Riesgo*: descalibra las probabilidades, lo que obliga a recalibrar
antes del análisis de costo-beneficio de la Fase 7.

**Opción C — remuestreo (SMOTE, submuestreo del mayoritario).** *Riesgo*: la peor
relación coste/beneficio aquí. No hay escasez que resolver, el remuestreo tiene que ir
dentro del fold para no contaminar la validación, y SMOTE interpola sobre variables con
sesgo del orden de 500 (`univariate_numeric.csv`), de modo que genera clientes sintéticos
que no se parecen a ninguno real.

---

## PROPUESTA 3 — Punto de operación y evaluación "@k"

**Evidencia.** `evaluation_at_k_reference.csv`. Una lista de 5.000 clientes es el 3,7 % de
la base. Ordenada al azar contendría 279 fraudes (precisión
5.58 %); con orden perfecto contendría 5.000 (precisión 100 %, recall
66.1 %). Entre esos dos extremos cabe cualquier modelo, y esa
distancia es lo que mide si el trabajo sirve operativamente.

**Opción A — evaluar @k con varios k (500, 1.000, 2.000, 5.000) y reportar la curva, sin
fijar umbral de probabilidad.** Es honesto respecto de lo que no se sabe, la capacidad real
de inspección de STEG. *Riesgo*: no produce un único número citable, lo que complica
comparar experimentos y redactar el resumen.

**Opción B — fijar el umbral maximizando F1 sobre la validación cruzada.** Da un punto de
operación único y reproducible. *Riesgo*: F1 pondera precisión y recall por igual sin
razón operativa. Una visita fallida cuesta horas de cuadrilla; un fraude no detectado,
meses de energía robada. No son costes simétricos.

**Opción C — aplazar el umbral a la Fase 7 y derivarlo del análisis de costo-beneficio con
parámetros explícitos.** Lo más defendible metodológicamente. *Riesgo*: los parámetros de
coste no están disponibles y habría que asumirlos, con análisis de sensibilidad que
sostenga la conclusión.

Las tres son compatibles con evaluar @k. Lo separable es si además se fija un umbral
único, y cuándo.

---

## PROPUESTA 4 — Estratificación de los folds

**Evidencia.** `evaluation_fold_prevalence.csv` y `fig_eval_fold_prevalence.png`. Con
5 folds agrupados por `client_id` sin estratificar, la desviación estándar de la
prevalencia entre pliegues es de 0.0873 puntos porcentuales, frente a
0.1395 esperados por azar binomial con 27.098
clientes por fold. Con `StratifiedGroupKFold` baja a 0.1673, desde un punto
de partida que ya estaba en el ruido.

**Opción A — `GroupKFold` sin estratificar.** Ya implementado y probado en
`src/steg/data/split.py` y `tests/test_split_anti_leakage.py`. *Riesgo*: su asignación de
grupos a folds es determinista y no acepta `random_state`, así que no se puede repetir la
validación con otra semilla para estimar la variabilidad de la partición en sí.

**Opción B — `StratifiedGroupKFold` con `shuffle=True` y SEED=42.** Garantiza
prevalencia homogénea y permite repetir la CV con varias semillas. *Riesgo*: añade una
restricción que la evidencia no reclama y cambia el esquema respecto de lo ya probado, lo
que obliga a revisar el test anti-fuga.

Como cada cliente aparece una sola vez en `client_train`, lo que impide la fuga entre
folds es la agrupación por `client_id`, y eso lo cumplen ambos esquemas. La estratificación
compra homogeneidad cosmética antes que validez.
