# 002 — Guardia "EDA bivariado solo sobre train": log de auditoría

Log solo de anexado, escrito por el PM. De cada veredicto se transcriben literales el
veredicto, el estado de cada AC y los findings (ID, Severity, Evidence, Required Change). El
texto descriptivo de la verificación puede quedar condensado. Formato y reglas en `.claude/skills/steg-plane-workflow/SKILL.md`,
Fases D-F.

## T001 — ronda 1

```
AUDIT T001 · ronda 1 · leakage-auditor · 2026-09-18
Veredicto: PASS
Criterios de aceptación:
- AC1: PASS — guards.py:88-113 exige pd.Index; rechaza MultiIndex, RangeIndex, vacío; valida
  cada elemento con _is_train_id (líneas 39-44: isinstance str, startswith "train_", sufijo no
  vacío) sin normalizar. Batería adversarial propia (17 entradas no cubiertas por los tests):
  CategoricalIndex con test_/NaN, bytes, guion bajo de ancho completo, espacio de ancho cero
  inicial, RangeIndex(0), string[pyarrow] con <NA>, IntervalIndex, None, strings numéricos →
  todas rechazadas; CategoricalIndex train puro y np.str_ → aceptados. Todo correcto.
- AC2: PASS — _raise (líneas 28-35) "N de M filas fallaron" + examples[:5] con repr;
  test_message_reports_count_and_at_most_five_examples y
  test_message_with_fewer_than_five_failures_shows_all.
- AC3: PASS — firma (index) única; sin environ/getenv/os; _MAX_EXAMPLES solo afecta al
  mensaje; test_has_no_parameter_to_disable_it y test_has_no_environment_switch.
- AC4: PASS — docstring líneas 64-75 con ambos límites; test_docstring_declares_both_limits.
- AC5: PASS — sintéticos + test real con load_raw_data/clean_client: 100 % train pasa
  (columna, set_index, invoice_train únicos); client_test e invoice_test fallan (conteo =
  len); train + 1 test falla (conteo 1); skipif con motivo; corrió, no se saltó.
- AC6: PASS — pytest -q → 49 passed, 1 skipped; test_data_guards → 33 passed, 0 skips;
  ruff check src tests → 5 errores idénticos a los declarados (load.py:83 E501, :193 UP017;
  profile.py:123 UP017, :128 E501; test_split_anti_leakage.py:34 B007); archivos tocados →
  "All checks passed!". Repo sin commits: preexistencia soportada por mtimes, no por git.
- Evidencia del ejecutor: coincide.
Findings:
- F-leakage-1-1 | MINOR | Evidence: pd.Index(["train_ "]), (["train_\n"]), (["train_C_1 "])
  se aceptan; el contrato fija train_Client_*. No es fuga (el prefijo es train). | Required
  Change: opcional/no bloqueante — endurecer _is_train_id (strip o regex ^train_Client_\d+$)
  en un requirement posterior.
- F-leakage-1-2 | MINOR | Evidence: pd.Index(["train_C_1","train_C_1"]) se acepta. Fuera de
  AC; no es fuga de partición. | Required Change: ninguno en T001; T002 debe verificar
  is_unique por su cuenta (ya es su AC3).
- F-leakage-1-3 | MINOR | Evidence: ruff format --diff reformatearía config.py:29 y un
  bloque de guards.py:109. AC6 solo exige ruff check. | Required Change: opcional.
Revisado: guards.py, test_data_guards.py, config.py completos; steg-data-contract; data/raw;
clean.py (client_id); pytest completo y de la tarea; ruff check global y por archivo; ruff
format --diff; script adversarial propio en %TEMP% fuera del repo. Sin modificar archivos
ni tocar Plane.
```

```
AUDIT T001 · ronda 1 · feature-engineer · 2026-09-18
Veredicto: PASS
Criterios de aceptación:
- AC1: PASS — pytest tests/test_data_guards.py (33 passed) cubre RangeIndex, no-string,
  100% test, 1 test entre N, NaN/None/pd.NA, vacío, Train_, ' train_', trainClient_0,
  train a secas y train_ solo-prefijo; confirmé además que no normaliza (mensaje conserva
  repr del id original).
- AC2: PASS — mensaje reporta N de M filas fallaron y hasta 5 ids; verificado con >5 y <5.
- AC3: PASS — firma solo (index) (TypeError con strict=False); sin environ/getenv;
  variables de entorno simuladas no la desactivan.
- AC4: PASS — docstring contiene literalmente "valid interno" y "reindexadas con ids de train".
- AC5: PASS — sintéticos + test_real_load_train_ids_pass_and_test_ids_fail con skipif
  explícito; corrió sin skip (data/raw/ presente) y pasó.
- AC6: PASS — pytest -q → 49 passed, 1 skipped (preexistente). ruff check src tests (v0.14
  instalado ad hoc en el entorno de auditoría, sin tocar el repo) → 5 errores
  preexistentes; cero en guards.py, config.py, test_data_guards.py. Coincide con la evidencia.
Verificación adicional (reutilización en Fase 3, no AC formal): índice de
groupby("client_id") (object, 135k ids, 30 ms); CategoricalIndex (incl. 1 test_ → falla
bien); string[pyarrow] con pd.NA → falla bien; índice con otro name → indiferente; 600k
filas ~120 ms. API apta tal cual para Fase 3.
Findings: ninguno.
Revisado: guards.py, config.py, test_data_guards.py, ficha T001; pytest de la tarea y
completo; ruff check; scripts ad hoc con groupby/CategoricalIndex/string[pyarrow]/índice
renombrado a escala 135k/600k.
```

### Quality gate T001 — 2026-09-18

| Chequeo | Resultado |
|---|---|
| Acceptance Criteria (AC1-AC6) | PASS (ambos auditores) |
| leakage-auditor | PASS (3 MINOR registrados, no bloqueantes) |
| feature-engineer (par) | PASS |
| Dependencies | SATISFIED (ninguna) |
| Tests | verdes (49 passed, 1 skipped preexistente) |
| **QUALITY GATE** | **PASS → DONE** |

Nota del PM: F-leakage-1-1 (endurecer el formato de `client_id`) queda como deuda
candidata para un requirement posterior; F-leakage-1-2 ya está cubierto por el AC3 de T002.

## T002 — ronda 1

```
AUDIT T002 · ronda 1 · leakage-auditor · 2026-09-18
Veredicto: FAIL
Criterios de aceptación:
- AC1: PASS — _check_label es la primera sentencia de las 7 funciones (bivariate.py:151,
  :200, :220, :245, :279, :327, :396); la antigua :90 (mask = values.notna()) queda después, en :153.
- AC2: PASS — _check_aligned usa features.index.equals(target.index) (:95), aplicado a values
  (:152, :221, :246), flag (:280), df (:201), X vs y (:328). Adversarial: mismos ids
  permutados, values con ids extra, ndarray sin índice, índice dtype string vs object →
  todos PartitionLeakError. Sin reindex/merge/.values previos al chequeo.
- AC3: PASS — _check_label lanza PartitionLeakError si not target.index.is_unique (:77-82).
- AC4: PASS (en su letra) — guardia (:396) + dtype entero + rango [0, len) (:398-408);
  [-1,3], [0,40], [0.5] lanzan. Regresión introducida en este bloque: ver F-leakage-2-1.
- AC5: PASS — _rank_biserial (:109), llamadas internas :162 y :169; sin definición pública.
- AC6: PASS — diff vs bivariate_old.py confirma retiro de "la garantía la pone quien llama";
  contrato en 4 puntos + límites; sin flag, env ni función pública nueva que salte la guardia.
- AC7: FAIL — ac7_compare.py compara lo que dice (24/24), pytest 49 passed 1 skipped, ruff
  limpio; pero existe una entrada válida de train cuya salida cambia y que el script no
  ejercita porque solo pasa list(...) (F-leakage-2-1).
Findings:
- F-leakage-2-1 | MAJOR | Evidence: fold_prevalence itera splits dos veces (bucle de
  validación bivariate.py:398 y bucle de cómputo :410). Con un iterador, el primer bucle lo
  consume y la función devuelve un DataFrame vacío sin error. steg.data.split.
  grouped_kfold_splits es un generador (-> Iterator, yield from splitter.split), igual que
  GroupKFold.split/StratifiedGroupKFold.split. Reproducido en scratchpad/adv_audit.py:
  old.fold_prevalence(y, gen()) → (5, 6); new.fold_prevalence(y, gen()) → (0, 0);
  new.fold_prevalence(y, GroupKFold(5).split(y, y, groups=ids)) → (0, 0). El notebook hoy
  envuelve con list(...) (01_eda.ipynb ~6573/6578), así que las tablas actuales no cambian,
  pero es un cambio silencioso de comportamiento y la tabla de prevalencia por fold es
  evidencia del protocolo de evaluación. | Required Change: materializar una sola vez al
  entrar — splits = list(splits) inmediatamente después de _check_label(target), antes de
  validar y de computar. Para T003: caso con generador (grouped_kfold_splits sin list) que
  exija salida idéntica a la previa; recomendable además exigir splits no vacío para que un
  resultado de cero folds nunca salga en silencio.
- F-leakage-2-2 | MINOR | Evidence: fold_prevalence ahora rechaza valid_idx booleano, que
  iloc aceptaba antes (old → (1, 6), new → PartitionLeakError). Fail-safe y documentado en
  el docstring (:392-394). | Required Change: dejarlo explícito en tests de T003 y en la
  nota de contrato de T005.
Revisado: diff completo bivariate_old.py → bivariate.py; guards.py (T001); las 7 funciones
(crosstab, target.loc[idx], target[f], y.to_numpy() — todo tras alineación estricta con
índice único); pytest -q (49/1), ruff limpio, neg.py OK, ac7_compare.py 24/24 (verificado
qué compara); adv_audit.py propio: generador, máscara booleana, ndarray, índice permutado,
índice con ids extra, CategoricalIndex, test_* mezclado, dtype string, valid_idx uint64,
lista vacía, etiqueta con NaN. Único cambio de salida con datos válidos: generador.
valid_idx vacío → ZeroDivisionError preexistente (verificado en la versión antigua), fuera
de alcance.
```

Resultado ronda 1: **FAIL** (1 MAJOR) → CHANGES_REQUESTED. Se redespacha a eda-analyst,
ronda 2.

## T002 — ronda 2

```
AUDIT T002 · ronda 2 · leakage-auditor · 2026-09-18
Veredicto: PASS
Findings previos:
- F-leakage-2-1: LEVANTADO — splits = list(splits) justo tras _check_label(target); luego
  "if not splits: raise PartitionLeakError", validación y cómputo sobre la misma lista.
  adv_r2.py propio: GroupKFold(5).split → (5, 6) (antes (0, 0)); StratifiedGroupKFold.split
  → (5, 6) = old; map/tupla → (5, 6). ac7_compare_r2.py (datos reales): generador
  grouped_kfold_splits sin list, GroupKFold.split y lista → idénticos a old con lista
  (check_exact=True). Cero folds ([] y generador vacío) → PartitionLeakError. Índice
  inválido → falla la guardia antes de consumir el generador (RangeIndex + generador
  instrumentado: 0 elementos consumidos).
- F-leakage-2-2: LEVANTADO en lo que toca a T002 — máscara booleana sigue lanzando
  PartitionLeakError y el docstring lo dice, con la alternativa np.flatnonzero(mask).
  Quedan pendientes, fuera de T002, el test (T003 AC7) y la nota de contrato (T005).
Criterios de aceptación:
- AC1: PASS — primera sentencia tras el docstring (inspect): _check_label(target) en 6/7,
  _check_label(y, "y") en mutual_information_ranking; mask = values.notna() después.
- AC2: PASS — _check_aligned (features.index.equals(target.index)) sobre values/flag/df/X.
  Diff --strip-trailing-cr vs bivariate_old.py: el reformateo solo tocó la firma de
  binary_flag_vs_target; ningún cambio de lógica fuera de T002.
- AC3: PASS — índice ["train_Client_1"]*2 → PartitionLeakError ("1 client_id duplicados").
- AC4: PASS — guardia antes de materializar; dtype entero; [-1, 3] y [0, 200] con n=200
  lanzan; valid_idx lista Python aceptada → (1, 6); target RangeIndex / test_* lanzan.
- AC5: PASS — hasattr(new, "rank_biserial") False; _rank_biserial en las 2 llamadas
  internas; sin referencias públicas en src/ ni tests/.
- AC6: PASS — contrato en 4 puntos (el 4 actualizado: materialización, ≥1 fold, rechazo
  bool) + límites + sin flag/parámetro/env; la frase antigua ya no aparece.
- AC7: PASS — ac7_compare_r2.py ejecutado por el auditor: 28/28 idénticas (con RangeIndex y
  client_id, generadores incluidos); pytest -q 49 passed 1 skipped; ruff 0.16.8 check
  "All checks passed!", format --check "1 file already formatted".
Findings:
- F-leakage-2-3 | MINOR | Evidence: src/steg/eda/bivariate.py quedó con CRLF en todas sus
  líneas (443/443); el resto de .py de src/steg/eda, src/steg/data y tests/ usan LF, igual
  que bivariate_old.py (0 CRLF). Un diff normal marca todo el archivo como cambiado; la
  evidencia "solo espacios" del reformateo solo se sostiene ignorando CR. Sin impacto en
  comportamiento ni en AC. | Required Change: devolver el archivo a LF (p. ej. ruff format
  con line-ending lf o fijar line-ending = "lf" en [tool.ruff.format] en tarea aparte).
Revisado: diff completo old→new (--strip-trailing-cr); ficha y evidencia ronda 2; pytest
-q; ruff check y format --check; ac7_compare_r2.py (ejecutado y revisado); adv_r2.py
propio (GroupKFold/StratifiedGroupKFold generadores, map, tupla, lista vacía, generador
vacío, máscara bool, negativos, fuera de rango, valid_idx lista, RangeIndex, test_*,
duplicado, splits=None → TypeError igual que old, orden guardia-vs-consumo); inspect de la
primera sentencia de las 7; alcance en disco (solo bivariate.py modificado en ronda 2).
Nota para T004: 01_eda.ipynb (~6582-6583) llama biv.fold_prevalence(y, …) con RangeIndex;
hay que adaptarlo.
```

### Quality gate T002 — 2026-09-18

| Chequeo | Resultado |
|---|---|
| Acceptance Criteria (AC1-AC7) | PASS (ronda 2) |
| leakage-auditor | PASS en ronda 2. FAIL de ronda 1 (F-leakage-2-1 MAJOR) levantado explícitamente |
| Findings CRITICAL/MAJOR abiertos | 0 |
| Dependencies | SATISFIED (T001 DONE) |
| Tests | verdes (49 passed, 1 skipped preexistente) |
| **QUALITY GATE** | **PASS → DONE** (2 rondas de auditoría) |

Nota del PM: F-leakage-2-3 (bivariate.py en CRLF) es MINOR. Se le encarga a T003 como
condición de su despacho: normalizar a LF solo `bivariate.py`, sin tocar la lógica.
