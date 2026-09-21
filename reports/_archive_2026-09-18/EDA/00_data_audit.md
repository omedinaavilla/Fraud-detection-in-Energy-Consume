# Auditoría de calidad de datos — Fase 0

Generado automáticamente por `src/steg/eda/profile.py` el 2026-09-17 23:53 UTC.

Hashes SHA-256 de los CSV crudos en `reports\data_checksums.json`.

## Dimensiones

| Tabla | Filas | Columnas |
|---|---|---|
| client_train | 135493 | 6 |
| client_test | 58069 | 5 |
| invoice_train | 4476749 | 16 |
| invoice_test | 1939730 | 16 |

## Distribución de la etiqueta (solo train)

7566 clientes fraudulentos de 135493 (5.58 %). No se explora relación con otras variables aquí: eso corresponde a la Fase 1.

## Resumen de limpieza (`src/steg/data/clean.py`)

| Tabla | Regla | Filas afectadas |
|---|---|---|
| client_train | (sin reglas aplicables) | 0 |
| client_test | (sin reglas aplicables) | 0 |
| invoice_train | exact_duplicates_dropped | 11 |
| invoice_train | logical_duplicate | 29278 |
| invoice_train | counter_statue_invalid | 47 |
| invoice_train | reading_remarque_invalid | 34 |
| invoice_train | months_number_invalid | 24043 |
| invoice_train | index_regression | 2264 |
| invoice_test | exact_duplicates_dropped | 8 |
| invoice_test | logical_duplicate | 14136 |
| invoice_test | counter_statue_invalid | 0 |
| invoice_test | reading_remarque_invalid | 0 |
| invoice_test | months_number_invalid | 10401 |
| invoice_test | index_regression | 1054 |

## Perfiles por columna

Detalle completo en `reports/tables/profile_<tabla>.csv`.
