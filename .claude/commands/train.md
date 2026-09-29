---
description: Fases 4-5 — baselines y modelos principales bajo el protocolo congelado
---

Invoca al agente `model-trainer` para entrenar bajo el protocolo congelado en
`reports/DECISIONS.md`, usando `src/steg/data/split.py` para toda partición. Fase 4:
`DummyClassifier`, regresión logística, LightGBM sin ajustar. Fase 5: LightGBM,
XGBoost, CatBoost con búsqueda de hiperparámetros y un ensamble. Registra cada corrida
según `.claude/skills/steg-experiment-tracking/SKILL.md` en `reports/metrics/`.

Argumentos: $ARGUMENTS
