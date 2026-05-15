import numpy as np


def auto_scale(
    value,
    unit
):
    """
    Define escala automática SI.
    """

    if value == 0:
        return 0, unit, 1

    exp = int(
        np.floor(
            np.log10(abs(value)) / 3
        ) * 3
    )

    scale_map = {

        -3: ("m", 1e-3),

        0: ("", 1),

        3: ("k", 1e3),

        6: ("M", 1e6),

        9: ("G", 1e9),
    }

    exp = max(
        min(exp, 9),
        -3
    )

    prefix, factor = scale_map.get(
        exp,
        ("", 1)
    )

    unidade_final = (
        prefix + unit
    )

    return (
        value / factor,
        unidade_final,
        factor
    )