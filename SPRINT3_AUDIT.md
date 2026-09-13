# Auditoria técnica e plano de execução — Sprint 3

Data da auditoria: 2026-09-13  
Projeto auditado: `Challenge_Motiva_demo_release_candidate`  
Checkout auditado: `C:\Temp\Challenge_Motiva_demo_release_candidate`  
Branch observada: `frontend/public-demo-polish`  
Commit observado: `901fdff`

> **Nota de escopo.** O diretório de trabalho solicitado, `C:\Users\jv921\OneDrive\Documentos\ChatGPT\Sprints 03`, está vazio, sem commits e sem os arquivos do projeto. O checkout funcional encontrado foi auditado como fonte de verdade. Este relatório foi criado no diretório de trabalho atual; nenhuma funcionalidade do checkout auditado foi modificada.

## Resumo executivo

O projeto atual é uma plataforma operacional demonstrável, com backend FastAPI, frontend React/Vite, PostgreSQL/Alembic, importação de KMZ/KML e XLSX, regras de priorização, crescimento vegetal, planejamento, equipes, ordens de serviço, alertas e relatórios.

O núcleo existente é funcional para o fluxo demo e possui boa separação entre rotas, serviços, repositórios, modelos e schemas. A base de testes do backend reportou 58 testes como `PASSED`, mas o processo não encerrou sozinho após o resumo e precisou ser interrompido. No frontend, lint, checagem de encoding e o teste Vitest passaram; o build chegou à compilação TypeScript, mas falhou ao remover um arquivo existente em `frontend/dist` por `EPERM`.

O principal limite para a Sprint 3 é que o sistema ainda não executa um pipeline de sensoriamento remoto real. Não foram encontrados dados Sentinel/Landsat, arquivos geoespaciais de domínio, dependências de raster/GIS, consultas a imagens, cálculo de NDVI/EVI por bandas, séries temporais orbitais ou jobs ativos. O provider GEE real inicializa opcionalmente, mas retorna dados determinísticos; os módulos Sentinel e GIS contêm apenas docstrings.

Recomendação: preservar o fluxo operacional atual e implementar uma fatia vertical controlada de aquisição real, com proveniência e qualidade explícitas, em um corredor rodoviário inicialmente delimitado. A expansão para todos os corredores deve ocorrer somente depois de validar geometria, cobertura temporal, nuvens, associação espacial e reprodutibilidade.

## 1. Arquitetura atual

### 1.1 Estrutura de pastas

```text
.
├── backend/
│   ├── app/
│   │   ├── api/routes/          # Rotas FastAPI
│   │   ├── core/                # Configuração, banco, erros, logs
│   │   ├── jobs/                # Arquivos placeholder de jobs
│   │   ├── models/              # Entidades SQLAlchemy
│   │   ├── repositories/        # Acesso a dados
│   │   ├── schemas/              # Contratos Pydantic
│   │   ├── seed_data/            # Dataset determinístico de demonstração
│   │   ├── services/              # Regras e orquestração
│   │   └── utils/                 # Helpers compartilhados
│   ├── migrations/versions/      # Alembic, revisões 0001 a 0010
│   ├── sql/                      # SQL de tuning para Supabase
│   ├── tests/                    # 58 testes coletados
│   ├── .env.example
│   ├── requirements.txt
│   ├── Dockerfile
│   └── README.md
├── frontend/
│   ├── src/app/                  # Provider e composição da aplicação
│   ├── src/components/           # Componentes UI e primitives operacionais
│   ├── src/data/                 # Configuração estática de redes no mapa
│   ├── src/features/             # Páginas por domínio
│   ├── src/layouts/              # App shell
│   ├── src/lib/                  # API client, fallback demo e exportação
│   ├── src/routes/               # TanStack Router
│   ├── src/services/             # Query options e composição de dados
│   ├── src/stores/               # Zustand: sessão, preferências e contexto
│   ├── .env.example
│   ├── package.json
│   └── scripts/                  # Dev, build, preview e encoding
├── docs/                         # Fluxos, deploy, demo e especificações
├── .github/workflows/            # CI e publicação de artefatos
├── docker-compose.yml            # PostgreSQL local e API
└── vercel.json                   # Configuração de serviços
```

### 1.2 Backend

- Entrypoint: `backend/app/main.py`.
- Framework: FastAPI com CORS, lifespan e handlers globais para erro de aplicação e validação.
- Persistência: SQLAlchemy síncrono com `SessionLocal`, engine lazy e Alembic.
- Banco previsto: PostgreSQL. A migration `0003_supabase_schema_tuning.py` tenta habilitar `pgcrypto` e `postgis`.
- Camada HTTP: routers finos em `backend/app/api/routes/`.
- Regras: serviços de análise, vegetação, crescimento, compliance, planejamento, roçada, notificações e importação.
- Acesso a dados: repositórios específicos por agregado/tabela.
- Contratos: schemas Pydantic separados para entradas e respostas.
- Erros: `ApplicationError` e `RequestValidationError` centralizados em `backend/app/core/exceptions.py`.
- Observabilidade: logging básico e endpoints `/health` e `/api/metrics`.

### 1.3 Banco e modelo de dados

As entidades atuais são:

- `road_segments`: rodovia, KM, risk zone e `geometry` como texto GeoJSON;
- `maintenance_history`: histórico de cortes/manutenções;
- `vegetation_analyses`: EVI/NDVI, chuva, IPO, prioridade, fonte, confiança e breakdown;
- `vegetation_inspections`: níveis 1/2/3, data, classe de altura e payload original;
- `weather_records`: chuva, temperatura, umidade, fonte e instante;
- `compliance_rules`: regras de conformidade;
- `operational_teams`, `service_orders`, `operational_notifications`;
- `planning_runs` e `planning_items`;
- `import_jobs` e `import_job_errors`.

As migrations estão encadeadas de `0001_initial_data_layer` a `0010_explainable_ipo`. Há índices de consulta por rodovia, data, prioridade, IPO, status e checksum. Não há coluna espacial nativa, tabela de cenas/imagens, tabela de métricas orbitais, catálogo de fontes ou registro de aquisição.

### 1.4 Frontend

- React 19, TypeScript, Vite, TanStack Router, TanStack Query, Zustand, Tailwind, Recharts e React Leaflet.
- Rotas existentes: login, dashboard, rodovias, trechos, vegetação, mapa, manutenções, criticidade, IA, relatórios, alertas, equipes e configurações.
- O app shell sincroniza contexto de rodovia/segmento entre mapa, trechos, alertas, equipes e IA.
- `frontend/src/lib/api.ts` concentra as chamadas HTTP e, quando `VITE_API_BASE_URL` está ausente ou a API falha, retorna valores demo determinísticos.
- O mapa efetivamente utiliza Leaflet, uma polilinha estática de `frontend/src/data/roadNetworks.ts` e marcadores derivados das análises. A resposta GeoJSON é consultada apenas para exibir a quantidade de features; suas geometrias não são renderizadas.
- `maplibre-gl` está no `package.json`, mas não foi encontrado uso correspondente no código fonte atual.
- O estado de sessão é persistido no navegador por Zustand; não há token nem comunicação com uma API de autenticação.

### 1.5 APIs e fluxos existentes

Os grupos de endpoint registrados em `backend/app/main.py` são:

- saúde e métricas;
- análise e histórico de análises;
- segmentos rodoviários e busca;
- dashboard e GeoJSON;
- relatórios e resumo semanal;
- inspeções e tendências de vegetação;
- importação/preview/rollback de KMZ/KML e XLSX;
- crescimento vegetal e notificações de roçada;
- planejamento semanal;
- equipes operacionais;
- ordens de serviço;
- notificações operacionais;
- compliance;
- inicialização do provider GEE;
- histórico de cortes.

O fluxo operacional central é: análise do trecho → IPO → crescimento estimado → equipe → rota → notificação → ordem de serviço → planejamento.

### 1.6 Variáveis de ambiente e serviços externos

Documentados em `backend/.env.example` e `frontend/.env.example`:

- Banco: `DATABASE_URL`, pooler, SSL e timeout;
- API: `APP_ENV`, `SECRET_KEY`, CORS e criação automática de tabelas;
- GEE: `GEE_MODE`, projeto, credenciais e service account;
- Clima: `WEATHER_MODE`, OpenWeather, URL e timeout;
- Texto de notificação: `GROQ_API_KEY`, modelo, URL e timeout;
- Frontend: `VITE_API_BASE_URL`.

O `.env.example` não contém credenciais reais. O `docker-compose.yml` usa credenciais locais explícitas para desenvolvimento (`user/password`) e define `SECRET_KEY=change-me`; isso é aceitável apenas como configuração local, não como configuração de produção.

### 1.7 Pipelines, scripts e documentação

- CI (`.github/workflows/ci.yml`): PostgreSQL/PostGIS em serviço, migrations Alembic, testes backend, encoding, lint, testes frontend e build.
- CD (`.github/workflows/cd.yml`): publicação da imagem backend no GHCR e artefato de build do frontend.
- Docker: imagem da API e compose local.
- Seed: `backend/app/seed.py`, com dados determinísticos para demo.
- Jobs: `daily_analysis.py`, `weekly_report.py` e `scheduler.py` ainda são placeholders.
- Documentação existente: setup, deploy, demo, fluxo de decisão, dados demo/reais e API operacional.

## 2. Funcionalidades existentes

| Funcionalidade | Classificação | Localização e comportamento atual | Problemas e impacto na Sprint 3 |
|---|---|---|---|
| API FastAPI e contratos | ✅ Implementado e funcional | Routers, schemas e serviços cobrem os fluxos operacionais; testes exercitam rotas e OpenAPI. | Depende de dados demo/importados; não representa ainda um pipeline orbital real. |
| Configuração e conexão lazy | ✅ Implementado e funcional | `backend/app/core/config.py` e `database.py` permitem configuração por ambiente e evitam criação eager do engine. | Migrations reais e conexão de banco não foram executadas nesta auditoria. |
| Migrations | ✅ Implementado | Dez revisões Alembic encadeadas, com tabelas e índices. `alembic history` foi validado. | A execução depende de um PostgreSQL disponível. O compose usa `postgres:16-alpine`, enquanto a migration exige extensão PostGIS; há risco de incompatibilidade local. |
| Modelo espacial | ⚠️ Implementado mas incompleto | `road_segments.geometry` recebe GeoJSON serializado em `Text`; o endpoint dashboard monta FeatureCollection. | Não há tipo geometry, SRID, índices espaciais, buffer, interseção ou join raster-vetor. É o principal gap estrutural. |
| Seed de demonstração | 🧪 Mockado | Gera 8 redes, 120 microtrechos, 500 inspeções, 300 observações climáticas, 150 manutenções/análises, 5 equipes, 30 OS e 20 notificações, conforme código/documentação. | É determinístico e sintético; não pode ser apresentado como medição pública ou evidência orbital. Deve permanecer isolado do dataset real. |
| Importação KMZ/KML | ✅ Implementado e funcional | `KmzImporter` lê KMZ compactado ou KML, extrai Point/LineString/Polygon, calcula checksum, persiste segmentos e registra histórico/rollback. | É ingestão por upload, não aquisição automática. A geometria ainda termina em texto; validação topológica e CRS são insuficientes. |
| Importação XLSX | ✅ Implementado e funcional | `XlsxVegetationImporter` lê contexto da planilha, percentuais, data do nome do arquivo e cria inspeções. | Não há contrato genérico de fonte; data sem padrão cai em `date.today()`. A associação por sobreposição de KM é simples e pode criar segmento sem geometria. |
| Preview/confirm/rollback | ⚠️ Implementado mas incompleto | Preview retorna checksum, amostra, avisos; confirmação processa arquivo; import job armazena contagens e IDs para rollback. | `confirm` não exige vínculo com uma execução de preview nem verifica que o arquivo confirmado corresponde a um preview. Idempotência é por checksum concluído. |
| Análise e IPO | ✅ Implementado e funcional | Usa inspeção real importada quando existe; caso contrário usa EVI/NDVI/chuva determinísticos. Persiste versão, fonte, confiança e fatores. | O caminho sem inspeção é mockado. A confiança de dados reais é fixa em `0.9`, sem cálculo por cobertura/qualidade. `get_or_create_demo` pode criar segmento sintético ao analisar ID inexistente. |
| NDVI/EVI | 🧪 Mockado | `VegetationIndexService` calcula números determinísticos a partir dos atributos do segmento; provider GEE mock também retorna números determinísticos. | Não há bandas, reflectância, máscara de nuvem, janela temporal ou cálculo em imagem Sentinel/Landsat. |
| Provider GEE | ⚠️ Implementado mas incompleto | `RealGeeProvider` tenta importar `ee` e inicializar com credenciais; fallback é determinístico. | Mesmo quando inicializado, `get_analysis_data` retorna `gee-ready` determinístico. Não consulta ImageCollection nem extrai pixels. A dependência `earthengine-api` não está em `requirements.txt`. |
| Sentinel-1/Sentinel-2 | ❌ Não implementado | `sentinel1.py` e `sentinel2.py` contêm apenas docstrings. | Não há aquisição de imagens, catálogo, filtros, composição ou evidência de cobertura. |
| Serviços GIS | ❌ Não implementado | `road_loader.py`, `buffer_generator.py` e `segmentation.py` contêm apenas docstrings. | Não existe corredor de análise configurável, segmentação geográfica, reprojeção, validação ou operações espaciais. |
| Clima | ⚠️ Implementado mas incompleto | Provider mock e adapter OpenWeather funcionam por coordenadas aproximadas por rodovia; `WeatherRecord` é consultado pelo crescimento. | Não há ingestão histórica automática. O adapter Open-Meteo é placeholder. Dados live não são persistidos pelo `WeatherService`; a análise usa override pontual. |
| Séries temporais | ⚠️ Implementado mas incompleto | Tendência usa inspeções armazenadas e compara primeiro/último registro; seed cria campanhas determinísticas. | Não é série temporal orbital. O cálculo de crescimento semanal usa somente delta de nível 3 e não trata lacunas, nuvens, sazonalidade observada ou qualidade. |
| Crescimento vegetal | ✅ Implementado, baseado em regras | `growth_service.py` e `species_growth_service.py` estimam espécie, estação, altura, taxa e projeções em 7/14/30/90 dias. | É modelo heurístico não treinado, com perfis calibrados para demo; não deve ser tratado como previsão validada até haver calibração com dados reais. |
| Score e recomendação | ✅ Implementado, baseado em regras | `ScoreCalculator`, `RealVegetationScoreCalculator` e `RecommendationService` calculam IPO e ação sugerida. | Pesos e faixas são regras de produto, não métricas aprendidas ou validadas estatisticamente. Devem ser versionados junto com a fonte/qualidade. |
| Equipes, OS e planejamento | ✅ Implementado e funcional | CRUD, transições, capacidade, alocação e planejamento semanal persistem no banco; decisão integrada foi testada. | Rota usa distância geográfica/haversine e continuidade simplificada, sem malha rodoviária, tráfego ou restrições reais. |
| Notificação/Groq | ⚠️ Implementado mas incompleto | Groq é opcional apenas para redação; fallback local monta mensagem determinística. | IA não decide IPO, equipe ou rota. Não há fila, retry, auditoria de prompt/resposta ou controle de custo. |
| Jobs agendados | ❌ Não implementado | Arquivos em `backend/app/jobs/` são placeholders. | Não há aquisição periódica, processamento incremental, retry, lock ou observabilidade de execução. |
| Dashboard e relatórios backend | ✅ Implementado e funcional | Endpoints agregam resumo, críticos, compliance, prioridade, histórico e GeoJSON; exportação é feita no frontend. | Agregações usam tabelas atuais e podem misturar dados demo e importados sem uma política de separação explícita. |
| Dashboard frontend | ✅ Implementado para demo | React Query, Recharts, cards, estados e navegação cobrem a apresentação operacional. | Sem API, os números vêm do dataset demo. Não há indicador consistente de cobertura, idade, qualidade ou fonte orbital. |
| Mapa frontend | ⚠️ Implementado mas incompleto / 🐛 Possui problemas | Leaflet renderiza uma única rede estática, pontos derivados de análises e popup de segmento. | A camada selecionada não altera a visualização; GeoJSON do backend não é desenhado; só há uma rede configurada no frontend; posições são aproximações. |
| Integração frontend-backend | ⚠️ Implementado mas incompleto | `api.ts` chama `/api/*` quando configurado e usa fallback em erro ou ausência de URL. | Fallback retorna sucesso sintético para mutações sem alterar arrays demo; a tela pode indicar operação concluída sem persistência. |
| Autenticação | 🧪 Mockado / ❌ Não implementado no backend | Login aceita e-mail válido e senha com pelo menos seis caracteres; sessão é persistida no localStorage via Zustand. | Não existe endpoint, JWT, hash, usuário, autorização por rota ou expiração de token. Não é segurança real. |
| CI/CD | ✅ Implementado | Workflows definem testes/migrations/build e publicação de artefatos. | Nesta máquina o Docker não está instalado e o pytest não encerrou limpo; o status real de CI remoto não foi consultado nesta auditoria. |

## 3. Problemas encontrados

### 3.1 Bloqueadores técnicos para o objetivo da Sprint 3

1. **Não há aquisição automatizada.** Os dados reais entram somente por upload manual de KMZ/KML/XLSX. Não existe cliente de catálogo, downloader, paginação, retry, cache, checksum por cena ou execução agendada.
2. **Não há sensoriamento remoto real.** GEE real não consulta imagens; Sentinel-1/Sentinel-2 são placeholders; não existem dependências de Earth Engine/raster/GIS no requirements.
3. **Não há processamento geoespacial.** Os segmentos usam GeoJSON em texto e não há PostGIS nativo, SRID, buffer, reprojeção, interseção ou segmentação espacial.
4. **Não há série temporal orbital.** O histórico atual é de inspeções e seed determinístico; não há observação por cena, data de aquisição, cobertura de nuvens, qualidade ou lacunas.
5. **Não há separação formal de proveniência.** Há `data_source`/`source_file` em alguns registros, mas falta um catálogo de fontes, versão de processamento, parâmetros, status e vínculo entre aquisição e métricas.

### 3.2 Problemas de ambiente e execução

- `docker compose config` não pôde ser validado porque o executável Docker não está disponível nesta máquina.
- O compose local usa `postgres:16-alpine`; as migrations tentam criar PostGIS. O CI usa `postgis/postgis:16-3.4-alpine`, portanto os ambientes não são equivalentes.
- `python -m pytest -q backend\tests` e a execução verbosa reportaram todos os 58 testes como aprovados, porém o processo permaneceu ativo após o último teste. Foi necessário interrompê-lo, deixando o comando com saída de processo não limpa.
- `npm run lint`, `npm test -- --run` e `npm run check:encoding` passaram. A checagem de encoding informou 55 arquivos e o Vitest informou 1 arquivo/1 teste.
- `npm run build` passou pela verificação TypeScript e falhou na etapa Vite ao remover `frontend/dist/assets/index-CoTiXACG.css` com `EPERM`. Portanto, o build não está aprovado nesta execução.
- `alembic history` passou, mas `alembic upgrade head` não foi validado contra um banco real nesta auditoria.

### 3.3 Problemas de produto e integração

- O menu principal não expõe as rotas de rodovias, vegetação e manutenções, embora elas existam no router; elas dependem de navegação direta ou de fluxos indiretos.
- A seleção de camada no mapa (`risk`, `vegetation`, `maintenance`) é armazenada na URL, mas não muda os dados/estilo renderizados.
- O endpoint GeoJSON é carregado no mapa apenas para contar features; as features não alimentam o mapa.
- `roadNetworks.ts` contém uma rede principal estática, enquanto o backend seed gera oito redes e 120 microtrechos. Isso produz divergência entre catálogo, mapa e banco.
- O frontend pode exibir “registrado”, “análise recalculada” ou “status atualizado” no fallback demo, mas o estado local não é realmente alterado de forma persistente.
- A sessão mock permite acesso com qualquer senha que satisfaça a validação mínima. O texto “Acesso seguro” não deve ser interpretado como autenticação implementada.
- O método `get_or_create_demo` cria um segmento inexistente durante análise/crescimento. Isso é útil para demo, mas pode poluir um banco que deveria conter apenas segmentos de fonte pública.
- O cálculo de crescimento mistura dados importados, seed e defaults sem um contrato de qualidade comparável entre fontes.

## 4. Funcionalidades mockadas

Os seguintes valores ou fluxos são explicitamente demo, simulados ou fallback:

- seed de rodovias, inspeções, clima, análises, equipes, ordens, notificações e planejamento;
- EVI, NDVI e chuva gerados por funções determinísticas;
- GEE quando `GEE_MODE=mock`, e também o retorno `gee-ready` após inicialização real;
- crescimento, espécie, sazonalidade, confiança e projeções;
- login e sessão do operador;
- fallback integral do frontend quando `VITE_API_BASE_URL` está vazio ou a API falha;
- valores de dashboard, críticos, compliance, rota e decisão no `frontend/src/lib/demo-data.ts`/`api.ts`;
- redação de notificações quando Groq não está configurado;
- mapa e rede frontend em `frontend/src/data/roadNetworks.ts`;
- aproximações de coordenada climática por código de rodovia;
- rota baseada em distância geográfica simples, sem rede viária real.

Esses mocks devem continuar disponíveis para a demonstração, mas precisam ser marcados visualmente e nos contratos como `demo`/`simulated`. Nenhum número demo deve ser usado como resultado da Sprint 3.

## 5. Gaps da Sprint 3

### Aquisição automática

- definir uma fonte pública real e uma área de estudo versionada;
- criar adaptadores com timeout, retry, paginação, rate limit, checksum e cache;
- registrar cada execução, origem, parâmetros, data de aquisição, status, erros e artefatos;
- suportar reprocessamento idempotente e retomada após falha;
- manter os arquivos brutos fora do repositório quando apropriado, com manifesto e checksum versionados.

### Processamento geoespacial

- decidir e documentar CRS/SRID e unidade de trabalho;
- migrar progressivamente de texto GeoJSON para geometry PostGIS, sem remover o contrato atual antes de compatibilidade;
- validar geometrias inválidas, ordem de coordenadas e extensão espacial;
- gerar corredor/buffer configurável ao redor da rodovia;
- segmentar a rodovia com regra operacional aprovada;
- associar cada observação espacial ao segmento por interseção/contensão espacial;
- devolver GeoJSON real e propriedades de qualidade para o frontend.

### Imagens e indicadores

- implementar provider Sentinel-2 ou equivalente público aprovado;
- aplicar filtro de nuvem e máscara de qualidade;
- obter bandas necessárias e calcular NDVI/EVI por pixel/área;
- agregar estatísticas por segmento/corredor, mantendo quantidade de pixels válidos;
- registrar data, cena, resolução, cobertura, método e versão do processamento;
- definir tratamento para ausência de cena, baixa cobertura e inconsistência entre datas.

### Análise temporal

- criar série por segmento e data de observação;
- separar data de aquisição, data de processamento e data de publicação;
- calcular tendência somente com número suficiente de observações válidas;
- registrar lacunas e evitar interpolação silenciosa;
- diferenciar tendência observada de projeção heurística;
- medir qualidade e confiança a partir de evidências, não de constantes fixas.

### Persistência

- adicionar catálogo de fontes e execuções de ingestão;
- adicionar tabela de cenas/observações orbitais e métricas agregadas;
- criar chaves idempotentes por fonte, cena, segmento e versão do algoritmo;
- indexar consultas temporais e espaciais;
- impedir que `get_or_create_demo` seja usado no caminho real;
- manter dados demo isolados por ambiente ou flag explícita.

### API

- endpoint para iniciar/consultar execução de ingestão;
- endpoint para cobertura e qualidade da aquisição;
- endpoint de série temporal por segmento;
- endpoint de indicadores NDVI/EVI com proveniência;
- endpoint de GeoJSON com propriedades de risco, vegetação, manutenção e qualidade;
- filtros por rodovia, intervalo de data, fonte e status;
- contratos que diferenciem `observed`, `derived`, `forecast` e `demo`.

### Dashboard

- mapa baseado na geometria retornada pelo backend;
- camadas realmente distintas para risco, vegetação e manutenção;
- legenda de fonte, data da última cena, cobertura e qualidade;
- gráfico temporal de NDVI/EVI por segmento;
- estado explícito de sem cobertura, baixa qualidade e dados ausentes;
- evidência visual de execução, não apenas números agregados;
- priorização que explique quais indicadores observados sustentam cada segmento.

### Evidências de execução

- manifesto de entrada com fonte, URL/identificador, checksum e data;
- logs de cada etapa e contagens de entrada/saída;
- amostras GeoJSON e tabelas de métricas exportadas;
- captura ou relatório da execução real do pipeline;
- testes com fixture pública pequena e dados incompletos;
- comparação entre modo real e modo demo sem misturar os resultados;
- documentação de limitações, cobertura e ausência de validação de campo.

## 6. Recomendações técnicas

1. **Preservar o fluxo operacional atual.** Criar adaptadores e novas tabelas/módulos ao redor do contrato existente; não reescrever dashboard, IPO, equipes e planejamento sem necessidade.
2. **Separar aquisição, processamento e decisão.** A aquisição deve produzir artefatos/proveniência; o processamento deve produzir métricas; a decisão deve consumir métricas versionadas.
3. **Escolher uma área piloto.** Começar por uma rodovia/corredor com geometria pública confirmada e cobertura orbital suficiente. A escala deve ser ampliada somente após o vertical slice funcionar.
4. **Usar PostGIS de fato ou assumir explicitamente a limitação.** Para a Sprint 3, operações de buffer/interseção tornam a extensão espacial necessária; alinhar compose local e CI com uma imagem PostGIS.
5. **Criar um modo real observável.** O provider deve informar `source`, `scene_id`, `acquired_at`, `cloud_cover`, `valid_pixel_ratio`, `algorithm_version` e status de fallback.
6. **Não esconder fallback.** Em qualquer resposta, incluir origem e qualidade. Fallback determinístico deve ser uma decisão explícita e visível.
7. **Evitar métricas inventadas.** Pesos do IPO e limiares atuais devem ser apresentados como regras de negócio provisórias até haver justificativa e validação documental.
8. **Adicionar testes de contrato e fixtures.** Testar arquivos reais anonimizados/públicos, CRS, geometria inválida, ausência de cenas, nuvens, duplicidade e reprocessamento.
9. **Manter o real e o demo isolados.** Preferir `APP_ENV`/namespace de dados e impedir que endpoints de análise criem segmentos sintéticos no banco real.
10. **Corrigir o pipeline de validação antes do merge da Sprint 3.** O pytest deve encerrar com código zero; o build deve usar uma pasta de saída desbloqueada; migration deve ser executada em PostGIS.

## 7. Roadmap de implementação

| Fase | Objetivo | Arquivos/módulos afetados | Dependências | Riscos | Complexidade | Prioridade |
|---|---|---|---|---|---|---|
| 1. Contrato e governança de dados | Definir fonte, área piloto, CRS, granularidade, nomenclatura, proveniência e política demo/real. | `docs/`, `backend/app/schemas/`, novas especificações de ingestão e qualidade. | Decisão de produto e fonte pública confirmada. | Escolher fonte sem cobertura ou sem licença adequada. | M | P0 |
| 2. Infraestrutura espacial | Alinhar compose/CI com PostGIS e preparar migração aditiva para geometry, SRID e índices espaciais. | `docker-compose.yml`, `backend/requirements.txt`, migrations, `models/road.py`, config de banco. | PostGIS e GeoAlchemy2 ou abordagem SQL equivalente. | Migration incompatível, geometrias inválidas, downtime em banco existente. | M | P0 |
| 3. Aquisição automatizada | Implementar provider público com cache, retry, checksum, rate limit e execução registrada. | Novo `backend/app/services/ingestion/`, `jobs/`, `models/`, `repositories/`, migrations, `.env.example`. | Cliente HTTP/STAC/GEE escolhido, armazenamento de artefatos. | Rate limit, API instável, volume, credenciais e cobertura insuficiente. | G | P0 |
| 4. Geoprocessamento | Validar rodovias, gerar corredor configurável, segmentar e fazer associação espacial. | `services/gis/`, modelos espaciais, schemas GeoJSON, testes GIS. | PostGIS, CRS definido, geometria de entrada real. | CRS errado e associação espacial incorreta podem invalidar todos os indicadores. | G | P0 |
| 5. Indicadores orbitais | Obter cenas, mascarar nuvens, calcular NDVI/EVI e agregar por segmento com qualidade. | `services/gee/` ou novo provider, `services/vegetation/`, modelos de observação/métrica, testes. | Provider orbital, bandas, biblioteca raster/algoritmo aprovado. | Nuvens, resolução, ausência de pixels e custo de processamento. | G | P0 |
| 6. Série temporal e priorização | Persistir observações por data, calcular tendência observada e conectar indicadores ao IPO versionado. | `models/analysis.py`, novos modelos de série, `analysis_service.py`, scoring, migrations e schemas. | Dados reais suficientes, regra de qualidade, versão do algoritmo. | Confundir correlação com causalidade ou criar confiança artificial. | G | P1 |
| 7. API e dashboard | Expor execução, cobertura, séries, GeoJSON e camadas reais; manter fallback demo claramente marcado. | `backend/app/api/routes/`, `schemas/`, `frontend/src/lib/api.ts`, `features/map`, `features/vegetation`, `queries.ts`. | Fases 2–6 concluídas, contratos estabilizados. | Divergência frontend/backend e regressão nos fluxos demo. | M/G | P1 |
| 8. Testes, evidências e operação | Validar pipeline real, falhas, reprocessamento, build, migrations e produzir artefatos da Sprint. | `backend/tests/`, testes frontend, `.github/workflows/`, `docs/`, manifesto de execução. | Ambiente PostGIS, fonte acessível e fixture pública. | Não reproduzir execução ou apresentar demo como resultado real. | M | P0 |

### Ordem recomendada de entrega

1. Fechar o contrato de dados e a área piloto.
2. Resolver PostGIS/CRS e o modelo de proveniência.
3. Implementar aquisição real de uma fonte e registrar a execução.
4. Implementar geometria, buffer e segmentação.
5. Processar uma coleção pequena de imagens reais e persistir indicadores com qualidade.
6. Expor série temporal e GeoJSON real.
7. Conectar mapa/dashboard sem remover o fallback demo.
8. Executar testes de falha e publicar evidências.

## 8. Critérios de aprovação da Sprint 3

Antes de declarar a Sprint 3 concluída, exigir evidência dos seguintes itens:

- fonte pública identificada e documentada;
- processo executável sem upload manual de cada registro;
- artefatos de entrada preservados por checksum/manifesto;
- pelo menos uma execução real reproduzível;
- geometrias validadas e associadas a segmentos por operação espacial;
- indicadores orbitais calculados a partir de bandas/imagens reais, sem números fabricados;
- série temporal com datas e qualidade;
- persistência e consulta via API;
- mapa consumindo GeoJSON real e exibindo origem/qualidade;
- priorização explicável e marcada como observada, derivada ou prevista;
- testes automatizados para sucesso, duplicidade, ausência de dados, baixa qualidade e falha de provider;
- `alembic upgrade head`, testes backend com término limpo, lint/test/build frontend e evidências da execução real.

## 9. Validação realizada nesta auditoria

| Comando | Resultado |
|---|---|
| `git status --short --branch` no checkout auditado | Branch `frontend/public-demo-polish`, árvore sem alterações observadas. |
| `alembic history` | Passou; cadeia até `0010_explainable_ipo` encontrada. |
| `python -m pytest -vv --maxfail=1 backend\\tests` | Os 58 testes coletados exibiram `PASSED`; o processo não encerrou após o último teste e foi interrompido. Não é um passe limpo do comando. |
| `npm run lint` | Passou sem erros observados. |
| `npm test -- --run` | Passou: 1 arquivo e 1 teste. |
| `npm run check:encoding` | Passou: UTF-8 validado em 55 arquivos. |
| `npm run build` | Falhou na limpeza de `frontend/dist` por `EPERM`; TypeScript foi executado antes da falha. |
| `docker compose config` | Não executado com sucesso porque Docker não está instalado/disponível nesta máquina. |

## Conclusão

O projeto está em uma boa base para uma Sprint 3 incremental: o domínio operacional, os contratos HTTP, a persistência, os importadores e a apresentação já existem. Entretanto, a capacidade central solicitada — aquisição e análise automatizada de dados públicos de sensoriamento remoto — ainda é um gap, não uma funcionalidade pronta.

Este relatório não implementa funcionalidades, não altera código existente e não apresenta métricas ou resultados ambientais novos. A próxima ação recomendada é aprovar a área piloto, a fonte pública e o contrato de proveniência antes de iniciar a Fase 1 do roadmap.
