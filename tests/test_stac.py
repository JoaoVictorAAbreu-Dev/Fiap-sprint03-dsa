import json
from datetime import datetime, timezone
from urllib.request import Request

from motiva_sprint3.models import RoadSegment
from motiva_sprint3.errors import PipelineError
from motiva_sprint3.stac import StacClient, resolve_band_asset


def test_stac_search_sends_segment_bbox_and_parses_assets():
    captured: dict[str, object] = {}

    def opener(request: Request) -> bytes:
        captured["url"] = request.full_url
        captured["payload"] = json.loads(request.data.decode("utf-8"))
        return json.dumps(
            {
                "features": [
                    {
                        "id": "scene-01",
                        "collection": "sentinel-2",
                        "properties": {"datetime": "2026-01-01T12:00:00Z", "eo:cloud_cover": 4.5},
                        "assets": {"B04": {"href": "https://example/red.tif"}, "B08": {"href": "https://example/nir.tif"}, "B02": {"href": "https://example/blue.tif"}},
                    }
                ]
            }
        ).encode("utf-8")

    segment = RoadSegment("seg-1", {"type": "LineString", "coordinates": [[-46.8, -23.5], [-46.7, -23.4]]}, (-46.8, -23.5, -46.7, -23.4), {})
    item = StacClient("https://stac.example/api", opener=opener).search(
        segment,
        collections=["sentinel-2"],
        date_range="2026-01-01/2026-01-31",
        max_cloud_cover=10,
    )[0]

    assert captured["url"] == "https://stac.example/api/search"
    assert captured["payload"]["bbox"] == [-46.8, -23.5, -46.7, -23.4]
    assert item.acquired_at == datetime(2026, 1, 1, 12, tzinfo=timezone.utc)
    assert resolve_band_asset(item, "red") == "https://example/red.tif"


def test_stac_search_rejects_non_positive_limit():
    segment = RoadSegment("seg-1", {"type": "LineString", "coordinates": [[0, 0], [1, 1]]}, (0, 0, 1, 1), {})

    try:
        StacClient("https://stac.example/api").search(segment, collections=["sentinel-2"], date_range="2026-01-01/2026-01-31", limit=0)
    except PipelineError as exc:
        assert str(exc) == "STAC limit must be positive"
    else:
        raise AssertionError("Expected invalid STAC limit to fail")
