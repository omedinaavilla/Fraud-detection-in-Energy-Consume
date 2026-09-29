---
name: steg-human-academic-prose
description: Reglas de redacción académica en español para que el manuscrito de STEG no se lea como generado por IA ni como la bitácora de un sistema de agentes — prohibiciones concretas de estructura y muletillas, con su alternativa, la regla de nunca revelar la arquitectura interna, y verificación obligatoria de que cada cifra citada existe en reports/. Úsala al escribir o revisar cualquier texto en paper/secciones/, al redactar una entrada de reports/PLANNER.md, y antes de entregar cualquier borrador o informe.
---

# Prosa académica humana — STEG

Esta skill es la referencia obligatoria del agente `academic-writer` (Fase 9), de
cualquier revisión de `paper/secciones/`, y de todo agente ejecutor al redactar en
`reports/PLANNER.md` o en los informes de `reports/EDA/`. Cada regla trae su alternativa
concreta, no solo la prohibición.

## Prohibiciones y su alternativa

- **Nada de aperturas de relleno** ("En el panorama actual…", "Es importante destacar
  que…", "Cabe resaltar que…"). *Alternativa*: empezar por la afirmación. En vez de "Es
  importante destacar que el modelo LightGBM obtuvo el mejor desempeño", escribir
  "LightGBM obtuvo el mejor desempeño (PR-AUC 0,XX, IC 95 % [0,XX, 0,XX])".
- **Nada de "no solo X, sino también Y" ni "no es X, es Y"**. *Alternativa*: afirmar
  directamente lo que es cierto. "El modelo mejora la discriminación y reduce la
  varianza entre folds" en vez de "no solo mejora la discriminación, sino que también
  reduce la varianza".
- **Nada de enumeraciones de tres elementos por costumbre**. *Alternativa*: el número
  de elementos lo da el contenido. Si hay dos razones, van dos; si hay cuatro, van
  cuatro. Nunca se rellena o se recorta una lista para que "se vea bien" en tríos.
- **Nada de párrafos de cierre que resumen lo que se acaba de decir**. *Alternativa*:
  el párrafo anterior ya dijo lo que tenía que decir; el siguiente introduce
  información nueva o termina la sección sin repetir.
- **Nada de guiones largos como inciso ni de conectores en cadena** ("Además, …
  Asimismo, … Por otro lado, …"). *Alternativa*: subordinar la idea dentro de la misma
  frase, o partir en dos frases independientes sin conector de relleno.
- **Nada de intensificadores vagos** ("significativamente mejor", "notablemente
  robusto"). *Alternativa*: el número y la comparación. "AUC 0,84 frente a 0,79 del
  baseline (diferencia pareada, Wilcoxon, p = 0,00X)" en vez de "significativamente
  mejor".
- **Longitud de frase y de párrafo variable**. Un párrafo de tres líneas junto a uno de
  diez es señal humana; alternar longitudes deliberadamente en la revisión final.
- **Voz consistente con la revista objetivo**, sin alternar entre primera persona del
  plural ("evaluamos") e impersonal ("se evaluó") dentro del mismo apartado. Fijar una
  al empezar cada sección y mantenerla.
- **Las limitaciones se escriben concretas y en su sitio**, no como disclaimer
  genérico al final. Ejemplo concreto para este proyecto: "La partición de Zindi es
  aleatoria por cliente, no temporal, así que el desempeño reportado no mide
  necesariamente la capacidad del modelo de generalizar a fraude futuro" — no "el
  modelo tiene limitaciones y se necesita más investigación".
- **Referencias a figuras y tablas integradas en la frase**, no como muletilla
  repetida. "La Figura 3 muestra que el consumo del nivel 1 se concentra por debajo de
  X" en vez de siempre "Como se puede observar en la Figura 3, …".

## No revelar la arquitectura interna

El contenido final (manuscrito, `reports/PLANNER.md`, informes) se lee como el trabajo
de un equipo de investigación humano, nunca como la descripción de un sistema de
agentes. Los procesos internos usados para producirlo quedan completamente ocultos de la
narrativa.

No se mencionan: IA, inteligencia artificial como autora, agentes, agente EDA, agente
investigador, ejecutor, auditor, PM, skills, prompts, herramientas internas, arquitectura
de agentes, coordinación entre agentes, ni ningún otro proceso interno.

Nunca se escribe "el agente encontró...", "la IA decidió...", "el agente EDA
identificó...", "el agente investigador determinó...", "el auditor validó...". Se
transforma en redacción académica normal:

- ❌ "El agente EDA encontró muchos valores atípicos y el agente investigador mostró que
  un paper los eliminaba." → ✅ "El análisis exploratorio evidenció la presencia de
  valores atípicos en la variable X. Debido a las características observadas y al
  comportamiento de estos registros, se evaluaron diferentes alternativas de tratamiento
  y se decidió conservarlos para las siguientes etapas."
- ❌ "El agente investigador vio que el paper utilizaba Random Forest y decidió
  probarlo." → ✅ "A partir de las características del problema y de los antecedentes
  metodológicos disponibles, se consideró Random Forest como una de las alternativas
  para el modelado."
- ❌ "El Ejecutor decidió utilizar la transformación X después de mirar el paper." →
  ✅ "Debido al comportamiento observado en la distribución de X, se aplicó la
  transformación correspondiente con el objetivo de mejorar las condiciones para las
  etapas posteriores."

## Conclusiones concretas, no preguntas abiertas

Cada etapa cierra con **qué se encontró → qué significa → qué decisión se tomó → cómo
afecta lo siguiente**, nunca con una repetición de los resultados a modo de resumen.
Cuando la evidencia disponible ya permite decidir, se decide: se evita cerrar con
"sería interesante analizar...", "podría ser útil...", "queda por determinar..." si esa
pregunta ya tiene respuesta en los datos. Si de verdad no hay evidencia suficiente para
decidir, se dice explícitamente qué análisis adicional hace falta antes de poder
hacerlo — no se deja la pregunta flotando sin más.

## Verificación obligatoria antes de entregar

Cada cifra del texto se contrasta contra `reports/tables/` y `reports/metrics/`. Cifra
que no esté en disco, se borra o se reemplaza por `\todo{}` (ver más abajo). Esto
incluye:

- Números de desempeño (AUC, precisión, recall, ganancia esperada).
- Cifras descriptivas de los datos (tasa de positivos, tamaño de muestra, número de
  clientes con historial corto) — deben coincidir exactamente con
  `reports/EDA/00_data_audit.md` o el archivo de origen correspondiente, no
  redondearse ni "recordarse de memoria".
- Cualquier comparación con el leaderboard de Zindi (~0,86 AUC): se cita como contexto
  de dificultad del problema, nunca se compara directamente como si fuera la misma
  métrica bajo el mismo protocolo, salvo que se aclare explícitamente la diferencia de
  protocolo.

## `\todo{}` en vez de rellenar

Si falta evidencia en disco para una afirmación que el texto necesita, se deja
`\todo{cifra pendiente: <qué falta y de qué experimento}` y se continúa. Nunca se
inventa, se redondea a conveniencia, ni se interpola un número plausible. Esto aplica
también a interpretación: si un patrón "parece" existir pero no hay una tabla o figura
que lo sustente, se deja el `\todo{}` en vez de afirmarlo.
