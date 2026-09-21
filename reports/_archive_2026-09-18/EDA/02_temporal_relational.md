# EDA Fase 1 — Temporal y relacional entre tablas

El análisis completo, con su código y sus salidas intermedias, está documentado en `notebooks/01_eda.ipynb`; este informe recoge en texto plano lo que allí se calcula e interpreta. Las cifras corresponden a la ejecución del 2026-09-18 sobre `data/interim/*.parquet`, las tablas limpias con las banderas de anomalía de `src/steg/data/clean.py`.

Pasos 5 y 6 del protocolo de exploración. Nada de lo que sigue mira `target`.

## 1. Cobertura temporal

`invoice_train` cubre de 1977 a 2019, pero el
volumen no está repartido: los 28 años anteriores a 2005 suman
22.112 facturas (0.494 % del total), frente a
4.454.626 desde 2005 (99.51 %).

El corte de 2005 lo imponen los datos y no una elección analítica: es la
fecha en la que la tabla de facturación empieza a existir. Para todos los clientes dados de
alta antes, la ventana de historial disponible está truncada por la izquierda por cómo se
construyó la base, y no por su comportamiento.

| year | train_pct | test_pct |
|---|---|---|
| 2005 | 1.444 | 1.434 |
| 2006 | 4.954 | 4.942 |
| 2007 | 5.499 | 5.504 |
| 2008 | 5.88 | 5.878 |
| 2009 | 6.352 | 6.339 |
| 2010 | 7.064 | 7.077 |
| 2011 | 6.934 | 6.963 |
| 2012 | 7.195 | 7.226 |
| 2013 | 7.504 | 7.511 |
| 2014 | 7.67 | 7.692 |
| 2015 | 8.059 | 8.04 |
| 2016 | 8.57 | 8.569 |
| 2017 | 9.179 | 9.132 |
| 2018 | 7.498 | 7.482 |
| 2019 | 5.704 | 5.726 |

Tabla completa: `reports/tables/temporal_invoices_per_year.csv`. Figura:
`reports/figures/fig_temporal_invoices_per_year.png`.

### Estacionalidad

Restringido a 2005+, el mes con más facturas en train es el
5 (9.35 %) y el de menos el
12 (7.37 %). Frente al reparto uniforme de
8,33 %, la desviación máxima es de 1.02 puntos
porcentuales. La lectura de contadores se reparte a lo largo del año, sin campañas
concentradas en un trimestre. Figura: `reports/figures/fig_temporal_invoices_per_month.png`.

## 2. Historial por cliente

| table | column | n | p01 | p25 | p50 | p75 | p99 | max |
|---|---|---|---|---|---|---|---|---|
| invoice_train | n_invoices | 135493 | 1 | 10 | 30 | 50 | 98 | 439 |
| invoice_train | span_years | 135493 | 0 | 3.335 | 9.306 | 13.32 | 14.45 | 14.9 |
| invoice_train | n_streams | 135493 | 1 | 1 | 1 | 2 | 2 | 2 |
| invoice_train | median_gap_days | 131281 | 0 | 4 | 106 | 122 | 366 | 3518 |
| invoice_train | max_gap_days | 131281 | 28 | 253 | 357 | 426 | 1446 | 3796 |
| invoice_train | median_gap_days_within_stream | 130422 | 0 | 119 | 121 | 125 | 397 | 3518 |
| invoice_train | max_gap_days_within_stream | 130422 | 62 | 256 | 364 | 450 | 1485 | 4208 |
| invoice_train | invoices_per_year | 130246 | 1.101 | 2.76 | 3.675 | 5.395 | 14.98 | 730.5 |
| invoice_test | n_invoices | 58069 | 1 | 11 | 30 | 50 | 103 | 412 |
| invoice_test | span_years | 58069 | 0 | 3.398 | 9.333 | 13.33 | 14.45 | 14.9 |
| invoice_test | n_streams | 58069 | 1 | 1 | 1 | 2 | 2 | 2 |
| invoice_test | median_gap_days | 56309 | 0 | 4 | 107 | 122 | 367 | 3633 |
| invoice_test | max_gap_days | 56309 | 30 | 253 | 358 | 426 | 1455 | 4052 |
| invoice_test | median_gap_days_within_stream | 55967 | 0 | 119 | 121.5 | 125 | 401 | 3633 |
| invoice_test | max_gap_days_within_stream | 55967 | 62 | 258 | 364 | 447 | 1491 | 4052 |
| invoice_test | invoices_per_year | 55895 | 1.072 | 2.763 | 3.669 | 5.398 | 15.54 | 730.5 |

Tabla: `reports/tables/temporal_client_summary.csv`. Figura:
`reports/figures/fig_temporal_client_coverage.png`.

La mediana de facturas por cliente en train es
30, con percentil 1 en
1 y percentil 99 en
98.

### Dos medidas de hueco entre facturas

El 45.3 % de los clientes tiene contador eléctrico y de gas a la vez
(`reports/tables/relational_counter_type_mix.csv`), y sus dos series de facturas se
intercalan. Medido sobre el flujo completo del cliente, el hueco mediano tiene percentil
25 en 4 días, como si a una
cuarta parte de los clientes se le leyera el contador cada cuatro días. La cifra mide el
intercalado de las dos series, no la cadencia de lectura.

Medido dentro de cada `counter_type` por separado, que es la cadencia real de lectura, el
hueco mediano es de 121
días (p25 119,
p75 125), coherente
con facturación cuatrimestral. Toda variable del tipo "meses sin lectura" tiene que
construirse dentro del tipo de contador; calculada sobre el flujo mezclado mediría cuántos
contadores tiene el cliente.

El percentil 99 del hueco máximo llega a
1446 días: hay clientes con cuatro
años seguidos sin una sola factura dentro de su historial.

La ventana del historial tiene mediana de
9.3 años y máximo de
14.9, que es la distancia de
2005 a 2019. El techo lo impone la tabla, que no guarda
nada anterior.

## 3. Facturas por cliente

| table | n | p01 | p50 | p99 | max | n_clients_le_0 | n_clients_le_1 | n_clients_le_3 | n_clients_le_5 | n_clients_le_10 |
|---|---|---|---|---|---|---|---|---|---|---|
| client_train | 135493 | 1 | 30 | 98 | 439 | 0 | 4212 | 15269 | 21502 | 33931 |
| client_test | 58069 | 1 | 30 | 103 | 412 | 0 | 1760 | 6422 | 9034 | 14374 |

Tabla: `reports/tables/relational_invoices_per_client.csv`.

En train hay 0 clientes sin ninguna factura,
4.212 con una o menos y 15.269 con tres
o menos (11.27 %). En test las proporciones son
3.03 % y 11.06 %. Es el insumo de la
decisión diferida sobre clientes con historial corto (Fase 3).

## 4. counter_number no identifica un medidor

En `invoice_train`, excluidas las 43.161 filas con
`counter_number = 0`, hay 201.892 valores distintos. De ellos
20.365
(10.09 %) están asociados a más de un cliente,
y el más compartido aparece en 23 clientes. En total,
36.602 clientes tocan al menos un contador
compartido.

**Corrección a una cifra de la Fase 0.** El contrato de datos del proyecto afirmaba 20.366
valores compartidos, uno por hasta 5.149 clientes. Ese cálculo incluía el valor `0`, que
funciona como centinela de "sin número registrado" y no como contador: los 5.149 son los
clientes con al menos una factura sin número de contador
(5.149 en este recuento). Excluyéndolo quedan
20.365 valores compartidos y un máximo real
de 23 clientes por contador. La documentación del contrato de datos se
corrigió con estas cifras.

| table | column | n | p50 | p75 | p99 | max |
|---|---|---|---|---|---|---|
| invoice_train | n_counter_number_per_client | 135493 | 2 | 2 | 4 | 8 |
| invoice_train | n_clients_per_counter_number (counter_number != 0) | 201892 | 1 | 1 | 3 | 23 |
| invoice_test | n_counter_number_per_client | 58069 | 2 | 2 | 4 | 8 |
| invoice_test | n_clients_per_counter_number (counter_number != 0) | 91965 | 1 | 1 | 2 | 11 |

Figura: `reports/figures/fig_relational_counter_sharing.png`. La Fase 3 tiene que tratar
`counter_number` como conteo (cuántos contadores distintos aparecen en el historial del
cliente), nunca como identidad ni como categórica.

## 5. creation_date contra la primera factura

8.748 clientes de train
(6.46 %, IC Wilson 95 %
[6.33 %, 6.59 %]) tienen su primera factura
antes de la fecha de alta registrada. El desfase mediano en esos casos es de
75 días y el máximo de
322 días. No hay ni un caso con más de un año de anticipación.

Eso cambia la lectura respecto de la Fase 0: un desfase de esa magnitud se explica por el
retardo entre el inicio del suministro y el registro administrativo del contrato,
razonable en una utility con facturación cuatrimestral, antes que por una inconsistencia
estructural entre las dos tablas.

El problema está en el otro extremo. El percentil 75 de
`primera factura − creation_date` es de 3890 días y el máximo llega a
13314 (36 años). Esos clientes no tardaron décadas en
recibir su primera factura: fueron dados de alta antes de 2005 y su
facturación solo existe en la tabla desde entonces. Lo que mide la variable es el
truncamiento de la base, no la antigüedad del cliente.

Consecuencia para la Fase 3: `hoy − creation_date` es interpretable;
`primera factura − creation_date` mide la migración del sistema; y
`última factura − primera factura` está acotada artificialmente a 15 años para todos. Las
tres son construibles y significan cosas distintas. Figura:
`reports/figures/fig_relational_creation_vs_first_invoice.png`, tablas:
`reports/tables/relational_creation_vs_first_invoice.csv` y
`reports/tables/relational_counter_type_mix.csv`.
