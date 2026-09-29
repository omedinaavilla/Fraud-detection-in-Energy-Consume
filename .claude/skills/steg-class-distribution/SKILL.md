---
name: steg-class-distribution
description: Explica qué mirar para caracterizar la distribución de la etiqueta en STEG (5,58% de positivos observado en Fase 0) y, solo si el EDA muestra que hace falta, cómo comparar honestamente class_weight, scale_pos_weight, ajuste de umbral y remuestreo, con la advertencia de que el remuestreo va dentro del fold. No prescribe una estrategia por defecto. Úsala al discutir la decisión de desbalance de la Fase 2, o antes de aplicar cualquier técnica de balanceo de clases.
---

# Distribución de clases — STEG

## Lo que ya se sabe (Fase 0)

7.566 clientes fraudulentos de 135.493 en train: **5,58 % de positivos**. Esto es un
hecho, no todavía una decisión. 5,58 % no es un desbalance extremo (no es 0,1 %), y
antes de reflexivamente aplicar SMOTE o `scale_pos_weight` porque "así se hace en fraude",
la Fase 2 debe verificar si el desbalance es realmente un problema para el modelo y la
métrica elegida, o si un modelo bien calibrado sin ninguna técnica de balanceo ya
funciona.

## Qué mirar antes de decidir que hay un problema

1. **Desempeño de un baseline sin ninguna técnica de balanceo** (regresión logística,
   LightGBM con `class_weight=None`, Fase 4). Si el recall de la clase minoritaria ya es
   razonable para el uso previsto (priorización de inspecciones, no clasificación
   binaria dura), no hay problema que resolver.
2. **Varianza entre folds** de la métrica primaria (una vez elegida en Fase 2). Un
   desbalance moderado con folds agrupados por cliente (~1.500 positivos por fold con
   5 folds) puede o no producir varianza alta; medirlo, no asumirlo.
3. **Si el punto de operación es "@k"** (una lista de los k clientes más sospechosos
   para inspeccionar, ver `steg-metrics-catalog`), el desbalance de clases en el
   entrenamiento importa menos que la calibración del ranking — otra razón para no
   aplicar balanceo por reflejo.

## Si el EDA muestra que sí hace falta actuar

Comparación honesta entre alternativas, todas evaluadas bajo el mismo protocolo
congelado (`steg-validation-protocol`) y la misma métrica primaria:

| Técnica | Qué hace | Cuándo se ajusta | Riesgo si se hace mal |
|---|---|---|---|
| `class_weight='balanced'` (scikit-learn) | Pondera la función de pérdida por la frecuencia inversa de clase. | Es un hiperparámetro del modelo: se fija dentro del `Pipeline`, no requiere ajuste de datos. | Ninguno de fuga; el riesgo es solo de calibración de probabilidades. |
| `scale_pos_weight` (LightGBM/XGBoost) | Equivalente a `class_weight` para boosting. | Igual que arriba. | Igual que arriba. |
| Ajuste de umbral de decisión | Mueve el punto de corte sobre las probabilidades ya entrenadas, sin tocar el entrenamiento. | Se ajusta con las probabilidades del fold de validación, nunca con las de test. | Si se ajusta mirando el fold de test, es fuga del punto de operación. |
| Remuestreo (SMOTE, undersampling) | Cambia la composición de clases del conjunto de entrenamiento. | **Dentro del fold de entrenamiento, dentro del `Pipeline`** (p. ej. `imblearn.pipeline.Pipeline` con el remuestreador como paso). Nunca antes de partir. | Remuestrear antes de partir duplica o interpola información de un cliente y la reparte entre folds — es la forma más común de fuga en este tipo de proyecto. |

Ninguna de estas se aplica por defecto. Si la Fase 2 decide que hace falta una, la
comparación (con intervalos, no un número suelto — ver `steg-validation-protocol`) va a
`reports/DECISIONS.md` con su evidencia.

## Advertencia central

El remuestreo synthetic (SMOTE y variantes) genera filas de cliente interpoladas entre
clientes reales de train. Si eso ocurre antes del split o fuera del fold, un cliente
sintético "parecido" a un cliente de validación puede filtrar información. Este es el
motivo de que `steg-validation-protocol` exija que todo remuestreo viva dentro del
`Pipeline` ajustado por fold — no es una preferencia de estilo, es la garantía
anti-fuga aplicada a esta técnica específica.
