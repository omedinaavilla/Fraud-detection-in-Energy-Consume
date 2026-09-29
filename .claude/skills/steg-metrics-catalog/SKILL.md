---
name: steg-metrics-catalog
description: Cataloga métricas de clasificación con sus supuestos, qué pregunta responde cada una, cuándo engaña, y criterios para elegir la métrica primaria del proyecto STEG en función de lo que muestre el EDA y del uso operativo previsto (una lista de inspecciones en campo). Incluye métricas de priorización y costo-beneficio configurables. Úsala al discutir la decisión de métrica primaria de la Fase 2, o al interpretar cualquier resultado de modelo antes de reportarlo.
---

# Catálogo de métricas — STEG

Ninguna métrica de esta lista es la métrica primaria del proyecto por defecto. La
decisión se toma al final de la Fase 2, con evidencia del EDA y en función del uso
operativo: STEG no clasifica clientes en abstracto, prioriza una lista de inspecciones
de campo con recursos limitados. Referencia externa: el leaderboard público de Zindi
usa AUC y ronda 0,86 — eso mide la dificultad del problema para ese objetivo (ranking
global), no dicta la métrica de este proyecto.

## Métricas de ranking / discriminación global

| Métrica | Qué responde | Cuándo engaña |
|---|---|---|
| **ROC-AUC** | Qué tan bien el modelo separa fraude de no-fraude a través de todos los umbrales. | Con 5,58 % de positivos, ROC-AUC puede verse alto aunque la precisión en la región de interés (los primeros k) sea mala — la curva ROC promedia sobre umbrales que en la práctica nunca se usarían. |
| **PR-AUC (average precision)** | Igual, pero sensible al desbalance: más informativa que ROC-AUC cuando la clase positiva es minoritaria. | Compararla entre experimentos con distinta tasa base de positivos (p. ej. un subconjunto filtrado) no es válido sin ajustar por la tasa base. |
| **Brier score / calibración** | Si las probabilidades predichas corresponden a frecuencias reales. | Un modelo puede discriminar bien (AUC alto) y estar mal calibrado; si el uso operativo depende de una probabilidad absoluta (no solo del ranking), la calibración importa tanto como la discriminación. |

## Métricas de punto de operación fijo

| Métrica | Qué responde | Cuándo engaña |
|---|---|---|
| **Precisión, recall, F1 a un umbral** | Desempeño en un punto de corte específico. | Sin justificar el umbral con el uso operativo (¿cuántas inspecciones puede hacer STEG al mes?), el número es arbitrario y no comparable entre experimentos que usan umbrales distintos. |
| **Matriz de confusión** | Distribución completa de aciertos y errores en un punto. | Se reporta siempre junto a la métrica agregada, nunca como sustituto — un F1 igual puede esconder matrices muy distintas. |

## Métricas orientadas a priorización ("@k")

Relevantes si la Fase 2 decide que el uso operativo es "ordenar candidatos e
inspeccionar los primeros k", que es como opera STEG en la práctica (recursos de
inspección limitados, no un clasificador binario para todos los clientes).

| Métrica | Qué responde | Parámetro configurable |
|---|---|---|
| **Precision@k** | De los k clientes con mayor probabilidad, qué fracción es fraude real. | `k` = capacidad de inspección mensual/anual de STEG (a decidir con el usuario, Fase 7). |
| **Recall@k** | De todo el fraude real, qué fracción se captura inspeccionando los primeros k. | mismo `k`. |
| **Lift@k** | Cuánto mejor es el modelo que seleccionar k clientes al azar. | mismo `k`. |
| **Curva de ganancia acumulada / Gini de la curva de Lorenz sobre fraude** | Qué proporción del fraude total se captura según qué proporción de clientes se inspecciona, a través de todos los tamaños de lista. | ninguno adicional; complementa a Precision@k con la vista completa. |

## Métricas de costo-beneficio (Fase 7, parámetros configurables)

Requieren parámetros de costo que no se inventan: costo de una inspección, ganancia
esperada de detectar un fraude real, costo de una inspección en falso. Estos parámetros
se deciden con el usuario en la Fase 7 y se registran en `reports/DECISIONS.md`
(sección "Parámetros de costo del análisis de inspección" en `contextPrompt.md`).

| Métrica | Fórmula (conceptual) | Uso |
|---|---|---|
| **Ganancia esperada neta** | `n_fraudes_detectados × ganancia_por_fraude - n_inspecciones × costo_por_inspección` | Compara puntos de operación en unidades de negocio, no solo estadísticas. |
| **Análisis de sensibilidad** | Recalcular la ganancia esperada variando cada parámetro de costo en un rango razonable. | Muestra qué tan frágil es la recomendación de umbral/k a los supuestos de costo — se reporta siempre junto a la ganancia puntual. |

## Criterio de elección de la métrica primaria (a decidir en Fase 2, no aquí)

La elección debe responder, con evidencia del EDA:

1. ¿STEG va a operar por umbral fijo o por lista priorizada de tamaño k? Si es lo
   segundo (más consistente con "recursos de inspección limitados"), la métrica
   primaria debe ser una de la familia `@k`, no ROC-AUC.
2. ¿El desbalance observado (5,58 %) exige una métrica sensible a la clase minoritaria
   (PR-AUC) en vez de ROC-AUC como métrica secundaria de referencia frente al
   leaderboard de Zindi?
3. ¿Importa la probabilidad calibrada en sí misma, o solo el orden? Si solo el orden,
   la calibración es secundaria, no primaria.

Cualquier número de este catálogo que aparezca en `reports/RESULTS.md` o en el
manuscrito debe existir primero en `reports/metrics/` — ver `steg-experiment-tracking`.
