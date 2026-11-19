# Informe final (LaTeX)

1. Regenerar tablas y figuras desde `reports/`: `python paper/exportar_artefactos.py` (desde la raíz del repo, con el `.venv`).
2. En Overleaf: subir la carpeta `paper/` completa (o un .zip) como proyecto nuevo y fijar `main.tex` como documento principal.
3. Compilador: pdfLaTeX; la bibliografía usa `biblatex` con `biber`, que Overleaf ejecuta solo (Menu → Compiler: pdfLaTeX).
4. No quedan `\todo{...}` ni entradas pendientes: los artículos de `referencias.bib` se verificaron en Crossref y las cifras del contexto colombiano citan notas de prensa (El Heraldo y Portafolio) consultadas el 18 de noviembre de 2026. Si se agrega texto con algo por confirmar, el comando `\todo{...}` de `main.tex` lo marca en rojo.
5. Las figuras son PNG copiados de `reports/figures/`; si se regeneran en PDF vectorial, cambiar la lista `FIGURAS` del script.
