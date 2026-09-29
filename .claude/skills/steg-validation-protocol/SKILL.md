---
name: steg-validation-protocol
description: Explica cómo partir los datos de STEG por cliente sin fuga, cómo correr validación cruzada anidada, cómo reportar intervalos por bootstrap, y cómo manejar la dimensión temporal del historial de facturación (1977-2019, sin fecha de fraude en la etiqueta). Úsala al escribir o revisar cualquier código de partición de datos, de validación cruzada, o al decidir qué ventana temporal entra en las variables de un experimento.
---

# Protocolo de validación — STEG

## La regla que no se negocia

La unidad de análisis es el cliente. `src/steg/data/split.py` ya implementa y prueba
esto (`tests/test_split_anti_leakage.py`): `grouped_train_valid_split` y
`grouped_kfold_splits` agrupan por `client_id`, y `assert_no_group_leakage` verifica que
ningún cliente cae en dos lados de una partición. Ningún código de modelado parte los
datos por su cuenta — siempre pasa por estas funciones.

Esto aplica a cada nivel: el split train/valid interno, cada fold de CV, y también
cualquier remuestreo (bootstrap, sobremuestreo de la clase minoritaria si se decide
usarlo) — remuestrear filas de factura de un cliente que ya está en el fold de
validación es fuga aunque el remuestreo ocurra "solo en train".

## Qué se ajusta dentro del fold, y cómo

Todo lo que aprende de los datos (imputación, escalado, codificación de categóricas de
alta cardinalidad como `region` o `counter_code`, selección de variables, remuestreo,
las medianas de referencia de `rel_consumo_vs_region` en `steg-feature-engineering`) va
dentro de un `Pipeline` de scikit-learn ajustado únicamente con los índices de train de
cada fold. Nunca se calcula una estadística sobre el dataset completo antes de partir,
ni siquiera "solo para explorar" — si ese número termina influyendo una decisión de
modelado, ya es fuga.

## Validación cruzada anidada

- **Bucle externo**: `grouped_kfold_splits` (o `StratifiedGroupKFold` si la Fase 2
  decide que hace falta estratificar por `target` — ver más abajo) da la estimación de
  desempeño que se reporta.
- **Bucle interno**: dentro de cada fold externo de entrenamiento, otra partición
  agrupada por cliente (o `grouped_train_valid_split`) para la búsqueda de
  hiperparámetros (Optuna). El bucle interno nunca toca los índices de validación del
  bucle externo.
- Con 135.493 clientes y 5,58 % de positivos, cada fold de 5 tiene del orden de 1.500
  positivos — suficiente para CV anidada sin que el fold interno se quede sin
  positivos, pero verificarlo empíricamente antes de fijar `N_FOLDS` en
  `steg.config`, no asumirlo.

## Estratificación: pendiente de Fase 2

`GroupKFold` no estratifica por `target`. Si el desbalance (decisión pendiente en
`reports/DECISIONS.md`) resulta severo y la varianza entre folds sin estratificar es
alta, la alternativa es `StratifiedGroupKFold` (disponible en scikit-learn 1.5.1, ya
instalado). El cambio es de una línea en `src/steg/data/split.py` — no se hace hasta que
la Fase 2 lo decida con evidencia, y el motivo se registra en `DECISIONS.md`.

## Bootstrap para intervalos

Al reportar una métrica (Fase 5 en adelante), el bootstrap se hace **remuestreando
clientes, no filas de factura**: se remuestrea la lista de `client_id` del conjunto de
evaluación con reemplazo, se reconstruyen las predicciones de esos clientes, y se
recalcula la métrica. Remuestrear filas de factura directamente rompe la unidad de
análisis del mismo modo que un split mal hecho. Semilla: `steg.config.SEED`, con un
generador de NumPy inicializado explícitamente para que el bootstrap sea reproducible
número por número.

## Dimensión temporal

Dos hechos ya verificados en la Fase 0 que cualquier decisión temporal debe tener en
cuenta:

1. El historial va de 1977 a 2019, pero el volumen real arranca en 2005; antes de esa
   fecha hay menos de 2.200 facturas por año en total.
2. La partición train/test de Zindi es **aleatoria por cliente, no temporal**: la
   distribución del año de la última factura es casi idéntica entre train y test. No
   existe un corte cronológico que separe ambos conjuntos.

La etiqueta no trae fecha de fraude, así que no hay forma de saber desde cuándo un
cliente etiquetado como fraudulento lo era. Esto obliga a decidir explícitamente, en la
Fase 3 y con evidencia del EDA temporal (`steg-eda-protocol`), qué ventana de historial
entra en las variables agregadas (¿todo el historial? ¿los últimos N años? ¿desde
2005?) — no se asume "usar todo el historial" solo porque es lo más simple.

## Qué hace este protocolo y qué no

Esta skill fija **cómo** partir y validar. **No** fija la métrica ni el punto de
operación (eso es `steg-metrics-catalog` y la decisión de Fase 2), ni implementa el
código de features (`steg-feature-engineering`). El protocolo completo de evaluación —
métrica primaria, folds, estratificación — se congela al final de la Fase 2 y no cambia
después de ver resultados de modelos (sección 2 de `contextPrompt.md`); si hace falta
cambiarlo más adelante, el cambio y el motivo se documentan y se reportan ambas
versiones.
