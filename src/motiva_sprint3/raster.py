from __future__ import annotations

from typing import Any, Protocol

from motiva_sprint3.errors import PipelineError
from motiva_sprint3.models import BandValues, RoadSegment, StacItem
from motiva_sprint3.stac import resolve_band_asset


class ZonalReader(Protocol):
    def read(self, item: StacItem, segment: RoadSegment) -> BandValues:
        ...


class RasterioZonalReader:
    """Read aligned Sentinel bands over a road geometry using rasterio.mask."""

    def __init__(self, timeout_seconds: float = 60.0) -> None:
        self.timeout_seconds = timeout_seconds

    def read(self, item: StacItem, segment: RoadSegment) -> BandValues:
        try:
            import numpy as np
            import rasterio
            from rasterio.io import MemoryFile
            from rasterio.mask import mask
            from rasterio.warp import transform_geom
        except ImportError as exc:
            raise PipelineError("Runtime raster processing requires numpy and rasterio") from exc

        arrays: list[Any] = []
        crs: str | None = None
        for band in ("red", "nir", "blue"):
            href = resolve_band_asset(item, band)
            try:
                from urllib.request import urlopen

                with urlopen(href, timeout=self.timeout_seconds) as response:
                    content = response.read()
            except Exception as exc:
                raise PipelineError(f"Unable to download {band} asset for {item.item_id}") from exc
            with MemoryFile(content) as memory_file:
                with memory_file.open() as dataset:
                    crs = str(dataset.crs) if dataset.crs else None
                    geometry = segment.geometry
                    if dataset.crs:
                        geometry = transform_geom("EPSG:4326", dataset.crs, geometry, precision=6)
                    data, _ = mask(dataset, [geometry], crop=True, filled=False)
                    arrays.append(data[0])

        if not all(array.shape == arrays[0].shape for array in arrays):
            raise PipelineError(f"Band windows are not aligned for {item.item_id}")
        valid = ~np.ma.getmaskarray(arrays[0])
        for array in arrays[1:]:
            valid &= ~np.ma.getmaskarray(array)
        red = np.asarray(arrays[0].data)[valid]
        nir = np.asarray(arrays[1].data)[valid]
        blue = np.asarray(arrays[2].data)[valid]
        return BandValues(
            red=tuple(float(value) for value in red),
            nir=tuple(float(value) for value in nir),
            blue=tuple(float(value) for value in blue),
            total_pixels=int(arrays[0].size),
            crs=crs,
        )
