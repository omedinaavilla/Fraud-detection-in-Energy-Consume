# Implicaciones para el modelado y la evaluación — Fase 2

Exportado desde `notebooks/01_eda.ipynb`, que es la fuente de estos resultados. Ejecución del 2026-09-18. Las cifras proceden de `reports/tables/` y las figuras de `reports/figures/`; regenerar el informe exige volver a ejecutar el cuaderno, no editar este archivo.

Cuatro decisiones del protocolo quedaron abiertas hasta tener evidencia. Lo que sigue reúne
la que se generó, con las alternativas razonables y el riesgo de cada una. Ninguna está
cerrada: las entradas correspondientes de `reports/DECISIONS.md` están marcadas como
propuesta.

## Métrica primaria

| referencia | valor | unidad |
|---|---|---|
| exactitud del clasificador que predice siempre la clase mayoritaria | 94,42 | % |
| línea base de PR-AUC (igual a la prevalencia) | 5,58 | % |
| línea base de ROC-AUC | 50 | % |
| ROC-AUC del mejor agregado exploratorio por sí solo (exp_n_counters) | 70,74 | % |
| positivos en entrenamiento | 7.566 | clientes |
| negativos por cada positivo | 16,9 | razón |
| AUC del liderato público del reto (contexto externo, otro protocolo) | 86 | % |

Predecir siempre la clase mayoritaria acierta el 94,42 %, de modo que
la exactitud queda descartada. La línea base de PR-AUC es la prevalencia,
5,58 %. El mejor agregado exploratorio por sí solo alcanza un ROC-AUC de
70,7 %, frente al 86 % del liderato público del reto, que se cita como
referencia de dificultad y no como comparación directa, porque el protocolo es distinto.

Alternativas. PR-AUC como primaria es sensible a la zona de alta precisión, que es donde
opera una lista de inspecciones, pero depende de la prevalencia y no permite comparar
subgrupos con prevalencias distintas. ROC-AUC da comparabilidad externa e interna, con el
inconveniente de promediar regiones del umbral que ninguna operación usaría. Una métrica @k
como primaria sería la más fiel al uso previsto, y exige fijar un k que hoy no se conoce.

## Desbalance

Hay 7.566 positivos de 135.493 clientes
(5,58 %), 16,9 negativos por positivo, y entre
1.486 y 1.549 positivos en cada pliegue de validación
agrupado por cliente (`evaluation_fold_prevalence.csv`). El error estándar relativo al
estimar una proporción sobre un pliegue es del 2,5 %. Es desbalance sin
escasez de casos.

Alternativas. No aplicar ninguna técnica y ajustar el umbral al final es lo más simple y
mantiene las probabilidades calibradas, con el riesgo de que un modelo muy regularizado
ignore la clase minoritaria, algo verificable con los baselines. Ponderar las clases es
barato y suele bastar, pero descalibra las probabilidades y obliga a recalibrar antes del
análisis de inspección. Remuestrear no tiene escasez que resolver, debe ir dentro del
pliegue para no contaminar, e interpolar casos sintéticos sobre variables con sesgo del
orden de 526 produciría clientes que no existen.

## Punto de operación y evaluación @k

| k | pct_de_la_base | fraudes_esperados_al_azar | recall_techo_pct |
|---|---|---|---|
| 500 | 0,37 | 27,9 | 6,61 |
| 1.000 | 0,74 | 55,8 | 13,22 |
| 2.500 | 1,85 | 139,6 | 33,04 |
| 5.000 | 3,69 | 279,2 | 66,09 |
| 10.000 | 7,38 | 558,4 | 100 |
| 20.000 | 14,76 | 1117 | 100 |

Una lista de 5.000 clientes cubre el 3,69 % de la base; con orden aleatorio
contiene 279,2 fraudes y con orden perfecto llegaría a un recall del
66,09 % (`fig_eval_at_k.png`). El techo de recall lo impone el tamaño de
la lista, no el modelo.

Alternativas. Reportar la curva @k para varios k sin fijar umbral es honesto y deja el
proyecto sin un número único citable. Fijar el umbral que maximiza F1 es reproducible y
pondera precisión y recall por igual sin ninguna razón operativa que lo respalde. Aplazar el
umbral al análisis de costo-beneficio es lo más defendible y exige asumir parámetros de coste
que hoy no están, con su análisis de sensibilidad.

## Estratificación de los pliegues

Con 5 pliegues agrupados por cliente, la desviación de la prevalencia entre pliegues
es de 0,0873 puntos porcentuales, por debajo de los 0,1395 que produce
el azar binomial; el esquema estratificado la deja en 0,1673
(`fig_eval_pliegues.png`). No hay heterogeneidad que corregir.

Alternativas. `GroupKFold` está implementado y cubierto por la prueba anti-fuga, y es
determinista, lo que impide repetir la validación con otra semilla para medir la varianza del
propio reparto. `StratifiedGroupKFold` con barajado y semilla fija permite esa repetición y
garantiza homogeneidad, a cambio de añadir una restricción que la evidencia no reclama. Lo
que impide la fuga entre pliegues es la agrupación por cliente, que ambos cumplen.

## Evidencia disponible para las decisiones de la fase siguiente

Tres decisiones se toman al construir las variables, y esta fase deja preparada su
evidencia. Sobre la codificación de categóricas: `region` tiene 25 valores y `counter_code`
42, con categorías que aparecen solo en entrenamiento, así que el esquema elegido tiene que
resolver el caso de una categoría no vista. Sobre los clientes con poco historial:
4.212 tienen una sola factura y 15.269 tres o
menos, y su tasa de fraude es del 0,642 %, muy por debajo de la global, de modo
que descartarlos eliminaría un grupo genuinamente de bajo riesgo y alteraría la prevalencia
del conjunto. Sobre la ventana temporal: el volumen anterior a 2005 es el
0,49 % de las facturas y la separación entre particiones no es cronológica,
con lo que un recorte de la ventana tendría que justificarse por comparabilidad entre
clientes y no por evitar fuga temporal.
