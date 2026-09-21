# Comprensión de los datos y calidad — Fase 0-1

Exportado desde `notebooks/01_eda.ipynb`, que es la fuente de estos resultados. Ejecución del 2026-09-18. Las cifras proceden de `reports/tables/` y las figuras de `reports/figures/`; regenerar el informe exige volver a ejecutar el cuaderno, no editar este archivo.

## Qué representa cada tabla

Los cuatro archivos forman dos tablas en dos particiones. En `client_train` y
`client_test` cada fila es un cliente, con su distrito, región, categoría y fecha de alta;
solo la de entrenamiento trae la etiqueta de fraude. En `invoice_train` e `invoice_test`
cada fila es una factura, con la fecha, la tarifa, los identificadores y el estado del
contador, las lecturas anterior y nueva, el consumo desglosado en cuatro niveles
tarifarios y los meses que cubre el documento. La relación es uno a muchos por
`client_id`, y como la etiqueta vive del lado del cliente, la unidad de análisis del
proyecto es el cliente.

El historial de facturación cubre de 1977-06-09 a
2019-12-07, más de lo que declara el diccionario de
variables, que anuncia 2005-2019. Las altas de clientes van de
1977-02-05 a 2019-09-10.

## Lo que los datos no permiten saber

El consumo no trae unidad de medida en ninguna de las fuentes disponibles, así que los
niveles se leen como magnitudes relativas. `counter_number` y `counter_code` no están
definidos en el diccionario oficial, y de `counter_statue` y `reading_remarque` se describe
la idea general sin la tabla de correspondencias, de modo que ningún código se interpreta
por su valor. La etiqueta no tiene fecha asociada: consta que un cliente fue identificado
como defraudador, no cuándo, lo que impide separar el historial anterior a la detección del
posterior. Estas lagunas se declaran en vez de rellenarse con supuestos.

## Inspección

Ninguna de las cuatro tablas declara un valor faltante y ninguna columna es constante. La
facturación es cuatrimestral: `months_number` vale 4 en el 82 % de las filas. Los niveles de
consumo 2, 3 y 4 son cero en el 85 %, 96 % y 98 % de las facturas, así que el desglose
tarifario solo se activa por encima de cierto volumen. El detalle columna por columna está
en `reports/tables/inspection_overview.csv` y en los perfiles de la auditoría de fase 0.

## Calidad: cinco anomalías investigadas

La auditoría reproducible de la fase 0 detectó y contó las anomalías
(`reports/EDA/00_data_audit.md` y `reports/tables/quality_checks.csv`). Cinco de ellas no
se explican con el conteo y se investigaron aquí; el resultado está en
`reports/tables/quality_deepdive.csv`.

| anomalia | n_filas | hallazgo | lectura |
|---|---|---|---|
| months_number fuera de [1,12] | 24.043 | 1357 valores distintos por encima de 12; el tramo >1000 no admite lectura como período de facturación | captura defectuosa en la mayoría; 13-24 puede ser regularización real |
| counter_statue / reading_remarque fuera de dominio | 81 | los valores extraños de reading_remarque son códigos válidos de counter_code | filas con columnas corridas en la captura original |
| duplicados por clave lógica | 29.278 | 17768 de 18363 grupos difieren en consumo o índices | no son copias: son líneas distintas del mismo documento o refacturaciones |
| counter_number compartido entre clientes | 43.161 | 20366 valores en más de un cliente, hasta 5149 | no es un identificador de equipo |
| primera factura anterior al alta | 8.748 | adelanto mediano de 75 días, máximo 322 | creation_date no es el inicio del historial para estos clientes |

Tres conclusiones cambian la lectura que sugería el conteo. Los duplicados por clave lógica
no son copias: 17.768 de 18.363 grupos
difieren en consumo o en índices, y dentro de un grupo suele haber más de un tipo de
tarifa, así que eliminarlos restaría consumo realmente facturado. Los valores imposibles de
`reading_remarque` son códigos válidos de `counter_code`, lo que identifica el defecto como
filas con las columnas desplazadas en la captura original. Y `months_number` mezcla dos
fenómenos: entre 13 y 24 meses hay períodos largos plausibles, mientras que por encima de
mil no hay lectura posible como período de facturación.

Ninguna anomalía se corrige en esta fase. Todas quedan marcadas con una columna booleana en
`data/interim/*.parquet`, y el análisis bivariado comprueba si alguna se concentra en
clientes con fraude. Dos lo parecen: un cliente con al menos una factura duplicada por clave
lógica o con al menos un retroceso de índice dobla la tasa de fraude (riesgo relativo
2,16 y 2,06). Medida como proporción de
las facturas del cliente, en cambio, esa asociación se desvanece
(0,019 y 0,015 de rank-biserial, frente
a un umbral de 0,1), y el riesgo de la marca binaria se atenúa a medida que crece el
historial. La frecuencia de anomalías no informa sobre la etiqueta; lo que informa en parte
es cuántas facturas tiene el cliente, que es un asunto distinto.
