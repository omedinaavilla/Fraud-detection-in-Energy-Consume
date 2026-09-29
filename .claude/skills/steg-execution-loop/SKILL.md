---
name: steg-execution-loop
description: Reemplaza el flujo Scrum con PM del 2026-09-18 y elimina el gate de auditoría obligatoria del 2026-09-18 (segunda revisión). Define cómo cada agente ejecutor de STEG (eda-analyst, feature-engineer, model-trainer, results-analyst, academic-writer) planifica, ejecuta y cierra su propia tarea sin una capa de coordinación intermedia ni auditoría previa obligatoria, y cómo mantiene actualizado el Planner vivo (reports/PLANNER.md) y su propio work item en Plane. Úsala en cualquier tarea de desarrollo del proyecto y al actualizar reports/PLANNER.md.
---

# Flujo de ejecución directa — STEG

Rige desde 2026-09-18 (segunda revisión del mismo día) y reemplaza el flujo Scrum con
Product Manager (`reports/DECISIONS.md`, entrada "Fin del flujo con PM"). Una revisión
posterior del mismo día (`reports/DECISIONS.md`, entrada "Se elimina el gate de
auditoría obligatoria") quitó además la auditoría previa obligatoria: ningún ejecutor
espera un veredicto ajeno para cerrar su propia tarea. No existe un rol de
planificación, reparto o coordinación entre agentes. Cada agente ejecutor es
responsable directo de planificar, realizar y cerrar su propio trabajo.

## Roles

| Rol | Quién lo cumple | Qué hace | Qué NO hace |
|---|---|---|---|
| Ejecutor | `eda-analyst`, `feature-engineer`, `model-trainer`, `results-analyst`, `academic-writer`, cada uno en su fase | Analiza la tarea, planifica los pasos, ejecuta, analiza resultados, decide, documenta en el Planner, gestiona su propio work item en Plane de punta a punta hasta Done | No coordina a otros agentes, no cierra tareas de otro, no decide el trabajo de otro |
| Auditor (bajo pedido) | `leakage-auditor` | Revisa lo que se le pida explícitamente — una fase completa (`/leak-check`) o una tarea puntual — buscando fuga, cálculos incorrectos e incoherencias. Emite PASS/FAIL o BLOQUEADO/APROBADO | No es un paso obligatorio del ciclo de ninguna tarea, no planifica, no dirige el proyecto, no implementa correcciones, no toca Plane |
| Agente Investigador | `literature-researcher` | Investigación inicial de literatura (una sola vez, ver `.claude/agents/literature-researcher.md`) | No se consulta en cada tarea posterior |
| Agente EDA | `eda-analyst` | Análisis exploratorio de los datos, sin cambios respecto a como ya funciona | — |

El hilo principal (la sesión de Claude Code que el usuario usa directamente) despacha a
estos agentes con los slash commands de fase (`/audit`, `/eda`, `/decide`, `/features`,
`/train`, `/evaluate`, `/explain`, `/inspect`, `/leak-check`, `/paper`,
`/research`) y, cuando un ejecutor entrega evidencia, despacha al Auditor. Esto **no** es
un rol de coordinación: es la única forma técnica de invocar a un agente distinto de uno
que ya está corriendo, porque los subagentes no pueden convocar a otros agentes. El hilo
principal no consolida propuestas, no vota, no arma backlog ni decide por su cuenta a
quién asignar una tarea nueva: el dueño de cada fase ya está fijado en la tabla de arriba
y en `contextPrompt.md` sección 6.

## El ciclo de cada tarea

**Planificar → Ejecutar → Analizar → Decidir → Documentar → Continuar.**

1. **Analizar.** Qué pide la tarea actual, qué existe ya en disco que sea relevante
   (código, artefactos, entradas previas del Planner y de `reports/DECISIONS.md`).
2. **Planificar.** Los pasos concretos para esta tarea. No hace falta un plan rígido de
   todo el proyecto: solo el siguiente tramo de trabajo, a la luz de lo que ya se sabe.
3. **Ejecutar.** Implementar, correr pruebas, generar artefactos en disco. Nunca solo en
   conversación.
4. **Analizar resultados.** Qué se encontró y qué significa, con la evidencia concreta
   (archivo, tabla, cifra, test) que lo respalda.
5. **Decidir.** Qué se hace a partir de ese hallazgo. Si la decisión es de diseño de
   investigación (afecta el protocolo, la metodología o el alcance), se presenta al
   usuario con alternativas y riesgo antes de aplicarla — igual que ya exige
   `contextPrompt.md` sección 3 para las decisiones diferidas.
6. **Documentar.** Actualizar `reports/PLANNER.md` (formato abajo) **antes de pasar a la
   tarea siguiente**, no al final de la fase ni "cuando haya tiempo".
7. **Continuar.** Usar lo aprendido en esta tarea (qué funcionó, qué resultado fue
   inesperado, qué implicación deja) para planificar la tarea siguiente. Si un resultado
   inesperado cambia lo que corresponde hacer después, el ejecutor adapta la
   planificación de las tareas siguientes en vez de seguir un plan que ya quedó
   invalidado por la evidencia.

Esta lógica se aplica a **toda** etapa del proyecto (EDA, limpieza, preprocesamiento,
tratamiento de faltantes y atípicos, transformación de variables, feature engineering,
selección de variables, partición de datos, entrenamiento, validación, ajuste de
hiperparámetros, evaluación, comparación de modelos, interpretación, conclusiones
finales), no solo al EDA.

## El Planner (`reports/PLANNER.md`)

Documento único y vivo, no una lista de pendientes. Registra la evolución metodológica
del proyecto. Cada agente ejecutor agrega o actualiza su propia entrada al terminar una
tarea relevante — nunca reescribe la entrada de otro agente ni de una tarea ajena.

Trazabilidad exigida por entrada: **Tarea → Ejecución → Resultado → Análisis →
Conclusión → Decisión → Siguiente paso.** Plantilla:

```markdown
## <YYYY-MM-DD> — <título de la tarea, imperativo y verificable>

**Fase / agente:** <fase del pipeline (contextPrompt.md §7) — quién la realizó>
**Qué debía hacerse:** ...
**Qué se hizo:** ...
**Qué se encontró:** evidencia concreta (archivo, tabla, cifra, test)
**Qué significa:** ...
**Decisión tomada:** ... (o "ninguna: se presentó al usuario, pendiente")
**Por qué:** ...
**Implicaciones para lo siguiente:** ...
```

El campo `Auditoría` deja de ser parte de la plantilla: ya no hay un veredicto que
esperar antes de cerrar la tarea. Si en algún momento se pide una revisión puntual a
`leakage-auditor` sobre esta entrada, su resultado se agrega como una línea adicional
(`**Revisión de leakage-auditor:** ...`), no como requisito para haber llegado hasta
acá.

La entrada se redacta con el mismo estándar de `.claude/skills/steg-human-academic-prose/SKILL.md`
(prosa académica, sin relleno, sin abrir preguntas que la evidencia ya permite cerrar, y
sin mencionar la arquitectura interna de agentes: se escribe qué se hizo y qué se
concluyó, no "el agente X encontró Y"). Un lector externo debe poder reconstruir el
proyecto leyendo solo el Planner y `reports/DECISIONS.md`.

## Plane (tablero, sin PM)

Cada ejecutor gestiona directamente su propio work item, con las herramientas
`mcp__plane__workitem`, `mcp__plane__state`, `mcp__plane__workitem_comment` que ya tiene
en su ficha:

1. Al empezar una tarea, resuelve o crea su work item (proyecto `PROYE`) y lo mueve a
   **In Progress**.
2. Al terminar con evidencia y el Planner actualizado, el ejecutor mismo mueve el work
   item a **Done** y deja **un** comentario con el resumen de la evidencia y la ruta a
   la entrada del Planner. No hay un estado intermedio de espera ni un veredicto ajeno
   que aguardar.
3. Si la tarea resulta bloqueada por algo fuera de su alcance (una decisión de diseño no
   tomada, un artefacto de otra fase que no existe), la mueve a **Blocked**, comenta el
   motivo una vez, lo registra en el Planner como "Siguiente paso: pendiente de
   decisión del usuario" y lo plantea directamente al usuario. No existe un PM que
   replanifique por el ejecutor.

Nadie más toca el work item de otro agente. Si Plane no responde, el ejecutor sigue
igual (Plane es tablero, no gate) y lo anota en el comentario cuando vuelva a conectar.

## Auditoría (bajo pedido, no obligatoria)

`leakage-auditor` ya no es un paso obligatorio de ningún ciclo de tarea. Ningún
ejecutor mueve su work item a un estado de espera de auditoría ni necesita un PASS
ajeno para llegar a Done. La auditoría sigue existiendo como revisión que se pide
explícitamente:

- **De fase** (`/leak-check`): revisión adversarial de fuga sobre el repositorio
  completo o una fase específica, con veredicto `BLOQUEADO`/`APROBADO` en
  `reports/LEAKAGE_AUDIT.md`.
- **De una tarea puntual**: si el usuario o el propio ejecutor quiere una segunda
  mirada sobre algo concreto (un cálculo dudoso, un resultado sospechosamente bueno),
  se convoca a `leakage-auditor` con la tarea, la evidencia y la entrada del Planner, y
  devuelve el mismo formato estructurado que antes:

```
AUDIT <tarea> · ronda N · leakage-auditor · YYYY-MM-DD
Veredicto: PASS | FAIL
Criterios de aceptación:
- AC1: PASS | FAIL — evidencia verificada por el auditor (no la del ejecutor)
Planner: PASS | FAIL — la entrada del Planner refleja lo realizado y su conclusión es
  coherente con el análisis
Findings:
- F-<n> | Severity: CRITICAL | MAJOR | MINOR
  Evidence: archivo:línea / comando y salida
  Required Change: qué debe cambiar, concreto y verificable
```

Si hay un finding CRITICAL/MAJOR, el ejecutor dueño del código lo corrige — el Auditor
nunca corrige él mismo — y decide si vale la pena volver a pedir revisión. No hay ronda
obligatoria ni bloqueo automático de Plane: el ejecutor ya movió su work item a Done
antes de que exista este resultado, y si la corrección es necesaria la documenta como
una tarea nueva en el Planner.

## Reemplaza a

`reports/tasks/NNN-slug-{planning,tasks,audit}.md` deja de usarse para tareas nuevas: el
Planner es ahora la única fuente de trazabilidad narrativa. `reports/tasks/001-*` y
`002-*` quedan como histórico cerrado, sin reescribirse.
