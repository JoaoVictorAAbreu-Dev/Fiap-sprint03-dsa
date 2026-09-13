from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class RoadSegment:
    segment_id: str
    geometry: dict[str, Any]
    bbox: tuple[float, float, float, float]
    properties: dict[str, Any]


@dataclass(frozen=True)
class StacItem:
    item_id: str
    collection: str | None
    acquired_at: datetime
    cloud_cover: float | None
    assets: dict[str, str]


@dataclass(frozen=True)
class BandValues:
    red: tuple[float, ...]
    nir: tuple[float, ...]
    blue: tuple[float, ...]
    total_pixels: int
    crs: str | None


@dataclass(frozen=True)
class VegetationMetric:
    segment_id: str
    scene_id: str
    acquired_at: datetime
    source: str
    processing_version: str
    ndvi_mean: float
    evi_mean: float
    valid_pixel_count: int
    total_pixel_count: int
    valid_pixel_ratio: float
    cloud_cover: float | None
    crs: str | None


@dataclass(frozen=True)
class PipelineErrorRecord:
    segment_id: str
    scene_id: str | None
    message: str


@dataclass
class PipelineRun:
    started_at: datetime
    finished_at: datetime
    source: str
    metrics: list[VegetationMetric] = field(default_factory=list)
    errors: list[PipelineErrorRecord] = field(default_factory=list)

    @property
    def status(self) -> str:
        if not self.metrics and self.errors:
            return "FAILED"
        if self.errors:
            return "PARTIAL"
        return "COMPLETED"

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "started_at": self.started_at.isoformat(),
            "finished_at": self.finished_at.isoformat(),
            "source": self.source,
            "metrics": [
                {
                    **metric.__dict__,
                    "acquired_at": metric.acquired_at.isoformat(),
                }
                for metric in self.metrics
            ],
            "errors": [error.__dict__ for error in self.errors],
        }
