---
description: Fase 2 — cierra las decisiones diferidas de evaluación con evidencia del EDA
---

Invoca al agente `eda-analyst` para presentar, con evidencia de `reports/EDA/` y
`reports/tables/`, las decisiones diferidas de la sección 3 de `contextPrompt.md` que
corresponden a esta fase: métrica primaria, si hay o no problema de desbalance,
punto de operación/umbral (y si aplica "@k"), y estratificación de folds. Usa
`.claude/skills/steg-metrics-catalog/SKILL.md` y
`.claude/skills/steg-class-distribution/SKILL.md` como catálogo de alternativas.

Presenta alternativas con riesgos, escribe entradas `PROPUESTA` en
`reports/DECISIONS.md`, y espera confirmación del usuario antes de marcarlas como
definitivas y congelar el protocolo de evaluación.

Argumentos: $ARGUMENTS
