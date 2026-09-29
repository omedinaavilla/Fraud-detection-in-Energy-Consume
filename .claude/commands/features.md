---
description: Fase 3 — ingeniería de variables (factura → cliente, cliente, matriz final)
---

Invoca al agente `feature-engineer` para implementar el catálogo de
`.claude/skills/steg-feature-engineering/SKILL.md` sobre `data/interim/*.parquet`:
agregación de facturas a cliente, variables propias del cliente, ensamblaje de
`data/processed/`, y `reports/tables/feature_dictionary.csv`. Toda estadística de
referencia se ajusta dentro del fold, según
`.claude/skills/steg-validation-protocol/SKILL.md`. Corre
`pytest tests/test_feature_dictionary.py` al terminar.

Argumentos: $ARGUMENTS
