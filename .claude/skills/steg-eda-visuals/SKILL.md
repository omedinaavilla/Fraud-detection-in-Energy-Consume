---
name: steg-eda-visuals
description: Define la gramática visual única del proyecto STEG (paleta, tipografía, tamaños), qué tipo de gráfico corresponde a qué pregunta, cómo mostrar faltantes y variables de alta cardinalidad, cómo etiquetar ejes y unidades, y por qué se evitan gráficos decorativos. Las figuras del EDA y las del artículo comparten este estilo. Úsala antes de generar cualquier figura en src/steg/eda/figures.py o en src/steg/reporting/, y al revisar si una figura ya hecha cumple el estándar del proyecto.
---

# Gramática visual — STEG

Una sola figura sirve tanto para `reports/EDA/` como para `paper/figuras/`: no hay dos
estilos. Si una figura no cumple esto, se rehace antes de guardarla.

## Estilo base (matplotlib)

- Backend y guardado: vectorial para el artículo (`.pdf` o `.svg`), 300 dpi si se
  exporta a raster para revisión rápida. Nunca `.jpg`.
- Una sola hoja de estilo, `src/steg/eda/figures.py::apply_style()` (a implementar en
  la Fase 1), aplicada con `plt.style.use` o `rcParams` antes de cualquier figura —
  nunca configurada gráfico por gráfico.
- Tipografía: la misma familia que usa el manuscrito LaTeX (serif, tamaño base 10-11pt
  para que la figura no desentone al insertarse en `paper/`). Tamaño de fuente de ejes
  y leyenda nunca menor al del pie de figura.
- Paleta: máximo 2-3 colores categóricos consistentes en todo el proyecto (por ejemplo,
  un color fijo para "no fraude" y otro para "fraude" — se reutiliza en cada figura que
  distinga por `target`, nunca se reasignan colores entre figuras). Para variables
  ordinales o secuenciales (percentiles, tiempo), usar un colormap perceptualmente
  uniforme (`viridis` o similar), nunca `jet`.
- Sin efectos 3D, sin sombra, sin degradados decorativos, sin líneas de cuadrícula por
  defecto de matplotlib sin atenuar (`alpha` bajo si se usan).

## Qué gráfico corresponde a qué pregunta

| Pregunta | Gráfico |
|---|---|
| Distribución de una numérica con cola larga (`consommation_level_1`, `months_number`) | Histograma en escala log del eje x, o ECDF. Un boxplot solo sin escala log oculta la forma. |
| Comparar una numérica entre fraude/no fraude | Boxplot o violin con escala log si la variable lo requiere, nunca solo medias con barras de error si la distribución es muy sesgada. |
| Frecuencia de una categórica de baja cardinalidad (`client_catg`, `counter_type`) | Barras horizontales ordenadas por frecuencia. |
| Categórica de alta cardinalidad (`region`, `counter_code`) | Agrupar categorías raras en "otras" antes de graficar; nunca más de ~12 barras. Alternativa: tabla en `reports/tables/`, no gráfico. |
| Tasa de `target` por categoría | Barras con intervalo (bootstrap o Wilson), no solo el punto — con `n` por categoría anotado, porque algunas categorías tienen pocos clientes. |
| Evolución temporal (facturas por año, cobertura por cliente) | Línea o barras por año; marcar visualmente el quiebre de volumen en 2005 si la figura incluye años anteriores. |
| Relación entre dos numéricas | Scatter con transparencia (`alpha`) si hay muchos puntos (aquí, casi siempre 4M+ filas) o hexbin/densidad en vez de scatter denso ilegible. |
| Matriz de correlación | Heatmap con anotación numérica solo si la matriz es pequeña (≤10 variables); si es grande, sin anotación y con colorbar clara. |

## Faltantes y anomalías

Este dataset no tiene nulos declarados pero sí banderas de anomalía
(`counter_statue_invalid`, `months_number_invalid`, etc., ver `steg-data-contract`).
Se visualizan igual que se visualizaría un faltante: barra de "tasa de anomalía" por
columna, y si se cruza con `target`, barras con intervalo como en la tabla de arriba.
Nunca se ocultan quitando esas filas del gráfico sin decirlo en el pie de figura.

## Ejes y unidades

- Todo eje numérico de consumo lleva unidad en la etiqueta (el README no la especifica
  explícitamente; documentar el supuesto de unidad en el pie de figura o en el texto
  si no está confirmada).
- Fechas en el eje: formato consistente (año, o año-mes), nunca la fecha cruda de
  `invoice_date`/`creation_date` sin formatear.
- Todo eje logarítmico se anota como tal en la etiqueta ("consumo (log₁₀)"), nunca
  silenciosamente.

## Por qué se evitan gráficos decorativos

Cada figura en `reports/figures/` debe poder citarse en el texto del artículo
respondiendo una pregunta concreta (ver la tabla de arriba). Una figura que solo
"se ve bien" pero no reduce a una pregunta específica no se guarda — se descarta en el
EDA exploratorio y no llega a `reports/figures/`.

## Reproducibilidad de las figuras

Cada figura se genera desde un script versionado (no desde una celda de notebook
suelta), con la semilla del proyecto (`steg.config.SEED`) si hay cualquier muestreo o
jitter aleatorio, para que sea regenerable de forma idéntica.
