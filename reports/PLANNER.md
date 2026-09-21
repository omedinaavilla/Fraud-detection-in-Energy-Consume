# Planner — STEG

Documento vivo. Registra la evolución metodológica del proyecto tarea por tarea, con
trazabilidad **Tarea → Ejecución → Resultado → Análisis → Conclusión → Decisión →
Siguiente paso**. Formato y reglas de actualización en
`.claude/skills/steg-execution-loop/SKILL.md`. Cada agente ejecutor agrega su propia
entrada al terminar una tarea relevante, antes de pasar a la siguiente; no reescribe la
entrada de otro. Redacción en español académico natural, sin mencionar la arquitectura
interna de agentes (`.claude/skills/steg-human-academic-prose/SKILL.md`).

Empieza a llenarse desde 2026-09-18 (segunda revisión del día) en adelante. El trabajo
anterior a esta fecha — Fase 0 y Fase 1 completas, cuatro decisiones de evaluación
propuestas y pendientes de cierre por el usuario — está documentado en
`reports/DECISIONS.md` y en `reports/EDA/`, y no se retrofitea aquí.

---

<!-- Nueva entrada abajo de esta línea, agregada por el agente ejecutor que la genera. -->

## 2026-09-18 — Reescribir en registro académico la prosa interpretativa de la Fase 1

**Fase / agente:** Fase 1 (análisis exploratorio) — exploración de datos.

**Qué debía hacerse:** dejar el registro narrativo de la Fase 1 en un tono de informe
académico, apto para lectura externa, sin que ninguna cifra, tabla, figura, hallazgo o
conclusión cambiara de valor. La fuente de verdad es `notebooks/01_eda.ipynb`; los cuatro
informes de `reports/EDA/` son su exportación y no se editan por separado.

**Qué se hizo:** se reescribieron las 33 celdas de markdown interpretativo del notebook, el
texto literal de las seis celdas de exportación de la sección 10 y dos pies de figura,
dejando intactas las interpolaciones que inyectan las cifras calculadas. La cabecera común de los
informes pasó de una nota de generación automática a una nota de reproducibilidad que
remite al notebook y fecha la ejecución. Se eliminaron las construcciones del tipo «no es
X, es Y», las enumeraciones anunciadas por costumbre y los intensificadores sin cifra, y
se sustituyeron las referencias a documentos internos de configuración y a roles de
ejecución por la fase del pipeline correspondiente. La exportación se regeneró ejecutando
el notebook completo con
`python -m nbconvert --to notebook --execute --inplace 01_eda.ipynb --ExecutePreprocessor.timeout=3600`.

**Qué se encontró:** los 29 CSV de `reports/tables/` quedaron byte a byte idénticos a los
de la ejecución anterior. Los cuatro informes conservan exactamente la misma secuencia de
cifras (407, 301, 320 y 67 tokens numéricos) salvo la fecha de ejecución de la cabecera. El
contraste directo de dieciséis afirmaciones repartidas entre los cuatro informes contra su
tabla de origen coincide en los dieciséis casos, entre ellas la mediana 274 y el máximo
999.910 de `consommation_level_1`, el D de Kolmogorov-Smirnov de `new_index` (0,0091 frente
a un crítico de 0,0043), los 20.365 valores de `counter_number` compartidos, el 6,46 % de
clientes con primera factura anterior al alta con su intervalo de Wilson [6,33 %, 6,59 %],
el rank-biserial de `exp_n_counters` (0,415, IC 95 % [0,404, 0,425]) y el recall techo de
66,1 % para una lista de 5.000 clientes.

Dos hallazgos colaterales. La celda que escribe el bloque de propuestas en
`reports/DECISIONS.md` truncaba el archivo desde su propia marca hasta el final, de modo
que una nueva ejecución habría borrado las 178 líneas de entradas posteriores a ese bloque;
ahora lo sustituye en su sitio y conserva la cola. Y la sección 9 del notebook cita de
memoria un rango de 1.487 a 1.540 positivos por pliegue, mientras que
`evaluation_fold_prevalence.csv` y el informe exportado dan 1.486 a 1.549 para el esquema
agrupado.

**Qué significa:** el contenido analítico de la Fase 1 es estable frente a la reescritura,
lo que confirma que la separación entre cálculo (funciones de `src/steg/eda/`) y narrativa
(notebook) funciona como se diseñó. La discrepancia del rango de positivos por pliegue
afecta solo a una frase escrita a mano dentro del notebook: el informe, la tabla y la
bitácora de decisiones usan el valor calculado, así que ninguna decisión se apoya en la
cifra desfasada.

**Decisión tomada:** ninguna metodológica; el cambio es de redacción. La cifra desfasada de
la sección 9 se dejó intacta en la primera ronda y se planteó al usuario, por tocar una
afirmación numérica y no el registro; la revisión posterior pidió corregirla y se corrigió
en la ronda 2.

**Por qué:** una reescritura de estilo que además ajusta cifras deja de ser verificable: la
única forma de sostener que «ninguna cifra cambió» es que la comparación numérica antes y
después sea exacta.

**Implicaciones para lo siguiente:** las cuatro propuestas de evaluación siguen abiertas y
son el bloqueo real para empezar la Fase 3. El rango de positivos por pliegue quedó
corregido en la ronda 2, con lo que la única cifra de la Fase 1 escrita a mano desapareció
del notebook.

**Ronda 2 — correcciones exigidas por la revisión.** La revisión devolvió FAIL con cinco
observaciones, todas sobre texto de esta misma tarea, y las cinco quedaron resueltas.

La sección 9 afirmaba que ninguna variable exploratoria alcanza |rank-biserial| ≥ 0,3
cuando cuatro lo superan, y la afirmación además contradecía al informe exportado, que ya
citaba 0,415 para `exp_n_counters`. La sección pasó de celda de texto a celda que compone
su propia prosa con las cifras interpoladas desde el diccionario `ev`, igual que hacen las
celdas que escriben `04_implicaciones.md` y el bloque de `reports/DECISIONS.md`; ahora dice
que ninguna supera 0,42, que la de mayor señal llega a 0,415 y que 24 de 39 pasan el umbral
de 0,1, con todos esos números tomados de `bivariate_numeric_target.csv`.

El rango de positivos por pliegue escrito a mano (1.487 a 1.540) se sustituyó por el
calculado, 1.486 a 1.549, nombrando el esquema: ese rango es el de la validación cruzada
agrupada por cliente, mientras que el estratificado va de 1.442 a 1.552. La misma precisión
se aplicó al error estándar relativo del 2,6 %, que se estima sobre el pliegue más pequeño
de los dos esquemas, el de 1.442 positivos, y que hasta ahora leía como si describiera los
mismos pliegues que el rango anterior. La tasa base de 7.566 positivos sobre 135.493
clientes pasó a citar `evaluation_metric_baselines.csv`, que es donde vive, y
`evaluation_fold_prevalence.csv` quedó como fuente solo del reparto por pliegue.

Quedaban dos restos de registro: un pie de figura que citaba un documento interno de
configuración, reformulado como referencia al contrato de datos de la Fase 0, y los incisos
entre guiones largos, eliminados en los seis puntos donde aparecían. Tras la corrección no
queda ningún inciso de ese tipo en los cuatro informes ni ninguna referencia interna en el
notebook.

**Verificación de la ronda 2:** los 29 CSV de `reports/tables/` siguen siendo idénticos a
los previos a la tarea, y dieciocho afirmaciones contrastadas contra su tabla de origen
coinciden, entre ellas las tres cifras corregidas (0,415 para `exp_n_counters`, 1.486–1.549
por pliegue agrupado y 1.442 en el pliegue más pequeño de los dos esquemas).

**Auditoría:** FAIL en ronda 1 (cinco observaciones sobre texto de esta tarea, ninguna sobre
el cálculo); corregidas y devuelto a revisión en ronda 2.

## 2026-09-18 — Restaurar el guard de regresión de `fold_prevalence`

**Fase / agente:** Fase 1-2 (exploración y protocolo de evaluación) — exploración de datos.

**Qué debía hacerse:** dejar en verde las tres pruebas de
`tests/test_eda_bivariate_guard.py` que fallaban con `KeyError: 5`, porque mientras
estuvieran rojas el guard que protege las cifras por pliegue citadas en las cuatro
propuestas de evaluación no estaba comprobando nada.

**Qué se hizo:** las tres pruebas llamaban `grouped_kfold_splits(frame, N_SPLITS)` pasando
el número de folds en la segunda posición, que en la firma corresponde a `group_col`. El
valor `5` llegaba así como nombre de columna de agrupación y pandas lo rechazaba al
indexar. Las cuatro llamadas afectadas pasaron a usar `n_splits=N_SPLITS`, la forma que ya
empleaba el resto del archivo y el notebook.

**Qué se encontró:** `pytest tests/ -q` pasó de 3 fallos y 146 pruebas en verde a 149 en
verde con una omitida. No hay ninguna llamada posicional restante a `grouped_kfold_splits`
en `src/`, `tests/` ni en el notebook.

**Qué significa:** el defecto estaba en las pruebas y no en `grouped_kfold_splits` ni en
`fold_prevalence`, de modo que las cifras por pliegue publicadas en `reports/EDA/` y en
`reports/DECISIONS.md` nunca estuvieron comprometidas; lo que faltaba era la red que las
protege de una regresión futura. El guard vuelve a comparar la salida de `fold_prevalence`
contra su referencia congelada.

**Decisión tomada:** corregir las llamadas en las pruebas y no tocar la firma de
`grouped_kfold_splits`.

**Por qué:** `group_col` como segundo parámetro posicional es coherente con el resto del
módulo de particiones y la firma está usada correctamente en todas partes menos en esas
tres pruebas; cambiar la firma para acomodar un error de llamada rompería el código que sí
la usa bien.

**Implicaciones para lo siguiente:** cualquier cambio futuro en el esquema de partición,
incluida la eventual adopción de `StratifiedGroupKFold` que plantea la cuarta propuesta,
queda cubierto por un guard que vuelve a ejecutarse de verdad.

**Auditoría:** pendiente, ronda 1.

## 2026-09-18 — Rehacer desde cero la exploración de datos (fases 0, 1 y 2)

**Fase / agente:** Fases 0 a 2 (contrato de datos y auditoría de calidad, exploración,
conclusiones para el protocolo de evaluación) — exploración de datos.

**Qué debía hacerse:** repetir el análisis exploratorio completo como ejecución nueva e
independiente, siguiendo una rúbrica metodológica explícita (comprender el problema antes
de calcular, inspección básica antes de cualquier estadístico, calidad tratada como
detectar → cuantificar → investigar → interpretar, univariado condensado por grupos de
variables en vez de un gráfico por columna, y bivariado dirigido por el problema en vez de
por todas las combinaciones posibles). El resultado anterior quedó archivado en
`reports/_archive_2026-09-18/` y no se reutilizó: ni el cuaderno, ni los informes, ni las
tablas, ni las figuras, ni las cuatro propuestas previas.

**Qué se hizo:** se amplió la auditoría reproducible de la fase 0 con un catálogo de
verificaciones de calidad (`reports/tables/quality_checks.csv`, 60 comprobaciones) y una
comparación del esquema real contra el diccionario oficial
(`schema_vs_readme.csv`), de modo que `00_data_audit.md` pasó de listar dimensiones y
conteos de limpieza a sostener nueve apartados con su evidencia. La fase 1 se reconstruyó
en `notebooks/01_eda.ipynb`, 81 celdas que producen 37 tablas, 18 figuras y cinco informes
en `reports/EDA/`. Los hashes SHA-256 de los cuatro CSV se recalcularon y coinciden con los
registrados, así que los resultados nuevos y los archivados provienen del mismo dato.

**Qué se encontró:** la tasa de fraude crece del 0,64 % al 9,76 % entre el decil de
clientes con menos facturas y el de más, un factor de 15,2
(`confounding_history_length.csv`). Los agregados que encabezan el ranking de tamaño de
efecto miden longitud de historial y no comportamiento de consumo: `exp_n_counters` llega a
0,415 de rank-biserial y `exp_new_index_max` a 0,305, frente a 0,062 de la mediana de
consumo. Al recalcular cada efecto dentro de estratos de longitud comparable
(`confounding_conditional_effects.csv`), `exp_new_index_max` cae a −0,015 en el quintil de
historial más largo mientras `exp_n_counters` conserva entre 0,22 y 0,40 en los cinco.

La misma confusión aparece en las banderas de anomalía de captura. Un cliente con al menos
una factura duplicada por clave lógica tiene un riesgo relativo de 2,16 (IC 95 %
[1,92, 2,42]), pero la proporción de facturas duplicadas sobre su historial da 0,019 de
rank-biserial, y el riesgo de la marca binaria se atenúa de 2,31 a 1,26 del quintil de
historial más corto al más largo (`confounding_flags.csv`).

La investigación de las cinco anomalías que el conteo no explicaba
(`quality_deepdive.csv`) cambió la lectura de tres: 17.768 de los 18.363 grupos con clave
lógica repetida difieren en consumo o índices y por tanto no son copias; los cuatro valores
imposibles de `reading_remarque` son códigos válidos de `counter_code`, lo que identifica
el defecto como columnas desplazadas en la captura; y `months_number` mezcla períodos
largos plausibles de 13 a 24 meses con valores que superan los mil. Se añadieron al
contrato de datos tres hallazgos que no estaban registrados: 46 facturas con
`counter_coefficient` igual a cero, dos con `months_number` igual a cero, y las categorías
`tarif_type` 18 y `counter_code` 0, 1 y 367, presentes solo en entrenamiento.

**Qué significa:** la etiqueta registra fraude detectado y la detección exige haber sido
inspeccionado, de modo que un historial largo implica más ocasiones de inspección. Parte de
lo que un modelo aprendería como señal es exposición acumulada. No invalida el problema,
pero obliga a tratar con sospecha toda variable de volumen acumulado en la fase de
construcción de variables, a distinguir señal de exposición al leer importancias, y a
reportar el desempeño desagregado por longitud de historial. Es el hallazgo que separa esta
ejecución de la anterior, que ordenaba los mismos tamaños de efecto sin preguntarse de
dónde venían.

**Decisión tomada:** ninguna de las cuatro decisiones diferidas queda cerrada. Las cuatro
se escribieron como propuesta con su evidencia y al menos dos alternativas con su riesgo,
en el bloque delimitado de `reports/DECISIONS.md`, que sustituye a las propuestas previas
sin tocar el resto del archivo. Sí se decidieron dos cosas de alcance propio de esta fase:
conservar los duplicados por clave lógica en vez de eliminarlos, porque difieren en
contenido y borrarlos restaría consumo facturado, y no recortar ni winsorizar los atípicos
de consumo, porque la tasa de fraude crece con el consumo máximo del cliente a lo largo de
casi todo el recorrido (`outliers_target_rate.csv`).

**Por qué:** el volumen de positivos por pliegue (entre 1.486 y 1.549) y la dispersión de
la prevalencia entre pliegues (0,0873 puntos porcentuales frente a 0,1395 esperados por
azar) permiten sostener las propuestas con evidencia propia y no por analogía con la
literatura. Mantener las cuatro abiertas respeta que la elección de métrica y de punto de
operación depende de la capacidad de inspección real, que es información que el conjunto
de datos no contiene.

**Implicaciones para lo siguiente:** la fase de construcción de variables arranca con tres
restricciones ya documentadas. La codificación de categóricas tiene que resolver el caso de
una categoría vista solo en entrenamiento. Los 4.212 clientes con una sola factura y los
15.269 con tres o menos no deberían descartarse, porque su tasa de fraude del 0,64 % los
convierte en un grupo genuinamente de bajo riesgo cuya eliminación alteraría la prevalencia.
Y el recorte de la ventana temporal, si se hace, tendrá que justificarse por comparabilidad
entre clientes y no por evitar fuga temporal, porque la separación entre las dos particiones
es aleatoria por cliente y no cronológica (`temporal_train_test_last_year.csv`).
