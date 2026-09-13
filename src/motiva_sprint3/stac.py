from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Callable
from urllib.request import Request, urlopen

from motiva_sprint3.errors import PipelineError
from motiva_sprint3.models import RoadSegment, StacItem

JsonOpener = Callable[[Request], bytes]


class StacClient:
    """Small STAC API client with no provider-specific result fabrication."""

    def __init__(self, api_url: str, timeout_seconds: float = 30.0, opener: JsonOpener | None = None) -> None:
        if not api_url.strip():
            raise PipelineError("STAC_API_URL is required")
        self.api_url = api_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self._opener = opener or self._open

    def search(
        self,
        segment: RoadSegment,
        *,
        collections: list[str],
        date_range: str,
        max_cloud_cover: float | None = None,
        limit: int = 100,
    ) -> list[StacItem]:
        if not collections:
            raise PipelineError("At least one STAC collection is required")
        if not date_range.strip():
            raise PipelineError("A STAC date range is required")
        if limit < 1:
            raise PipelineError("STAC limit must be positive")
        query: dict[str, Any] = {}
        if max_cloud_cover is not None:
            query["eo:cloud_cover"] = {"lte": max_cloud_cover}
        payload = {
            "collections": collections,
            "bbox": list(segment.bbox),
            "datetime": date_range,
            "limit": limit,
            "query": query,
        }
        request = Request(
            f"{self.api_url}/search",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json", "Accept": "application/geo+json"},
            method="POST",
        )
        try:
            raw = self._opener(request)
            document = json.loads(raw.decode("utf-8"))
        except Exception as exc:
            raise PipelineError(f"STAC search failed: {exc.__class__.__name__}") from exc
        if not isinstance(document, dict):
            raise PipelineError("STAC response must be a JSON object")
        features = document.get("features")
        if not isinstance(features, list):
            raise PipelineError("STAC response has no features list")
        return [self._parse_item(item) for item in features if isinstance(item, dict)]

    def _open(self, request: Request) -> bytes:
        with urlopen(request, timeout=self.timeout_seconds) as response:
            return response.read()

    def _parse_item(self, item: dict[str, Any]) -> StacItem:
        properties = item.get("properties") or {}
        acquired_value = properties.get("datetime") or properties.get("start_datetime")
        if not acquired_value:
            raise PipelineError(f"STAC item {item.get('id', '<unknown>')} has no acquisition datetime")
        try:
            acquired_at = datetime.fromisoformat(str(acquired_value).replace("Z", "+00:00"))
        except ValueError as exc:
            raise PipelineError(f"STAC item {item.get('id', '<unknown>')} has invalid acquisition datetime") from exc
        cloud_cover = properties.get("eo:cloud_cover", properties.get("cloud_cover"))
        try:
            parsed_cloud = float(cloud_cover) if cloud_cover is not None else None
        except (TypeError, ValueError) as exc:
            raise PipelineError(f"STAC item {item.get('id', '<unknown>')} has invalid cloud cover") from exc
        item_id = str(item.get("id", "")).strip()
        if not item_id:
            raise PipelineError("STAC item has no id")
        assets: dict[str, str] = {}
        for key, asset in (item.get("assets") or {}).items():
            if isinstance(asset, dict) and isinstance(asset.get("href"), str) and asset["href"].strip():
                assets[str(key)] = asset["href"]
        return StacItem(
            item_id=item_id,
            collection=(item.get("collection") or (item.get("collection", [None])[0] if isinstance(item.get("collection"), list) else None)),
            acquired_at=acquired_at,
            cloud_cover=parsed_cloud,
            assets=assets,
        )


def resolve_band_asset(item: StacItem, band: str) -> str:
    aliases = {
        "red": (band, "B04", "B4", "red", "red_band"),
        "nir": (band, "B08", "B8", "nir", "nir08", "nir_band"),
        "blue": (band, "B02", "B2", "blue", "blue_band"),
    }
    for alias in aliases.get(band, (band,)):
        if alias in item.assets:
            return item.assets[alias]
    raise PipelineError(f"STAC item {item.item_id} has no {band} asset")
