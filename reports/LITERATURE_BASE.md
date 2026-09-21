# Base de literatura: antecedentes metodológicos

Documento de referencia. Recoge y examina dos trabajos publicados sobre detección de
fraude y de pérdidas no técnicas (NTL) en distribución eléctrica a partir de datos de
facturación. Su función es dejar disponible el estado de la práctica con suficiente
detalle como para poder contrastarlo más adelante contra la evidencia de los datos
propios. Ninguna de las decisiones descritas aquí está adoptada por este proyecto: cada
etapa (limpieza, variables, partición, modelo, métrica, umbral) se resuelve con la
evidencia del conjunto de datos disponible y con el objetivo del estudio, y los
antecedentes solo aportan el repertorio de alternativas y los riesgos ya documentados.

Las cifras que aparecen atribuidas a un autor son cifras suyas, medidas sobre sus datos y
bajo su protocolo. No son resultados de este estudio ni cotas esperables para él.

## Criterio de selección y transparencia sobre la búsqueda

La prioridad de búsqueda fue trabajo publicado sobre el mismo conjunto de datos: la
competencia de Zindi *Fraud Detection in Electricity and Gas Consumption Challenge*, con
datos de facturación de la Société Tunisienne de l'Électricité et du Gaz (STEG),
estructurados en una tabla de clientes y una tabla de historial de facturas.

Sobre esa competencia no existe documentación metodológica publicada por los ganadores.
La página oficial del reto lo describe como competencia de aprendizaje sin premio
monetario, con 3.576 participantes inscritos y 775 activos, evaluación por AUC y sin
división entre tabla pública y privada. Ese formato explica la ausencia de *writeups* de
solución: el material accesible de participantes se limita a repositorios con notebooks
sin justificación metodológica (por ejemplo `matzolla/STEG_fraud_detection...`,
`imgremlin/Fraud-Detection-by-Zindi`, `janejeshen/Fraud-Detection-in-Electricity-and-Gas-Consumption-in-tunisia`,
`AmirFARES/Tunisia_Energy_Fraud_Detection_STEG`), a entradas de blog divulgativas en
Medium y al tutorial introductorio publicado por Zindi. Ninguno desarrolla problema,
datos, metodología, entrenamiento, evaluación y resultados con el nivel que exige servir
de antecedente citable, por lo que todos quedaron descartados.

La preferencia por un documento vinculado a la competencia se cubrió por la vía
disponible: un artículo revisado por pares que trabaja exactamente sobre los datos
liberados en ese reto y que lo cita como fuente. El segundo trabajo se eligió sobre el
mismo problema de investigación con datos de otra empresa distribuidora, buscando
deliberadamente que aportara lo que el primero no trae (procedencia de las etiquetas,
sesgo de muestreo, métricas orientadas a la decisión operativa). El apéndice lista los
candidatos revisados y la razón de su descarte.

---

## Paper 1. Oprea y Bâra (2022): ingeniería de variables con funciones analíticas SQL sobre los datos de STEG

**Cita.** Oprea, S.-V., y Bâra, A. (2022). *Feature engineering solution with structured
query language analytic functions in detecting electricity frauds using machine
learning*. **Scientific Reports**, 12, 3257. DOI:
[10.1038/s41598-022-07337-7](https://doi.org/10.1038/s41598-022-07337-7). Acceso abierto;
texto completo consultado en
[PMC8885834](https://pmc.ncbi.nlm.nih.gov/articles/PMC8885834/).

### 1. Problema abordado

Detección de fraude en el consumo eléctrico de clientes medidos con contadores
convencionales, es decir, sin telemetría ni curva de carga. El argumento de los autores es
que el fraude resulta más fácil de detectar con contadores inteligentes, pero que en los
países donde el fraude es mayor esos equipos todavía no son asequibles, de modo que la
única señal disponible es el historial de facturación. Sobre esa señal, separar consumidores
normales de sospechosos es difícil porque el contador convencional no registra
periodicidad ni variabilidad del consumo.

### 2. Datos

Los datos provienen de STEG (Túnez) y los autores los citan explícitamente como
"Zindi. *Fraud Detection in Electricity and Gas Consumption Challenge* (2019)". Son dos
archivos: `client`, con 135.493 registros y 6 variables (`client_id`, `district`,
`client_categ`, `region`, `creation_date`, `target`), e `invoice`, con 4.471.651 registros
y 16 variables (`client_id`, `invoice_date`, `tarif_type`, `counter_number`,
`counter_statue`, `counter_code`, `reading_remarque`, `counter_coefficient`,
`consommation_level_1` a `consommation_level_4`, `old_index`, `new_index`,
`months_number`, `counter_type`). Tras la unión reportan 4.476.749 filas y 21 columnas en
su primer escenario.

Sobre el desbalance afirman: "The analyzed dataset is highly unbalanced as the ratio is
12:1". No reportan la tasa de positivos como porcentaje ni la desagregan por categoría de
cliente, y no describen el rango temporal cubierto por las facturas.

### 3. Limpieza

Describen una exploración previa que examina "Gaussian distribution, missing values,
outliers, etc." y luego un preprocesamiento que consiste en conversión de cadenas a fecha,
extracción de mes, año y condición de día laborable o fin de semana, codificación de
categóricas, cálculo de variables derivadas (consumo mensual y diario, `delta index`,
`delta time`) y eliminación de variables redundantes. El resumen de la operación de
saneamiento es literalmente "encoding and mapping some seldom values to the most frequent
ones, correcting the inconsistent data and eliminating missing values".

### 4. Faltantes y atípicos

Los faltantes se eliminan, sin que el artículo cuantifique cuántos registros se pierden ni
en qué variables se concentraban. Las categorías poco frecuentes se recodifican hacia la
categoría más frecuente. Los atípicos no reciben tratamiento explícito de recorte o
winsorización: se abordan por la vía del escalado, comparando `MinMaxScaler`,
`StandardScaler`, `RobustScaler` y `Normalizer`, con la observación de que "*RobustScaler*
is much better when there are numerous outliers". Queda sin definir la regla con la que se
declara atípico un registro.

### 5. Construcción de variables

Es la contribución central del artículo, presentada como novedad: "To the best of our
knowledge, the SQL analytic functions have not been implemented yet to create new
features". El mecanismo consiste en aplicar funciones analíticas sobre la tabla de detalle
(facturas) con una cláusula `PARTITION BY` (por ejemplo tipo de tarifa o distrito), una
cláusula `ORDER BY` (típicamente fecha de factura) y una ventana `ROWS` o `RANGE` relativa
a la fila actual. Las funciones empleadas son `dense_rank`, `first`, `lag`, `last`, `lead`,
`max`, `min`, `percent_rank`, `rank` y `ratio_to_report`.

En paralelo agregan el detalle por `client_id` y `counter_type` con `min`, `mean`,
`median`, `max`, `sum`, `std` y `var`, y derivan rangos (`max − min`) y razones
(`max / mean`). El paso que llaman doble fusión encadena las dos vías: "The aggregated
datasets `agg_dfidetail` are merged with the pre-processed master dataset
`pp_dfimaster`, and the result is again merged with the analytic detail datasets". El
resultado son "almost 200 new features", pensadas para capturar picos de consumo dentro
del propio historial del cliente y comparaciones contra clientes semejantes.

Sobre ese espacio aplican selección por puntaje de Fisher y se quedan con quince
variables para entrenar. El artículo no nombra cuáles son esas quince.

### 6. Partición de datos

Un único corte aleatorio, descrito como `split(red_X, y, sample_size) → X_train, y_train,
X_test, y_test` con `sample_size ∈ 0,1 ÷ 0,3`. No hay validación cruzada, ni repeticiones
con semillas distintas, ni intervalos de confianza. Tampoco hay partición temporal ni
conjunto de validación separado del de prueba para ajustar hiperparámetros.

### 7. Manejo del desbalance

Aplican SMOTE y ADASYN exclusivamente al conjunto de entrenamiento y argumentan por qué no
al de prueba: balancear los datos de evaluación arriesga "obtaining an algorithm that
overall detects more fake or synthetically created fraudsters than real ones". El efecto
medido que reportan es modesto: con SMOTE y razón de muestreo 0,5 el AUC llega a 0,7281, y
al subir la razón a 1,0 llega a 0,7331. ADASYN no mejoró los resultados.

### 8. Decisiones metodológicas principales y su justificación

- Construir variables con funciones analíticas de ventana en lugar de solo agregados, con
  el argumento de que el ordenamiento y la partición permiten expresar el comportamiento
  del cliente respecto de su propio pasado y respecto de sus pares, que es la forma en que
  se manifiesta la irregularidad cuando no hay curva de carga.
- Encadenar dos fusiones para llevar a nivel de cliente tanto los agregados del historial
  como las variables de ventana, en vez de resolver todo con un solo `group by`.
- Reducir de más de doscientas variables a quince por puntaje de Fisher, con el argumento
  de que "selecting the right set of features or reducing dimensionality for
  classification is significant".
- Fijar hiperparámetros a mano en lugar de buscarlos: mencionan `GridSearchCV` y Optuna,
  pero los consideran demasiado costosos en tiempo con conjuntos de este tamaño, y
  resuelven por compromiso entre desempeño y costo computacional.
- Incorporar el resultado de un algoritmo no supervisado como variable adicional:
  "a new feature is created with an unsupervised algorithm to better identify anomalies in
  consumption, Isolation Forest". Reportan que en el primer escenario esa variable no
  mejoró el desempeño.

### 9. Técnicas y modelos

Dos escenarios. El Escenario 1 es la línea base, "a classic data pre-processing procedure
and feature processing", donde "outliers, non-numerical and missing values are handled",
y compara regresión logística, descenso de gradiente estocástico, XGBoost, árbol de
decisión, bosque aleatorio, perceptrón multicapa, LightGBM, análisis discriminante
cuadrático, CatBoost y AdaBoost. El Escenario 2 es la propuesta, donde "an extensive
calculation is performed using SQL analytic functions and aggregation, joining the
datasets, and inserting features that reflect the anomaly in data", y se reduce a
regresión logística, XGBoost, árbol de decisión y bosque aleatorio, más Isolation Forest
como generador de variable.

Los hiperparámetros reportados son escasos: árbol de decisión con `max_depth = 10` y
criterio de entropía; bosque aleatorio con `max_depth = 5` y `n_estimators = 200`. Para
XGBoost no se reportan.

### 10. Entrenamiento y evaluación

Calculan precisión, exhaustividad, F1, exactitud y AUC, con las fórmulas explícitas de
precisión y exhaustividad. El diagnóstico se apoya en curvas ROC, matrices de confusión y
curvas de aprendizaje y de validación, usadas para detectar sobreajuste o subajuste. La
evaluación es de un solo corte, sin repetición, por lo que no hay dispersión reportada
alrededor de ninguna cifra.

### 11. Resultados principales

En el Escenario 1 el árbol de decisión alcanza AUC 0,6805, con precisión 0,40,
exhaustividad 0,41 y F1 0,41 en la clase fraude, exactitud 0,91 y una tasa de falsos
positivos cercana a 5,22 %. El mejor AUC del escenario base, tras escalado, ampliación de
variables y SMOTE, queda en 0,7331.

En el Escenario 2 reportan árbol de decisión con AUC 0,997, precisión 0,99, exhaustividad
0,98 y exactitud 0,997695; bosque aleatorio con AUC 0,990, exhaustividad 0,67 en la clase
fraude y exactitud 0,973896, con 46 falsos positivos sobre 412.385 casos no fraude;
XGBoost con AUC 0,776 y exhaustividad 0,13; regresión logística con AUC 0,616. La
conclusión que extraen es haber identificado "97.67% of the fraudsters" con "0.05% false
positive", y resumen el aporte del método como una mejora de AUC "from 0.68 to 0.99".

### 12. Limitaciones reconocidas por los autores

- Alcance de la replicación: "As a limitation, the proposed approach can only be
  replicated for similar datasets measured by conventional meters", aunque sostienen que
  las funciones analíticas sirven igualmente para datos de contador inteligente.
- Calidad de los datos de origen, con "missing and inconsistent records, faults,
  misinterpretation of meter reading remarks, status, etc.".
- Dependencia débil entre variables y etiqueta: "The main problem lies in the lack of
  correlation between data features and target. If the target is less dependent on the
  input variables, the model has real issues to learn."
- Dificultad persistente del desbalance severo y el compromiso entre precisión y
  exhaustividad.
- Trabajo futuro orientado a lecturas de contadores inteligentes.

### Observaciones de lectura crítica

No son afirmaciones de los autores, sino puntos a verificar antes de usar sus cifras como
referencia:

- El salto de AUC 0,68 a 0,997 no tiene explicación en el texto. El artículo documenta
  ganancias incrementales pequeñas por escalado (0,6812), por ampliación de variables
  (0,6993) y por SMOTE (0,7331), y no hay ninguna frase que conecte esa progresión con el
  valor final del Escenario 2.
- Las variables de ventana se calculan con `PARTITION BY` y `ORDER BY` sobre el conjunto
  completo antes de la partición, y el doble merge reintroduce a nivel de cliente
  estadísticos calculados sobre poblaciones que incluyen registros del conjunto de prueba.
  Es un patrón compatible con fuga de información, y el artículo no discute el riesgo: la
  única mención a sobreajuste es el uso de `max_depth = 10`.
- La evaluación descansa en un solo corte aleatorio sin validación cruzada, y las quince
  variables finalmente usadas no se nombran, lo que impide reproducir el Escenario 2.
- Alcanzar exhaustividad 0,98 sobre la misma señal de facturación en la que el Escenario 1
  se quedaba en 0,41 es una diferencia demasiado grande para atribuirla a ingeniería de
  variables sin una comprobación independiente.

El valor del artículo para un proyecto sobre estos datos está entonces en su inventario de
transformaciones aplicables a la estructura cliente más historial de facturas, no en las
cifras de desempeño que reporta.

---

## Paper 2. Coma-Puig y Carmona (2022): regresión sobre energía recuperable y explicabilidad en detección de NTL

**Cita.** Coma-Puig, B., y Carmona, J. (2022). *Non-technical losses detection in energy
consumption focusing on energy recovery and explainability*. **Machine Learning**, 111(2),
487–517 (publicado en línea el 29 de septiembre de 2021). DOI:
[10.1007/s10994-021-06051-1](https://doi.org/10.1007/s10994-021-06051-1). Acceso abierto.

### 1. Problema abordado

Detección de pérdidas no técnicas en una empresa distribuidora real, Naturgy (España),
con un sistema ya en operación. El artículo parte de tres obstáculos concretos que los
autores encontraron al desplegar un clasificador supervisado convencional: robustez
técnica insuficiente cuando la campaña de inspección es genérica, porque los datos de
entrenamiento son observacionales y no representativos; eficiencia económica pobre, porque
el sistema tiende a señalar casos de NTL de poca energía en lugar de fraudes de alto valor;
y falta de transparencia, porque un modelo de caja negra no permite al personal de la
empresa validar los patrones aprendidos.

### 2. Datos

Cuatro dominios definidos por el cruce de dos regiones (A, B) y dos tarifas (1, 2), con
clientes de potencia contratada inferior a 10 kW. El tamaño lo describen así: "The domain
D_{A1} (i.e. the customers from region A and tariff 1) has more than 1,000,000 customers,
and domain D_{B2} has less than 50,000 customers. The other two datasets fall between
these two datasets in terms of population. The proportion of the NTL cases in each domain
is lower than 5%. We have around 300,000 labelled instances for the D_{A1} domain, several
thousand cases for D_{A2} and D_{B1}, and several hundred cases for D_{B2}."

Las fuentes son registros históricos de consumo, informes de visitas de técnicos, lecturas
de contador e información estática del cliente. La actualización del consumo es mensual.
El punto decisivo es el origen de la etiqueta: proviene de campañas históricas de
inspección, no de un censo, y la empresa "visits more customers suspected of NTL", lo que
sobrerrepresenta a reincidentes y produce zonas geográficas con etiquetado desigual. Los
autores lo nombran explícitamente como datos observacionales producidos con otro
propósito.

### 3. Limpieza

El artículo no organiza la preparación como una etapa de saneamiento separada. El trabajo
de calidad se concentra en la definición de las variables y en la corrección iterativa de
las que resultan sesgadas o dominadas por valores extremos, diagnosticada mediante
diagramas de valores de Shapley.

### 4. Faltantes y atípicos

Tratados como parte del diseño de variables y no con imputación o recorte global. La
ausencia de lectura se convierte en información: entre las variables que analizan
figuran meses sin consumo y ausencias de lectura, que pasan a ser señal en lugar de hueco
a rellenar. Los atípicos se identifican por su efecto sobre las atribuciones del modelo y
se atenúan reduciendo su peso o eliminando la variable implicada.

### 5. Construcción de variables

Alrededor de 150 variables agrupadas en cuatro familias con significado de negocio:

- **Consumo**: consumo crudo en ventanas de doce y de tres meses, diferencias entre el
  consumo actual y el histórico del propio cliente, comparación contra clientes
  semejantes, picos anómalos y meses sin consumo.
- **Visitas**: historial de casos de NTL detectados, visitas sin hallazgo, visitas
  imposibles de realizar, incidentes con el técnico.
- **Estáticas**: tarifa, ubicación del contador, tipo de inmueble.
- **Sociológicas**: renta de la zona, desempleo, características del vecindario como
  aproximación a la densidad de fraude.

### 6. Partición de datos

"Each model is trained using the same 80% of the positive instances and 80% of the
negative instances. We split in half 20% of instances left, keeping the positive/negative
ratio, to build the validation dataset". El conjunto de validación se usa para ajustar
hiperparámetros y el de prueba queda aparte. La elección de partición aleatoria
estratificada frente a partición temporal está justificada de forma explícita: "The random
partition is chosen over considering the timestamp (e.g. the last 10% of NTL cases as the
test dataset) to guarantee diversity and reduce the differences."

### 7. Manejo del desbalance

No aplican remuestreo. Con menos de 5 % de positivos en cada dominio, el desbalance se
aborda por dos vías distintas del sobremuestreo: la función de pérdida, que al pasar a
regresión sobre kWh deja de tratar todos los positivos como equivalentes, y la métrica de
evaluación, que es de ordenamiento y no depende de un umbral de decisión.

### 8. Decisiones metodológicas principales y su justificación

- **Reformular el problema de clasificación binaria a regresión sobre la energía
  recuperable.** El argumento es que la etiqueta binaria trata igual a fraudes de duración
  y magnitud muy distintas: "By breaking the NTL/non-NTL binary representation... the
  system should focus on learning patterns from high NTL cases". La conclusión que
  reportan es que la regresión "provides better results than the classical classification
  approach, recovering more energy but especially learning more reliable patterns".
- **Elegir RMSE en lugar de MAE** como pérdida de la regresión, porque "The square of the
  errors means higher errors have more weight in RMSE", lo que encaja con un problema de
  ordenamiento donde interesa no equivocarse en los casos grandes.
- **Evaluar con métricas de ordenamiento y de negocio en lugar de una métrica escalar de
  clasificación**, dado que reconocen "the difficulty of benchmarking our NTL system on
  validation datasets and a scalar metric" cuando el conjunto de validación hereda el
  sesgo de las campañas.
- **Usar valores de Shapley como instrumento de validación del modelo, no solo de
  presentación.** Descartan la importancia global de variables por ser únicamente global e
  insuficiente para validar una instancia, y descartan LIME por su componente aleatorio y
  la dificultad de configurarlo; se quedan con TreeSHAP por consistencia, robustez y costo
  computacional manejable.
- **Cerrar el ciclo con intervención humana**: el experto de la empresa revisa las
  atribuciones, detecta sesgos y valores extremos, se modifica la ingeniería de variables
  y se reentrena.

### 9. Técnicas y modelos

CatBoost en ambas formulaciones, con `LogLoss` como pérdida en la variante de
clasificación y RMSE en la de regresión. La parada temprana se controla con *Average
Precision Score* en clasificación y con RMSE en regresión. Sobre las predicciones aplican
un post-procesado basado en reglas construidas a partir de las atribuciones de Shapley,
que descarta casos en los que la variable de mayor contribución no es de consumo.

### 10. Entrenamiento y evaluación

Tres instrumentos de evaluación, todos orientados a la decisión de a quién inspeccionar:

- **NDCG_n**, ganancia acumulada descontada normalizada, `NDCG_n = DCG_n / IDCG_n` con
  `DCG_n = Σ (Rel_i − 1) / log₂(i + 1)`, que evalúa la calidad del ordenamiento sin
  necesidad de fijar umbral.
- **Energía recuperada en kWh** en los primeros n clientes del ranking, con n definido
  como el número de casos de NTL del conjunto de prueba dividido entre 2, 5, 10 y 25, es
  decir, simulando campañas de inspección de distinto tamaño.
- **Precision@k**.

Para interpretar la energía recuperada fijan bandas operativas: por encima de 3.500 kWh
caso prioritario, entre 2.000 y 3.500 kWh importante, entre 500 y 2.000 kWh prioridad
secundaria, y por debajo de 500 kWh posible ruido o efecto del sesgo de los datos.

### 11. Resultados principales

La regresión supera a la clasificación en NDCG en los cuatro dominios y en los cuatro
tamaños de campaña, y la ventaja crece al reducir el tamaño de la campaña: "the regression
approach is superior to the classification approach; the amount of energy recovered in our
results is usually higher than the energy recovered with the classification models,
especially for small-sized campaigns".

El hallazgo de explicabilidad es tan relevante como el de desempeño. Al examinar las ocho
variables de mayor contribución, el modelo de clasificación apoyaba sus predicciones
mayoritariamente en el historial de visitas, con una sola variable de consumo entre las
ocho, mientras el de regresión usaba cuatro de consumo. Dado que el historial de visitas
es precisamente el reflejo de las decisiones pasadas de la empresa, ese contraste muestra
que el clasificador estaba aprendiendo el proceso de inspección más que el comportamiento
de consumo.

El post-procesado con reglas derivadas de Shapley "outperforms the regression approach by
up to 34%" en energía recuperada por visita realizada.

### 12. Limitaciones reconocidas por los autores

- Los datos etiquetados no son una muestra aleatoria de la población, de modo que el
  supuesto de representatividad no se cumple.
- El desplazamiento de distribución entre los clientes inspeccionados y el conjunto de
  clientes al que se aplicará el modelo.
- La comparación sobre conjuntos de validación sesgados y con una métrica escalar resultó
  inconcluyente, lo que motivó el recurso a la explicabilidad.
- La validación por explicabilidad depende del juicio de un experto y arrastra
  subjetividad, incluida la dificultad de distinguir correlación de causalidad.
- El costo computacional de la interpretabilidad a gran escala sigue siendo un problema
  aun usando TreeSHAP.
- Los sesgos son específicos de cada dominio y de cada campaña, y el procedimiento
  iterativo debe repetirse en lugar de resolverse una vez.

---

## Síntesis metodológica

### Dónde coinciden

Los dos trabajos parten del mismo tipo de insumo: lecturas de consumo agregadas por
período de facturación, sin curva de carga, más atributos administrativos del cliente, y
los dos resuelven el problema llevando el historial a una fila por cliente mediante
variables derivadas. Las familias de variables que construyen son reconociblemente las
mismas dos: comparación del cliente contra su propio pasado y comparación del cliente
contra clientes semejantes. Oprea y Bâra las implementan como funciones de ventana con
partición y ordenamiento; Coma-Puig y Carmona las definen como diferencias respecto del
histórico y razones respecto del grupo de referencia. La coincidencia es de fondo, no de
herramienta: cuando el contador no entrega periodicidad, la irregularidad solo se
manifiesta como ruptura respecto de un patrón propio o ajeno.

Coinciden también en el orden de magnitud del desbalance, con una minoría por debajo de
aproximadamente 8 % en un caso y de 5 % en el otro, y en resolver la partición de forma
aleatoria y no temporal. Coma-Puig y Carmona además justifican esa elección, mientras
Oprea y Bâra la ejecutan sin discutirla. Ambos trabajan con árboles con impulso de
gradiente entre sus modelos principales, y ninguno reporta resultados de modelos lineales
competitivos: en el Escenario 2 de Oprea y Bâra la regresión logística queda en AUC 0,616
frente a 0,99 de los modelos de árbol, y Coma-Puig y Carmona usan CatBoost en ambas
formulaciones sin considerar alternativas lineales.

### Dónde difieren

**Qué se predice.** Oprea y Bâra predicen la probabilidad de que un cliente sea
fraudulento. Coma-Puig y Carmona predicen cuántos kWh se recuperarían al inspeccionarlo, y
argumentan que la etiqueta binaria borra la diferencia entre un fraude marginal y uno
grande. Esta es la divergencia de fondo, porque de ella se derivan la pérdida, la métrica
y el criterio de éxito.

**Cómo se mide el éxito.** El primer trabajo reporta AUC, precisión, exhaustividad, F1 y
exactitud sobre el conjunto completo de prueba. El segundo rechaza depender de una métrica
escalar en presencia de etiquetas sesgadas y evalúa con NDCG y con energía recuperada en
los primeros n del ranking, donde n replica el tamaño real de una campaña de inspección.
La segunda opción responde a la pregunta operativa, a quién visitar primero con
presupuesto limitado; la primera responde a la pregunta estadística, qué tan separables
son las clases.

**Cómo se trata el desbalance.** Oprea y Bâra recurren a sobremuestreo sintético sobre el
entrenamiento, con ganancia medida pequeña (AUC de 0,7281 a 0,7331 al pasar la razón de
muestreo de 0,5 a 1,0) y ADASYN sin efecto. Coma-Puig y Carmona no remuestrean: desplazan
el problema a la pérdida y a la métrica de ordenamiento. Quedan así documentadas dos rutas
distintas, y la evidencia que aporta el primer trabajo sobre el rendimiento del
remuestreo en este tipo de datos es más bien tibia.

**Rigor del protocolo de validación.** El primer trabajo evalúa sobre un único corte
aleatorio, sin validación cruzada ni repeticiones, sin conjunto de validación separado del
de prueba, y con hiperparámetros fijados a mano por costo computacional. El segundo separa
validación de prueba manteniendo la proporción de clases y usa la validación para el
ajuste y la parada temprana. Ninguno de los dos reporta dispersión entre repeticiones ni
intervalos de confianza.

**Tratamiento de la procedencia de la etiqueta.** Coma-Puig y Carmona hacen de esto el eje
del artículo: la etiqueta viene de campañas dirigidas, la empresa inspecciona más a quien
ya sospecha, y por lo tanto el conjunto etiquetado no es una muestra de la población a la
que se aplicará el modelo. Muestran incluso la consecuencia medible de ignorarlo, con un
clasificador cuyas ocho variables más influyentes eran casi todas historial de visitas.
Oprea y Bâra no discuten cómo se generó `target` en los datos de STEG ni qué sesgo de
selección podría arrastrar.

**Credibilidad de las cifras.** El desempeño reportado por Coma-Puig y Carmona es
consistente con un problema difícil, y su mejora se expresa como ganancia relativa en
energía recuperada por visita, hasta 34 %. El desempeño del Escenario 2 de Oprea y Bâra,
con AUC 0,997 y exhaustividad 0,98, contrasta con el 0,73 que ellos mismos obtienen en el
escenario base sobre los mismos datos y con la dificultad que la propia competencia de
Zindi documenta al fijar AUC como métrica de un reto masivamente participado. La
diferencia de protocolo impide una comparación directa, pero la magnitud del salto, junto
con el cálculo de variables de ventana sobre el conjunto completo antes de partir, obliga a
tratar esas cifras como no verificadas.

**Explicabilidad.** Ausente en el primer trabajo, central en el segundo, donde los valores
de Shapley se usan para auditar el modelo y detectar que estaba aprendiendo el proceso de
inspección, y después como insumo de un post-procesado por reglas.

### Qué antecedentes quedan disponibles

Del lado de la construcción de variables sobre la estructura cliente más historial de
facturas: agregados por cliente y por tipo de contador con estadísticos de posición y
dispersión, rangos y razones entre ellos, funciones de ventana con partición por tarifa o
distrito y orden por fecha (`lag`, `lead`, `rank`, `percent_rank`, `ratio_to_report`),
variables de comparación contra el propio histórico en ventanas de distinta longitud,
variables de comparación contra clientes semejantes, conteo de períodos sin consumo o sin
lectura tratado como señal, atributos administrativos estáticos, y la salida de un
detector no supervisado de anomalías como variable adicional.

Del lado del protocolo: partición aleatoria estratificada con validación separada de
prueba y justificación explícita frente a la alternativa temporal; sobremuestreo sintético
restringido al entrenamiento con la advertencia expresa de no tocar el conjunto de prueba;
selección de variables por criterio univariado tipo Fisher cuando la dimensión crece;
fijación manual de hiperparámetros como compromiso frente al costo de la búsqueda.

Del lado de la evaluación: métricas de clasificación por clase con AUC y curvas ROC;
métricas de ordenamiento sin umbral tipo NDCG; métricas de recuperación en los primeros n
del ranking con n atado al tamaño de campaña factible; precision@k; bandas de magnitud
para separar hallazgos relevantes de posible ruido; atribuciones de Shapley como
instrumento de auditoría del modelo y no solo de reporte.

### Qué alternativas quedan abiertas

Los dos trabajos dejan sin resolver, y explícitamente en el caso del segundo, la relación
entre lo que se mide y lo que se decide. Coma-Puig y Carmona reconocen que su comparación
sobre validación sesgada con métrica escalar fue inconcluyente y que los sesgos deben
tratarse dominio por dominio. Oprea y Bâra reconocen que la dependencia entre variables y
etiqueta es débil y que el compromiso entre precisión y exhaustividad sigue abierto.
Quedan por tanto disponibles como alternativas no zanjadas: la elección entre objetivo
binario y objetivo continuo cuando no se dispone de la magnitud recuperada; el uso de
remuestreo frente a ajuste de la pérdida o del umbral; la validación aleatoria frente a la
temporal cuando interesa generalizar a fraude futuro; y la elección de la métrica
principal entre una de separabilidad global y una de ordenamiento en la cabeza de la lista.
Cuál corresponde en cada caso depende de la evidencia de los datos y del uso previsto del
modelo, y se resuelve en la fase correspondiente del estudio.

---

## Apéndice. Candidatos revisados y descartados

| Trabajo | Motivo del descarte |
|---|---|
| Notebooks y repositorios de participantes de Zindi (`matzolla`, `imgremlin`, `janejeshen`, `AmirFARES`), entradas en Medium, tutorial oficial de Zindi | Sin desarrollo de problema, metodología, protocolo de evaluación ni resultados justificados. No citables como antecedente. |
| Oprea, S.-V. y Bâra, A. (2021). *Machine learning classification algorithms and anomaly detection in conventional meters and Tunisian electricity consumption large datasets*. Computers & Electrical Engineering, 94, 107329 | Mismos autores y mismos datos que el trabajo ya incluido, con lo cual aporta poca diversidad metodológica. Texto completo sin acceso. |
| Ghori, K. M. et al. (2020). *Performance Analysis of Different Types of Machine Learning Classifiers for Non-Technical Loss Detection*. IEEE Access, 8, 16033–16048 | Muy pertinente por temática (datos de facturación de una distribuidora en Pakistán, 71 variables, 15 clasificadores), pero no fue posible obtener el texto completo para leerlo, solo el resumen. No se cita lo que no se pudo leer. |
| Buzau, M. M. et al. (2018). *Detection of Non-Technical Losses Using Smart Meter Data and Supervised Learning*. IEEE Transactions on Smart Grid | Datos de contador inteligente con telemetría, distintos de facturación convencional. Acceso cerrado. |
| Glauner, P. et al. (2016). *Large-Scale Detection of Non-Technical Losses in Imbalanced Data Sets*. arXiv:1602.08350 | Aporta el análisis de sensibilidad al nivel de desbalance y el sesgo de inspección, pero los modelos comparados (reglas booleanas, lógica difusa, SVM lineal) alcanzan AUC apenas superior a 0,5 en sus propios resultados, lo que lo hace poco útil como referencia de clasificación. |
| Hussain, S. et al. (2021). *A novel feature-engineered NGBoost machine-learning framework for fraud detection in electric power consumption data*. Sensors, 21(24), 8423 | Usa el conjunto de la State Grid Corporation of China, con lecturas diarias de contador inteligente. La ingeniería de variables es de series temporales densas, no de facturación. |
| Abro, S. A. et al. (2025). *Non-technical loss detection in power distribution networks using machine learning*. Scientific Reports, 15, 36189 | Protocolo limpio sobre consumo mensual de contadores convencionales, con remuestreo aplicado solo al entrenamiento, pero con 2.762 clientes y 23 % de positivos, condiciones muy distantes de un problema con más de cien mil clientes y minoría por debajo de 10 %. |
| Coma-Puig, B. y Carmona, J. (2020). *A Human-in-the-Loop Approach based on Explainability to Improve NTL Detection*. arXiv:2009.13437 | Preprint de los mismos autores con alcance más estrecho que el artículo de Machine Learning finalmente seleccionado. |
