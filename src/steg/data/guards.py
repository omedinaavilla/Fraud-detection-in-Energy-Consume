"""Guardias de partición: impiden que un análisis que mira ``target`` corra fuera de train.

Regla de higiene del EDA (``contextPrompt.md`` y ``.claude/agents/eda-analyst.md``):
todo análisis que use ``target`` corre exclusivamente sobre ``client_train`` /
``invoice_train``. Esta guardia hace cumplir la regla por construcción, en vez de
confiar en la disciplina de quien llama. La Fase 3 puede reutilizarla.

La guardia es deliberadamente estricta y **no tiene interruptor**: no acepta
parámetro, variable de entorno ni flag que la desactive. Tampoco normaliza: un id
``"Train_Client_0"`` o ``" train_Client_0"`` no se "corrige", se rechaza, porque un id
con ese formato ya indica que algo en la carga se salió del contrato de datos.
"""

from __future__ import annotations

import pandas as pd

from steg.config import TRAIN_ID_PREFIX

# Número máximo de ids de ejemplo que se muestran en el mensaje de error.
_MAX_EXAMPLES: int = 5


class PartitionLeakError(ValueError):
    """El índice recibido no pertenece (entero) a la partición de entrenamiento."""


def _raise(reason: str, n_failed: int, n_total: int, examples: list[object]) -> None:
    shown = ", ".join(repr(x) for x in examples[:_MAX_EXAMPLES])
    raise PartitionLeakError(
        f"assert_train_partition: {reason}. {n_failed} de {n_total} filas fallaron; "
        f"ejemplos (hasta {_MAX_EXAMPLES}): [{shown}]. Se exige que todo id sea un str "
        f"que empiece exactamente por {TRAIN_ID_PREFIX!r} (sin normalizar mayúsculas "
        f"ni espacios)."
    )


def _is_train_id(value: object) -> bool:
    return (
        isinstance(value, str)
        and value.startswith(TRAIN_ID_PREFIX)
        and len(value) > len(TRAIN_ID_PREFIX)
    )


def assert_train_partition(index: pd.Index) -> None:
    """Verifica que ``index`` contiene solo ``client_id`` de la partición de train.

    Acepta únicamente un ``pd.Index`` no vacío cuyos elementos sean todos ``str`` y
    empiecen exactamente por ``TRAIN_ID_PREFIX`` (``"train_"``) seguido de al menos un
    carácter. Lanza :class:`PartitionLeakError` en cualquier otro caso:

    - el argumento no es un ``pd.Index``, o es un ``MultiIndex``;
    - es un ``RangeIndex`` (índice posicional: se perdió el ``client_id``);
    - está vacío (un análisis sobre cero filas no demuestra nada);
    - algún elemento no es ``str`` (numérico, ``NaN``, ``None``, ``pd.NA``);
    - algún elemento no empieza por ``"train_"`` — incluye ``test_*``, ``Train_*``,
      ``" train_*"`` y ``"train"`` sin guion bajo. Basta una fila para fallar.

    El mensaje de error informa cuántas filas fallaron y muestra hasta 5 ids de
    ejemplo (con ``repr``, para que los espacios sean visibles).

    Límites conocidos (lo que esta guardia NO detecta):

    1. **No distingue train de un valid interno.** Una partición de validación
       interna (p. ej. los folds de ``src/steg/data/split.py``) también tiene ids
       ``train_*``; la guardia la aceptará. Separar train de valid es
       responsabilidad del split agrupado por cliente, no de esta función.
    2. **No detecta features de test reindexadas con ids de train.** Solo inspecciona
       el índice, no el origen de los valores: si alguien construye features a partir
       de ``client_test`` y luego les asigna un índice ``train_*``, la guardia pasa.
       Lo mitiga la alineación por firma de T002 (``bivariate.py`` exige que features
       y ``target`` compartan exactamente el mismo índice), no esta función.

    No hay parámetro, variable de entorno ni flag que desactive la verificación.

    Args:
        index: índice de ``client_id`` del DataFrame/Series que se va a analizar.

    Raises:
        PartitionLeakError: si ``index`` no cumple todo lo anterior.
    """
    if not isinstance(index, pd.Index):
        raise PartitionLeakError(
            f"assert_train_partition: se esperaba un pd.Index de client_id y se recibió "
            f"{type(index).__name__}."
        )

    n_total = len(index)
    head = list(index[:_MAX_EXAMPLES])

    if isinstance(index, pd.MultiIndex):
        _raise("el índice es un MultiIndex, no un índice de client_id", n_total, n_total, head)
    if isinstance(index, pd.RangeIndex):
        _raise(
            "el índice es un RangeIndex posicional; se perdió el client_id",
            n_total,
            n_total,
            head,
        )
    if n_total == 0:
        _raise("el índice está vacío", 0, 0, [])

    # Iteración elemento a elemento sobre los valores originales: NaN, None y pd.NA
    # no son str y caen aquí sin ninguna conversión intermedia.
    failed = [v for v in index.tolist() if not _is_train_id(v)]
    if failed:
        n_non_str = sum(1 for v in failed if not isinstance(v, str))
        reason = (
            f"hay ids que no pertenecen a la partición de train "
            f"({n_non_str} no son str)"
        )
        _raise(reason, len(failed), n_total, failed)
