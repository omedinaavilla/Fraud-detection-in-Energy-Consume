---
description: Fase 1 — EDA profesional completo de STEG
---

Invoca al agente `eda-analyst` para ejecutar la Fase 1 siguiendo
`.claude/skills/steg-eda-protocol/SKILL.md`: univariado → bivariado (solo sobre
`client_train`/`invoice_train`) → multivariado → temporal → relacional entre tablas.
Usa `.claude/skills/steg-eda-statistics/SKILL.md` para elegir cada prueba y
`.claude/skills/steg-eda-visuals/SKILL.md` para cada figura. Deja el informe en
`reports/EDA/`, tablas en `reports/tables/`, figuras en `reports/figures/`.

Argumentos: $ARGUMENTS
