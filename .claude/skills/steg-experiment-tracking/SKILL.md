---
name: steg-experiment-tracking
description: Define la convención de nombres de experimentos del proyecto STEG, qué se guarda por experimento (config, semilla, hash de datos, métricas por fold, artefactos), en qué formato y cómo se comparan dos corridas. Úsala al implementar cualquier código en src/steg/models/ o src/steg/evaluation/ que entrene o evalúe un modelo, y al escribir un número en reports/metrics/ o reports/tables/.
---

# Trazabilidad de experimentos — STEG

## Regla central

Ningún número del reporte o del artículo se escribe a mano (sección 2 de
`contextPrompt.md`). Si un número no está en `reports/tables/` o `reports/metrics/`, no
existe. Este módulo es lo que garantiza que todo número que sí existe se pueda rastrear
hasta el experimento y el hash de datos que lo produjeron.

## Convención de nombres

`<fase>_<algoritmo>_<variante>_<fecha>`, por ejemplo:

- `f4_dummy_baseline_20260917`
- `f4_logreg_baseline_20260917`
- `f5_lightgbm_optuna50_20260920`
- `f5_ensamble_lgbm_xgb_cat_20260922`

`fase` referencia la fase del pipeline (`f4` baselines, `f5` modelos principales, etc.).
No se reutiliza un nombre de experimento para una corrida distinta, aunque sea "solo
para probar" — cada corrida con configuración distinta es un experimento nuevo.

## Qué se guarda por experimento

En `reports/metrics/<nombre_experimento>.json`:

```json
{
  "experiment": "f5_lightgbm_optuna50_20260920",
  "seed": 42,
  "data_checksums_ref": "reports/data_checksums.json",
  "protocol_version": "frozen_2026-XX-XX",
  "model": {"type": "lightgbm", "hyperparameters": {"...": "..."}},
  "cv": {"n_folds": 5, "group_col": "client_id", "stratified": false},
  "metrics_by_fold": [{"fold": 0, "roc_auc": 0.0, "pr_auc": 0.0, "...": "..."}],
  "metrics_aggregate": {"roc_auc_mean": 0.0, "roc_auc_ci95": [0.0, 0.0]},
  "artifacts": {"model_path": "...", "predictions_path": "..."}
}
```

Campos obligatorios: `seed` (siempre `steg.config.SEED` salvo que el experimento sea
explícitamente un análisis de sensibilidad a la semilla), referencia al hash de datos
usado (para saber contra qué versión exacta de `data/raw/*.csv` corrió, ver
`reports/data_checksums.json`), la versión del protocolo de evaluación congelado en
Fase 2, y las métricas **por fold**, no solo el agregado — el agregado sin el detalle
por fold no permite calcular varianza después.

## Formato de artefactos

- Métricas: JSON, uno por experimento, en `reports/metrics/`.
- Tablas comparativas entre experimentos: CSV en `reports/tables/`, más su versión
  `.tex` si va al manuscrito (ver `steg-latex-outputs`).
- Modelos entrenados: no se versionan en git (son binarios grandes); se guardan en una
  carpeta local excluida de git, referenciada por ruta en el JSON del experimento.
- Configuración: cada experimento serializa los hiperparámetros efectivamente usados,
  no solo el espacio de búsqueda de Optuna — si Optuna eligió un valor, ese valor
  concreto es el que se guarda.

## Cómo se comparan dos corridas

1. Nunca comparar un número agregado suelto de un experimento contra otro. Comparar
   las distribuciones por fold (boxplot o test pareado, ver `steg-eda-statistics` para
   la prueba adecuada — los folds no son independientes entre modelos si comparten la
   misma partición, así que un test pareado como Wilcoxon es más apropiado que un
   Mann-Whitney entre grupos independientes).
2. Verificar primero que ambos experimentos usan la misma versión del protocolo
   (`protocol_version`) y el mismo hash de datos. Si difieren, la comparación no es
   válida y se documenta por qué difieren antes de comparar igualmente.
3. La tabla comparativa final (`reports/tables/model_comparison.csv`) incluye siempre
   intervalo, no solo la media — ver `results-analyst` en `.claude/agents/`.

## Relación con el resto del proyecto

Este módulo no decide la métrica primaria (`steg-metrics-catalog`) ni el protocolo de
partición (`steg-validation-protocol`); solo garantiza que, una vez decididos, cada
corrida quede registrada de forma que se pueda auditar y comparar sin ambigüedad.
