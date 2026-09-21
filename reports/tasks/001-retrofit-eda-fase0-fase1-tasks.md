# 001 — Retrofit a Plane: Fase 0 (contrato de datos) y Fase 1 (EDA)

Origen: pedido del usuario de evidenciar en Plane el trabajo de EDA ya realizado.
Excepción deliberada al alcance temporal del flujo de `/request` — ver
`.claude/skills/steg-plane-workflow/SKILL.md`. Todas las tareas de este archivo ya
estaban terminadas al momento de escribirlo: se crean directamente en `[x]` y sus
work items espejo se crean directamente en estado Done.

- T001 [x] Contrato de datos y limpieza documentada (Fase 0)
  - Agente dueño: eda-analyst
  - Criterio de aceptación: reglas de limpieza de `src/steg/data/clean.py` aplicadas y
    contadas por regla/tabla; hashes SHA-256 de los CSV crudos.
  - Artefactos: `reports/EDA/00_data_audit.md`, `reports/data_checksums.json`
  - Plane: PROYE-9

- T002 [x] Perfilado automático de las cuatro tablas (Fase 0)
  - Agente dueño: eda-analyst
  - Criterio de aceptación: dimensiones, tipos y perfil por columna de
    `client_train`, `client_test`, `invoice_train`, `invoice_test` generados por
    `src/steg/eda/profile.py`.
  - Artefactos: `reports/tables/profile_*.csv`
  - Plane: PROYE-10

- T003 [x] Análisis univariado (Fase 1, paso 1-4 del protocolo)
  - Agente dueño: eda-analyst
  - Criterio de aceptación: distribución de variables de consumo, `months_number`,
    y tasas base de las banderas de anomalía, sin mirar `target`.
  - Artefactos: `reports/EDA/01_univariate.md`, `reports/tables/univariate_numeric.csv`,
    `reports/figures/fig_univ_*.png`
  - Plane: PROYE-11

- T004 [x] Análisis temporal y relacional cliente-factura (Fase 1, pasos 5-6)
  - Agente dueño: eda-analyst
  - Criterio de aceptación: cobertura temporal de `invoice_train`/`invoice_test`,
    estacionalidad, e historial por cliente (n_facturas, span, streams, gaps).
  - Artefactos: `reports/EDA/02_temporal_relational.md`,
    `reports/tables/temporal_invoices_per_year.csv`,
    `reports/figures/fig_temporal_*.png`
  - Plane: PROYE-12

- T005 [x] Análisis bivariado y multivariado contra la etiqueta (Fase 1)
  - Agente dueño: eda-analyst
  - Criterio de aceptación: asociación de categóricas y numéricas con `target`
    (Cramér's V corregido, Mann-Whitney/rank-biserial) y de banderas de anomalía
    contra la etiqueta, corriendo solo sobre `client_train`/`invoice_train`.
  - Artefactos: `reports/EDA/03_bivariate.md`,
    `reports/tables/bivariate_categorical_target.csv`,
    `reports/tables/bivariate_numeric_target.csv`
  - Plane: PROYE-13

- T006 [x] Implicaciones para el modelado y propuestas para la Fase 2 (Fase 1)
  - Agente dueño: eda-analyst
  - Criterio de aceptación: las cuatro decisiones diferidas de la sección 3 de
    `contextPrompt.md` (métrica primaria, desbalance, punto de operación/@k,
    estratificación de folds) documentadas como PROPUESTA con evidencia y
    alternativas, sin decidir por el usuario.
  - Artefactos: `reports/EDA/04_implicaciones.md`, entradas "PROPUESTAS de la Fase 1"
    en `reports/DECISIONS.md`
  - Plane: PROYE-14

## Nota

Las cuatro decisiones PROPUESTA de T006 siguen pendientes de que el usuario las
cierre (Fase 2, `/decide`) — este retrofit documenta que el EDA que las sustenta ya
existe, no que las decisiones ya se tomaron.
