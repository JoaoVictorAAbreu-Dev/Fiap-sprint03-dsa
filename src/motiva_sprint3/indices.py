from __future__ import annotations

import math

from motiva_sprint3.errors import PipelineError


def calculate_metrics(
    red: tuple[float, ...],
    nir: tuple[float, ...],
    blue: tuple[float, ...],
) -> tuple[float, float, int]:
    """Calculate mean NDVI/EVI from aligned, valid band samples.

    The function never substitutes a value for an invalid pixel. A caller must
    decide what to do when no valid samples remain.
    """

    if not red or len(red) != len(nir) or len(red) != len(blue):
        raise PipelineError("Red, NIR and blue samples must be non-empty and aligned")
    ndvi_values: list[float] = []
    evi_values: list[float] = []
    for red_value, nir_value, blue_value in zip(red, nir, blue):
        if not all(math.isfinite(value) for value in (red_value, nir_value, blue_value)):
            continue
        ndvi_denominator = nir_value + red_value
        evi_denominator = nir_value + 6.0 * red_value - 7.5 * blue_value + 1.0
        if ndvi_denominator == 0 or evi_denominator == 0:
            continue
        ndvi_values.append((nir_value - red_value) / ndvi_denominator)
        evi_values.append(2.5 * (nir_value - red_value) / evi_denominator)
    if not ndvi_values:
        raise PipelineError("No valid pixels remained after index calculation")
    return (
        sum(ndvi_values) / len(ndvi_values),
        sum(evi_values) / len(evi_values),
        len(ndvi_values),
    )
