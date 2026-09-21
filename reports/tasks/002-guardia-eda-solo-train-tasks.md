# 002 — Guardia "EDA bivariado solo sobre train": tareas

Fuente de verdad ejecutable. Planificación y consenso en
`002-guardia-eda-solo-train-planning.md`; veredictos en `002-guardia-eda-solo-train-audit.md`.
Plan aprobado por el usuario el 2026-09-18. Módulo de Plane: `002-guardia-eda-solo-train`.
Snapshot de referencia de tablas (para T004): `002-baseline-sha256.txt`, tomado antes de
cualquier cambio.

### T001 — Validador `assert_train_partition` + `PartitionLeakError` + `TRAIN_ID_PREFIX`, con sus tests
- Estado: DONE
- Plane: PROYE-15
- Requirement: 002-guardia-eda-solo-train
- Agente asignado: eda-analyst
- Auditores: leakage-auditor, feature-engineer
- Prioridad: high
- Depende de: —
- Descripción: crear `src/steg/data/guards.py` con `assert_train_partition(index: pd.Index) -> None`
  y la excepción `PartitionLeakError(ValueError)`, y la constante `TRAIN_ID_PREFIX = "train_"`
  en `src/steg/config.py`. Es la pieza compartida que hará cumplir la regla de higiene del EDA
  (y que la Fase 3 podrá reutilizar).
- Criterios de aceptación:
  - AC1: acepta solo un `pd.Index` de strings. Lanza `PartitionLeakError` si es
    `RangeIndex` o si no es de strings, con 100 % de ids test, con 1 fila `test_` entre N,
    con NaN, si está vacío y con los prefijos `Train_`, ` train_` y `train` (sin guion bajo).
    No normaliza en silencio.
  - AC2: el mensaje de error informa cuántas filas fallaron y muestra hasta 5 ids de
    ejemplo.
  - AC3: no hay parámetro, variable de entorno ni flag que lo desactive.
  - AC4: el docstring declara los dos límites: no distingue train de valid interno y no
    detecta features de test reindexadas con ids de train (lo mitiga la alineación de T002).
  - AC5: `tests/test_data_guards.py` cubre AC1-AC3 con datos sintéticos y además trae un
    test sobre la carga real (`load.py` + `clean.py`): el 100 % de los `client_id` de train
    pasa y los de test fallan. Ese test lleva `skipif` con un motivo explícito si falta
    `data/raw/`.
  - AC6: `pytest` completo en verde y `ruff check src tests` sin errores nuevos.
- Contexto relevante: `.claude/skills/steg-data-contract/SKILL.md` (formato de
  `client_id`), `src/steg/data/load.py`, `src/steg/data/clean.py`, `tests/conftest.py`,
  `tests/test_feature_dictionary.py` (precedente de skip condicional).
- Historial:
  - 2026-09-18 TODO — creada (PM)
  - 2026-09-18 READY — sin dependencias (PM)
  - 2026-09-18 IN_PROGRESS — ronda 1 (eda-analyst, movido en Plane por el agente)
  - 2026-09-18 READY_FOR_AUDIT — ronda 1 (eda-analyst; comentario Plane c54e7833)
  - 2026-09-18 AUDIT ronda 1 — leakage-auditor PASS (3 MINOR), feature-engineer PASS
  - 2026-09-18 DONE — quality gate PASS (PM)
- Evidencia ronda 1 (eda-analyst): `src/steg/data/guards.py` (nuevo), `src/steg/config.py`
  (`TRAIN_ID_PREFIX`), `tests/test_data_guards.py` (33 tests, incluye carga real sin skip
  porque `data/raw/` existe). `pytest -q` → 49 passed, 1 skipped (feature_dictionary,
  preexistente). `ruff check src tests` → 5 errores preexistentes (load.py:83,193;
  profile.py:123,128; test_split_anti_leakage.py:34); los 3 archivos tocados → limpio. ruff
  no estaba instalado; el agente lo instaló en temp de sesión. Decisión propia: también
  rechaza `train_` sin sufijo.

### T002 — Hacer cumplir la guardia y la alineación por firma en las 7 funciones de `bivariate.py`
- Estado: DONE
- Plane: PROYE-16
- Requirement: 002-guardia-eda-solo-train
- Agente asignado: eda-analyst
- Auditores: leakage-auditor
- Prioridad: high
- Depende de: T001
- Descripción: las 7 funciones públicas que reciben etiqueta (`numeric_vs_target`,
  `numeric_table_vs_target`, `categorical_vs_target`, `target_rate_by_category`,
  `binary_flag_vs_target`, `mutual_information_ranking`, `fold_prevalence`) llaman a
  `assert_train_partition` sobre el índice de la etiqueta y exigen alineación.
- Criterios de aceptación:
  - AC1: la guardia corre sobre `target.index` (o `y.index`) **antes** de cualquier filtro
    o máscara (hoy, `bivariate.py:90`).
  - AC2: alineación estricta por firma: `values.index.equals(target.index)` en
    `numeric_vs_target`, `categorical_vs_target`, `target_rate_by_category` y
    `binary_flag_vs_target`; `df.index.equals(target.index)` en `numeric_table_vs_target`;
    `X.index.equals(y.index)` en `mutual_information_ranking`.
  - AC3: el índice de la etiqueta tiene que ser único; si no, `PartitionLeakError`.
  - AC4: `fold_prevalence` aplica la guardia y además valida que todo `valid_idx` esté en
    `[0, len(target))`.
  - AC5: `rank_biserial` pasa a `_rank_biserial`, ajustando sus llamadas internas.
  - AC6: el docstring del módulo (líneas 8-14) deja de decir "la garantía la pone quien
    llama" y describe el contrato nuevo y sus límites. No hay flag de desactivación.
  - AC7: con datos válidos de train, las salidas numéricas no cambian. `pytest` en verde.
- Contexto relevante: `src/steg/eda/bivariate.py`, `src/steg/data/guards.py` (T001),
  `.claude/skills/steg-eda-protocol/SKILL.md`.
- Historial:
  - 2026-09-18 TODO — creada (PM)
  - 2026-09-18 READY — T001 DONE (PM)
  - 2026-09-18 IN_PROGRESS — ronda 1 (eda-analyst)
  - 2026-09-18 READY_FOR_AUDIT — ronda 1 (eda-analyst; comentario Plane 7e2e722b, primer intento bloqueado por WAF 403 y reenviado en texto plano)
- Evidencia ronda 1 (eda-analyst): solo `src/steg/eda/bivariate.py`. Helpers `_check_label`
  (guardia + unicidad) y `_check_aligned` (Index.equals) como primera sentencia de las 7
  funciones; `fold_prevalence` valida dtype entero y rango de `valid_idx`; `_rank_biserial`
  privada; docstring nuevo con contrato y límites. AC7: script `ac7_compare.py`
  (scratchpad) contra la copia previa `bivariate_old.py` sobre train real → 24/24 idénticas
  (`check_exact=True`), con n_boot 100/300 y n_permutations 3. `pytest -q` → 49 passed,
  1 skipped. `ruff check bivariate.py` → limpio.
  - 2026-09-18 AUDIT ronda 1 — leakage-auditor FAIL: F-leakage-2-1 MAJOR (fold_prevalence agota splits si es generador), F-leakage-2-2 MINOR
  - 2026-09-18 CHANGES_REQUESTED — redespacho ronda 2 (PM)
  - 2026-09-18 IN_PROGRESS — ronda 2 (eda-analyst)
  - 2026-09-18 READY_FOR_AUDIT — ronda 2 (eda-analyst)
- Evidencia ronda 2 (eda-analyst): F-leakage-2-1 → `splits = list(splits)` tras
  `_check_label`; cero folds → `PartitionLeakError`; tipo `Iterable`; docstrings actualizados.
  F-leakage-2-2 → sin cambio de conducta, documentado (usar `np.flatnonzero(mask)`).
  `ac7_compare_r2.py` → 28/28 idénticas, con generador (`grouped_kfold_splits` sin `list`,
  `GroupKFold.split`) → (5,6) como antes. `pytest -q` → 49 passed, 1 skipped. `ruff check` y
  `ruff format --check` → OK (format reflowó la firma de `binary_flag_vs_target`, solo espacios).
  - 2026-09-18 AUDIT ronda 2 — leakage-auditor PASS; F-leakage-2-1 y 2-2 LEVANTADOS; F-leakage-2-3 MINOR (CRLF)
  - 2026-09-18 DONE — quality gate PASS (PM)

### T003 — Tests de la guardia en `bivariate.py`: `inspect` + igualdad con la lista, casos adversariales y regresión
- Estado: READY
- Plane: PROYE-17
- Requirement: 002-guardia-eda-solo-train
- Agente asignado: eda-analyst
- Auditores: leakage-auditor, feature-engineer
- Prioridad: high
- Depende de: T001, T002
- Descripción: `tests/test_eda_bivariate_guard.py` hace que una función nueva sin guardia
  no pueda entrar sin que falle el test.
- Criterios de aceptación:
  - AC1: descubre por `inspect` las funciones públicas de `steg.eda.bivariate` con
    `target`, `y` o `X`+`y` en la firma, y compara ese conjunto **por igualdad** con la
    lista esperada de 7.
  - AC2: cada función descubierta lanza `PartitionLeakError` con ids 100 % test, con 1 fila
    `test_` entre N, con `RangeIndex`, con índice duplicado y con índices desalineados.
  - AC3: cada función funciona con un fixture válido de solo train.
  - AC4: hay un test de regresión: con train válido, cada función devuelve exactamente lo
    mismo que la implementación previa (valores de referencia fijados en el test).
  - AC5: hay un caso con ids reales de `client_test` vía `load.py`, con `skipif` y motivo
    explícito si falta `data/raw/`.
  - AC6: `pytest` en verde.
  - AC7 (replan 2026-09-18, de F-leakage-2-1/2-2): `fold_prevalence` con splits como
    **generador** (`grouped_kfold_splits` sin `list`) da la misma salida que con lista; con
    `valid_idx` booleano lanza `PartitionLeakError` (rechazo documentado, no regresión).
- Contexto relevante: `tests/conftest.py`, `src/steg/eda/bivariate.py`,
  `src/steg/data/guards.py`.
- Historial:
  - 2026-09-18 TODO — creada (PM)
  - 2026-09-18 REPLAN — se agrega AC7 por findings F-leakage-2-1/2-2 de la auditoría de T002 (PM)
  - 2026-09-18 READY — T001 y T002 DONE (PM)

### T004 — Adaptar `notebooks/01_eda.ipynb` con tablas bivariadas idénticas por SHA-256
- Estado: READY
- Plane: PROYE-18
- Requirement: 002-guardia-eda-solo-train
- Agente asignado: eda-analyst
- Auditores: leakage-auditor
- Prioridad: medium
- Depende de: T002
- Descripción: el notebook pasa hoy las series con `RangeIndex`. Hay que reindexarlas por
  `client_id` para cumplir el contrato nuevo, sin cambiar ningún resultado.
- Criterios de aceptación:
  - AC1: `y` y las series derivadas (`client_features`, `client_train_mix`, `tarif_mode`,
    ...) quedan indexadas por `client_id` desde la carga, con `set_index` sin reordenar
    filas.
  - AC2: el notebook se re-ejecuta de punta a punta sin errores
    (`jupyter nbconvert --execute` o equivalente).
  - AC3: los SHA-256 de `reports/tables/bivariate_*.csv` y
    `reports/tables/evaluation_fold_prevalence.csv` coinciden con
    `reports/tasks/002-baseline-sha256.txt`. Si hay alguna diferencia inevitable, se
    documenta por columna con su magnitud; no se acepta en silencio.
  - AC4: ninguna llamada bivariada queda envuelta en `try/except`, y la sección bivariada
    no referencia `client_test` ni `invoice_test`.
  - AC5: los `splits` de `fold_prevalence` se generan sobre el mismo orden de `target` que
    se le pasa.
  - AC6: la evidencia pide explícitamente `/leak-check` de la Fase 1, que debe cubrir esta
    guardia.
- Contexto relevante: `notebooks/01_eda.ipynb` (sección bivariada, celdas ~45-80),
  `002-baseline-sha256.txt`.
- Historial:
  - 2026-09-18 TODO — creada (PM)
  - 2026-09-18 READY — T002 DONE (PM)

### T005 — Actualizar `steg-eda-protocol` y `steg-data-contract`, más la entrada PROPUESTA en DECISIONS
- Estado: TODO
- Plane: PROYE-19
- Requirement: 002-guardia-eda-solo-train
- Agente asignado: eda-analyst
- Auditores: leakage-auditor
- Prioridad: medium
- Depende de: T003, T004
- Descripción: dejar la documentación normativa alineada con el código.
- Criterios de aceptación:
  - AC1: `steg-eda-protocol` dice que la regla de higiene la hace cumplir el código y cita
    `assert_train_partition` y `tests/test_eda_bivariate_guard.py`.
  - AC2: `steg-data-contract` declara el prefijo `train_`/`test_` de `client_id` como
    invariante, con referencia a `TRAIN_ID_PREFIX`.
  - AC3: `reports/DECISIONS.md` tiene una entrada de cambio de contrato de ingeniería,
    marcada PROPUESTA, que repite los dos límites, cita el test por `inspect` y registra
    como deuda la distinción train/valid interno.
- Contexto relevante: las dos skills, `reports/DECISIONS.md`.
- Historial:
  - 2026-09-18 TODO — creada (PM)
