# 002 — Guardia "EDA bivariado solo sobre train": planificación

PM: hilo principal vía `/request` (2026-09-18). Proceso: `.claude/skills/steg-plane-workflow/SKILL.md`.
Además de su valor propio, este requerimiento es la validación de punta a punta del flujo Scrum.

## Requerimiento

> Garantizar por código y por test que el análisis bivariado del EDA (las funciones de
> `src/steg/eda/bivariate.py` que reciben `target`) solo pueda ejecutarse sobre la
> partición de entrenamiento (`client_train` / `invoice_train`, identificables por
> `client_id` con prefijo `train_`), y que falle ruidosamente si recibe filas de test.

Motivo: `bivariate.py` documenta la regla de higiene de `steg-eda-protocol` en su
docstring (líneas 9-13), pero nada la hace cumplir. Quien la respeta es el llamador (el
notebook).

## Agentes convocados

| Agente | Convocado | Motivo |
|---|---|---|
| eda-analyst | sí | Dueño de `src/steg/eda/` y de la regla de higiene del EDA |
| leakage-auditor | sí | Dueño transversal de la ausencia de fuga; auditor obligatorio |
| feature-engineer | no | No toca `src/steg/eda/`; la Fase 3 no consume `bivariate.py` |
| model-trainer | no | Sin relación con entrenamiento |
| results-analyst | no | Sin relación con comparación ni con SHAP |
| academic-writer | no | Sin impacto en el manuscrito |

## Ronda 1 — propuestas (en paralelo, Opus)

### eda-analyst
- Diagnóstico: en el notebook, `y = client_train["target"]` y las columnas llegan con
  RangeIndex, sin `client_id`. Ninguna función puede verificar la partición.
- P-eda-1 Guardia `assert_train_partition(ids)`, aplicada en las 7 funciones que reciben
  etiqueta (`numeric_vs_target`, `numeric_table_vs_target`, `categorical_vs_target`,
  `target_rate_by_category`, `binary_flag_vs_target`, `mutual_information_ranking`,
  `fold_prevalence`), con `target` indexado por `client_id` y alineación de índices.
- P-eda-2 Tests `tests/test_eda_bivariate_guard.py` (depende de P-eda-1).
- P-eda-3 Adaptar `notebooks/01_eda.ipynb`, con las tablas bivariadas idénticas tras
  re-ejecutarlo (depende de P-eda-1).
- P-eda-4 Actualizar `steg-eda-protocol` (depende de P-eda-2 y P-eda-3).
- Riesgos: la guardia no distingue train de valid interno; hay que reindexar varias
  series derivadas; costo del chequeo en unas 40 llamadas con bootstrap.
- Objeción prevista: la guardia debería vivir en un módulo compartido.

### leakage-auditor
- Diagnóstico: igual. Una guardia basada en el prefijo sin `client_id` obligatorio
  sería cosmética.
- P-leak-1 Validador en `src/steg/data/` (`guards.py`), sin flag para desactivarlo.
  Falla con 100 % test, 1 fila de test entre N, NaN, vacío, `Train_` o ` train_`, y
  serie vacía.
- P-leak-2 Hacerlo cumplir en las 7 funciones; `rank_biserial` pasa a privada; se exige
  `values.index.equals(target.index)`.
- P-leak-3 Test parametrizado por **descubrimiento con `inspect`** de toda función
  pública con `target`/`y` en su firma, para que una función nueva sin guardia haga
  fallar el test.
- P-leak-4 Notebook con las tablas bivariadas idénticas.
- P-leak-5 Auditoría con entrada en `LEAKAGE_AUDIT.md`.
- Riesgos: el prefijo es una convención de Zindi (verificar que `load.py`/`clean.py` lo
  conservan); la guardia no detecta features de test reindexadas con ids de train (solo
  la alineación lo mitiga, y el docstring debe decirlo); `fold_prevalence` usa `iloc`.
- Objeciones: rechaza de antemano flags desactivables, validar solo si la columna
  existe o validar solo en el notebook. Propone otro dueño para P-leak-2/3.

## Consolidación del PM

| Punto | Resolución | Motivo |
|---|---|---|
| Dueño | **eda-analyst** en las 5 tareas | Es dueño de `src/steg/eda/` y del notebook. La independencia que busca leakage-auditor la dan el test por `inspect` (AC obligatorio) y su auditoría, no un cambio de dueño. feature-engineer entra como **auditor par** del validador y de los tests, porque va a reutilizar la guardia en la Fase 3 |
| Ubicación | `src/steg/data/guards.py` más la constante del prefijo en `src/steg/config.py` | Ambos agentes piden un módulo compartido |
| Test por `inspect` | Adoptado como AC de T003 | Cierra el hueco de "función nueva sin guardia" |
| Flags desactivables | Prohibidos (AC de T001/T002) | Objeción de leakage-auditor, aceptada |
| P-leak-5 | **Se elimina como tarea** | La auditoría es la Fase D del flujo (obligatoria en toda tarea). La entrada en `LEAKAGE_AUDIT.md` se hace por `/leak-check` cuando se certifique la Fase 1 |
| Entrada en `DECISIONS.md` | Se incluye en T005 | Pedido por leakage-auditor; cambia el contrato de las funciones |

### Plan borrador

| ID | Título | Dueño | Auditores | Depende de |
|---|---|---|---|---|
| T001 | Validador `assert_train_partition` en `src/steg/data/guards.py` | eda-analyst | leakage-auditor, feature-engineer | — |
| T002 | Hacer cumplir la guardia en las 7 funciones de `bivariate.py` | eda-analyst | leakage-auditor | T001 |
| T003 | Tests de la guardia, con descubrimiento por `inspect` | eda-analyst | leakage-auditor, feature-engineer | T002 |
| T004 | Adaptar el notebook con tablas bivariadas idénticas | eda-analyst | leakage-auditor | T002 |
| T005 | Actualizar `steg-eda-protocol` y `DECISIONS.md` | eda-analyst | leakage-auditor | T003, T004 |

## Ronda 2 — votación (en paralelo, Opus)

Desviación registrada: `leakage-auditor` salió del registro de agentes de la sesión tras
un error de YAML en su frontmatter (introducido por el PM al extender su `description`
y corregido de inmediato). El registro no lo recargó, así que votó un
`general-purpose` con `model: opus` que cargó `.claude/agents/leakage-auditor.md` como
instrucciones y quedó restringido por instrucción a solo lectura.

| Tarea | eda-analyst | leakage-auditor |
|---|---|---|
| T001 | MODIFY: pruebas propias del validador en `tests/test_data_guards.py`; test de que `load.py` y `clean.py` conservan el prefijo; mensaje con conteo y ejemplos; docstring con los dos límites | MODIFY: acepta solo `pd.Index` de strings (rechaza `RangeIndex`); excepción dedicada `PartitionLeakError(ValueError)`; casos `Train_`, ` train_`, `train`; constante en `config.py`; prueba sobre la carga real; sin flag |
| T002 | MODIFY: contrato de alineación por firma; rechaza `RangeIndex`; `fold_prevalence` valida `max(valid_idx) < len(target)` | MODIFY: `_rank_biserial` privada; la guardia corre antes de cualquier filtro (línea 90); alineación por firma; `target.index` único; rango de `valid_idx` |
| T003 | MODIFY: meta-aserción de igualdad con las 7 funciones; casos con ids `test_` y con desalineación; caso válido de solo train | MODIFY: igualdad con la lista de 7; casos adversariales; caso con ids reales (con skip explícito si no hay datos); regresión; agregar dependencia de T001 |
| T004 | MODIFY: orden de filas preservado; diff vacío en `bivariate_*.csv` y `evaluation_fold_prevalence.csv`; cualquier diferencia se documenta; la sección bivariada no referencia test | MODIFY: igualdad byte a byte; sin `try/except` alrededor de llamadas bivariadas; `y` indexada por `client_id` desde la carga; splits sobre el mismo orden |
| T005 | MODIFY: incluir `steg-data-contract` (prefijo como invariante); entrada en DECISIONS como cambio de contrato, en estado PROPUESTA; registrar como deuda la distinción train/valid | APPROVE, con la condición de que la entrada repita los límites y cite el test por `inspect` |

Condiciones cruzadas aceptadas por ambos: se elimina P-leak-5 como tarea, **con la
condición** de que la próxima certificación `/leak-check` de la Fase 1 cubra esta
guardia de forma explícita. Hay acuerdo en que el dueño sea eda-analyst, y leakage-auditor
retira su voto si se debilita el AC de igualdad contra la lista de T003.

## Discusión y resolución del PM

- **No hay posiciones enfrentadas.** Los cambios de las dos columnas se suman sin
  contradecirse. El plan final es su unión. No hace falta ronda 3.
- **Corrección técnica del PM:** ambos piden `git diff` para demostrar tablas
  idénticas, pero el repo no tiene ningún commit (`git log` vacío). Se reemplaza por un
  snapshot SHA-256 de las tablas tomado **antes** de ejecutar
  (`reports/tasks/002-baseline-sha256.txt`) y una comparación después.
- **Tensión con `tests/conftest.py`** ("ningún test depende de los CSV reales"). El caso
  con datos reales (T001 y T003) se acepta **solo** como test marcado
  `skipif(not data/raw)` con motivo explícito. `test_feature_dictionary.py` ya sienta ese
  precedente con un skip condicional.
- Mensaje de error: hasta 5 ids de ejemplo (se toma el máximo de las dos propuestas).

## Plan final (pendiente de aprobación del usuario)

| ID | Título | Dueño | Auditores | Prioridad | Depende de |
|---|---|---|---|---|---|
| T001 | Validador `assert_train_partition` + `PartitionLeakError` + `TRAIN_ID_PREFIX`, con sus tests | eda-analyst | leakage-auditor, feature-engineer | high | — |
| T002 | Hacer cumplir la guardia y la alineación por firma en las 7 funciones de `bivariate.py` | eda-analyst | leakage-auditor | high | T001 |
| T003 | Tests de la guardia en `bivariate.py`: `inspect` + igualdad con la lista, casos adversariales y regresión | eda-analyst | leakage-auditor, feature-engineer | high | T001, T002 |
| T004 | Adaptar `notebooks/01_eda.ipynb` con tablas bivariadas idénticas por SHA-256 | eda-analyst | leakage-auditor | medium | T002 |
| T005 | Actualizar `steg-eda-protocol` y `steg-data-contract`, más la entrada PROPUESTA en DECISIONS | eda-analyst | leakage-auditor | medium | T003, T004 |

Criterios de aceptación completos: en `002-guardia-eda-solo-train-tasks.md`, una vez
aprobado.

## Replanificaciones

### 2026-09-18 — MODIFY_TASK T003 (origen: auditoría de T002, ronda 1)
La auditoría de T002 (FAIL por F-leakage-2-1 MAJOR) mostró un hueco en la cobertura de
tests: ningún AC de T003 cubría splits pasados como generador. Se agrega a T003 el AC7:
generador con salida igual a la de la lista, y `valid_idx` booleano rechazado (F-leakage-2-2).
No cambia el alcance aprobado ni las dependencias, así que no requiere reconsulta al usuario.
Se modificó la ficha y el work item PROYE-17 (sin crear un plan paralelo).
