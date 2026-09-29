---
name: steg-eda-protocol
description: Define el orden de trabajo del análisis exploratorio del proyecto STEG (perfilado, univariado, bivariado, multivariado, temporal, relacional entre client e invoice), qué reportar para cada tipo de variable, cómo tratar los faltantes y anomalías como fenómeno a estudiar en vez de solo imputar, cómo documentar hallazgos en reports/EDA/, y la regla de higiene de que el EDA que mira target solo corre sobre la partición de entrenamiento. Úsala al planear o ejecutar cualquier fase de exploración de datos (Fase 0 y Fase 1), y antes de escribir cualquier análisis que compare una columna con la etiqueta.
---

# Protocolo de EDA — STEG

## Orden de trabajo

1. **Perfilado y auditoría de calidad** (`src/steg/eda/profile.py`, `make audit`). Tipo,
   nulos, cardinalidad, rango, constantes y duplicados por columna y por tabla, más el
   catálogo de verificaciones: valores imposibles o fuera del dominio declarado,
   incoherencias entre `client_*` e `invoice_*`, y categorías que existen en una sola
   partición. Nunca mira `target` más allá de la prevalencia global. Salidas:
   `reports/EDA/00_data_audit.md`, `reports/tables/profile_*.csv`,
   `reports/tables/quality_checks.csv` y `reports/tables/schema_vs_readme.csv`.
   Detectar y cuantificar no basta: cada anomalía que el conteo no explique se
   investiga en el notebook antes de proponer qué hacer con ella (ver
   `reports/tables/quality_deepdive.csv`).
2. **Univariado** (`src/steg/eda/univariate.py`, Fase 1). Distribución de cada columna
   por sí sola: histogramas/boxplots para numéricas, barras de frecuencia para
   categóricas, línea temporal para fechas. Reporta la forma de la distribución
   (sesgo, colas, multimodalidad), no solo media y desviación.
3. **Bivariado** (`src/steg/eda/bivariate.py`, Fase 1). Relación de cada variable con
   `target`, y relaciones entre pares de variables explicativas. **Regla de higiene: se
   ejecuta solo sobre la partición de entrenamiento**, nunca sobre `client_test` ni
   sobre una mezcla de ambos — mirar `target` contra test no tiene sentido (no existe)
   y mirar variables explicativas de test contra la etiqueta de train sería fuga.
4. **Multivariado**. Interacciones de orden superior sugeridas por lo anterior
   (ej. `target` × región × categoría de cliente). Solo si el bivariado da motivo.
   **Control obligatorio de confusión por longitud de historial.** La tasa de fraude
   pasa del 0,64 % al 9,77 % entre el decil de clientes con menos facturas y el de más
   (`reports/tables/confounding_history_length.csv`). Como la etiqueta registra fraude
   *detectado* y la detección exige haber sido inspeccionado, cualquier variable
   correlacionada con el volumen acumulado hereda esa exposición. Todo efecto
   bivariado que supere el umbral se vuelve a medir dentro de estratos de
   `n_invoices` antes de interpretarlo como señal de comportamiento
   (`confounding_conditional_effects.csv`): `new_index` máximo pierde el efecto al
   condicionar, mientras que el número de contadores distintos lo conserva.
5. **Temporal**. Cobertura de facturación por cliente en el tiempo, estacionalidad,
   diferencia de distribución de fechas entre train y test (ver
   `steg-eda-statistics` para la prueba formal). El historial cubre 1977–2019 con un
   quiebre de volumen real en 2005; cualquier estadístico temporal debe decidir qué
   hacer con las facturas anteriores a 2005 y documentarlo.
6. **Relacional entre tablas**. Cómo se agregan las facturas por cliente (facturas por
   cliente, contadores por cliente, consistencia de `creation_date` vs. primera
   factura — hay 8.748 clientes en train con una factura anterior a su alta).

## Qué reportar por tipo de variable

- **Categórica de baja cardinalidad** (`disrict`, `client_catg`, `counter_type`,
  `tarif_type`): tabla de frecuencias, y en bivariado, tasa de positivos por categoría
  con su intervalo (no un único número).
- **Categórica de alta cardinalidad** (`region`, `counter_code`, `counter_number`):
  agrupar categorías raras antes de tabular; nunca listar las 40+ categorías sin
  agregación. `counter_number` en particular no debe tratarse como identificador de
  medidor sin antes reportar cuántos clientes comparten cada valor.
- **Numérica de consumo** (`consommation_level_1..4`, `old_index`, `new_index`): la
  cola es extrema (máximos en el orden de 10^5–10^6). Reportar percentiles (1, 25, 50,
  75, 99), no solo media/desviación, y decidir explícitamente si se transforma
  (log, winsorización) antes de modelar — esa decisión va a `reports/DECISIONS.md`.
- **Fecha**: nunca reportar solo el rango. Reportar la distribución por año, porque
  aquí el volumen no es uniforme (ver punto temporal arriba).
- **Bandera de limpieza** (`counter_statue_invalid`, `months_number_invalid`, etc. de
  `src/steg/data/clean.py`): reportar su tasa de positivos frente a `target`. Una
  anomalía de captura que se concentra en clientes fraudulentos es un candidato a
  variable, no solo un defecto a limpiar.

## Faltantes como fenómeno

Este dataset no tiene nulos declarados, pero sí tiene el equivalente: valores fuera de
rango que probablemente codifican "no se pudo leer" (`counter_statue` no numérico,
`months_number` imposible). Trátalos como faltantes informativos: reporta su tasa base
y su asociación con `target` antes de decidir si se imputan, se dejan como categoría
propia o se usan como variable. No los descartes por default.

## El notebook es la fuente de verdad

La Fase 1 (investigación de las anomalías, univariado, atípicos, temporal, relacional,
bivariado, multivariado, implicaciones — puntos 2 a 6 de arriba) se hace en
`notebooks/01_eda.ipynb`: código y prosa interpretativa (celdas de markdown y las cadenas
que arman la exportación) viven ahí. Estos cinco informes son una exportación de ese
notebook, generada por sus últimas celdas (sección "Exportación"):

| Informe | Contenido |
|---|---|
| `01_comprension_y_calidad.md` | Qué representa cada tabla, lo que los datos no permiten saber, inspección básica y las cinco anomalías investigadas |
| `02_univariado_y_atipicos.md` | Distribuciones por grupo de variables y tratamiento propuesto de los atípicos |
| `03_temporal_y_relacional.md` | Cobertura temporal, naturaleza de la partición, heterogeneidad del historial, comparabilidad train/test |
| `04_bivariado_y_multivariado.md` | Relación con la etiqueta y control de confusión por longitud de historial |
| `05_implicaciones.md` | Las cuatro decisiones de Fase 2 con su evidencia y alternativas |

Nunca se editan a mano por separado, porque quedarían desincronizados de la fuente.
Cualquier cambio de contenido, cifra o redacción en esos informes se hace primero en el
notebook (con `NotebookEdit`) y después se regenera la exportación corriendo esas celdas;
recién ahí se actualizan los `.md`. El notebook también reescribe el bloque de propuestas
de `reports/DECISIONS.md` delimitado por `<!-- BEGIN PROPUESTAS-EDA -->` y
`<!-- END PROPUESTAS-EDA -->`, y conserva intacto el resto del archivo. La Fase 0
(`00_data_audit.md`) es la excepción: la produce directamente `src/steg/eda/profile.py`,
sin notebook de por medio.

## De hallazgo a decisión

Cada hallazgo bivariado que toque una de las decisiones diferidas de
`contextPrompt.md` (sección 3) se documenta en `reports/EDA/` con su evidencia (tabla o
figura en `reports/tables/` o `reports/figures/`) y se resume como una entrada
propuesta en `reports/DECISIONS.md`, marcada `PROPUESTA` hasta que el usuario la
confirme. El agente `eda-analyst` propone; no decide solo (ver
`.claude/agents/eda-analyst.md`).
