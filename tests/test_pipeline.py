from datetime import datetime, timezone

from motiva_sprint3.models import BandValues, RoadSegment, StacItem
from motiva_sprint3.pipeline import VegetationPipeline


class FakeStacClient:
    api_url = "https://stac.example/api"

    def search(self, segment, **kwargs):
        return [
            StacItem(
                item_id="scene-1",
                collection="sentinel-2",
                acquired_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
                cloud_cover=3.0,
                assets={"B04": "red", "B08": "nir", "B02": "blue"},
            )
        ]


class FakeZonalReader:
    def read(self, item, segment):
        return BandValues(red=(0.2, 0.2), nir=(0.6, 0.6), blue=(0.1, 0.1), total_pixels=4, crs="EPSG:4326")


def test_pipeline_creates_provenance_and_quality_fields():
    segment = RoadSegment("seg-1", {"type": "LineString", "coordinates": [[-46.8, -23.5], [-46.7, -23.4]]}, (-46.8, -23.5, -46.7, -23.4), {})

    result = VegetationPipeline(FakeStacClient(), FakeZonalReader()).run(
        [segment], collections=["sentinel-2"], date_range="2026-01-01/2026-01-31"
    )

    assert result.status == "COMPLETED"
    assert len(result.metrics) == 1
    assert result.metrics[0].scene_id == "scene-1"
    assert result.metrics[0].valid_pixel_ratio == 0.5
    assert result.metrics[0].processing_version == "sprint3-ndvi-evi-v1"
