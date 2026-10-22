# Targets del pipeline STEG. En Windows sin `make` disponible, ejecuta el comando
# `python -m ...` de la línea correspondiente directamente.

.PHONY: setup audit eda decide features train evaluate explain inspect report paper test lint

setup:
	pip install -e ".[dev]"

audit:
	python -m steg.data.load
	python -m steg.eda.profile

eda:
	@echo "Fase 1 (EDA completo): pendiente de incremento posterior."

decide:
	@echo "Fase 2 (protocolo de evaluación): pendiente de incremento posterior."

features train:
	python -m steg.data.clean
	python -m nbconvert --to notebook --execute --inplace notebooks/02_modelado.ipynb --ExecutePreprocessor.timeout=-1

evaluate:
	@echo "Comparación de experimentos: pendiente de incremento posterior."

explain:
	@echo "Fase 6 (SHAP y subgrupos): pendiente de incremento posterior."

inspect:
	@echo "Fase 7 (priorización de inspecciones): pendiente de incremento posterior."

report:
	@echo "Consolidación de reports/RESULTS.md: pendiente de incremento posterior."

paper:
	@echo "Fase 9 (manuscrito LaTeX): pendiente de incremento posterior."

test:
	pytest -v

lint:
	ruff check src tests
