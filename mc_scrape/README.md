# mc_scrape

Scraper do Metacritic que coleta informações gerais, reviews de críticos e reviews de usuários de filmes, gravando a saída como JSON puro consumido pelo loader da camada bronze. Suporta descoberta de slugs via busca por título ou navegação em massa por todo o catálogo (~17 mil filmes).

## Requisitos

- Python 3.10+

## Configuração

```bash
python -m venv .venv
source .venv/bin/activate   # .venv\Scripts\activate no Windows
pip install -e .
```

## Uso

### Python

O CLI tem quatro subcomandos: `movie`, `apikey`, `search` e `browse`.

---

#### `movie` — coleta um filme específico pelo slug

```bash
python -m metacritic movie <movie_slug> <action>
```

| Argumento | Descrição |
|---|---|
| `movie_slug` | Identificador do filme como aparece na URL do Metacritic (ex.: `the-godfather`) |
| `action` | Um de: `general`, `critic_reviews`, `user_reviews`, `all` |

```bash
# Busca apenas informações gerais
python -m metacritic movie the-godfather general

# Busca todos os reviews de críticos (paginado)
python -m metacritic movie the-godfather critic_reviews

# Busca todos os reviews de usuários (paginado)
python -m metacritic movie the-godfather user_reviews

# Busca tudo
python -m metacritic movie the-godfather all
```

---

#### `search` — descobre slugs por título

Busca no Metacritic filmes que correspondam a uma query e grava os resultados na saída JSON de `discovered_movies`.

```bash
python -m metacritic search "godfather"

# Limita os resultados (útil para testes)
python -m metacritic search "godfather" --max-items 3
```

---

#### `browse` — descoberta em massa de slugs em todo o catálogo

Pagina por todos os ~17 mil filmes do Metacritic com filtros opcionais. Os resultados são gravados na saída JSON de `discovered_movies`.

```bash
python -m metacritic browse [--sort-by SORT] [--year-min YEAR] [--year-max YEAR] [--genre GENRE ...]
```

| Opção | Descrição | Padrão |
|---|---|---|
| `--sort-by` | `'-metaScore'`, `'-userScore'` ou `'-releaseDate'` | `-metaScore` |
| `--year-min` | Filtra filmes lançados a partir deste ano | — |
| `--year-max` | Filtra filmes lançados até este ano | — |
| `--genre` | Filtra por gênero (repetível) | — |
| `--max-items` | Número máximo de itens a extrair (útil para testes e geração de tasks no Airflow) | — |

```bash
# Todos os filmes ordenados por Metascore
python -m metacritic browse

# Dramas recentes
python -m metacritic browse --year-min 2020 --genre Drama

# Múltiplos gêneros
python -m metacritic browse --genre Action --genre Thriller --sort-by -releaseDate

# Teste com amostra pequena (primeiros 100 filmes)
python -m metacritic browse --max-items 100
```

---

#### `apikey` — busca e imprime a chave de API do Metacritic

Resolve a chave de API do Metacritic uma única vez e a imprime em stdout (o restante do log vai para stderr). Usado internamente pela DAG `mc_scraper` para obter a chave uma vez e repassá-la a todas as tasks de coleta via `MC_API_KEY`, evitando que ~20 mil coletas de filmes acessem repetidamente a home page (o principal gatilho de bloqueio de bot).

```bash
python -m metacritic apikey
```

---

**Local de saída:**

Por padrão, os arquivos JSON são gravados em `./delta/` (controlado pela constante `FEED_URI` em `metacritic/output.py`):

```
./delta/
├── general/              (metadados completos do filme)
├── critic_reviews/       (reviews individuais de críticos)
├── user_reviews/         (reviews individuais de usuários)
└── discovered_movies/    (slugs descobertos)
```

Nota: esses são os nomes reais das subpastas em disco. O prefixo `mc_` (`mc_general`, `mc_critic_reviews`, `mc_user_reviews`) aparece apenas mais tarde, como nome das tabelas `bronze.*` no DuckDB depois que a DAG `mc_scraper` carrega esses arquivos (veja `airflow/dags/mc_scraper_dag.py`) — não é o nome do diretório de saída.

O arquivo `discovered_movies` funciona como uma "fila de descobertas" leve que rastreia:
- `slug` — o identificador do filme
- `discovered_at` — timestamp de quando foi descoberto
- `method` — como foi descoberto (`browse` ou `search`)

Para o Airflow: use a lista de slugs retornada diretamente para as tasks downstream.

Defina a variável de ambiente `FEED_URI` para gravar em outro lugar:

```bash
# Grava em um caminho local customizado
FEED_URI=/data/metacritic python -m metacritic movie the-godfather all

# Grava no S3
FEED_URI=s3://my-bucket/metacritic python -m metacritic browse
```

## Lendo a saída com DuckDB

```sql
-- Informações gerais
SELECT * FROM read_json_auto('./delta/general/*.json');

-- Reviews de críticos
SELECT * FROM read_json_auto('./delta/critic_reviews/*.json');

-- Reviews de usuários
SELECT * FROM read_json_auto('./delta/user_reviews/*.json');

-- Filmes descobertos (fila de descoberta de slugs)
SELECT * FROM read_json_auto('./delta/discovered_movies/*.json');

-- Exemplo: encontrar todos os filmes descobertos via busca por "godfather"
SELECT slug, discovered_at 
FROM read_json_auto('./delta/discovered_movies/*.json')
WHERE method = 'search';
```

A partir do S3 (a saída é JSON simples, não Delta Lake — use `read_json_auto`, não `delta_scan`):

```sql
SELECT * FROM read_json_auto('s3://my-bucket/metacritic/general/*.json');
```

## Encontrando slugs de filmes

O slug é o último segmento da URL do filme no Metacritic:

```
https://www.metacritic.com/movie/the-godfather/
                                  ^^^^^^^^^^^^^
                                  slug: the-godfather
```

Você também pode descobrir slugs programaticamente:

```bash
# Busca por título
python -m metacritic search "the godfather"

# Navega por todo o catálogo (grava slugs em ./delta/discovered_movies)
python -m metacritic browse
```
