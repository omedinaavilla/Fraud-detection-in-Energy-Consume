# Auditoría de calidad de datos — Fase 0

Informe reproducible: lo genera `src/steg/eda/profile.py` (`make audit`) a partir de `data/raw/*.csv`. Última ejecución: 2026-09-18 15:16 UTC. Los hashes SHA-256 de los cuatro CSV están en `data_checksums.json`, y cada cifra de aquí sale de `reports/tables/quality_checks.csv`, `reports/tables/profile_<tabla>.csv` o `reports/tables/schema_vs_readme.csv`.

El alcance de esta fase es detectar y cuantificar. Ninguna anomalía se corrige aquí: `src/steg/data/clean.py` la marca con una columna booleana y la Fase 1 estudia si es defecto de captura o señal, antes de que la Fase 3 decida qué hacer.

## 1. Qué contiene cada archivo

| Tabla | Filas | Columnas | Unidad de observación |
|---|---|---|---|
| client_train | 135.493 | 6 | un cliente con etiqueta |
| client_test | 58.069 | 5 | un cliente sin etiqueta |
| invoice_train | 4.476.749 | 16 | una factura de un cliente de train |
| invoice_test | 1.939.730 | 16 | una factura de un cliente de test |

Las dos tablas se relacionan por `client_id` en una cardinalidad uno a muchos: un cliente tiene tantas facturas como lecturas se le hayan tomado, y la etiqueta vive en la tabla de clientes. La unidad de análisis del proyecto es el cliente.

## 2. Distribución de la etiqueta (solo train)

7.566 clientes fraudulentos de 135.493 (5,58 %), es decir 16,9 negativos por positivo. La etiqueta toma 2 valores distintos y no tiene fecha asociada: no se sabe cuándo se detectó el fraude, lo que impide construir un corte temporal honesto entre historial y etiqueta. La relación de la etiqueta con el resto de las variables pertenece a la Fase 1.

## 3. Esquema real contra el README oficial

Las 21 columnas distintas de los cuatro archivos aparecen en `data/raw/README.md` salvo en dos puntos. El README lista `counter_number`, `counter_code` sin definición, de modo que su significado no está documentado por la fuente y cualquier interpretación es una hipótesis del análisis. Y el nombre de `disrict` no coincide con el del README (`District`): el archivo trae una errata que se respeta tal cual en la carga, porque renombrar rompería la trazabilidad con el original.

Detalle columna por columna en `reports/tables/schema_vs_readme.csv`.

## 4. Faltantes, duplicados y claves

| table | column | check | n_affected | pct_affected |
|---|---|---|---|---|
| client_train | (todas) | filas_con_algun_nulo | 0 | 0 |
| client_train | (todas) | filas_exactamente_duplicadas | 0 | 0 |
| client_train | client_id | client_id_duplicado | 0 | 0 |
| client_test | (todas) | filas_con_algun_nulo | 0 | 0 |
| client_test | (todas) | filas_exactamente_duplicadas | 0 | 0 |
| client_test | client_id | client_id_duplicado | 0 | 0 |
| invoice_train | (todas) | filas_con_algun_nulo | 0 | 0 |
| invoice_train | (todas) | filas_exactamente_duplicadas | 11 | 0,000246 |
| invoice_train | client_id+invoice_date+counter_number | duplicado_por_clave_logica | 29.289 | 0,6542 |
| invoice_test | (todas) | filas_con_algun_nulo | 0 | 0 |
| invoice_test | (todas) | filas_exactamente_duplicadas | 8 | 0,000412 |
| invoice_test | client_id+invoice_date+counter_number | duplicado_por_clave_logica | 14.144 | 0,7292 |
| train | client_id | cliente_sin_ninguna_factura | 0 | 0 |
| train | client_id | factura_sin_cliente | 0 | 0 |
| test | client_id | cliente_sin_ninguna_factura | 0 | 0 |
| test | client_id | factura_sin_cliente | 0 | 0 |
| train vs. test | client_id | clientes_en_ambas_particiones | 0 | 0 |

Ninguna de las cuatro tablas declara un solo valor faltante, lo que no significa que no haya información ausente: las columnas que la codifican con valores imposibles aparecen en el apartado siguiente. Los duplicados exactos son un puñado de filas y se eliminan; los duplicados por la clave lógica (`client_id`, `invoice_date`, `counter_number`) son dos órdenes de magnitud más frecuentes y no se eliminan, porque esas filas difieren en consumo o en índices y esa diferencia puede ser refacturación en vez de error.

## 5. Valores imposibles o fuera del dominio declarado

| table | column | check | n_affected | pct_affected | detail |
|---|---|---|---|---|---|
| client_train | creation_date | creation_date_fuera_de_rango_plausible | 0 | 0 | rango observado 1977-02-05 a 2019-09-10 |
| client_test | creation_date | creation_date_fuera_de_rango_plausible | 0 | 0 | rango observado 1977-02-05 a 2019-08-26 |
| invoice_train | counter_statue | valor_fuera_del_dominio_documentado | 47 | 0,00105 | valores inesperados: ['269375', '420', '46', '618', '769', 'A'] |
| invoice_train | reading_remarque | valor_fuera_del_dominio_observado_en_test | 34 | 0,000759 | valores inesperados: [5, 203, 207, 413] |
| invoice_train | months_number | igual_a_cero | 2 | 4,5e-05 | período nulo |
| invoice_train | months_number | mayor_que_12 | 24.041 | 0,537 | máximo observado 636624 |
| invoice_train | months_number | negativo | 0 | 0 |  |
| invoice_train | old_index/new_index | new_index_menor_que_old_index | 2.264 | 0,05057 | el contador retrocede: cambio de equipo no señalizado o error de captura |
| invoice_train | old_index/new_index | indice_negativo | 0 | 0 |  |
| invoice_train | consommation_level_1..4 | suma_niveles_distinta_de_new_menos_old | 18.935 | 0,423 | la descomposición por nivel tarifario no reconstruye el diferencial de índice |
| invoice_train | consommation_level_1..4 | consumo_negativo | 0 | 0 |  |
| invoice_train | consommation_level_1..4 | consumo_total_cero | 467.553 | 10,44 | factura emitida sin consumo registrado |
| invoice_train | counter_number | igual_a_cero | 43.161 | 0,9641 | valor centinela: no identifica ningún contador |
| invoice_train | counter_coefficient | igual_a_cero | 46 | 0,001028 | máximo observado 50 |
| invoice_train | invoice_date | anterior_al_quiebre_de_volumen | 22.112 | 0,4939 | el README declara cobertura 2005-2019; rango real 1977-06-09 a 2019-12-07 |
| invoice_test | counter_statue | valor_fuera_del_dominio_documentado | 0 | 0 | ninguno |
| invoice_test | reading_remarque | valor_fuera_del_dominio_observado_en_test | 0 | 0 | ninguno |
| invoice_test | months_number | igual_a_cero | 9 | 0,000464 | período nulo |
| invoice_test | months_number | mayor_que_12 | 10.392 | 0,5357 | máximo observado 990688 |
| invoice_test | months_number | negativo | 0 | 0 |  |
| invoice_test | old_index/new_index | new_index_menor_que_old_index | 1.054 | 0,05434 | el contador retrocede: cambio de equipo no señalizado o error de captura |
| invoice_test | old_index/new_index | indice_negativo | 0 | 0 |  |
| invoice_test | consommation_level_1..4 | suma_niveles_distinta_de_new_menos_old | 8.119 | 0,4186 | la descomposición por nivel tarifario no reconstruye el diferencial de índice |
| invoice_test | consommation_level_1..4 | consumo_negativo | 0 | 0 |  |
| invoice_test | consommation_level_1..4 | consumo_total_cero | 201.836 | 10,41 | factura emitida sin consumo registrado |
| invoice_test | counter_number | igual_a_cero | 18.455 | 0,9514 | valor centinela: no identifica ningún contador |
| invoice_test | counter_coefficient | igual_a_cero | 30 | 0,001547 | máximo observado 21 |
| invoice_test | invoice_date | anterior_al_quiebre_de_volumen | 9.357 | 0,4824 | el README declara cobertura 2005-2019; rango real 1977-07-13 a 2019-12-07 |

`months_number` fuera de `[1, 12]` y `counter_statue` con letras o con números de seis cifras no son valores mal medidos: son celdas que se llenaron con otra cosa. El caso de `reading_remarque` lo muestra sin ambigüedad, porque los cuatro valores inesperados que aparecen ahí (5, 203, 207, 413) son valores propios de `counter_code`, lo que apunta a filas con las columnas corridas en la captura original. Son el equivalente de un faltante en un archivo que no declara ninguno, y por eso se marcan en vez de imputarse.

## 6. Incoherencias de identidad y de fecha entre tablas

| table | column | check | n_affected | n_total | detail |
|---|---|---|---|---|---|
| invoice_train | counter_number | valor_compartido_por_varios_clientes | 20.366 | 201.893 | máximo 5149 clientes con el mismo valor; el denominador son valores distintos, no filas |
| invoice_test | counter_number | valor_compartido_por_varios_clientes | 4.276 | 91.966 | máximo 2196 clientes con el mismo valor; el denominador son valores distintos, no filas |
| train | creation_date vs. min(invoice_date) | primera_factura_anterior_al_alta | 8.748 | 135.493 | mediana del adelanto 75 días, máximo 322 días |
| test | creation_date vs. min(invoice_date) | primera_factura_anterior_al_alta | 3.677 | 58.069 | mediana del adelanto 77 días, máximo 323 días |

Una factura anterior a la fecha de alta del cliente contradice la definición del README (`Creation_date: Date client joined`). Cualquier variable de antigüedad construida como diferencia contra `creation_date` hereda ese defecto y saldrá negativa para esos clientes. Y `counter_number` no identifica un contador: el mismo valor aparece en clientes distintos, así que usarlo como identificador de equipo sin verificarlo produciría agregaciones sin sentido.

## 7. Comparabilidad entre train y test

| column | check | n_affected | detail |
|---|---|---|---|
| client_id | clientes_en_ambas_particiones | 0 | un solapamiento invalidaría cualquier evaluación |
| region | categorias_presentes_en_una_sola_particion | 1 | solo en train: [199]; solo en test: [] |
| disrict | categorias_presentes_en_una_sola_particion | 0 | solo en train: []; solo en test: [] |
| client_catg | categorias_presentes_en_una_sola_particion | 0 | solo en train: []; solo en test: [] |
| tarif_type | categorias_presentes_en_una_sola_particion | 1 | solo en train: [18]; solo en test: [] |
| counter_code | categorias_presentes_en_una_sola_particion | 3 | solo en train: [0, 1, 367]; solo en test: [] |

Ningún cliente aparece en las dos particiones, así que la separación de Zindi es limpia a nivel de cliente. Las categorías exclusivas de train son de frecuencia marginal y afectan a la codificación de categóricas de la Fase 3: un esquema que aprenda una columna por categoría producirá columnas que en test valen cero siempre. La comparación de distribuciones entre las dos particiones, que es lo que decide si el modelo puede extrapolar, corresponde a la Fase 1.

## 8. Reglas de limpieza aplicadas (`src/steg/data/clean.py`)

| Tabla | Regla | Filas afectadas |
|---|---|---|
| client_train | (sin reglas aplicables) | 0 |
| client_test | (sin reglas aplicables) | 0 |
| invoice_train | exact_duplicates_dropped | 11 |
| invoice_train | logical_duplicate | 29.278 |
| invoice_train | counter_statue_invalid | 47 |
| invoice_train | reading_remarque_invalid | 34 |
| invoice_train | months_number_invalid | 24.043 |
| invoice_train | index_regression | 2.264 |
| invoice_test | exact_duplicates_dropped | 8 |
| invoice_test | logical_duplicate | 14.136 |
| invoice_test | counter_statue_invalid | 0 |
| invoice_test | reading_remarque_invalid | 0 |
| invoice_test | months_number_invalid | 10.401 |
| invoice_test | index_regression | 1.054 |

Solo `exact_duplicates_dropped` elimina filas. El resto añade una columna booleana a `data/interim/*.parquet` y deja la decisión para más adelante.

## 9. Qué queda abierto al terminar la Fase 0

El significado de `counter_number` y `counter_code` no está documentado, y el de los códigos de `counter_statue` y `reading_remarque` se describe en el README de forma genérica, sin la tabla de correspondencias. Ninguna de las cuatro tablas declara la unidad de medida del consumo. Estas lagunas no se resuelven con los datos disponibles, así que el análisis las trata como categóricas sin semántica en vez de atribuirles un significado por el nombre.

El perfil columna por columna de las cuatro tablas está en `reports/tables/profile_<tabla>.csv`; el catálogo completo de verificaciones, con las que no dieron ningún hallazgo, en `reports/tables/quality_checks.csv`.
