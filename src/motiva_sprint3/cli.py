from __future__ import annotations

import argparse
import json
from pathlib import Path

from motiva_sprint3.geojson import load_segments
from motiva_sprint3.pipeline import VegetationPipeline
from motiva_sprint3.raster import RasterioZonalReader
from motiva_sprint3.stac import StacClient


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Processamento real de NDVI/EVI por segmentos rodoviarios")
    parser.add_argument("--roads", required=True, help="GeoJSON FeatureCollection de segmentos")
    parser.add_argument("--stac-api", required=True, help="URL do endpoint STAC aprovado")
    parser.add_argument("--collections", required=True, help="Colecoes STAC separadas por virgula")
    parser.add_argument("--date-range", required=True, help="Intervalo RFC 3339 aceito pelo catalogo")
    parser.add_argument("--max-cloud-cover", type=float)
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--output", required=True, help="Arquivo JSON do resultado da execucao")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    segments = load_segments(args.roads)
    pipeline = VegetationPipeline(StacClient(args.stac_api), RasterioZonalReader())
    result = pipeline.run(
        segments,
        collections=[value.strip() for value in args.collections.split(",") if value.strip()],
        date_range=args.date_range,
        max_cloud_cover=args.max_cloud_cover,
        limit=args.limit,
    )
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"status": result.status, "metrics": len(result.metrics), "errors": len(result.errors)}))


if __name__ == "__main__":
    main()
