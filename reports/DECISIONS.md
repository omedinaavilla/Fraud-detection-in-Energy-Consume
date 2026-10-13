# Bitácora de decisiones

Cada entrada lleva fecha, la decisión tomada y la evidencia que la sustenta (figura,
tabla o estadístico en disco). Ninguna decisión de modelado o evaluación se toma por
defecto ni por costumbre (sección 2 de `contextPrompt.md`).

---

## 2026-09-17 — Infraestructura del repositorio (Incremento 1)

Estas cuatro decisiones no son de modelado: son de entorno de trabajo, y se tomaron
con el usuario antes de escribir código (ver `AskUserQuestion` en la sesión de
planificación).

**Control de versiones.** El único repositorio git accesible desde este directorio
está en la carpeta de usuario de Windows (`C:\Users\...\.git`), sin commits, y mezcla
todo el perfil del sistema operativo. Se decidió **no versionar todavía**: no se
ejecutó `git init` en `Seminario/` ni se tocó el repo de la carpeta de usuario. El
`.gitignore` del proyecto queda escrito para cuando se decida versionar.
*Riesgo si se revierte*: sin git, no hay historial de qué código produjo qué resultado
más allá de los hashes de datos y las fechas de los artefactos en `reports/`.

**Ubicación de los datos crudos.** `contextPrompt.md` asume `data/raw/*.csv`; los
archivos originales estaban en la raíz del proyecto. Se **movieron** (no copiaron) a
`data/raw/`, junto con el diccionario de variables (ahora `data/raw/README.md`).

**Entorno de Python.** El prompt pide Python 3.11; el intérprete disponible es
Anaconda 3.12.7. Se decidió **usar el 3.12.7 existente** en vez de crear un entorno
3.11 dedicado: todo el stack requerido (pandas, scikit-learn, lightgbm, xgboost,
catboost, shap, optuna) soporta 3.12, y crear un entorno nuevo no aporta nada a la
validez de los resultados. Las versiones quedan fijadas en `pyproject.toml` contra lo
que efectivamente está instalado. Pendiente de instalar en el target `setup` de
`Makefile`: `lightgbm`, `catboost`, `shap`, `ruff` (no bloquean la Fase 0).

**Alcance del primer incremento.** Andamiaje completo + Fase 0 (contrato de datos,
limpieza documentada, hashes, perfilado), sin avanzar a la Fase 1 (EDA profesional)
todavía.

---

## PENDIENTES — decisiones diferidas hasta que el EDA las sustente

No se ha tomado ninguna de estas decisiones. No se aplica la receta habitual de la
literatura de fraude eléctrico sin verificarla contra estos datos (sección 3 de
`contextPrompt.md`).

| Decisión | Se toma en | Estado |
|---|---|---|
| Métrica primaria y secundarias del proyecto | Fin de Fase 2 | ADOPTADA 2026-10-07 (ver "Protocolo adoptado para la etapa de modelado") |
| Si hay o no un problema de desbalance, y qué hacer al respecto | Fin de Fase 2 | ADOPTADA 2026-10-07 (ver "Protocolo adoptado para la etapa de modelado") |
| Punto de operación / umbral, y si tiene sentido evaluar "@k" | Fin de Fase 2 | ADOPTADA 2026-10-07 (ver "Protocolo adoptado para la etapa de modelado") |
| Estratificación o no de los folds | Fin de Fase 2 | ADOPTADA 2026-10-07 (ver "Protocolo adoptado para la etapa de modelado") |
| Cómo codificar categóricas de alta cardinalidad | Fase 3 | ADOPTADA 2026-10-07 (ver "Protocolo adoptado para la etapa de modelado") |
| Qué hacer con clientes con muy pocas facturas | Fase 3 | ADOPTADA 2026-10-07 (ver "Protocolo adoptado para la etapa de modelado") |
| Ventana temporal del historial usada para construir variables | Fase 3 | ADOPTADA 2026-10-07 (ver "Protocolo adoptado para la etapa de modelado") |
| Parámetros de costo del análisis de inspección | Fase 7 | PENDIENTE |
| Encuadre del modelo ante el lector (detección de fraude vs. priorización de inspecciones) | Antes de la Fase 9 | PENDIENTE, sin decidir |

Evidencia preliminar ya disponible para cuando se discutan estas decisiones (de la
auditoría de Fase 0, `reports/EDA/00_data_audit.md`):

- Tasa de positivos: 5,58 % (7.566 de 135.493 clientes) — insumo directo para la
  discusión de desbalance.
- 4.212 clientes con una sola factura y 15.269 con tres o menos — insumo directo para
  la decisión sobre clientes con historial corto.
- La partición train/test de Zindi es aleatoria por cliente, no temporal (la
  distribución del año de última factura es casi idéntica entre ambos) — relevante
  para decidir la ventana temporal de las variables y para no asumir un corte
  cronológico que no existe.

---

<!-- BEGIN PROPUESTAS-EDA -->
<!-- Bloque generado por notebooks/01_eda.ipynb (sección de exportación). No editar a
     mano: cualquier cambio se hace en el notebook y se regenera ejecutándolo. El resto
     de este archivo queda intacto al regenerarlo. -->

## PROPUESTAS de la Fase 2 (protocolo de evaluación) — 2026-09-18

Estado: **PROPUESTA**. Ninguna está decidida. La evidencia procede del análisis
exploratorio de `notebooks/01_eda.ipynb`, de las tablas que esa ejecución escribe en
`reports/tables/` y de las figuras de `reports/figures/`; el desarrollo completo está en
`reports/EDA/05_implicaciones.md`.

### PROPUESTA — Métrica primaria

Evidencia: `evaluation_metric_baselines.csv`. El clasificador trivial acierta el
94,42 %, de modo que la exactitud queda fuera. La línea base de
PR-AUC es 5,58 %. El mejor agregado exploratorio por sí solo da un
ROC-AUC de 70,7 % (`exp_n_counters`, rank-biserial 0,415,
`bivariate_numeric_target.csv`), así que el ordenamiento tendrá solapamiento fuerte entre
clases.

Alternativas y riesgo. (A) PR-AUC primaria: sensible a la zona de alta precisión, que es
donde opera una lista de inspecciones; depende de la prevalencia y no compara entre
subgrupos. (B) ROC-AUC primaria: comparabilidad interna y externa, con el liderato del
reto (86 %) como referencia de dificultad; promedia umbrales que ninguna operación usaría.
(C) Métrica @k primaria: fiel al uso operativo; exige fijar k sin conocer la capacidad de
inspección.

### PROPUESTA — Desbalance

Evidencia: `evaluation_metric_baselines.csv` y `evaluation_fold_prevalence.csv`.
7.566 positivos de 135.493 (5,58 %),
16,9 negativos por positivo, y entre 1.486 y
1.549 positivos por pliegue agrupado por cliente. El error estándar
relativo de una proporción estimada sobre un pliegue es del 2,5 %: hay
desbalance, sin escasez de casos.

Alternativas y riesgo. (A) Ninguna técnica y ajuste de umbral al final: mantiene la
calibración; riesgo de que un modelo muy regularizado ignore la minoritaria, verificable
con los baselines. (B) Ponderación de clases: barata; descalibra y obliga a recalibrar
antes del análisis de inspección. (C) Remuestreo: sin escasez que resolver, debe ir dentro
del pliegue, e interpolar sobre variables con sesgo del orden de 526
(`univariate_numeric_invoice.csv`) generaría clientes inexistentes.

### PROPUESTA — Punto de operación y "@k"

Evidencia: `evaluation_at_k_reference.csv` y `fig_eval_at_k.png`. Una lista de 5.000
clientes cubre el 3,69 % de la base, contiene 279,2 fraudes
con orden aleatorio y alcanza como techo un recall del 66,09 % con
orden perfecto.

Alternativas y riesgo. (A) Curva @k para varios k sin fijar umbral: honesto; sin número
único citable. (B) Umbral que maximiza F1: reproducible; pondera precisión y recall por
igual sin razón operativa. (C) Aplazar el umbral al análisis de costo-beneficio: lo más
defendible; exige asumir parámetros de coste y su análisis de sensibilidad.

### PROPUESTA — Estratificación de los pliegues

Evidencia: `evaluation_fold_prevalence.csv` y `fig_eval_pliegues.png`. Con 5
pliegues agrupados por `client_id`, la desviación de la prevalencia entre pliegues es de
0,0873 puntos porcentuales frente a 0,1395 esperados por azar
binomial; el esquema estratificado la deja en 0,1673.

Alternativas y riesgo. (A) `GroupKFold`: implementado y cubierto por la prueba anti-fuga;
determinista, lo que impide repetir la validación con otra semilla. (B)
`StratifiedGroupKFold` con barajado y semilla fija: homogeneidad garantizada y repetible;
añade una restricción que la evidencia no reclama y obliga a revisar la prueba anti-fuga.
Lo que impide la fuga entre pliegues es la agrupación por cliente, que ambos esquemas
cumplen.

### Hallazgo transversal que condiciona las cuatro

La tasa de fraude crece del 0,642 % al 9,756 % entre el decil
de clientes con menos facturas y el de más (`confounding_history_length.csv`). Como la
etiqueta registra fraude detectado, parte de esa relación es exposición a inspección y no
propensión a defraudar. Cualquier métrica y cualquier punto de operación que se elija
deberá reportarse también desagregado por longitud de historial.

<!-- END PROPUESTAS-EDA -->

---

## 2026-10-07 — Hallazgos del EDA que condicionan el preprocesamiento, las variables y el entrenamiento

Estado: **PROPUESTA** para lo que atañe a la Fase 3 en adelante; ninguna práctica de este
bloque está cerrada. La evidencia procede de `reports/EDA/01` a `05` y de las tablas
citadas. Este bloque complementa el generado desde el notebook (que cubre métrica,
desbalance, punto de operación y pliegues) y se mantiene fuera de él para que regenerarlo
no lo borre.

### Limitación de fondo: la etiqueta es fraude detectado, no fraude cometido

La etiqueta solo vale 1 para clientes que STEG inspeccionó y en los que confirmó fraude.
Un fraude cometido y no inspeccionado figura como 0, de modo que ninguna métrica calculada
contra `target` puede respaldar que el modelo detecte fraude cometido. Evidencia: la tasa
de fraude pasa de 0,642 % a 9,756 % entre el decil con menos facturas y el de más
(`confounding_history_length.csv`), y Coma-Puig y Carmona documentan el mismo mecanismo en
`reports/LITERATURE_BASE.md`: un clasificador entrenado sobre etiquetas de campañas
dirigidas termina aprendiendo el proceso de inspección.

Matiz medido: dentro de cada quintil de longitud de historial, `exp_n_counters` conserva
un rank-biserial de 0,22 a 0,40 (global 0,415), mientras `exp_new_index_max` cae a -0,015
en el quintil más largo y `exp_antiguedad_dias` a 0,04 (`confounding_conditional_effects.csv`).
La acumulación de lecturas y la antigüedad miden exposición; el número de contadores dice
algo propio, aunque los datos no distinguen si es patrón de fraude o consecuencia de haber
sido inspeccionado (una visita puede implicar cambio de contador).

### Preprocesamiento: prácticas propuestas

| Hallazgo | Práctica propuesta | Evidencia |
|---|---|---|
| Consumo e índices con cola extrema (sesgo hasta 526) y fraude creciente con el consumo máximo | Transformación logarítmica; no truncar ni winsorizar | `univariate_numeric_invoice.csv`, `outliers_target_rate.csv` |
| 29.278 filas duplicadas por clave lógica; 17.768 de 18.363 grupos difieren en consumo o índices | No eliminarlas: no son copias | `quality_deepdive.csv` |
| `months_number` fuera de [1, 12] en 24.043 filas | Marcar como anomalía; 13-24 puede ser real, por encima de 1.000 no admite lectura | `quality_deepdive.csv` |
| 81 filas con `counter_statue` y `reading_remarque` desplazados | Marcar; no interpretar por su valor | `quality_deepdive.csv` |
| 8.748 clientes con primera factura anterior al alta | Medir antigüedad desde la primera factura observada, no desde `creation_date` | `quality_deepdive.csv` |
| `counter_number` compartido entre clientes (20.366 valores) | No usarlo como identificador de equipo | `quality_deepdive.csv` |
| `counter_statue` (97,8 % en un código) y `counter_coefficient` (99,97 % igual a 1) | Sin variación aprovechable tal cual | `univariate_high_cardinality.csv` |
| Consumo sin unidad y códigos sin diccionario | Leer el consumo como magnitud relativa; no interpretar códigos por su valor | `EDA/01_comprension_y_calidad.md` |

### Construcción de variables: prácticas propuestas

Cada una debe poder calcularse con información disponible al predecir y, cuando se ajuste
algún estadístico de referencia (medianas por región, escalado, codificación), ajustarse
solo con el pliegue de entrenamiento.

- **Normalizar por período y por longitud.** Consumo por mes (consumo dividido entre
  `months_number`); tasas y proporciones en lugar de conteos o máximos acumulados. Evidencia:
  como proporción de las facturas, las banderas de duplicado y de retroceso de índice
  pasan de riesgo relativo 2,16 y 2,06 a rank-biserial de 0,019 y 0,015
  (`confounding_flags.csv`).
- **Evitar como predictores** el número de facturas, la antigüedad y los índices
  acumulados, que miden exposición. Si se incluyen, que sea como control explícito y con
  ablación.
- **Medir al cliente contra su propio pasado** (consumo reciente frente a su mediana
  histórica, pendiente, coeficiente de variación, consistencia entre consumo facturado y
  diferencia de índices) y **contra sus pares** (región, distrito, categoría).
- **Ventana fija de últimas N facturas** con indicador de historial incompleto, para que
  dos clientes se comparen con la misma cantidad de información.
- **`exp_n_counters`**: probar el conteo y la tasa de cambios de contador por año de
  historial.
- **Historiales cortos**: 4.212 clientes con una factura y 15.269 con tres o menos, con
  tasa de fraude de 0,642 %. Descartarlos eliminaría un grupo genuino de bajo riesgo y
  alteraría la prevalencia. Un estadístico sobre una factura y otro sobre cuatrocientas no
  son comparables, así que se resuelve con ventana fija o indicadores de longitud, no con
  exclusión.
- **Categóricas**: `region` (25 valores) y `counter_code` (42) tienen categorías por debajo
  del 1 %, y la región 199, la tarifa 18 y tres códigos de contador aparecen solo en
  entrenamiento. El esquema de codificación debe resolver la categoría no vista.
- **Intervalos entre lecturas** calculados dentro de cada tipo de contador (el 45 % de los
  clientes tiene eléctrico y gas).
- **Ventana temporal**: lo anterior a 2005 es el 0,49 % de las facturas. Recortarlo se
  justifica por comparabilidad entre clientes y no por fuga temporal, porque la partición
  no es cronológica.

### Riesgo sin resolver: historial posterior a la detección

La etiqueta no tiene fecha, de modo que no se puede separar el historial anterior a la
detección del posterior. Si el cliente se regulariza tras la inspección, su consumo sube, y
las variables de tendencia o de últimos períodos podrían medir el efecto de haber sido
detectado y no el comportamiento previo. Propuesta de verificación: entrenar con variables
de la primera mitad del historial y de la segunda y comparar; un desempeño mucho mayor con
la segunda indicaría ese efecto.

### Validación y fuga: prácticas propuestas

- Agrupar por `client_id` en todos los pliegues; la partición de Zindi es aleatoria por
  cliente (chi-cuadrado de homogeneidad sobre el año de última factura: V de Cramér
  corregida 0,003, p = 0,32; Kolmogorov-Smirnov sobre la fecha: D = 0,0055, por debajo del
  crítico 0,0067; `temporal_train_test_last_year.csv`).
- Todo ajuste (codificación, escalado, estadísticos de pares, remuestreo si lo hubiera) va
  dentro del pliegue.
- Sin corte temporal; el desempeño no responde a si el modelo detecta fraude futuro, y eso
  se declara como limitación.
- **Controles obligatorios sobre la longitud del historial**: (1) desempeño por quintil o
  decil de longitud; (2) ablación con y sin variables de longitud; (3) línea base de solo
  longitud, para ver cuánto aporta el resto.

### Encuadre del modelo ante el lector: SIN DECIDIR

Dos encuadres posibles, con el mismo modelo y las mismas variables; cambia lo que se
afirma que significa la probabilidad y con qué métricas se respalda.

- **Detección de fraude.** El nombre estándar del problema. Riesgo: los datos no permiten
  respaldar que detecte fraude cometido, solo fraude confirmado por inspección; debe
  declararse como limitación.
- **Priorización de inspecciones.** La probabilidad se lee como probabilidad de que una
  inspección confirme fraude, que es exactamente lo que mide la etiqueta. Se respalda con
  métricas @k y análisis de costo-beneficio. Riesgo: menos peso narrativo y menor
  comparabilidad con trabajos que reportan AUC.

No son excluyentes: puede nombrarse el problema como detección de fraude y reportar el
resultado operativo como ordenamiento con métricas @k, con la limitación declarada.

### Métricas: SIN DECIDIR, candidatas registradas

Contexto ya registrado en el bloque de propuestas: exactitud descartada (el clasificador
trivial acierta 94,42 %), línea base de PR-AUC 5,58 %, ROC-AUC 50 %, techo de recall de
66,09 % con una lista de 5.000 clientes. Candidatas y referencia en la literatura
(`reports/LITERATURE_BASE.md`):

| Métrica | Qué responde | Uso en la literatura |
|---|---|---|
| ROC-AUC | Separabilidad global | Oprea y Bâra (2022); métrica del reto de Zindi |
| PR-AUC | Calidad en la zona de alta precisión; línea base igual a la prevalencia | Parada temprana en Coma-Puig y Carmona (Average Precision) |
| Precisión@k, recall@k, lift@k | Calidad de la cabeza de la lista, con k atado a la capacidad de inspección | Precision@k en Coma-Puig y Carmona |
| NDCG@n | Calidad del ordenamiento sin umbral | Coma-Puig y Carmona |
| Costo-beneficio de la lista | Valor neto de inspeccionar los k primeros | Pendiente de parámetros de costo (Fase 7) |

Notas para cuando se decida: (a) reportar la curva @k para varios k (500, 1.000, 2.500,
5.000, 10.000) y no un solo k, porque la capacidad de inspección no se conoce; (b) comparar
el recall@k contra su techo y no contra 100 %; (c) reportar intervalos por bootstrap o por
pliegue, que ninguno de los dos trabajos de referencia ofrece; (d) la energía recuperada en
kWh de Coma-Puig y Carmona no es replicable, porque la etiqueta de este conjunto es
binaria; (e) las cifras de Oprea y Bâra (AUC 0,997) están marcadas como no verificadas y no
sirven de referencia de lo alcanzable.

---

## 2026-10-07 — Protocolo adoptado para la etapa de modelado (Fases 3 a 6)

Estado: **ADOPTADA** para la primera iteración de modelado, por delegación explícita del
usuario ("trabaja de forma autónoma"). Cierra las cuatro propuestas de la Fase 2 y las tres
decisiones de la Fase 3 con la evidencia ya registrada arriba; no reabre ningún análisis del
EDA. Cualquier cambio posterior se documenta como entrada nueva y se reportan ambas versiones.

### Entorno y datos

Los cuatro CSV se obtuvieron en esta máquina del espejo público de Kaggle
(`mrmorj/fraud-detection-in-electricity-and-gas-consumption`) y se aceptaron porque sus
cuatro SHA-256 coinciden byte a byte con `reports/data_checksums.json`. El entorno es un
`.venv` del proyecto con las versiones de `pyproject.toml`.

### Partición: holdout sellado + validación cruzada sobre el resto (NUEVO, no estaba propuesto)

- `client_test` de Zindi no tiene etiqueta y no sirve para evaluar.
- El 20 % de `client_train`, estratificado por `target` con `SEED`, queda como **holdout
  sellado** (`make_holdout_assignment` en `src/steg/data/split.py`). Se evalúa **una sola
  vez**, con el modelo final ya elegido. Todo el diseño de variables, las ablaciones, la
  comparación de modelos y la búsqueda de hiperparámetros ocurren en el 80 % restante
  (`dev`).
- Por qué: la construcción de variables y la elección de modelo serán iterativas y guiadas
  por la CV; sin una partición nunca usada, la cifra final heredaría el sesgo optimista de
  esa iteración. Con ~1.500 positivos, el holdout sostiene intervalos útiles.
- Ningún análisis que mire `target` (incluidas comprobaciones univariadas de variables
  nuevas) corre sobre el holdout antes de la evaluación final.

### Pliegues: `StratifiedGroupKFold`, 5 pliegues, barajado con `SEED` (propuesta B)

La evidencia (`evaluation_fold_prevalence.csv`) no exigía estratificar, pero el esquema B
permite repetir la CV con otra semilla para medir la varianza del propio reparto, que es
la razón citada en la propuesta. La agrupación por cliente se mantiene en ambos niveles
(facturas y matriz por cliente). La búsqueda de hiperparámetros usa partición interna
agrupada dentro de `dev`; su sesgo optimista sobre la CV se declara y lo corrige el
holdout.

### Métrica primaria: PR-AUC (average precision); ROC-AUC y @k co-reportadas (propuesta A con B y C como secundarias)

- El uso previsto es una lista de inspección: lo que importa es la cabeza del
  ordenamiento, que es donde PR-AUC concentra su peso. Línea base: 5,58 %.
- ROC-AUC se reporta siempre por comparabilidad con el reto (liderato ~0,86, otro
  protocolo) y porque no depende de la prevalencia, lo que la hace la métrica correcta
  para comparar **subgrupos** con prevalencias distintas.
- Curva @k (precisión, recall, lift) con k como fracción de la base: 0,5 %, 1 %, 2 %, 5 % y
  10 %, porque la capacidad de inspección no se conoce. El recall@k se compara contra su
  techo.
- Regla de selección: entre modelos cuya diferencia de PR-AUC con el mejor no sea
  distinguible (comparación pareada por pliegue y bootstrap por cliente), se prefiere el
  más simple. Ninguna elección se hace por una diferencia dentro del ruido.

### Desbalance: sin remuestreo; ponderación solo como experimento controlado (propuesta A)

Hay desbalance sin escasez (~1.200 positivos por pliegue de entrenamiento en `dev`). Las
métricas elegidas son de ordenamiento y no dependen del umbral. Se prueba
`scale_pos_weight`/`class_weight` una vez contra la versión sin ponderar; se adopta solo si
mejora PR-AUC por encima del ruido, y en ese caso se recalibra.

### Punto de operación: sin umbral fijo en esta etapa (propuesta A, con C aplazada)

Se reporta la curva @k. El umbral queda para el análisis de costo-beneficio (Fase 7), que
sigue esperando parámetros de costo del usuario.

### Fase 3

- **Ventana temporal**: facturas desde 2005-01-01 (99,51 % del volumen), por
  comparabilidad entre clientes, no por fuga temporal (la partición no es cronológica).
  Además, las variables de nivel de consumo se calculan también sobre una **ventana fija de
  las últimas 12 facturas** con indicador de historial incompleto.
- **Historiales cortos**: no se excluyen; se representan con indicadores de longitud y con
  valores faltantes explícitos donde un estadístico no es calculable.
- **Categóricas** (`region` 25 valores, `disrict` 4, `client_catg` 3): sin codificación
  por objetivo. Boosting usa categoría nativa; la regresión logística usa one-hot con
  `min_frequency` y `handle_unknown="infrequent_if_exist"` ajustado en el pliegue. Las
  categorías de factura (`tarif_type`, `counter_code`) entran como proporciones por
  cliente.
- **Variables de exposición** (número de facturas, antigüedad, extensión del historial,
  índices acumulados) se aíslan en una familia propia y se evalúan con los tres controles
  ya registrados: línea base de solo longitud, ablación con y sin la familia, y
  desempeño por quintil de longitud. Ninguna variable de comportamiento usa conteos o
  máximos acumulados que crezcan con la longitud del historial.
- **Riesgo de historial posterior a la detección**: se ejecuta la verificación propuesta
  (variables de la primera mitad del historial frente a la segunda).

---

## 2026-10-08 — Modelado: historial censurado en el primer evento de equipo o de contrato

Estado: **ADOPTADA**. Modifica la entrada anterior en cuatro puntos: la tasa de cambios de
contador, el número de contadores en la familia de exposición, la representación del
historial y las variables con deriva de calendario. Se apoya en evidencia nueva obtenida
durante el modelado. Todo el proceso está en `notebooks/02_modelado.ipynb`, sección 4. Las
cifras salen de `reports/tables/modeling_*.csv` y de `reports/metrics/*_20261008.json`,
calculadas sobre `dev` y sin tocar el holdout. Antes de evaluar el holdout se hizo una
revisión adversarial de fuga sobre el notebook. Su primer veredicto fue de bloqueo, y las
correcciones que exigió están incorporadas aquí.

### Evidencia

- **Los eventos de equipo y de contrato son huella de la inspección.**
  - Se consideran tres eventos sobre el mismo contador: reemplazo de contador, cambio de
    `counter_code` y cambio de `tarif_type`.
  - Los clientes de `dev` con alguno de ellos tienen una tasa de fraude del 18,7 %, frente
    al 2,2 % del resto.
  - En los clientes con fraude, el reemplazo de contador cae al final del historial: posición
    relativa mediana de 0,70, frente a 0,41 en el resto.
  - Después del último reemplazo les queda menos historial: 2,7 años, frente a 5,7
    (`modeling_diagnostico_eventos_equipo.csv`).
  - El código de contador 207 pasa del 7,4 % al 10,8 % de las facturas entre la primera y la
    segunda mitad del historial, y solo en los clientes con fraude.
- **La verificación por mitades confirma el riesgo registrado.**
  - Con el historial completo, las variables de la segunda mitad dan un PR-AUC de 0,396 y las
    de la primera, 0,182. La diferencia es de 0,213 (IC 95 % [0,199, 0,227]).
  - Con el historial censurado, la diferencia baja a 0,032 (IC 95 % [0,022, 0,041])
    (`modeling_verificacion_mitades_historial.csv`).
  - La tasa de cambio de contador aporta por sí sola 0,10 de PR-AUC: 0,363 frente a 0,260
    (`model_comparison.csv`).
- **El calendario delata la fecha del corte.**
  - Varias magnitudes cambian con los años en toda la base
    (`modeling_diagnostico_calendario_anual.csv`):
    - la codificación de `reading_remarque` (la nota 6 va de 0,90 de las facturas en 2005 a
      0,20 en 2019);
    - la fracción del consumo en niveles superiores;
    - los intervalos de más de 240 días entre lecturas;
    - el estado del contador;
    - la mezcla de códigos de contador.
  - Un historial cortado antes tiene otro perfil, y ese perfil vuelve a señalar que hubo un
    evento.
- **El ajuste por año empeora el problema en vez de resolverlo.** Se probó expresar cada
  indicador frente a la tasa típica de su año y se descartó, porque el valor ajustado de un
  indicador poco frecuente acaba codificando la época del historial. Con ese ajuste:
  - las variables predicen el evento con un ROC-AUC de 0,952, frente a 0,905 sin ajuste;
  - el PR-AUC dentro del grupo sin evento baja de 0,091 a 0,084;
  - fuentes: `modeling_diagnostico_ajuste_calendario_descartado.csv` y
    `reports/metrics/descartados/`.
- **La exposición calculada sobre el historial censurado también delata el evento.** La
  diferencia entre la antigüedad y la extensión censurada revelaba su fecha. Se detectó en la
  prueba previa y se corrigió: la exposición se calcula sobre la ventana completa.

### Decisión

1. **Representación del historial.** Las variables de comportamiento se calculan sobre el
   historial **censurado en el primer evento de equipo o de contrato**. La regla no usa la
   etiqueta, se aplica igual a todos los clientes y puede usarse en el momento de puntuar.
   No cuentan como evento dos registros del mismo día con códigos distintos.
2. **Variables que salen.** La tasa de cambio de contador sale del modelo, y el número de
   contadores sale de la familia de exposición. La familia de exposición se calcula siempre
   sobre la ventana completa.
3. **Variables con deriva de calendario.** Se decidió con una regla: cada grupo se retira
   salvo que hacerlo cueste más de 0,005 de ROC-AUC dentro del grupo sin evento. Cada
   diferencia lleva su intervalo bootstrap pareado del 95 % por cliente
   (`modeling_diagnostico_calendario_decision.csv`).
   - **Grupo A** (notas de lectura y fracción en niveles superiores): **se retira**.
     Retirarlo mejora el ROC-AUC sin evento en 0,008 (IC 95 % [0,003, 0,013]) y reduce de
     0,905 a 0,871 la capacidad de las variables para predecir el evento.
   - **Grupo B** (intervalos largos, estado del contador y códigos de contador): **se
     conserva**. Retirarlo cuesta 0,008 (IC 95 % [0,003, 0,014]). El intervalo excluye el
     cero, así que B aporta señal dentro del grupo sin evento. Pero contiene el umbral, así
     que la decisión cae **dentro del ruido**. Por eso, antes de abrir el holdout, se declaró
     como control de sensibilidad el modelo sin el grupo B: se evalúa en el holdout junto al
     principal y sus cifras se reportan siempre.
   - **Cuándo se fijó la regla.** La regla y el umbral se fijaron después de la primera
     revisión de fuga y después de ver una versión anterior de estos resultados. No es un
     registro previo a todo análisis, y así se declara.
4. **Control del historial completo.** El modelo sobre el historial completo (PR-AUC 0,363)
   se conserva como control. Es un techo contaminado por huellas de la inspección, no una
   expectativa de desempeño.
5. **Métrica por subgrupo.** Junto a la cifra global se reporta siempre el desempeño dentro
   del grupo **sin ningún evento** (86.177 clientes de `dev`, prevalencia del 2,2 %). Es la
   medida más limpia de la señal de comportamiento.
6. **Ablación con exposición.** Solo se interpreta dentro del grupo sin evento. En el
   agregado, combinar la exposición de la ventana completa con los faltantes del historial
   censurado delata un corte temprano.

### Lo que no cambia

Se mantienen como en la entrada anterior:

- el holdout;
- los pliegues;
- la métrica primaria;
- la ausencia de remuestreo;
- la exclusión de la familia de exposición del modelo principal.

La regla de selección se precisa: un modelo solo es peor que el mejor si el intervalo
bootstrap de la diferencia excluye el cero **y** además es peor en al menos 4 de los 5
pliegues.

### Riesgo residual declarado

- **Inspecciones sin evento.** Una inspección que confirma fraude sin cambiar el equipo ni el
  contrato no deja evento que censurar. Persiste una brecha de 0,032 de PR-AUC entre mitades
  del historial censurado: es compatible con la mayor relevancia de lo reciente, pero no
  descarta un efecto residual.
- **El grupo B delata el evento.** Las variables del modelo todavía predicen el evento con un
  ROC-AUC de 0,871, y el grupo B contribuye a ello. Lo hacen, por ejemplo, el estado de
  contador distinto de cero, que suele preceder al reemplazo, y el código 207, que además se
  asocia con equipos más recientes.
- **Duplicados lógicos.** Muestran una firma tardía débil en los clientes con fraude.
- **El ajuste por año descartado.** Su código está archivado en
  `notebooks/_archive_2026-10-08/02_modelado_ajuste_calendario.ipynb` para poder reproducir
  el experimento.

### Hallazgo colateral sobre la ventana temporal

- La ventana desde 2005 recorta el 0,49 % de las facturas, pero deja sin ninguna factura a
  7.129 clientes de `client_train` (5,3 %), cuyo historial completo es anterior a 2005.
- En `dev` son 5.700 y ninguno tiene fraude registrado.
- Se mantienen en la población con el indicador `exp_sin_facturas_desde_2005` de la familia
  de exposición, y las métricas se reportan también sobre clientes activos.
- Una versión anterior de esta entrada daba la tasa de fraude de este grupo calculada sobre
  todo `client_train`, holdout incluido. Se corrigió para cumplir la regla de no mirar la
  etiqueta del holdout.

---

## 2026-09-17 — Planificación con consenso y Plane (infraestructura)

Decisión de proceso, no de modelado, tomada con el usuario vía `AskUserQuestion`.

**Conexión a Plane.** Se agrega `.mcp.json` (servidor oficial
`makeplane/plane-mcp-server`, transporte stdio vía `uvx`) y `.env.example` con las
variables requeridas (`PLANE_API_KEY`, `PLANE_WORKSPACE_SLUG`, `PLANE_BASE_URL`
opcional). El repositorio clonado que el usuario pidió como referencia
(`fastapi-harness-template`, en `Documents/ML/`, fuera de este proyecto) **no
contiene integración con Plane**: es una plantilla de Spec-Driven Development para
FastAPI sin relación con Plane ni `.mcp.json`. Se verificó el MCP oficial de Plane por
separado (documentación de developers.plane.so y el repo de GitHub); hay una
inconsistencia entre ambas fuentes sobre los nombres exactos de las herramientas, que
se resuelve verificando con `/mcp` en el momento de usarlas, no de memoria.
*Pendiente*: el usuario debe completar `.env` con credenciales reales y exportarlas
antes de que la conexión funcione — no se pudo probar en vivo en este incremento.

**Alcance temporal.** El flujo nuevo (solicitud → consenso → Plane → ejecución) rige
**hacia adelante únicamente**. La Fase 0 y el EDA de Fase 1 ya ejecutados no se
retrofitean a Plane.

**Quiénes consensuan.** Los 6 agentes de dominio ya existentes (`eda-analyst`,
`feature-engineer`, `model-trainer`, `results-analyst`, `leakage-auditor`,
`academic-writer`), no agentes de planificación nuevos y separados.

**Política de comentarios en Plane.** Solo el agente que ejecuta una tarea comenta su
work item correspondiente, una vez, al terminar. Ningún otro agente comenta —
en particular, `leakage-auditor` nunca comenta en Plane; su veredicto sigue yendo
exclusivamente a `reports/LEAKAGE_AUDIT.md`. Detalle completo en
`.claude/skills/steg-plane-workflow/SKILL.md` y en el nuevo comando `/request`.

---

## 2026-09-17 — Corrección del diseño anterior contra la branch `plane` real

El usuario señaló que `fastapi-harness-template` (el repo clonado como referencia)
tiene una branch `origin/plane` con una integración de Plane ya implementada.
Se revisó esa branch (`git diff main plane`) y se encontraron tres desajustes con lo
que se había construido en la entrada anterior, que se corrigen aquí:

1. **Secretos.** La branch de referencia gitignorea `.mcp.json` directamente (valores
   literales reales) y commitea `.mcp.json.example` con placeholders de texto — no usa
   `.env` ni sustitución `${VAR}`. Se corrigió: se eliminaron `.mcp.json` (con
   `${VAR}`) y `.env.example`; ahora existe `.mcp.json.example` versionado y
   `.mcp.json`/`.claude/claude_code_config.json` en `.gitignore`.
2. **Plane es espejo, no gate.** La branch de referencia es explícita: "Plane nunca es
   un prerrequisito para implementar"; degradación elegante si el MCP falla, la fuente
   de verdad sigue siendo el artefacto local (`tasks.md` en esa plantilla). El diseño
   anterior bloqueaba la ejecución hasta crear los work items. Se corrigió: ahora
   `reports/tasks/NNN-slug-tasks.md` es la fuente de verdad ejecutable y Plane es el
   espejo; ningún agente se bloquea si Plane no responde.
3. **Nombres de herramientas.** La inconsistencia documental mencionada en la entrada
   anterior queda resuelta con evidencia directa: la branch declara
   `mcp__plane__list_projects`, `list_modules`, `create_module`, `list_states`,
   `create_work_item`, `retrieve_work_item_by_identifier`, `update_work_item`,
   `add_work_items_to_module`, `list_module_work_items`, `create_work_item_comment` en
   el `tools:` de sus propios sub-agents. Se adoptan estos nombres tal cual.

**Lo que NO se copió de la branch, a propósito.** Ahí comentan `test-engineer`
(resultado de tests) y `code-reviewer` (veredicto), y es `code-reviewer` quien mueve
el work item a Done — el implementador no comenta. El usuario pidió explícitamente lo
inverso para este proyecto: solo el agente ejecutor comenta y cierra su propio work
item; el rol adversarial (`leakage-auditor`, equivalente a `code-reviewer` aquí) no
toca Plane en absoluto. Esta es una personalización deliberada, no un desajuste sin
resolver.

Detalle completo actualizado en `.claude/skills/steg-plane-workflow/SKILL.md`,
`.claude/commands/request.md` y el `tools:` de los 5 agentes ejecutores.

---

## 2026-09-18 — Retrofit a Plane del trabajo de EDA ya realizado (excepción deliberada)

El usuario pidió evidenciar en Plane lo ya hecho en la parte de EDA. Esto choca con la
regla anterior ("la Fase 0 y el EDA de Fase 1 ya ejecutados no se retrofitean a
Plane"), así que se confirmó explícitamente con el usuario vía `AskUserQuestion` antes
de actuar. Eligió actualizar la política y crear los work items.

**Lo que se hizo.** Se creó el módulo `001-retrofit-eda-fase0-fase1` en el único
proyecto del workspace de Plane (`Proyectos_Omar`, identificador real **`PROYE`**, no
`STEG` como asumía el placeholder `<PREFIJO>` sin completar en el skill — es el
proyecto demo por defecto del workspace, no uno creado a medida para STEG) y 6 work
items en estado **Done** (`PROYE-9` a `PROYE-14`), uno por artefacto de
`reports/EDA/*.md` y del perfilado de Fase 0. Detalle en
`reports/tasks/001-retrofit-eda-fase0-fase1-tasks.md`.

**Lo que no cambia.** Las 4 decisiones PROPUESTA de la Fase 2 (métrica, desbalance,
punto de operación, estratificación) siguen `PENDIENTE` — este retrofit documenta que
el EDA que las sustenta existe, no que ya se decidieron.

**Alcance de la excepción.** Es puntual, para el trabajo ya hecho hasta esta fecha.
Cualquier solicitud nueva sigue el flujo completo de `/request` (consenso → artefacto
local → Plane → ejecución), sin retrofit posterior.

---

## 2026-09-18 — Flujo Scrum multiagente (reemplaza el flujo de 4 pasos de `/request`)

Decisión de proceso tomada con el usuario vía `AskUserQuestion`, tras auditar la
arquitectura existente. No se creó ningún agente nuevo.

**Hallazgo que motivó una corrección obligatoria.** El `tools:` de los 5 agentes
ejecutores declaraba `mcp__plane__list_projects`, `update_work_item`,
`create_work_item_comment`, etc. El servidor `plane-mcp-server` instalado ya no expone
esos nombres: los consolidó por recurso (`mcp__plane__workitem`, `mcp__plane__state`,
`mcp__plane__workitem_comment`, ...). Los subagentes no podían tocar Plane. Se
corrigió en las 5 fichas.

**Roles sobre lo existente.**
- *Product Manager / Orchestrator*: el hilo principal ejecutando `/request`. No puede
  ser un subagente porque los subagentes no convocan a otros agentes.
- *Developers*: los 5 agentes de fase, sin cambios de alcance.
- *Auditores* (opción elegida por el usuario: "ampliar leakage-auditor + auditor
  par"): `leakage-auditor` pasa a ser el auditor obligatorio de toda tarea (AC,
  evidencia, tests y fuga) y conserva su veto de fase en `LEAKAGE_AUDIT.md`. Un agente
  de dominio puede auditar como par, en solo lectura, las tareas de otro agente.

**Comentarios en Plane** (opción elegida: "PM registra auditorías"). Esto sustituye la
política del 2026-09-17 ("solo el ejecutor comenta, una vez, y cierra su work item").
Ahora el ejecutor comenta una vez por ronda al pedir auditoría, y una vez si se bloquea.
El auditor sigue sin tocar Plane. El PM traslada cada veredicto a Plane y es el
único que mueve a Done, después del quality gate.

**Task system extendido, no duplicado.** En Plane se agregaron los estados `Ready`,
`Ready for Audit`, `Changes Requested` y `Blocked`, más las etiquetas `agent:<nombre>` y
`audit:<nombre>` (todos los agentes actúan con el mismo usuario de Plane, así que
*assignee* no los distingue). Las dependencias usan la relación nativa `blocked_by`.
Localmente, cada requerimiento tiene `reports/tasks/NNN-slug-{planning,tasks,audit}.md`,
escritos solo por el PM para evitar escrituras concurrentes. Work item types y
propiedades personalizadas quedaron sin activar: la plantilla de tarea va en la
descripción.

**Consenso en dos rondas** (propuestas; luego APPROVE/REQUEST_CHANGE/ADD_TASK/
REMOVE_TASK/MODIFY_TASK por tarea), con un máximo de 3 rondas antes de escalar al
usuario. **Quality gate**: AC = PASS, todas las auditorías requeridas = PASS,
dependencias en Done y tests verdes. Un FAIL no se puede ignorar ni rebajar.

Detalle normativo: `.claude/skills/steg-plane-workflow/SKILL.md` y
`.claude/commands/request.md`.

---

## 2026-09-18 — Fin del flujo con PM: ejecución directa, Auditor y Agente Investigador

Decisión de proceso, tomada con el usuario. Revierte la entrada anterior ("Flujo Scrum
multiagente") el mismo día en que se había introducido: el usuario no había pedido esa
capa de coordinación y pidió volver a un modelo más directo.

**Qué cambia.** Se elimina el rol de Product Manager / Orchestrator y el comando
`/request` (borrados, no archivados). `.claude/skills/steg-plane-workflow/SKILL.md` se
reemplaza por `.claude/skills/steg-execution-loop/SKILL.md`. La estructura queda en
cuatro roles: **Ejecutor** (los cinco agentes de fase existentes — `eda-analyst`,
`feature-engineer`, `model-trainer`, `results-analyst`, `academic-writer` —, cada uno
responsable de planificar y ejecutar su propio trabajo, sin un agente único que los
sustituya), **Auditor** (`leakage-auditor`, ahora con alcance explícito sobre
coherencia del análisis, justificación de las decisiones y consistencia del Planner,
además de fuga), **Agente Investigador** (`literature-researcher`, nuevo, `/research`) y
**Agente EDA** (`eda-analyst`, sin cambios de alcance).

**Planner.** `reports/PLANNER.md` es ahora el documento vivo de trazabilidad
(tarea → ejecución → resultado → análisis → conclusión → decisión → siguiente paso) para
todo trabajo nuevo. `reports/tasks/NNN-slug-*.md` deja de usarse hacia adelante;
`001-*` y `002-*` quedan como histórico cerrado, sin reescribirse.

**Plane.** Se mantiene como tablero (decisión explícita del usuario), pero cada ejecutor
gestiona directamente su propio work item — igual que en la política del 2026-09-17,
antes del PM — en vez de que una capa central lo haga por todos.

**Redacción.** `steg-human-academic-prose` se amplía con la regla de no revelar nunca la
arquitectura interna de agentes en ningún entregable (manuscrito, Planner, informes) y
con la regla de cerrar cada etapa con una decisión cuando la evidencia ya alcanza, en vez
de dejar preguntas abiertas de relleno.

Detalle normativo: `.claude/skills/steg-execution-loop/SKILL.md`,
`.claude/agents/literature-researcher.md`, `.claude/skills/steg-human-academic-prose/SKILL.md`.

---

## 2026-09-18 — Se elimina el gate de auditoría obligatoria (tercera revisión de proceso del día)

Decisión de proceso, tomada con el usuario. Revierte, sobre la misma entrada anterior
("Fin del flujo con PM"), el rasgo de que `leakage-auditor` fuera un paso obligatorio
antes de cerrar cualquier tarea.

**Qué cambia.** Cada agente ejecutor (`eda-analyst`, `feature-engineer`,
`model-trainer`, `results-analyst`, `academic-writer`) mueve su propio work item de
**In Progress** directamente a **Done** al terminar, publica su comentario de cierre y
actualiza el Planner, sin pasar por **Ready for Audit** ni esperar un veredicto de
`leakage-auditor`. El campo `Auditoría` deja de ser parte obligatoria de la plantilla de
`reports/PLANNER.md`.

**Qué no cambia.** `leakage-auditor` sigue existiendo como agente de revisión
adversarial de fuga, disponible bajo pedido: por `/leak-check` sobre una fase o el
pipeline completo, o por una convocatoria puntual del usuario o de un ejecutor sobre una
tarea concreta. Su alcance de revisión (fuga entre folds, variables con información
futura, transformaciones fuera del fold, métricas mal calculadas, resultados
sospechosamente buenos) no cambia; lo que deja de existir es la obligación de pasar por
él antes de cerrar una tarea o de citar un resultado.

**Por qué.** El usuario pidió explícitamente que el `eda-analyst` (y por extensión el
resto de los ejecutores) publique, cambie de estado y comente sus propias tareas sin
pasar por un auditor.

**Implicaciones para lo siguiente.** Los resultados que lleguen a `reports/RESULTS.md`
o al manuscrito ya no requieren un `APROBADO` previo de `leakage-auditor`; si se quiere
esa revisión, se pide explícitamente con `/leak-check` en el momento que se decida.

Detalle normativo: `.claude/skills/steg-execution-loop/SKILL.md`,
`.claude/agents/leakage-auditor.md` y la ficha de cada agente ejecutor.
