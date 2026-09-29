---
description: Fase 8 — auditoría adversarial de fuga bajo pedido, sobre el pipeline completo o una parte puntual
---

Invoca al agente `leakage-auditor` para revisar el repositorio completo: partición
por cliente, variables con información futura, transformaciones ajustadas fuera del
fold, métricas mal calculadas, y resultados sospechosamente buenos frente a la
referencia externa del leaderboard de Zindi (~0,86 AUC bajo su propio protocolo).
Escribe el veredicto (`BLOQUEADO`/`APROBADO`, con alcance y fecha) en
`reports/LEAKAGE_AUDIT.md`. Si bloquea, indica al agente dueño de cada corrección qué
debe cambiar; no corrige él mismo.

Argumentos: $ARGUMENTS
