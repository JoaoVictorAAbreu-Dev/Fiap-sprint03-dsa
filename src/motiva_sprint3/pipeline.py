from __future__ import annotations

from datetime import datetime, timezone

from motiva_sprint3.errors import PipelineError
from motiva_sprint3.indices import calculate_metrics
from motiva_sprint3.models import PipelineErrorRecord, PipelineRun, RoadSegment, VegetationMetric
from motiva_sprint3.raster import ZonalReader
from motiva_sprint3.stac import StacClient


class VegetationPipeline:
    def __init__(self, stac_client: StacClient, zonal_reader: ZonalReader, processing_version: str = "sprint3-ndvi-evi-v1") -> None:
        self.stac_client = stac_client
        self.zonal_reader = zonal_reader
        self.processing_version = processing_version

    def run(
        self,
        segments: list[RoadSegment],
        *,
        collections: list[str],
        date_range: str,
        max_cloud_cover: float | None = None,
        limit: int = 100,
    ) -> PipelineRun:
        started_at = datetime.now(timezone.utc)
        result = PipelineRun(started_at=started_at, finished_at=started_at, source=self.stac_client.api_url)
        for segment in segments:
            try:
                items = self.stac_client.search(
                    segment,
                    collections=collections,
                    date_range=date_range,
                    max_cloud_cover=max_cloud_cover,
                    limit=limit,
                )
            except PipelineError as exc:
                result.errors.append(PipelineErrorRecord(segment.segment_id, None, str(exc)))
                continue
            for item in items:
                try:
                    bands = self.zonal_reader.read(item, segment)
                    ndvi, evi, valid_pixels = calculate_metrics(bands.red, bands.nir, bands.blue)
                    if bands.total_pixels <= 0:
                        raise PipelineError("Zonal window has no pixels")
                    result.metrics.append(
                        VegetationMetric(
                            segment_id=segment.segment_id,
                            scene_id=item.item_id,
                            acquired_at=item.acquired_at,
                            source="stac",
                            processing_version=self.processing_version,
                            ndvi_mean=ndvi,
                            evi_mean=evi,
                            valid_pixel_count=valid_pixels,
                            total_pixel_count=bands.total_pixels,
                            valid_pixel_ratio=valid_pixels / bands.total_pixels,
                            cloud_cover=item.cloud_cover,
                            crs=bands.crs,
                        )
                    )
                except PipelineError as exc:
                    result.errors.append(PipelineErrorRecord(segment.segment_id, item.item_id, str(exc)))
        result.finished_at = datetime.now(timezone.utc)
        return result
