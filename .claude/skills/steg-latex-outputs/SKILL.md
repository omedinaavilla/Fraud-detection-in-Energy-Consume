---
name: steg-latex-outputs
description: Explica cómo generar figuras y tablas listas para el manuscrito LaTeX del proyecto STEG con booktabs y siunitx, notas al pie de tabla, etiquetas y referencias cruzadas consistentes, figuras vectoriales, y el script que reexporta todo de una pasada. Úsala al implementar src/steg/reporting/, al preparar cualquier tabla o figura que vaya a paper/, o al revisar si el manuscrito referencia artefactos que sí existen en disco.
---

# Exportación a LaTeX — STEG

## Principio

`paper/` nunca contiene un número o una figura que no venga de `reports/tables/` o
`reports/figures/`. `src/steg/reporting/` es el único código que escribe en
`paper/figuras/` y que genera los `.tex` de tabla — el manuscrito no se edita a mano
para insertar un número.

## Tablas (`booktabs` + `siunitx`)

- Toda tabla exportada usa `\toprule`, `\midrule`, `\bottomrule` (booktabs), nunca
  líneas verticales ni `\hline` de LaTeX estándar.
- Columnas numéricas alineadas por el punto decimal con `siunitx`
  (`S[table-format=1.3]` o el formato que corresponda), no alineación de texto
  centrada para números.
- Cada tabla lleva `\caption` descriptivo (qué se mide, sobre qué partición, con qué
  intervalo) y `\label{tab:<nombre>}` consistente con cómo se referencia en el texto.
- Notas al pie de tabla (`threeparttable` o `tablenotes`) para aclarar abreviaturas,
  el número de folds, o el hash de datos/experimento que la produjo — nunca en el
  cuerpo del caption si rompe la legibilidad.
- Ejemplo de esqueleto para una tabla comparativa de modelos
  (`reports/tables/model_comparison.csv` → `paper/tablas/model_comparison.tex`):

```latex
\begin{table}[t]
  \centering
  \caption{Comparación de modelos bajo el protocolo de validación cruzada agrupada por
    cliente (5 folds, semilla 42).}
  \label{tab:model-comparison}
  \begin{threeparttable}
    \begin{tabular}{l S[table-format=1.3] S[table-format=1.3]}
      \toprule
      {Modelo} & {Métrica primaria} & {IC 95\%} \\
      \midrule
      % filas generadas por src/steg/reporting/ desde reports/tables/model_comparison.csv
      \bottomrule
    \end{tabular}
    \begin{tablenotes}
      \small
      \item Generado automáticamente desde \texttt{reports/tables/model\_comparison.csv}.
    \end{tablenotes}
  \end{threeparttable}
\end{table}
```

## Figuras

- Formato vectorial (`.pdf` idealmente, `.svg` si el flujo lo requiere) — nunca `.png`
  para el manuscrito final, aunque `.png` a 300 dpi sirva para revisión rápida en
  `reports/EDA/`.
- Mismo estilo que `steg-eda-visuals`: tipografía, paleta y tamaños consistentes con el
  resto del documento, para que una figura no "se note" insertada de otro sistema.
- `\includegraphics` referencia siempre la copia en `paper/figuras/`, generada por el
  script de reexportación — nunca apunta directamente a `reports/figures/` (rutas
  relativas distintas entre el repo de trabajo y el manuscrito).

## Etiquetas y referencias cruzadas

- Prefijo por tipo: `tab:` para tablas, `fig:` para figuras, `eq:` para ecuaciones,
  `sec:` para secciones. Sin espacios ni tildes en la clave.
- Cada figura y tabla debe estar referenciada al menos una vez en el texto con
  `\cref` o `\ref` — una figura sin referencia en el cuerpo no se incluye (ver
  `steg-human-academic-prose`: las referencias van integradas en la frase).

## Script de reexportación de una pasada

`src/steg/reporting/` implementa un único punto de entrada (invocado por
`make paper` o el slash command `/paper`) que:

1. Lee todo `reports/tables/*.csv` y `reports/metrics/*.json` vigente.
2. Regenera cada `.tex` de tabla y cada figura vectorial en `paper/figuras/` /
   `paper/tablas/`.
3. No modifica el texto en prosa de `paper/secciones/` — solo los artefactos
   generados. Si una tabla cambia de forma (columnas nuevas), el `.tex` se regenera
   pero el texto que la describe se revisa a mano.

Correr este script antes de compilar el manuscrito es obligatorio después de cualquier
cambio en `reports/`; un PDF compilado con tablas desactualizadas no se distribuye.
