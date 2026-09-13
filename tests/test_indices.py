import pytest

from motiva_sprint3.errors import PipelineError
from motiva_sprint3.indices import calculate_metrics


def test_calculate_metrics_uses_real_band_values_without_substitution():
    ndvi, evi, valid_pixels = calculate_metrics(
        red=(0.2, 0.2),
        nir=(0.6, 0.6),
        blue=(0.1, 0.1),
    )

    assert valid_pixels == 2
    assert ndvi == pytest.approx(0.5)
    assert evi == pytest.approx(0.48780487804878037)


def test_calculate_metrics_rejects_empty_or_unaligned_bands():
    with pytest.raises(PipelineError, match="aligned"):
        calculate_metrics((), (0.5,), (0.1,))
