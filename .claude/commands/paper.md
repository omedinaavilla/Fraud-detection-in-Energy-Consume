---
description: Fase 9 — manuscrito en LaTeX a partir de los artefactos en reports/
---

Invoca al agente `academic-writer` para redactar `paper/` en español académico,
siguiendo `.claude/skills/steg-human-academic-prose/SKILL.md`. Antes de escribir,
asegúrate de que `steg-latex-outputs` ya reexportó tablas y figuras vigentes a
`paper/tablas/` y `paper/figuras/`. Ninguna cifra sin respaldo en `reports/`: usar
`\todo{}` para lo que falte. No requiere una auditoría previa de `leakage-auditor`;
si querés una revisión puntual de los resultados antes de citarlos, pedila aparte con
`/leak-check`.

Argumentos: $ARGUMENTS
