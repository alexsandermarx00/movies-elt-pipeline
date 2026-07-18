# Rotten Tomatoes Spider

Um spider Scrapy para extrair dados abrangentes do Rotten Tomatoes.

## Instalação

Certifique-se de ter instalado as dependências necessárias a partir do arquivo `requirements.txt` antes de rodar o spider.

```bash
pip install -r requirements.txt
```

## Uso

Este projeto contém um spider principal chamado `rtspider`. Você pode passar parâmetros dinamicamente pela linha de comando para indicar qual filme está sendo coletado e qual tipo de dado deseja extrair.

### Sintaxe geral

```bash
scrapy crawl rtspider -a movie=<movie_name_slug> -a action=<extraction_mode> [options]
```

- `movie`: O slug da URL do filme no Rotten Tomatoes. (ex.: `godzilla_x_kong_the_new_empire`, `dune_part_two`)
- `action`: O modo de extração a ser executado (`score`, `reviews` ou `details`).
- `max_pages`: *(Opcional)* Define o número máximo de páginas paginadas a coletar ao usar a action `reviews` (padrão: `2`).
- `-o`: *(Opcional)* Override manual de saída local. Nota: a execução padrão despacha automaticamente a saída para o diretório `.output/`, ou para uma instância de objeto S3 se a variável de ambiente `FEED_URI` estiver definida.

---

## Modos de extração (`action`)

O spider suporta quatro modos distintos de extração de dados.

### 1. `score`
Extrai informações de nota geral e sinopse.
**Dados extraídos:** ID do filme, nota geral/verificada do público, nota geral/dos principais críticos, e descrição. 

**Exemplo de execução:**
```bash
scrapy crawl rtspider -a movie=dune_part_two -a action=score
```

### 2. `reviews`
Extrai e pagina pelos reviews de usuários do filme especificado.
**Dados extraídos:** ID do filme, nota do review, citação, ID do review, status de verificação, flags de palavrão/spoiler, detalhes do usuário e data de criação.

**Exemplo de execução:**
```bash
scrapy crawl rtspider -a movie=dune_part_two -a action=reviews -a max_pages=5
```

### 3. `details`
Extrai detalhes técnicos a partir da integração de metadados da página.
**Dados extraídos:** ID do filme, título, classificação indicativa (ex.: PG-13), data de lançamento e IDs internos (`rtid`, `urlid`).

**Exemplo de execução:**
```bash
scrapy crawl rtspider -a movie=dune_part_two -a action=details
```

### 4. `critic_reviews`
Extrai e pagina pelos reviews de críticos do filme especificado.
**Dados extraídos:** ID do filme, ID do review, nome do crítico, veículo, nota, citação, data do review.

**Exemplo de execução:**
```bash
scrapy crawl rtspider -a movie=dune_part_two -a action=critic_reviews -a max_pages=5
```

---

## Descoberta via crosswalk do Wikidata

Anteriormente, este projeto incluía o `rt_discovery_spider.py` para descoberta dinâmica de filmes. Isso foi substituído por um mapeamento crosswalk do Wikidata (ID do IMDB → slug de URL do RT), conectando registros direta e deterministicamente ao nosso pipeline sem exigir coleta exploratória.

---

## Orquestração

O scraper é executado via Apache Airflow. O Dockerfile de execução está localizado no diretório raiz `airflow/`. O Airflow executa os scrapers como subprocessos (usando BashOperator), gravando a saída como arquivos JSON que são então carregados no DuckDB.
