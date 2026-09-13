import json

import pytest

from motiva_sprint3.errors import PipelineError
from motiva_sprint3.geojson import load_segments


def test_load_segments_preserves_source_geometry_and_calculates_bbox(tmp_path):
    path = tmp_path / "roads.geojson"
    path.write_text(
        json.dumps(
            {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "id": "seg-01",
                        "properties": {"highway_code": "SP-021"},
                        "geometry": {"type": "LineString", "coordinates": [[-46.8, -23.5], [-46.7, -23.4]]},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    segments = load_segments(path)

    assert segments[0].segment_id == "seg-01"
    assert segments[0].bbox == (-46.8, -23.5, -46.7, -23.4)
    assert segments[0].geometry["type"] == "LineString"


def test_load_segments_rejects_feature_without_identifier(tmp_path):
    path = tmp_path / "roads.geojson"
    path.write_text(json.dumps({"type": "FeatureCollection", "features": [{"type": "Feature", "geometry": {"type": "LineString", "coordinates": [[0, 0], [1, 1]]}}]}), encoding="utf-8")

    with pytest.raises(PipelineError, match="no segment_id"):
        load_segments(path)
