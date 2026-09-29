---
name: steg-feature-engineering
description: Cataloga las variables derivadas del historial de facturación de STEG (estadísticos por cliente, tendencias, saltos entre índices consecutivos, meses sin factura, frecuencia y tipo de observaciones de lectura, consumo por tipo de tarifa, razones entre niveles de consumo, antigüedad del cliente, comportamiento relativo a región/distrito/categoría), con nombre explícito, unidad y una línea de documentación por variable. Úsala al implementar src/steg/features/invoice.py o client.py, y al llenar reports/tables/feature_dictionary.csv.
---

# Catálogo de variables derivadas — STEG

Cada variable de esta lista debe poder calcularse solo con información disponible en el
momento de la predicción (sin usar facturas futuras respecto al punto de corte que
defina la Fase 3), y debe quedar documentada en `reports/tables/feature_dictionary.csv`
con nombre, unidad, definición y fase de origen (test asociado en
`tests/test_feature_dictionary.py`).

Convención de nombres: `snake_case`, prefijo por origen (`inv_` para agregados de
factura, `cli_` para variables propias del cliente, `rel_` para variables relativas a un
grupo de referencia).

## Agregados de factura → cliente (`src/steg/features/invoice.py`)

| Variable | Definición | Unidad |
|---|---|---|
| `inv_n_facturas` | Número de facturas del cliente en la ventana de historial decidida en Fase 3. | conteo |
| `inv_consumo_total_nivel_{1..4}` | Suma de `consommation_level_{1..4}` en la ventana. | consumo |
| `inv_consumo_medio_nivel_{1..4}` | Media de `consommation_level_{1..4}` por factura. | consumo/factura |
| `inv_consumo_std_nivel_{1..4}` | Desviación estándar del consumo por nivel — variabilidad de consumo declarado. | consumo |
| `inv_ratio_nivel_{2,3,4}_sobre_1` | `consommation_level_i / (consommation_level_1 + 1)` agregado por cliente. Consumo en niveles altos relativo al nivel base; la literatura de fraude eléctrico sugiere que un patrón de consumo desplazado a niveles superiores puede señalar manipulación, pero esto se verifica contra `target`, no se asume. | razón adimensional |
| `inv_salto_indice_medio` | Media de `new_index - old_index` entre facturas consecutivas del mismo `counter_number`. | unidades de índice |
| `inv_salto_indice_max` | Máximo salto entre índices consecutivos — saltos anómalos grandes o negativos son de interés. | unidades de índice |
| `inv_pct_index_regression` | Proporción de facturas del cliente con `index_regression` = True (ver `steg-data-contract`). | proporción |
| `inv_meses_cubiertos_total` | Suma de `months_number` (ya limpio de valores fuera de 1–12). | meses |
| `inv_meses_sin_factura_max` | Mayor hueco en días/meses entre dos facturas consecutivas — meses sin lectura. | meses |
| `inv_pct_counter_statue_invalid` | Proporción de facturas con `counter_statue_invalid` = True. | proporción |
| `inv_pct_reading_remarque_tipo_{valor}` | Proporción de facturas con cada valor válido de `reading_remarque` ({6,7,8,9}) — la nota del agente en visita puede correlacionar con intervención manual. | proporción |
| `inv_n_counter_number_distintos` | Cuántos `counter_number` distintos tuvo el cliente — cambios de contador. | conteo |
| `inv_n_tarif_type_distintos` | Cuántos `tarif_type` distintos usó el cliente. | conteo |
| `inv_pct_counter_type_gaz` | Proporción de facturas con `counter_type == 'GAZ'` (vs. `ELEC`). | proporción |
| `inv_tendencia_consumo_nivel_1` | Pendiente de una regresión simple de `consommation_level_1` contra el tiempo, por cliente — consumo creciente/decreciente. | consumo/año |
| `inv_pct_duplicado_logico` | Proporción de facturas marcadas `logical_duplicate` (ver `steg-data-contract`) — puede ser artefacto de captura o señal de refacturación. | proporción |

## Variables propias del cliente (`src/steg/features/client.py`)

| Variable | Definición | Unidad |
|---|---|---|
| `cli_antiguedad_dias` | Días entre `creation_date` y la fecha de referencia decidida en Fase 3 (¿última factura del dataset? ¿fecha fija?). Documentar la elección en `DECISIONS.md`. | días |
| `cli_primera_factura_antes_de_alta` | Booleano: la primera factura del cliente es anterior a `creation_date`. 8.748 clientes en train caen en este caso — puede ser normal (migración de datos históricos) o error de captura; se deja como variable, no se corrige. | booleano |

## Variables relativas al grupo de referencia (`rel_`)

| Variable | Definición | Unidad |
|---|---|---|
| `rel_consumo_vs_region` | `inv_consumo_medio_nivel_1` del cliente dividido por la mediana de la misma variable en su `region`. Ajustado dentro del fold de entrenamiento (la mediana de referencia se calcula solo con clientes de train de ese fold). | razón adimensional |
| `rel_consumo_vs_distrito` | Igual que arriba, agrupado por `disrict`. | razón adimensional |
| `rel_consumo_vs_categoria` | Igual que arriba, agrupado por `client_catg`. | razón adimensional |

## Reglas duras

- **Ninguna variable usa `data/raw/*.csv` directamente en el pipeline de modelado**:
  todas se calculan desde `data/interim/*.parquet` (ya limpio y con banderas), para que
  las anomalías documentadas no se cuelen sin marcar.
- **Toda estadística de referencia para `rel_*` (mediana de región, etc.) se ajusta
  dentro del fold de entrenamiento**, dentro de un `Pipeline` de scikit-learn — nunca
  antes de partir (sección 2 de `contextPrompt.md`). Ver `steg-validation-protocol`.
- Antes de dar por buena una variable, verificar con `steg-eda-statistics` que su
  distribución no difiere de forma sospechosa entre train y test.
- Cada variable nueva se añade a esta tabla y a
  `reports/tables/feature_dictionary.csv` en el mismo cambio que el código que la
  calcula — no después.
