# movies-elt-pipeline

Pipeline ELT local que coleta dados de filmes do **Rotten Tomatoes** e do **Metacritic**, carrega o JSON bruto no **DuckDB** e o transforma com **dbt**. Orquestrado pelo Apache Airflow rodando em Docker Compose.

## Arquitetura

```
Rotten Tomatoes  ──► Scrapy spider  ──┐
                                       ├──► Arquivos JSON ──► DuckDB (raw) ──► dbt (silver/gold)
Metacritic       ──► Python scraper ──┘

Orquestração: Airflow 3.2.1 · LocalExecutor · Docker Compose
```

| Camada | Ferramenta |
|---|---|
| Extração | Scrapy (RT) · pacote Python `mc-scrape` (Metacritic) |
| Orquestração | Apache Airflow 3.2.1 (LocalExecutor) |
| Armazenamento bruto | Arquivos JSON em disco + schema `raw` do DuckDB |
| Transformação | dbt Core com `dbt-duckdb` |

## Pré-requisitos

- [Docker](https://docs.docker.com/get-docker/) + Docker Compose
- Python 3.10+ *(opcional — necessário apenas para rodar o `dbt` ou consultar o DuckDB a partir do seu host em vez de dentro dos containers)*
- [DuckDB CLI](https://duckdb.org/docs/installation/) *(opcional — necessário apenas para consultar o DuckDB a partir do seu host)*

O stack do Docker Compose é autocontido: a imagem do Airflow já embute os scrapers, o `dbt-core` e o `dbt-duckdb` (veja `airflow/Dockerfile`), então nada abaixo é necessário apenas para rodar o pipeline de ponta a ponta. Isso só é necessário se você quiser rodar comandos `dbt` ou consultar o warehouse diretamente a partir da sua máquina host.

## Configuração do ambiente de desenvolvimento local

Para rodar comandos `dbt` ou os scrapers diretamente no seu host (fora do Docker), crie um ambiente virtual e instale as dependências da parte com a qual você está trabalhando:

```bash
# A partir da raiz do repositório
python -m venv .venv
source .venv/bin/activate   # .venv\Scripts\activate no Windows

# dbt (cinemetrics/)
pip install -r cinemetrics/requirements.txt

# Spider do Rotten Tomatoes (opcional)
pip install -r rottentomatoes_spider/requirements.txt

# Scraper do Metacritic (opcional — instalado como pacote editável)
pip install -e mc_scrape/
```

`cinemetrics/requirements.txt` fixa os pacotes Python que o dbt precisa (`dbt-core`, `dbt-duckdb`). Ele não inclui o binário do DuckDB CLI — instale-o separadamente se quiser consultar `data/warehouse.duckdb` a partir de um terminal em vez de via Python.

## Rodando o pipeline (de ponta a ponta)

1. **Suba a infraestrutura**:
   ```bash
   # Sobe tudo (constrói a imagem na primeira execução)
   docker compose up --build -d
   ```
2. **Dispare as DAGs**: 
   Acesse a interface do Airflow em `http://localhost:8080` (credenciais padrão: `airflow` / `airflow`).
   Despause as DAGs: `rt_scraper`, `mc_scraper` e `dbt_build`.
3. **Rode o dbt manualmente (opcional)**:
   Com o [ambiente de desenvolvimento local](#configuração-do-ambiente-de-desenvolvimento-local) configurado e ativado, você também pode rodar as transformações manualmente:
   ```bash
   cd cinemetrics
   dbt deps --profiles-dir . --project-dir .    # instala os pacotes dbt declarados em packages.yml (ex.: dbt_expectations)
   dbt build --profiles-dir . --project-dir .
   ```
   A flag `--profiles-dir .` é necessária: sem ela, o dbt ignora o `cinemetrics/profiles.yml` do repositório e usa `~/.dbt/profiles.yml` (se existir) ou falha caso não exista — é exatamente assim que a DAG `dbt_build` invoca o dbt (veja `airflow/dags/dbt_build_dag.py`). Com a flag, `dbt build` lê/escreve em `data/warehouse.duckdb` (veja `cinemetrics/profiles.yml`), o mesmo arquivo usado pelo pipeline Docker — rode isso enquanto os containers estiverem parados para evitar conflitos de lock de arquivo no DuckDB. `dbt build` já executa os testes; não é necessário rodar `dbt test` separadamente depois.

## Consultando os dados

Os dados coletados são gravados em `data/warehouse.duckdb`. Consulte-os com o DuckDB CLI:

```bash
duckdb data/warehouse.duckdb
```

```sql
SHOW ALL TABLES;

-- Registros brutos
SELECT _source_file, _loaded_at FROM raw.rt_reviews LIMIT 5;

-- Extrai campos do JSON
SELECT
    json_extract_string(record, '$.movie_id') AS movie,
    json_extract_string(record, '$.quote')    AS quote
FROM raw.rt_reviews,
LATERAL (SELECT unnest(data::JSON[])) t(record)
LIMIT 10;
```

### Usando a interface web do DuckDB

O DuckDB traz uma interface web local para navegar por schemas/tabelas e rodar SQL visualmente, como alternativa ao prompt do CLI. Na mesma sessão do CLI `duckdb`:

```sql
CALL start_ui();
```

Isso abre `http://localhost:4213` no seu navegador. Observações:

- A primeira chamada baixa a extensão `ui` do repositório de extensões do DuckDB, então é necessário acesso à internet uma vez; depois disso ela fica em cache local e funciona offline.
- A interface se conecta ao arquivo de banco de dados com o qual você abriu o CLI (`data/warehouse.duckdb` no comando acima) — ela compartilha a mesma conexão, então qualquer query que você já tenha rodado no CLI é refletida ali.
- Use o navegador de schemas à esquerda para explorar os schemas/tabelas `raw`, `silver` e `gold`, e o painel de editor SQL para rodar queries ad-hoc com os resultados renderizados em tabela.
- Feche a interface com `CALL close_ui();`, ou simplesmente feche a sessão do CLI.

## Estrutura do projeto

```
.
├── airflow/
│   ├── Dockerfile          # Imagem do Airflow com os scrapers embutidos
│   ├── dags/
│   │   ├── rt_scraper_dag.py
│   │   ├── mc_scraper_dag.py
│   │   └── dbt_build_dag.py
│   └── sql/
│       └── init_warehouse.sql
├── cinemetrics/            # Projeto dbt para transformação de dados
├── docs/                   # Documentação e guias práticos
├── rottentomatoes_spider/  # Projeto Scrapy para o Rotten Tomatoes
├── mc_scrape/              # Pacote Python para o Metacritic
├── data/                   # Dados de runtime (ignorado pelo git)
│   └── warehouse.duckdb
└── docker-compose.yml
```

## DAGs

| DAG | Agendamento | Descrição |
|---|---|---|
| `rt_scraper` | diário | Descobre filmes em cartaz e, em seguida, coleta nota, detalhes e reviews de cada um |
| `mc_scraper` | diário | Navega pelo catálogo do Metacritic e, em seguida, coleta informações gerais e reviews de críticos/usuários |
| `dbt_build`  | diário | Roda os testes do dbt e constrói as camadas silver e gold no DuckDB |

Os dados brutos são carregados no DuckDB sob o schema `raw` com três colunas: `_loaded_at`, `_source_file` e `data` (JSON completo). As camadas Silver e Gold são criadas via dbt.
