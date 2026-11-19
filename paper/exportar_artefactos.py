"""Reexporta a paper/ las tablas y figuras que cita el informe.

Lee solo reports/tables/*.csv, reports/EDA/00_data_audit.md y reports/figures/*.png, y
escribe paper/tablas/*.tex y paper/figuras/*.png. No toca el texto de paper/secciones/.
Ejecutar desde la raíz del repositorio después de cualquier cambio en reports/:

    python paper/exportar_artefactos.py
"""

from __future__ import annotations

import re
import shutil
from pathlib import Path

import pandas as pd

PAPER = Path(__file__).resolve().parent
ROOT = PAPER.parent
TABLES = ROOT / "reports" / "tables"
FIGURES = ROOT / "reports" / "figures"
OUT_TAB = PAPER / "tablas"
OUT_FIG = PAPER / "figuras"

FIGURAS = [
    "fig_calidad_anomalias.png",
    "fig_confusion_historial.png",
    "fig_model_comparacion_pr_auc.png",
    "fig_model_quintiles_historial.png",
    "fig_model_holdout.png",
    "fig_model_shap_importancia.png",
]

NOMBRES = {
    "prevalencia": "Prevalencia (azar)",
    "solo_exposicion": "Solo exposición",
    "logreg_comportamiento": "Regresión logística",
    "xgb_comportamiento": "XGBoost",
    "lgbm_comportamiento_ponderado": "LightGBM ponderado",
    "lgbm_comportamiento_optuna": "LightGBM con Optuna",
    "lgbm_comportamiento": "LightGBM (seleccionado)",
    "lgbm_censurado_sin_grupo_B": "LightGBM sin grupo B",
    "lgbm_comportamiento_y_exposicion": "LightGBM con exposición",
    "lgbm_historial_completo": "LightGBM historial completo",
}

FAMILIAS = {
    "tarifa_contador": "Tarifa y contador",
    "consumo": "Nivel de consumo",
    "dinamica": "Dinámica del consumo",
    "lectura": "Regularidad de lectura",
    "cliente": "Atributos del cliente",
    "relativa_pares": "Relativas a pares",
}

EVENTOS = {
    "reemplazo_contador": "Reemplazo de contador",
    "cambio_codigo_contador": "Cambio de código de contador",
    "cambio_tarifa": "Cambio de tarifa",
    "cualquiera": "Cualquiera de los tres",
}


def num(x: float, dec: int = 3) -> str:
    """Número con coma decimal y signo menos tipográfico, para texto fuera de columnas siunitx."""
    texto = f"{abs(x):.{dec}f}".replace(".", ",")
    return f"$-${texto}" if x < 0 and float(texto.replace(",", ".")) != 0 else texto


def ic(lo: float, hi: float, dec: int = 3) -> str:
    """Intervalo con punto y coma como separador, porque la coma es el separador decimal."""
    return f"[{num(lo, dec)}; {num(hi, dec)}]"


def tex_escape(s: str) -> str:
    return s.replace("_", r"\_").replace("%", r"\%")


def tabla(nombre: str, caption: str, label: str, colspec: str, cabecera: str,
          filas: list[str], notas: list[str], fuente: str) -> None:
    cuerpo = "\n".join(f"      {f} \\\\" for f in filas)
    items = "\n".join(f"      \\item {n}" for n in [*notas, f"Fuente: \\texttt{{{tex_escape(fuente)}}}."])
    texto = f"""% Generado por paper/exportar_artefactos.py desde {fuente}. No editar a mano.
\\begin{{table}}[htbp]
  \\centering
  \\small
  \\caption{{{caption}}}
  \\label{{{label}}}
  \\begin{{threeparttable}}
    \\begin{{tabular}}{{{colspec}}}
      \\toprule
      {cabecera} \\\\
      \\midrule
{cuerpo}
      \\bottomrule
    \\end{{tabular}}
    \\begin{{tablenotes}}
      \\footnotesize
{items}
    \\end{{tablenotes}}
  \\end{{threeparttable}}
\\end{{table}}
"""
    (OUT_TAB / f"{nombre}.tex").write_text(texto, encoding="utf-8")


def tabla_datos() -> None:
    md = (ROOT / "reports" / "EDA" / "00_data_audit.md").read_text(encoding="utf-8")
    filas = []
    for tabla_csv in ["client_train", "client_test", "invoice_train", "invoice_test"]:
        m = re.search(rf"^\| {tabla_csv} \| ([\d.]+) \| (\d+) \| (.+?) \|$", md, re.M)
        filas_n = int(m.group(1).replace(".", ""))
        filas.append(f"\\texttt{{{tex_escape(tabla_csv)}}} & {filas_n} & {m.group(2)} & {m.group(3)}")
    tabla(
        "tab_datos",
        "Archivos del conjunto de datos de STEG publicados en el reto de Zindi.",
        "tab:datos",
        "l S[table-format=7.0] S[table-format=2.0] l",
        "{Archivo} & {Filas} & {Columnas} & {Unidad de observación}",
        filas,
        ["Solo \\texttt{client\\_train} trae la etiqueta; \\texttt{client\\_test} se usa para la validación adversarial."],
        "reports/EDA/00_data_audit.md",
    )


def tabla_eventos() -> None:
    df = pd.read_csv(TABLES / "modeling_diagnostico_eventos_equipo.csv").set_index("evento")
    filas = []
    for clave, nombre in EVENTOS.items():
        r = df.loc[clave]
        filas.append(
            f"{nombre} & {int(r.clientes_con_evento)} & {100 * r.tasa_fraude_con_evento:.1f} & "
            f"{100 * r.tasa_fraude_sin_evento:.1f} & {r.posicion_mediana_fraude:.2f} & "
            f"{r.posicion_mediana_no_fraude:.2f}"
        )
    tabla(
        "tab_eventos",
        "Eventos de equipo y de contrato en el historial de los clientes de \\textit{dev}.",
        "tab:eventos",
        "l S[table-format=5.0] S[table-format=2.1] S[table-format=1.1] S[table-format=1.2] S[table-format=1.2]",
        "{Evento} & {Clientes} & {\\shortstack{Fraude con\\\\evento (\\%)}} & {\\shortstack{Fraude sin\\\\evento (\\%)}} & "
        "{\\shortstack{Posición\\\\(fraude)}} & {\\shortstack{Posición\\\\(sin fraude)}}",
        filas,
        ["Posición: ubicación relativa mediana del evento dentro del historial del cliente (0 = primera factura, 1 = última)."],
        "reports/tables/modeling_diagnostico_eventos_equipo.csv",
    )


def tabla_mitades() -> None:
    df = pd.read_csv(TABLES / "modeling_verificacion_mitades_historial.csv")
    rep = {"historial_completo": "Completo", "historial_censurado": "Censurado"}
    var = {"primera_mitad": "Primera mitad", "segunda_mitad": "Segunda mitad", "historial_entero": "Historial entero"}
    filas = []
    for r_rep in ["historial_completo", "historial_censurado"]:
        for r_var in ["primera_mitad", "segunda_mitad", "historial_entero"]:
            r = df[(df.representacion == r_rep) & (df.variables == r_var)].iloc[0]
            delta = "{---}" if r_var == "primera_mitad" else (
                f"{{{num(r.delta_vs_primera_mitad)} {ic(r.delta_ic95_lo, r.delta_ic95_hi)}}}"
            )
            filas.append(
                f"{rep[r_rep]} & {var[r_var]} & {int(r.clientes)} & {r.pr_auc_media:.3f} & "
                f"{{{ic(r.pr_auc_ic95_lo, r.pr_auc_ic95_hi)}}} & {delta}"
            )
    tabla(
        "tab_mitades",
        "Verificación por mitades del historial: PR-AUC en validación cruzada sobre \\textit{dev} "
        "con variables calculadas en cada mitad.",
        "tab:mitades",
        "l l S[table-format=5.0] S[table-format=1.3] c c",
        "{Historial} & {Variables de} & {Clientes} & {PR-AUC} & {IC 95\\,\\%} & {Diferencia con la primera mitad}",
        filas,
        ["Clientes de \\textit{dev} con al menos 16 facturas, para que cada mitad tenga 8 o más; "
         "se usan los mismos pliegues restringidos a esa población."],
        "reports/tables/modeling_verificacion_mitades_historial.csv",
    )


def poblacion(archivo: str) -> tuple[int, int]:
    """Clientes y positivos de dev u holdout, sumando los grupos con y sin evento."""
    df = pd.read_csv(TABLES / archivo)
    df = df[df.modelo == "lgbm_comportamiento"]
    return int(df.clientes.sum()), int(df.positivos.sum())


def miles(n: int) -> str:
    return f"{n:,}".replace(",", ".")


def tabla_modelos() -> None:
    df = pd.read_csv(TABLES / "model_comparison.csv").set_index("modelo")
    n_dev, _ = poblacion("modeling_dev_por_evento_equipo.csv")
    orden = [
        "prevalencia", "solo_exposicion", "logreg_comportamiento", "xgb_comportamiento",
        "lgbm_comportamiento_ponderado", "lgbm_comportamiento_optuna", "lgbm_comportamiento",
    ]
    filas = []
    for m in orden:
        r = df.loc[m]
        delta = "{---}" if m == "lgbm_comportamiento" else (
            f"{{{num(r.delta_vs_lgbm_comportamiento)} {ic(r.delta_ic95_lo, r.delta_ic95_hi)}}}"
        )
        filas.append(
            f"{NOMBRES[m]} & {r.pr_auc_media:.3f} & {r.pr_auc_desv:.3f} & {r.roc_auc_media:.3f} & "
            f"{delta} & {r['lift@1%']:.1f}"
        )
    tabla(
        "tab_modelos",
        "Comparación de modelos en validación cruzada de 5 pliegues sobre \\textit{dev} "
        f"({miles(n_dev)} clientes, historial censurado).",
        "tab:modelos",
        "l S[table-format=1.3] S[table-format=1.3] S[table-format=1.3] c S[table-format=1.1]",
        "{Modelo} & {PR-AUC} & {Desv.} & {ROC-AUC} & {Diferencia de PR-AUC [IC 95\\,\\%]} & {Lift@1\\,\\%}",
        filas,
        [
            "PR-AUC y ROC-AUC: media de los 5 pliegues; Desv.: desviación estándar entre pliegues.",
            "Diferencia frente al modelo seleccionado sobre las predicciones fuera de pliegue, con IC por bootstrap pareado por cliente.",
        ],
        "reports/tables/model_comparison.csv",
    )


def tabla_holdout() -> None:
    df = pd.read_csv(TABLES / "modeling_holdout_metricas.csv").set_index("modelo")
    n_ho, p_ho = poblacion("modeling_holdout_por_evento_equipo.csv")
    orden = ["lgbm_comportamiento", "lgbm_censurado_sin_grupo_B", "solo_exposicion",
             "lgbm_comportamiento_y_exposicion", "lgbm_historial_completo"]
    filas = []
    for m in orden:
        r = df.loc[m]
        filas.append(
            f"{NOMBRES[m]} & {r.pr_auc:.3f} & {{{ic(r.pr_auc_ic95_lo, r.pr_auc_ic95_hi)}}} & {r.roc_auc:.3f} & "
            f"{r.brier:.4f} & {100 * r['precision@1%']:.1f} & {r['lift@1%']:.1f}"
        )
    tabla(
        "tab_holdout",
        f"Desempeño en el holdout sellado ({miles(n_ho)} clientes, {miles(p_ho)} positivos), "
        "evaluado una sola vez.",
        "tab:holdout",
        "l S[table-format=1.3] c S[table-format=1.3] S[table-format=1.4] S[table-format=2.1] S[table-format=2.1]",
        "{Modelo} & {PR-AUC} & {IC 95\\,\\%} & {ROC-AUC} & {Brier} & {Precisión@1\\,\\% (\\%)} & {Lift@1\\,\\%}",
        filas,
        [
            "Las dos últimas filas son controles: la exposición mide oportunidades de inspección y el "
            "historial completo contiene huellas posteriores a la detección; no son candidatos.",
            "IC del PR-AUC por bootstrap de clientes (1.000 réplicas).",
        ],
        "reports/tables/modeling_holdout_metricas.csv",
    )


def tabla_curva_k() -> None:
    df = pd.read_csv(TABLES / "modeling_holdout_metricas.csv").set_index("modelo")
    curva = pd.read_csv(TABLES / "modeling_holdout_curva_k.csv")
    _, p_ho = poblacion("modeling_holdout_por_evento_equipo.csv")
    prev = df.loc["lgbm_comportamiento", "prevalencia"]
    filas = []
    for _, r in curva.iterrows():
        etiqueta = f"{100 * r.fraccion:g}%"
        k = int(r.k)
        azar = prev * k
        expo = df.loc["solo_exposicion", f"precision@{etiqueta}"] * k
        modelo = r.precision * k
        filas.append(
            f"{num(100 * r.fraccion, 1)}\\,\\% & {k} & {azar:.0f} & {expo:.0f} & {modelo:.0f} & "
            f"{100 * r.precision:.1f} & {100 * r.recall:.1f} & {100 * r.techo_recall:.1f}"
        )
    tabla(
        "tab_curva_k",
        "Fraudes encontrados en el holdout según el tamaño de la lista de inspección.",
        "tab:curva-k",
        "l S[table-format=4.0] S[table-format=3.0] S[table-format=3.0] S[table-format=3.0] "
        "S[table-format=2.1] S[table-format=2.1] S[table-format=3.1]",
        "{Lista} & {$k$} & {Azar} & {\\shortstack{Regla de\\\\exposición}} & {Modelo} & "
        "{\\shortstack{Precisión\\\\(\\%)}} & {\\shortstack{Recall\\\\(\\%)}} & {\\shortstack{Techo de\\\\recall (\\%)}}",
        filas,
        [
            "Azar: prevalencia por $k$. Regla de exposición y modelo: precisión@$k$ por $k$. "
            "Precisión, recall y techo corresponden al modelo seleccionado.",
            f"Techo de recall: $\\min(k, P)/P$, con $P$ = {miles(p_ho)} positivos del holdout.",
        ],
        "reports/tables/modeling_holdout_curva_k.csv y modeling_holdout_metricas.csv",
    )


def tabla_subgrupos() -> None:
    df = pd.read_csv(TABLES / "modeling_holdout_por_evento_equipo.csv")
    filas = []
    for grupo, nombre in [("sin_evento", "Sin evento"), ("con_evento", "Con evento")]:
        m = df[(df.evento_equipo == grupo) & (df.modelo == "lgbm_comportamiento")].iloc[0]
        e = df[(df.evento_equipo == grupo) & (df.modelo == "solo_exposicion")].iloc[0]
        filas.append(
            f"{nombre} & {int(m.clientes)} & {100 * m.prevalencia:.1f} & {m.roc_auc:.3f} & {e.roc_auc:.3f} & "
            f"{m.pr_auc:.3f} & {e.pr_auc:.3f}"
        )
    tabla(
        "tab_subgrupos",
        "Desempeño en el holdout según el cliente haya tenido o no un evento de equipo o de contrato.",
        "tab:subgrupos",
        "l S[table-format=5.0] S[table-format=2.1] S[table-format=1.3] S[table-format=1.3] "
        "S[table-format=1.3] S[table-format=1.3]",
        "{Grupo} & {Clientes} & {Prevalencia (\\%)} & {\\shortstack{ROC-AUC\\\\modelo}} & "
        "{\\shortstack{ROC-AUC\\\\exposición}} & {\\shortstack{PR-AUC\\\\modelo}} & {\\shortstack{PR-AUC\\\\exposición}}",
        filas,
        ["El grupo sin evento no tiene corte que delatar y da la medida más limpia de la señal de comportamiento."],
        "reports/tables/modeling_holdout_por_evento_equipo.csv",
    )


def tabla_shap() -> None:
    df = pd.read_csv(TABLES / "modeling_importancia_shap.csv", index_col=0)
    grupos = df.groupby("familia").agg(variables=("participacion", "size"), participacion=("participacion", "sum"))
    principal = df.sort_values("media_abs_shap", ascending=False).groupby("familia").head(1)
    principal = principal.reset_index().set_index("familia")[df.index.name or "index"]
    grupos = grupos.sort_values("participacion", ascending=False)
    filas = []
    for fam, r in grupos.iterrows():
        filas.append(
            f"{FAMILIAS[fam]} & {int(r.variables)} & {100 * r.participacion:.1f} & "
            f"\\texttt{{{tex_escape(principal.loc[fam])}}}"
        )
    tabla(
        "tab_shap",
        "Participación de cada familia de variables en la media del valor absoluto de SHAP del modelo final.",
        "tab:shap",
        "l S[table-format=2.0] S[table-format=2.1] l",
        "{Familia} & {Variables} & {Participación (\\%)} & {Variable con mayor contribución}",
        filas,
        ["SHAP calculado sobre 20.000 clientes de \\textit{dev}; 42 entradas (38 variables por cliente y 4 relativas a pares)."],
        "reports/tables/modeling_importancia_shap.csv",
    )


def main() -> None:
    OUT_TAB.mkdir(exist_ok=True)
    OUT_FIG.mkdir(exist_ok=True)
    for f in FIGURAS:
        shutil.copy2(FIGURES / f, OUT_FIG / f)
    tabla_datos()
    tabla_eventos()
    tabla_mitades()
    tabla_modelos()
    tabla_holdout()
    tabla_curva_k()
    tabla_subgrupos()
    tabla_shap()
    print("tablas:", sorted(p.name for p in OUT_TAB.glob("*.tex")))
    print("figuras:", sorted(p.name for p in OUT_FIG.glob("*.png")))


if __name__ == "__main__":
    main()
