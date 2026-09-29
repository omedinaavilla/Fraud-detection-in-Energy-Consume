---
name: steg-data-contract
description: Documenta el esquema exacto de los cuatro CSV de STEG (client_train, client_test, invoice_train, invoice_test), el significado de cada columna según el README oficial y dónde ese README se equivoca frente a los datos reales, y las reglas de validación que aplica src/steg/data/load.py. Úsala antes de tocar cualquier CSV crudo, al escribir o revisar código de carga/limpieza, al decidir qué hacer con un valor inesperado en una columna, o cuando alguien proponga una columna que no está en esta lista.
---

# Contrato de datos STEG

No inventes columnas. Todo lo que sigue viene de leer `data/raw/README.md` y de perfilar
`data/raw/*.csv` con `src/steg/eda/profile.py` — no de la literatura del reto ni de
supuestos razonables. Si una versión futura de los datos cambia alguna cifra aquí, esta
skill y `src/steg/config.py::DataContract` se actualizan juntos.

## Tablas

| Tabla | Filas | Columnas | Unidad |
|---|---|---|---|
| `client_train` | 135.493 | 6 (incluye `target`) | 1 fila = 1 cliente |
| `client_test` | 58.069 | 5 (sin `target`) | 1 fila = 1 cliente |
| `invoice_train` | 4.476.749 | 16 | 1 fila = 1 factura |
| `invoice_test` | 1.939.730 | 16 | 1 fila = 1 factura |

Sin nulos en ninguna tabla. Sin `client_id` duplicado en las tablas de cliente. Cero
clientes en común entre train y test. Integridad referencial completa: todo `client_id`
de `invoice_*` existe en `client_*` correspondiente, y viceversa (los pocos clientes sin
factura se reportan como advertencia, no como error — un cliente sin historial es
posible, solo que no aporta variables agregadas). En la versión actual de los datos no
hay ningún cliente sin facturas en ninguna de las dos particiones.

**Duplicados.** 11 filas exactamente duplicadas en `invoice_train` y 8 en `invoice_test`,
que sí se eliminan. La clave lógica (`client_id`, `invoice_date`, `counter_number`) se
repite en 29.278 filas de train, agrupadas en 18.363 ternas; 17.768 de esas ternas
difieren en consumo o en índices y suelen traer más de un `tarif_type`, de modo que no
son copias sino líneas distintas del mismo documento o refacturaciones. No se eliminan.

**Categorías exclusivas de train.** `region` 199 (2 clientes), `tarif_type` 18 (4
facturas) y `counter_code` 0, 1 y 367. Ninguna aparece en test, así que la codificación
de categóricas tiene que resolver el caso de una categoría no vista sin fallar.

## Columnas de `client_{train,test}`

| Columna (nombre real en el CSV) | Tipo | Significado |
|---|---|---|
| `disrict` | int64 | Distrito del cliente. **El nombre trae un typo en el archivo** ("disrict", no "district"); se respeta tal cual, no se renombra en la carga. |
| `client_id` | string | Identificador único del cliente. Prefijo `train_Client_*` / `test_Client_*`. |
| `client_catg` | int64 | Categoría de cliente. 3 valores: `11` (131.494 filas, dominante), `12`, `51`. |
| `region` | int64 | Región. 25 valores en train, 24 en test — la región `199` solo existe en train. |
| `creation_date` | fecha | Fecha de alta del cliente. Formato **`DD/MM/YYYY`**, no ISO. Rango 1977-02-05 a 2019-09-10. |
| `target` (solo train) | float64, {0.0, 1.0} | 1 = fraude. 7.566 positivos de 135.493 (5,58 %). |

## Columnas de `invoice_{train,test}`

| Columna | Tipo | Significado |
|---|---|---|
| `client_id` | string | FK a `client_*`. |
| `invoice_date` | fecha | Formato **`YYYY-MM-DD`** (distinto del de `creation_date`). Rango real de volumen: 2005–2019; antes de 2005 hay menos de 2.200 facturas/año en total, residual. |
| `tarif_type` | int64 | Tipo de tarifa. 17 valores, dominan `11` y `40`. |
| `counter_number` | int64 | **No documentado en el README oficial.** No es un identificador único de medidor: 20.366 valores están compartidos por más de un cliente (uno por hasta 5.149 clientes), y 43.161 filas tienen `counter_number == 0`. Tratarlo como ID de contador sin verificar es un error. |
| `counter_statue` | **string**, no numérico | Estado del contador. El README dice "hasta 5 valores"; en `test` se cumple (`{0,1,2,3,4,5}`), pero en `train` aparecen además `46`, `A`, `618`, `769`, `420`, `269375` (47 filas) — basura de captura. Cargar siempre como texto: castear a int rompe con `'A'`. |
| `counter_code` | int64 | **No documentado en el README oficial.** 42 valores; dominan `203`, `5`, `207`. |
| `reading_remarque` | int64 | Nota del agente STEG durante la visita. Válido en test: `{6,7,8,9}`. En train aparecen además `203`, `207`, `413`, `5` (34 filas) — son valores propios de `counter_code`, evidencia de columnas corridas en la captura de esas filas. |
| `counter_coefficient` | int64 | Coeficiente adicional cuando se excede el consumo estándar. 16 valores, `1` en el 99,97 % de filas. 46 filas (train) y 30 (test) traen `0`, imposible para un multiplicador; 45 de esas 46 tienen consumo registrado. |
| `consommation_level_1..4` | int64 | Consumo desagregado por nivel tarifario. En el 99,58 % de las filas, `sum(level_1..4) == new_index - old_index`; las 18.935 excepciones (train) son candidatas a regla de limpieza adicional, no a error de lectura. Los niveles 2, 3 y 4 valen cero en el 85,2 %, 95,9 % y 97,9 % de las filas: el desglose solo se activa por encima de cierto volumen. |
| `old_index`, `new_index` | int64 | Lectura anterior y nueva del contador. `new_index < old_index` en 2.264 filas (train) — posible cambio de contador no señalizado, o error. Correlacionan a 0,99 (Spearman): no son variables independientes. |
| `months_number` | int64 | Meses que cubre la factura. Debería estar en 1–12; vale `4` en el 82 % de las filas (facturación cuatrimestral). 24.041 filas (train) superan 12 con 1.357 valores distintos y máximo 636.624, y 2 filas valen `0`. El tramo 13–24 admite lectura como período largo real; por encima de mil, no. |
| `counter_type` | string, {`ELEC`, `GAZ`} | Tipo de medidor. |

## Reglas de validación que aplica `src/steg/data/load.py`

Falla ruidosamente (levanta `SchemaValidationError`) ante:

- Columnas faltantes o columnas no esperadas en cualquiera de las cuatro tablas.
- `client_id` duplicado en `client_train` o `client_test`.
- Un `client_id` en `invoice_*` sin fila correspondiente en `client_*`.
- Solapamiento de `client_id` entre `client_train` y `client_test`.

No repara nada: reparar es trabajo de `src/steg/data/clean.py` (ver reglas y sus conteos
reales en `reports/EDA/00_data_audit.md`). La razón de separar carga de limpieza es que
si `load` empezara a corregir en silencio, un cambio futuro en el CSV podría colarse sin
que nadie lo note.

## Qué hacer ante un valor inesperado que no está en esta tabla

1. No lo descartes ni lo "arregles" a ojo. Perfílalo con
   `src/steg/eda/profile.py::profile_dataframe` y compara contra esta skill.
2. Si contradice el README oficial (`data/raw/README.md`), dilo explícitamente — no
   asumas cuál de los dos tiene razón.
3. Si es una anomalía nueva, propone una regla de limpieza que **marque** (columna
   booleana), no que borre, salvo que sea una fila exactamente duplicada. Ver el patrón
   en `src/steg/data/clean.py`.
4. Actualiza esta skill y `src/steg/config.py::DataContract` en el mismo cambio que el
   código.
