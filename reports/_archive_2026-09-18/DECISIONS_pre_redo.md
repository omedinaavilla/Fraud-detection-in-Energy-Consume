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
| Métrica primaria y secundarias del proyecto | Fin de Fase 2 | PENDIENTE |
| Si hay o no un problema de desbalance, y qué hacer al respecto | Fin de Fase 2 | PENDIENTE |
| Punto de operación / umbral, y si tiene sentido evaluar "@k" | Fin de Fase 2 | PENDIENTE |
| Estratificación o no de los folds | Fin de Fase 2 | PENDIENTE |
| Cómo codificar categóricas de alta cardinalidad | Fase 3 | PENDIENTE |
| Qué hacer con clientes con muy pocas facturas | Fase 3 | PENDIENTE |
| Ventana temporal del historial usada para construir variables | Fase 3 | PENDIENTE |
| Parámetros de costo del análisis de inspección | Fase 7 | PENDIENTE |

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

## PROPUESTAS de la Fase 1 (EDA) — 2026-09-18

Estado: **PROPUESTA**. Ninguna está decidida. La evidencia procede del análisis
exploratorio documentado en `notebooks/01_eda.ipynb` y de las tablas que esa ejecución
escribe en `reports/tables/`; el desarrollo completo de cada una está en
`reports/EDA/04_implicaciones.md`.

### PROPUESTA — Métrica primaria

El clasificador trivial acierta el 94.42 % (`evaluation_metric_baselines.csv`),
así que la exactitud queda fuera. Línea base de PR-AUC: 5.58 %.
La variable con más señal alcanza |rank-biserial| 0.415
(`exp_n_counters`, `bivariate_numeric_target.csv`), de modo que el ordenamiento tendrá
solapamiento fuerte entre clases.
Alternativas: (A) PR-AUC primaria — sensible a la zona de alta precisión, pero depende de
la prevalencia y no es comparable entre subgrupos ni con el reto; (B) ROC-AUC primaria —
ancla externa (leaderboard ~0,86) y comparabilidad, pero promedia umbrales que ninguna
operación usaría; (C) una métrica @k primaria — fiel al uso operativo, pero exige fijar k
sin conocer la capacidad de inspección.

### PROPUESTA — Desbalance

7.566 positivos de 135.493 (5.58 %),
16.9 negativos por positivo, y entre 1486 y
1549 positivos por pliegue con la validación cruzada agrupada por
cliente (`evaluation_fold_prevalence.csv`, que recoge también el esquema estratificado).
Hay desbalance, sin escasez: sobre el pliegue de validación más pequeño de los dos
esquemas, el de 1442 positivos, el error estándar relativo de una proporción
estimada es del 2.6 %.
Alternativas: (A) ninguna técnica, ajustar umbral al final — riesgo de que un modelo muy
regularizado ignore la minoritaria, verificable en Fase 4; (B) `class_weight` /
`scale_pos_weight` — barato, pero descalibra y obliga a recalibrar antes de la Fase 7;
(C) remuestreo — sin escasez que resolver, debe ir dentro del fold, y SMOTE interpola
sobre variables con sesgo ~500 (`univariate_numeric.csv`).

### PROPUESTA — Punto de operación y "@k"

`evaluation_at_k_reference.csv`: una lista de 5.000 clientes (3,7 % de la base) contiene
279 fraudes al azar y hasta 5.000 con orden perfecto, recall techo
66.1 %.
Alternativas: (A) reportar la curva @k para varios k sin fijar umbral — honesto, pero sin
número único citable; (B) umbral que maximiza F1 — reproducible, pero pondera precisión y
recall por igual sin razón operativa; (C) aplazar el umbral a la Fase 7 y derivarlo del
costo-beneficio — lo más defendible, pero exige asumir parámetros de coste y su análisis
de sensibilidad.

### PROPUESTA — Estratificación de los folds

Con 5 folds agrupados por `client_id`, la desviación de la prevalencia entre
pliegues es 0.0873 puntos porcentuales frente a 0.1395
esperados por azar binomial; `StratifiedGroupKFold` la baja a 0.1673
(`evaluation_fold_prevalence.csv`, `fig_eval_fold_prevalence.png`).
Alternativas: (A) `GroupKFold` — ya implementado y probado, pero determinista y sin
`random_state`, lo que impide repetir la CV con otra semilla; (B) `StratifiedGroupKFold`
con `shuffle=True` y SEED=42 — homogeneidad garantizada y semillas repetibles, pero
añade una restricción que la evidencia no reclama y obliga a revisar el test anti-fuga.
Lo que impide la fuga entre folds es la agrupación por cliente, que ambos cumplen.

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
