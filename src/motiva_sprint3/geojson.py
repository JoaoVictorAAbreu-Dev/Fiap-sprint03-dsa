from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from motiva_sprint3.errors import PipelineError
from motiva_sprint3.models import RoadSegment


def load_segments(path: str | Path) -> list[RoadSegment]:
    """Load GeoJSON segments without inventing identifiers or coordinates."""

    source = Path(path)
    try:
        document = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PipelineError(f"Unable to read GeoJSON: {source}") from exc

    if not isinstance(document, dict) or document.get("type") != "FeatureCollection":
        raise PipelineError("Road input must be a GeoJSON FeatureCollection")

    features = document.get("features")
    if not isinstance(features, list):
        raise PipelineError("Road input must contain a features list")

    segments: list[RoadSegment] = []
    for index, feature in enumerate(features, start=1):
        if not isinstance(feature, dict) or feature.get("type") != "Feature":
            raise PipelineError(f"Feature {index} is invalid")
        geometry = feature.get("geometry")
        if not isinstance(geometry, dict) or geometry.get("type") not in {"LineString", "MultiLineString", "Polygon", "MultiPolygon"}:
            raise PipelineError(f"Feature {index} must contain a supported geometry")
        properties = feature.get("properties") or {}
        segment_id = properties.get("segment_id", feature.get("id"))
        if segment_id is None or str(segment_id).strip() == "":
            raise PipelineError(f"Feature {index} has no segment_id or feature id")
        coordinates = _flatten_coordinates(geometry)
        if not coordinates:
            raise PipelineError(f"Feature {index} has no coordinates")
        longitudes = [point[0] for point in coordinates]
        latitudes = [point[1] for point in coordinates]
        segments.append(
            RoadSegment(
                segment_id=str(segment_id),
                geometry=geometry,
                bbox=(min(longitudes), min(latitudes), max(longitudes), max(latitudes)),
                properties=dict(properties),
            )
        )
    return segments


def _flatten_coordinates(geometry: dict[str, Any]) -> list[tuple[float, float]]:
    def walk(value: Any) -> list[tuple[float, float]]:
        if isinstance(value, (list, tuple)) and len(value) >= 2 and all(isinstance(item, (int, float)) for item in value[:2]):
            return [(float(value[0]), float(value[1]))]
        if isinstance(value, (list, tuple)):
            points: list[tuple[float, float]] = []
            for child in value:
                points.extend(walk(child))
            return points
        return []

    return walk(geometry.get("coordinates"))
