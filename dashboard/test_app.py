"""Prueba de humo del dashboard: recorre todas las pestañas y opciones sin excepciones.

python -m pytest dashboard/test_app.py -q
"""

from pathlib import Path

from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parent / "app.py")
FRACCIONES = [0.005, 0.01, 0.02, 0.05, 0.10]


def _app() -> AppTest:
    at = AppTest.from_file(APP, default_timeout=60)
    at.run()
    assert not at.exception, [e.value for e in at.exception]
    return at


def test_pestanas_renderizan():
    at = _app()
    assert len(at.tabs) == 6
    for tab in at.tabs:
        assert len(tab.children) > 0, tab.label


def test_cifras_del_resumen():
    at = _app()
    valores = {m.label: m.value for m in at.metric}
    assert valores["Clientes etiquetados"] == "135.493"
    assert valores["Fraude detectado"] == "5,58 %"
    assert valores["PR-AUC en el holdout"] == "0,191"
    assert valores["ROC-AUC en el holdout"] == "0,762"
    hero = [m.value for m in at.markdown if "fraudes en" in m.value]
    assert hero and "118 fraudes en 271 visitas" in hero[0]
    assert "serían 57" in hero[0] and "unos 15" in hero[0]


def test_simulador_todas_las_fracciones():
    at = _app()
    for f in FRACCIONES:
        at.radio(key="fraccion").set_value(f).run()
        assert not at.exception, (f, [e.value for e in at.exception])
        valores = {m.label: m.value for m in at.metric}
        assert "Visitas" in valores


def test_conjunto_quintiles():
    at = _app()
    for opcion in ["Holdout", "Validación cruzada"]:
        at.radio(key="conjunto_quintil").set_value(opcion).run()
        assert not at.exception, (opcion, [e.value for e in at.exception])
