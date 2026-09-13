# Motiva — Sprint 3 data pipeline

Implementação inicial do pipeline real de monitoramento da vegetação próxima a rodovias.

## O que existe

- leitura de segmentos rodoviários fornecidos como GeoJSON;
- consulta configurável a uma API STAC pública aprovada;
- seleção de cenas por coleção, intervalo e cobertura de nuvens;
- leitura zonal de bandas red, NIR e blue com `rasterio.mask`;
- cálculo de NDVI e EVI a partir dos valores de bandas, sem substituição de pixels inválidos;
- registro de cena, data, fonte, versão do processamento, CRS e qualidade da amostra;
- saída JSON da execução e CLI `motiva-sprint3`;
- testes unitários e de orquestração sem dados ambientais fabricados.

O pipeline não baixa nem embute dados de exemplo. A execução depende de um GeoJSON e de uma fonte STAC configurados pelo operador.

## Instalação

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[runtime,dev]"
```

## Execução

```powershell
python -m motiva_sprint3 `
  --roads C:\dados\segmentos.geojson `
  --stac-api https://endpoint-stac-aprovado.example/api `
  --collections sentinel-2 `
  --date-range 2026-01-01/2026-03-31 `
  --max-cloud-cover 30 `
  --output output\sprint3-run.json
```

O endpoint, coleção e intervalo acima são parâmetros de exemplo operacional; devem ser confirmados com a fonte escolhida antes da execução. O pipeline falha explicitamente quando os insumos obrigatórios não existem.

## Contrato de entrada

O arquivo de rodovias deve ser um `FeatureCollection` GeoJSON. Cada feature precisa ter `properties.segment_id` ou `id` e uma geometria `LineString`, `MultiLineString`, `Polygon` ou `MultiPolygon`. As coordenadas devem estar em WGS84/EPSG:4326.

## Bandas esperadas

O resolvedor aceita os aliases STAC `B04`/`B4`/`red`, `B08`/`B8`/`nir` e `B02`/`B2`/`blue`. A fonte escolhida deve expor hrefs de raster compatíveis e bandas espacialmente alinhadas.

## Testes

```powershell
python -m pytest
```

Os testes usam respostas e leitores controlados apenas para verificar contratos e fórmulas; não representam resultados ambientais reais.
