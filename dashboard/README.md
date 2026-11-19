# Dashboard

Tablero en Streamlit con los resultados del proyecto. Lee solo las tablas versionadas en
`reports/tables/` (las exportan `notebooks/01_eda.ipynb` y `notebooks/02_modelado.ipynb`),
así que no necesita los datos crudos. Si los notebooks se vuelven a ejecutar, el tablero
muestra las cifras nuevas sin tocar el código.

Pestañas: resumen, datos y exploración, huella de la inspección, modelos, simulador de
campaña e interpretación (SHAP).

## Correrlo en local

Desde la raíz del repositorio:

```bash
pip install -r dashboard/requirements.txt
streamlit run dashboard/app.py
```

Se abre en <http://localhost:8501>. El tema claro u oscuro sigue la configuración del
sistema y se cambia desde el menú de la esquina superior derecha.

Prueba de humo (recorre las seis pestañas y todas las opciones del simulador):

```bash
python -m pytest dashboard/test_app.py -q
```

## Publicarlo en Streamlit Community Cloud

1. Subir la carpeta `dashboard/` al repositorio de GitHub (las tablas de
   `reports/tables/` ya están versionadas).
2. Entrar a <https://share.streamlit.io> con la cuenta de GitHub y elegir **Create app**.
3. Repositorio `omedinaavilla/Fraud-detection-in-Energy-Consume`, rama `main`, archivo
   principal `dashboard/app.py`.
4. En **Advanced settings**, elegir Python 3.12 o superior. Community Cloud instala
   `dashboard/requirements.txt` porque está junto al archivo principal.
5. **Deploy**. El enlace público que entrega es el que se comparte.

El tema de `dashboard/.streamlit/config.toml` se aplica también en la nube, porque
Streamlit lo busca junto al archivo principal.
