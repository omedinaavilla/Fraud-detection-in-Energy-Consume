---
description: Fase 7 — priorización de inspecciones y análisis de costo-beneficio
---

Invoca al agente `results-analyst` para convertir probabilidades en una lista
priorizada usando las métricas `@k` de
`.claude/skills/steg-metrics-catalog/SKILL.md`. Antes de calcular ninguna ganancia
esperada, confirma con el usuario los parámetros de costo (costo de inspección,
ganancia por fraude detectado) y regístralos en `reports/DECISIONS.md`. Incluye
análisis de sensibilidad a esos parámetros.

Argumentos: $ARGUMENTS
