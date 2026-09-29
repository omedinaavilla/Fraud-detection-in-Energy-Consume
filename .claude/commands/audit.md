---
description: Fase 0 — contrato de datos y auditoría de calidad de STEG
---

Invoca al agente `eda-analyst` para ejecutar/revisar la Fase 0 del proyecto STEG:

1. Corre `python -m steg.data.load` (checksums + validación de esquema) y
   `python -m steg.eda.profile` (perfilado + limpieza + informe de auditoría).
2. Contrasta el resultado contra `.claude/skills/steg-data-contract/SKILL.md`; si
   aparece algo no documentado, actualiza esa skill en el mismo cambio.
3. Deja el informe en `reports/EDA/00_data_audit.md`, las tablas en
   `reports/tables/profile_*.csv` y los hashes en `reports/data_checksums.json`.
4. Reporta hallazgos y espera antes de pasar a `/eda`.

Argumentos: $ARGUMENTS
