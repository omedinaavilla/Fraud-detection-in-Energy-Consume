# Resultados del modelado

Generado por `notebooks/02_modelado.ipynb` el 2026-10-08. No editar a mano: las cifras salen de `reports/tables/` y `reports/metrics/`.

- Clientes en dev: 108,394 (6,053 positivos); holdout: 27,099.
- Variables de comportamiento: 38; descartadas por redundancia: ['inv_share_codigo_contador_5'].
- ROC-AUC adversarial train frente a test: 0.4986.
- Hiperparámetros de Optuna: {"num_leaves": 72, "min_child_samples": 161, "subsample": 0.643, "colsample_bytree": 0.7986, "reg_lambda": 3.9287, "reg_alpha": 0.1934}.
- Modelo seleccionado: `lgbm_comportamiento` (mejor PR-AUC fuera de pliegue: `lgbm_comportamiento`).

## Conclusiones

El modelo seleccionado, `lgbm_comportamiento`, obtiene en validación cruzada sobre dev un PR-AUC de 0,192 (desviación entre pliegues 0,006) y un ROC-AUC de 0,768. La prevalencia constante da 0,056 y la línea base de solo exposición 0,124. Entre semillas de partición el PR-AUC medio va de 0,188 a 0,192.

Dentro del grupo sin eventos de equipo o de contrato, donde no hay corte que delatar, el PR-AUC es 0,098 (prevalencia 2,2 %) y el ROC-AUC 0,778 frente a 0,714 de la línea base de solo exposición. Dentro de los quintiles de longitud del historial va de 0,707 a 0,775.

El modelo con historial completo llega a 0,363 de PR-AUC, pero con esa representación la segunda mitad del historial rinde 0,396 y la primera 0,182; con el historial censurado la brecha baja a 0,031. Esa diferencia de desempeño es, en buena parte, huella de la inspección y no capacidad de anticipar el fraude.

En el holdout sellado, evaluado una sola vez, el modelo obtiene un PR-AUC de 0,191 (IC 95 % [0,174, 0,211]) y un ROC-AUC de 0,762 (IC 95 % [0,750, 0,773]). En una lista del 1 % de los clientes (271) la precisión es 43,5 %, 7,8 veces la prevalencia, con un recall de 7,8 % sobre un techo de 17,9 %.

Dentro del grupo sin eventos del holdout (prevalencia 2,0 %), el PR-AUC es 0,086 y el ROC-AUC 0,758. El control sin el grupo B obtiene 0,174 de PR-AUC global y 0,753 de ROC-AUC sin evento.

## Validación cruzada en dev

| modelo | pr_auc_media | pr_auc_desv | roc_auc_media | pr_auc_oof | delta_vs_lgbm_comportamiento | delta_ic95_lo | delta_ic95_hi | lift@1% | recall@5% |
|---|---|---|---|---|---|---|---|---|---|
| lgbm_historial_completo | 0.3625 | 0.0145 | 0.8724 | 0.3614 | 0.1708 | 0.1597 | 0.1816 | 10.7172 | 0.3801 |
| lgbm_historial_completo_sin_cambio_contador | 0.2602 | 0.0168 | 0.8205 | 0.2588 | 0.0682 | 0.0587 | 0.0781 | 8.569 | 0.2947 |
| lgbm_censurado_todas | 0.2073 | 0.0125 | 0.7843 | 0.204 | 0.0135 | 0.009 | 0.018 | 7.159 | 0.2418 |
| lgbm_censurado_sin_grupo_B | 0.1715 | 0.0088 | 0.7418 | 0.1699 | -0.0206 | -0.0254 | -0.0159 | 6.4629 | 0.2057 |
| lgbm_comportamiento | 0.1921 | 0.0065 | 0.7683 | 0.1905 | 0.0 | 0.0 | 0.0 | 6.723 | 0.2226 |
| prevalencia | 0.0558 | 0.0011 | 0.5 | 0.0552 | -0.1353 | -0.1449 | -0.1271 | 0.9739 | 0.052 |
| solo_exposicion | 0.1238 | 0.0046 | 0.7319 | 0.1225 | -0.068 | -0.0766 | -0.0596 | 3.8331 | 0.1456 |
| logreg_comportamiento | 0.1306 | 0.0087 | 0.7206 | 0.129 | -0.0615 | -0.0686 | -0.0544 | 4.3483 | 0.1592 |
| lgbm_comportamiento_y_exposicion | 0.2408 | 0.0091 | 0.8212 | 0.2399 | 0.0493 | 0.0433 | 0.0553 | 8.0148 | 0.2683 |
| xgb_comportamiento | 0.1899 | 0.007 | 0.7669 | 0.189 | -0.0016 | -0.0044 | 0.0015 | 6.9028 | 0.2217 |
| lgbm_comportamiento_ponderado | 0.185 | 0.0086 | 0.7628 | 0.1834 | -0.0072 | -0.0105 | -0.0035 | 6.8533 | 0.2188 |
| lgbm_comportamiento_optuna | 0.1871 | 0.0082 | 0.7663 | 0.1861 | -0.0044 | -0.0074 | -0.0012 | 6.7874 | 0.2218 |

## Controles de exposición

| index | spearman_con_n_facturas |
|---|---|
| solo_exposicion | 0.688 |
| lgbm_comportamiento | 0.42 |
| lgbm_comportamiento_y_exposicion | 0.602 |
| lgbm_historial_completo | 0.529 |

| quintil_historial | lgbm_comportamiento | lgbm_comportamiento_y_exposicion | lgbm_historial_completo | solo_exposicion |
|---|---|---|---|---|
| 1 | 0.775 | 0.887 | 0.836 | 0.868 |
| 2 | 0.723 | 0.842 | 0.865 | 0.765 |
| 3 | 0.707 | 0.765 | 0.856 | 0.658 |
| 4 | 0.724 | 0.765 | 0.843 | 0.627 |
| 5 | 0.751 | 0.773 | 0.847 | 0.632 |

| index | pr_auc | roc_auc | prevalencia |
|---|---|---|---|
| solo_exposicion | 0.1225 | 0.7154 | 0.0589 |
| lgbm_comportamiento | 0.1905 | 0.7541 | 0.0589 |
| lgbm_comportamiento_y_exposicion | 0.2399 | 0.8101 | 0.0589 |
| lgbm_historial_completo | 0.3614 | 0.8644 | 0.0589 |
| logreg_comportamiento | 0.129 | 0.7039 | 0.0589 |

## Huellas de la inspección

| index | cambio_codigo_contador | cambio_tarifa | reemplazo_contador | cualquiera |
|---|---|---|---|---|
| clientes_con_evento | 4285.0 | 1612.0 | 19163.0 | 22217.0 |
| tasa_fraude_con_evento | 0.269 | 0.172 | 0.181 | 0.187 |
| tasa_fraude_sin_evento | 0.047 | 0.054 | 0.029 | 0.022 |
| posicion_mediana_fraude | 0.688 | 0.592 | 0.704 | 0.688 |
| en_ultimo_20pct_fraude | 0.295 | 0.276 | 0.385 | 0.345 |
| anios_tras_ultimo_fraude | 3.001 | 1.68 | 2.68 | 2.502 |
| posicion_mediana_no_fraude | 0.523 | 0.596 | 0.408 | 0.472 |
| en_ultimo_20pct_no_fraude | 0.183 | 0.289 | 0.143 | 0.187 |
| anios_tras_ultimo_no_fraude | 5.138 | 0.671 | 5.665 | 5.336 |

| index | duplicado_logico | estado_pasa_a_no_cero | retroceso_de_indice |
|---|---|---|---|
| clientes_con_evento | 1677.0 | 12895.0 | 1429.0 |
| tasa_fraude_con_evento | 0.122 | 0.105 | 0.112 |
| tasa_fraude_sin_evento | 0.055 | 0.049 | 0.055 |
| posicion_mediana_fraude | 0.511 | 0.396 | 0.516 |
| en_ultimo_20pct_fraude | 0.224 | 0.026 | 0.209 |
| anios_tras_ultimo_fraude | 3.254 | 5.979 | 4.133 |
| posicion_mediana_no_fraude | 0.549 | 0.25 | 0.514 |
| en_ultimo_20pct_no_fraude | 0.253 | 0.029 | 0.229 |
| anios_tras_ultimo_no_fraude | 0.0 | 8.485 | 4.112 |

| representacion | variables | clientes | positivos | pr_auc_media | pr_auc_desv | roc_auc_media | pr_auc_ic95_lo | pr_auc_ic95_hi | delta_vs_primera_mitad | delta_ic95_lo | delta_ic95_hi |
|---|---|---|---|---|---|---|---|---|---|---|---|
| historial_completo | historial_entero | 74109 | 5475 | 0.3752 | 0.0146 | 0.8513 | 0.3619 | 0.3882 | 0.1938 | 0.1812 | 0.206 |
| historial_completo | primera_mitad | 74109 | 5475 | 0.1817 | 0.0123 | 0.718 | 0.1717 | 0.1891 | 0.0 | 0.0 | 0.0 |
| historial_completo | segunda_mitad | 74109 | 5475 | 0.3959 | 0.0032 | 0.8479 | 0.381 | 0.4079 | 0.2133 | 0.1994 | 0.2272 |
| historial_censurado | historial_entero | 64437 | 4533 | 0.2258 | 0.0092 | 0.768 | 0.2123 | 0.2352 | 0.0407 | 0.0318 | 0.0493 |
| historial_censurado | primera_mitad | 64437 | 4533 | 0.1855 | 0.0151 | 0.729 | 0.1735 | 0.1941 | 0.0 | 0.0 | 0.0 |
| historial_censurado | segunda_mitad | 64437 | 4533 | 0.2169 | 0.0048 | 0.7601 | 0.204 | 0.2254 | 0.0318 | 0.0222 | 0.0408 |

| index | lgbm_censurado_todas | lgbm_censurado_sin_grupo_A | lgbm_censurado_sin_grupo_B |
|---|---|---|---|
| variables | 43.0 | 38.0 | 29.0 |
| pr_auc | 0.204 | 0.1905 | 0.1699 |
| roc_auc | 0.7821 | 0.7678 | 0.7415 |
| auc_puntuacion_separa_evento | 0.6912 | 0.6568 | 0.625 |
| auc_variables_predicen_evento | 0.9051 | 0.8713 | 0.8298 |
| roc_auc_sin_evento | 0.7698 | 0.7778 | 0.7694 |
| pr_auc_sin_evento | 0.0913 | 0.0981 | 0.0912 |
| roc_auc_con_evento | 0.6972 | 0.6868 | 0.6658 |
| pr_auc_con_evento | 0.354 | 0.3424 | 0.3245 |

## Desempeño por evento de equipo o de contrato (dev)

| evento_equipo | lgbm_comportamiento | lgbm_comportamiento_y_exposicion | lgbm_historial_completo | solo_exposicion |
|---|---|---|---|---|
| con_evento | 0.687 | 0.696 | 0.771 | 0.631 |
| sin_evento | 0.778 | 0.798 | 0.802 | 0.714 |

## Estabilidad frente a la semilla de partición

| semilla | pr_auc_media | pr_auc_desv_pliegues | roc_auc_media |
|---|---|---|---|
| 42 | 0.1921 | 0.0065 | 0.7683 |
| 7 | 0.1884 | 0.0108 | 0.7639 |
| 2026 | 0.1888 | 0.0069 | 0.7672 |

## Importancia por familia (SHAP)

| familia | participacion |
|---|---|
| tarifa_contador | 0.312 |
| consumo | 0.196 |
| dinamica | 0.182 |
| lectura | 0.139 |
| cliente | 0.096 |
| relativa_pares | 0.074 |

## Holdout sellado (evaluación única)

| modelo | pr_auc | pr_auc_ic95_lo | pr_auc_ic95_hi | roc_auc | brier |
|---|---|---|---|---|---|
| lgbm_comportamiento | 0.1915 | 0.1745 | 0.2108 | 0.7615 | 0.049 |
| solo_exposicion | 0.1316 | 0.1217 | 0.1437 | 0.7452 | 0.0506 |
| lgbm_comportamiento_y_exposicion | 0.2426 | 0.2235 | 0.2645 | 0.8179 | 0.0472 |
| lgbm_historial_completo | 0.3814 | 0.3589 | 0.4071 | 0.8789 | 0.0418 |
| lgbm_censurado_sin_grupo_B | 0.174 | 0.1582 | 0.192 | 0.7425 | 0.0497 |

| fraccion | k | precision | recall | techo_recall | lift |
|---|---|---|---|---|---|
| 0.005 | 135 | 0.4074 | 0.0364 | 0.0892 | 7.297 |
| 0.01 | 271 | 0.4354 | 0.078 | 0.1791 | 7.7988 |
| 0.02 | 542 | 0.3542 | 0.1269 | 0.3582 | 6.3448 |
| 0.05 | 1355 | 0.2598 | 0.2327 | 0.8956 | 4.6528 |
| 0.1 | 2710 | 0.1923 | 0.3443 | 1.0 | 3.4434 |

| evento_equipo | lgbm_censurado_sin_grupo_B | lgbm_comportamiento | lgbm_comportamiento_y_exposicion | lgbm_historial_completo | solo_exposicion |
|---|---|---|---|---|---|
| con_evento | 0.675 | 0.689 | 0.693 | 0.781 | 0.633 |
| sin_evento | 0.753 | 0.758 | 0.791 | 0.804 | 0.733 |

| quintil_historial | lgbm_censurado_sin_grupo_B | lgbm_comportamiento | lgbm_comportamiento_y_exposicion | lgbm_historial_completo | solo_exposicion |
|---|---|---|---|---|---|
| 1 | 0.782 | 0.798 | 0.903 | 0.872 | 0.909 |
| 2 | 0.631 | 0.676 | 0.807 | 0.856 | 0.732 |
| 3 | 0.666 | 0.699 | 0.763 | 0.862 | 0.663 |
| 4 | 0.699 | 0.71 | 0.754 | 0.845 | 0.663 |
| 5 | 0.737 | 0.755 | 0.779 | 0.859 | 0.644 |

| decil | prob_media | tasa_observada | clientes |
|---|---|---|---|
| 0 | 0.0024 | 0.0022 | 2710 |
| 1 | 0.0106 | 0.0114 | 2710 |
| 2 | 0.0172 | 0.0207 | 2710 |
| 3 | 0.024 | 0.0258 | 2710 |
| 4 | 0.0314 | 0.038 | 2710 |
| 5 | 0.0402 | 0.0425 | 2709 |
| 6 | 0.0517 | 0.0517 | 2710 |
| 7 | 0.0682 | 0.0672 | 2710 |
| 8 | 0.0969 | 0.1066 | 2710 |
| 9 | 0.2026 | 0.1923 | 2710 |
