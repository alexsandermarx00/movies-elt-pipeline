# 1 Introdução

A célebre expressão "dados são o novo petróleo", cunhada pelo matemático britânico
Clive Humby em 2006, e o influente artigo "The world's most valuable resource is no
longer oil, but data", publicado pela revista The Economist (2017), prenunciavam uma
nova era da transformação digital, na qual os dados se consolidariam como ativos
estratégicos de primeira ordem para as organizações.

Nesse cenário, os processos de tratamento e disponibilização de dados também
passaram por uma evolução significativa. Impulsionada pela ascensão e pela
escalabilidade dos Data Warehouses em nuvem, a arquitetura de dados presenciou
uma mudança de paradigma fundamental: a transição do modelo tradicional **ETL**
(Extract, Transform, Load) para o moderno **ELT** (Extract, Load, Transform)
(Fundamentals of Data Engineering). A capacidade de armazenamento e
processamento virtualmente ilimitada, oferecida por plataformas como Snowflake e
Google BigQuery, viabilizou o carregamento de dados em seu estado bruto diretamente
no ambiente de destino. Essa abordagem permitiu que as transformações complexas
fossem executadas posteriormente, conferindo maior flexibilidade e governança ao
processo analítico.

Contudo, embora a abordagem ELT tenha solucionado desafios históricos de
escalabilidade, ela introduziu novas complexidades. A transferência da etapa de
transformação para o ambiente analítico impulsionou o surgimento de novas
especialidades, notadamente a do **Engenheiro de Analytics** (Analytics Engineer),
responsável por garantir a qualidade e a lógica de negócio no "T" do ELT (What is
analytics engineering? | dbt Labs). Sem um modelo procedural claro, as equipes de
dados correm o risco de desenvolver sistemas inconsistentes, de difícil manutenção e
com baixa confiabilidade, comprometendo o valor estratégico que buscam
potencializar. Diante deste cenário, emerge o problema de pesquisa que norteia este
trabalho: como estruturar um modelo procedural para padronizar e otimizar a
construção de pipelines de ELT, garantindo qualidade, eficiência e reprodutibilidade?

A relevância deste estudo é, portanto, dupla. Do ponto de vista prático, alinha-se à
crescente demanda do mercado por profissionais capazes de construir ecossistemas
de dados modernos e robustos. Do ponto de vista acadêmico, busca preencher uma
lacuna observada na literatura sobre a formalização de metodologias para o
desenvolvimento de pipelines de dados no contexto do Modern Data Stack.

Nesse contexto, o objetivo geral deste trabalho é propor, documentar e validar um
modelo procedural para a construção de pipelines de ELT. Para alcançá-lo, os
seguintes objetivos específicos foram definidos: (1) realizar uma revisão aprofundada
da literatura sobre os conceitos do Modern Data Stack e do paradigma ELT; (2) detalhar
a proposta de um modelo procedural em etapas bem definidas; (3) aplicar e validar o
modelo proposto através de um estudo de caso prático no domínio cinematográfico; e
(4) analisar os resultados obtidos com a aplicação do modelo.

Este trabalho está estruturado da seguinte forma: o Capítulo 2 apresenta a
fundamentação teórica que suporta o estudo. O Capítulo 3 detalha a proposta do
modelo procedural. O Capítulo 4 descreve a aplicação prática e a validação do modelo
por meio do estudo de caso. O Capítulo 5 discute os resultados e, por fim, o Capítulo 6
apresenta a conclusão, as contribuições e as sugestões para trabalhos futuros.

---

# 2 Revisão bibliográfica

## 2.1 Data Warehouse

Para compreender a arquitetura de dados moderna, é essencial primeiro entender a
distinção fundamental entre os sistemas que suportam as operações diárias de uma
empresa e aqueles projetados para análise estratégica.

Os sistemas que registram as operações diárias — como vendas, transações bancárias
ou registros de estoque — são conhecidos como Sistemas de Processamento de
Transações Online (**OLTP** - Online Transaction Processing). Seus bancos de dados são
altamente normalizados, otimizados para operações de escrita, alteração e exclusão
(operações **CRUD** - Create, Read, Update, Delete) de forma rápida e consistente,
garantindo a integridade transacional.

Consultas analíticas, que frequentemente exigem a agregação de milhões de registros
e a junção de inúmeras tabelas, tornavam os sistemas OLTP lentos e podiam degradar
a performance das operações críticas do negócio (The datawarehouse toolkit). Além
disso, os dados corporativos costumam residir em "silos": sistemas isolados (ERP,
CRM, planilhas) com formatos e semânticas distintas, tornando uma visão unificada da
empresa uma tarefa difícil (Data Warehousing Fundamentals for IT Professionals,
capítulo 1).

É neste contexto de necessidade por uma visão integrada e otimizada para análise que
surge o conceito de **Data Warehouse (DW)**, definido por Inmon (2005) como um
repositório de dados orientado por assunto, integrado, variável no tempo e não volátil,
projetado especificamente para apoiar a tomada de decisões estratégicas.

### 2.1.1 As Abordagens de Inmon e Kimball

Dois pioneiros apresentaram visões distintas sobre como um Data Warehouse deveria
ser arquitetado: Bill Inmon, frequentemente chamado de "o pai do Data Warehouse", e
Ralph Kimball, um proeminente proponente da modelagem dimensional.

A abordagem de Inmon, conhecida como **Top-Down**, defende a criação de um Data
Warehouse corporativo centralizado e normalizado (geralmente na Terceira Forma
Normal - 3NF) como o primeiro passo. Este repositório, chamado de Corporate
Information Factory (CIF), atua como a "única fonte da verdade" para toda a
organização. A partir deste hub central, são criados Data Marts departamentais, que
contêm dados agregados ou específicos para as necessidades de cada área (Vendas,
Finanças, etc.). Nas palavras de Inmon (2005), um DW é uma coleção de dados
"orientada por assunto, integrada, variável no tempo e não volátil, que tem por objetivo
dar suporte às decisões da gerência". A principal vantagem desta abordagem é o alto
nível de integridade e consistência dos dados em escala corporativa (Building the Data
Warehouse).

Em contrapartida, a abordagem de Ralph Kimball, conhecida como **Bottom-Up**, foca em
entregar valor de negócio de forma mais rápida e interativa. Em vez de construir
primeiro um repositório central massivo, Kimball propõe a construção de Data Marts
individuais, orientados a processos de negócio (ex: um Data Mart para o processo de
"pedidos", outro para "entregas"). Cada Data Mart é construído desde o início usando a
modelagem dimensional, cuja estrutura mais comum é o **modelo estrela** (star schema).
Este modelo organiza os dados em (The datawarehouse toolkit, página 16):

- **Tabelas Fato:** Contêm as métricas e os eventos de negócio que se deseja analisar
  (ex: valor da venda, quantidade de itens). São tabelas "estreitas" e "longas".

- **Tabelas de Dimensão:** Contêm o contexto descritivo dos fatos (ex: dim_cliente,
  dim_produto, dim_tempo). São tabelas "largas" e "curtas" que permitem "fatiar e
  picar" (slice and dice) os dados dos fatos.

O Data Warehouse corporativo, na visão de Kimball, emerge como a união desses
Data Marts, que são integrados por meio de **dimensões conformadas** (dimensões
compartilhadas, como dim_cliente, que mantêm a consistência entre os diferentes Data
Marts). Kimball define o DW de forma mais pragmática: "um sistema que extrai, limpa,
conforma e entrega dados de origem para um repositório dimensional e, em seguida,
apoia a consulta e a análise para a tomada de decisão".

### 2.1.2 Justificativa da Abordagem Adotada

Embora ambas as abordagens tenham méritos e sejam aplicáveis em diferentes
cenários, este trabalho adota a filosofia de Ralph Kimball como base metodológica. A
escolha justifica-se pela sua afinidade direta com o paradigma ELT e as ferramentas do
Modern Data Stack.

No modelo ELT, os dados brutos são carregados no Data Warehouse e a
transformação ocorre subsequentemente, já dentro do ambiente analítico. A
modelagem dimensional de Kimball oferece um roteiro claro e um alvo prático para esta
etapa de transformação. Ferramentas modernas como o **dbt** são projetadas
especificamente para transformar dados brutos em modelos dimensionais (esquemas
estrela ou floco de neve) de forma eficiente e modular (dbt Labs).

Portanto, ao propor um modelo procedural para ELT, a abordagem de Kimball fornece
uma estrutura comprovada e orientada ao negócio para a etapa mais crítica e
complexa do processo: a transformação de dados brutos em informação.

Criada a necessidade de um repositório de dados dedicado à análise, o DW, para
oferecer suporte à inteligência de negócios (BI), surge uma questão importante: como
os dados de diversas fontes são movidos e integrados para popular este repositório
centralizado? Para tal, dois paradigmas de integração tomam a frente, os conhecidos
ETL e ELT. Apesar de este trabalho ser estruturado ao redor do ELT, uma distinção com
o ETL se faz necessária e é apresentada na próxima seção.

---

## 2.2 ETL e ELT

### 2.2.1 ETL (Extract, Transform, Load)

![Figura 1 — Comparação entre as abordagens de Inmon (Top-Down) e Kimball (Bottom-Up)](fluxo_etl.png)

O paradigma ETL (Extract, Transform, Load) representou por décadas o padrão ouro
para a integração de dados em Data Warehouses. Trata-se de um processo linear e
bem definido, cuja lógica se baseia em preparar os dados antes de sua chegada ao
repositório analítico. As etapas são:

- **Extração (Extract):** Nesta primeira fase, os dados são extraídos de suas diversas
  fontes de origem, que podem incluir bancos de dados transacionais (OLTP),
  sistemas de CRM e ERP, arquivos de log, planilhas ou APIs de serviços externos.

- **Transformação (Transform):** Esta é a etapa central e mais complexa do processo
  ETL. Os dados extraídos são movidos para uma área de preparação intermediária
  (staging area), localizada em um servidor dedicado, distinto do Data Warehouse.
  Neste ambiente, uma série de regras de negócio é aplicada: os dados são limpos
  (tratamento de nulos e inconsistências), validados, padronizados, enriquecidos com
  informações de outras fontes e, finalmente, remodelados para se adequarem ao
  esquema do Data Warehouse de destino (por exemplo, um modelo estrela).

- **Carga (Load):** Após a transformação, os dados, agora estruturados, limpos e em
  seu formato final, são carregados (loaded) no Data Warehouse. A partir deste ponto,
  estão prontos para serem consumidos por ferramentas de Business Intelligence (BI)
  e por analistas de dados.

A principal característica do ETL é o paradigma **Schema-on-Write**: o esquema dos
dados é rigorosamente definido e aplicado durante a transformação, garantindo que
apenas dados que atendam a esse formato sejam carregados no DW.

### 2.2.2 ELT (Extract, Load, Transform)

![Figura 2 — Fluxo comparativo entre os paradigmas ETL e ELT](fluxo_elt.png)

O surgimento dos Cloud Data Warehouses (como Snowflake, Google BigQuery e
Amazon Redshift), com sua capacidade de armazenamento de baixo custo e
processamento massivamente paralelo, foi o catalisador para uma inversão no
processo tradicional, dando origem ao paradigma ELT (Extract, Load, Transform).

- **Extração (Extract):** Similar ao ETL, os dados são extraídos de suas fontes. No
  entanto, a extração pode ser menos seletiva, capturando dados em seu formato
  bruto ou semiestruturado (como JSON).

- **Carga (Load):** Aqui reside a mudança fundamental. Em vez de passarem por um
  servidor intermediário, os dados brutos são carregados imediatamente no Data
  Warehouse de destino. Isso acelera drasticamente o tempo de ingestão e permite o
  armazenamento de um registro histórico fiel e inalterado dos dados de origem.

- **Transformação (Transform):** A etapa de transformação ocorre após o carregamento,
  utilizando o próprio motor de processamento do Data Warehouse. Através de
  linguagens como SQL, os dados brutos são modelados em estágios: de brutos para
  limpos, e de limpos para modelos analíticos prontos para o consumo, como tabelas
  fato e dimensão.

O ELT opera sob o princípio **Schema-on-Read**. Diferentemente do ETL, onde um
esquema analítico rígido é imposto antes da carga, no ELT a aplicação da estrutura
detalhada dos dados é adiada para o momento da leitura ou da transformação, já
dentro do Data Warehouse. Isso é viabilizado pelo carregamento de dados brutos em
áreas de preparação (staging areas) que utilizam tipos de dados flexíveis, como o
SUPER no Redshift ou o VARIANT no Snowflake. Embora o Data Warehouse em si,
por sua natureza, exija um esquema para a criação da tabela de staging (uma
característica Schema-on-Write), o esquema complexo e aninhado do dado de origem
não é imposto na carga, mas sim interpretado e modelado na etapa de transformação
(Read). Essa abordagem confere enorme flexibilidade, pois os mesmos dados brutos
podem ser remodelados de diferentes maneiras para atender a novas perguntas de
negócio, sem a necessidade de reprocessar todo o fluxo de extração.

### 2.2.3 O Surgimento do Engenheiro de Analytics

No mundo ETL, o Engenheiro de Dados era responsável por todo o pipeline,
entregando um conjunto de dados polido e pronto para uso. Com o ELT, a etapa de
transformação ("T") foi deslocada para dentro do Data Warehouse e passou a ser
realizada majoritariamente com SQL. Isso criou um vácuo:

- **Analistas de Dados**, embora proficientes em SQL e com vasto conhecimento de
  negócio, frequentemente não possuíam as melhores práticas de engenharia de
  software (versionamento com Git, testes, documentação, CI/CD).

- **Engenheiros de Dados**, especialistas em infraestrutura e movimentação de dados,
  nem sempre possuíam o contexto de negócio detalhado para construir as lógicas de
  transformação.

O **Engenheiro de Analytics** (Analytics Engineer) surge para preencher essa lacuna.
Conforme popularizado pela dbt Labs (What is analytics engineering? | dbt Labs), este
profissional atua na interseção entre engenharia e análise. Ele aplica os princípios de
engenharia de software ao código de transformação (SQL), construindo modelos de
dados robustos, testados, documentados e confiáveis diretamente no Data Warehouse.
Em suma, o Engenheiro de Analytics é o dono da etapa de transformação no
paradigma ELT, garantindo que a flexibilidade do modelo não se transforme em caos.

### 2.2.4 Quadro Comparativo: ETL vs. ELT

A análise comparativa entre os dois paradigmas pode ser estruturada em quatro
dimensões centrais:

**Local da Transformação:** No ETL, a etapa de transformação ocorre em um servidor
intermediário dedicado, externo ao Data Warehouse de destino. No ELT, a
transformação é deslocada para dentro do próprio ambiente analítico, aproveitando o
poder de processamento do Cloud Data Warehouse.

**Paradigma de Esquema:** O ETL adota o princípio Schema-on-Write — os dados são
estruturados no formato final antes de serem carregados. O ELT opera sob
Schema-on-Read — os dados brutos são carregados imediatamente e a estrutura
analítica é aplicada posteriormente, na etapa de transformação.

**Latência de Ingestão:** O ELT apresenta menor latência de ingestão, pois os dados são
carregados no Data Warehouse sem processamento intermediário. No ETL, a etapa de
transformação na staging area adiciona tempo ao ciclo de atualização dos dados.

**Flexibilidade de Reprocessamento:** O ELT preserva o histórico bruto dos dados no
Data Warehouse, permitindo que novas lógicas de transformação sejam aplicadas sobre
os mesmos dados sem necessidade de nova extração. No ETL tradicional, os dados
brutos frequentemente não são retidos após a carga, limitando a capacidade de
reprocessamento.

---

## 2.3 O Modern Data Stack

O paradigma ELT é o princípio motor de um ecossistema de ferramentas e tecnologias
conhecido como **Modern Data Stack (MDS)**. Diferentemente das soluções de dados
monolíticas do passado, onde um único fornecedor oferecia uma plataforma integrada
(e muitas vezes inflexível) para todas as tarefas, o MDS representa uma abordagem
modular e desagregada.

A filosofia do MDS é construir um pipeline de dados utilizando um conjunto de
ferramentas especializadas, independentes e interoperáveis, geralmente baseadas em
nuvem, onde cada uma é a "melhor da categoria" (best-of-breed) para uma função
específica. Como afirmam Reis e Housley (2022), esta abordagem modular não é uma
tendência passageira, mas estabeleceu-se como o novo padrão de fato para
arquiteturas de dados, graças à sua flexibilidade, escalabilidade e agilidade.

Um pipeline de dados construído sobre o MDS pode ser decomposto nas seguintes
camadas ou componentes principais:

![Figura 3 — Camadas do Modern Data Stack](camadas-mds.png)

### 2.3.1 Ingestão e Carregamento (E e L)

Esta camada é composta por ferramentas projetadas para automatizar a extração de
dados de centenas de fontes distintas (APIs, bancos de dados, plataformas de
marketing, etc.) e carregá-los de forma eficiente no Data Warehouse. Elas operam com
base em conectores pré-construídos, eliminando a necessidade de desenvolver e
manter scripts de extração complexos.

**Ferramentas:** Fivetran, Stitch, Airbyte (open-source), Matillion.

**Adotado neste trabalho:** Scrapy — framework Python de web scraping utilizado para extração de dados das fontes Rotten Tomatoes e Metacritic. Por não haver APIs públicas estáveis disponíveis, a extração é realizada diretamente sobre as páginas e endpoints internos dos sites.

### 2.3.2 Armazenamento e Processamento (O Cloud Data Warehouse)

O coração do MDS. Como discutido anteriormente, são os Cloud Data Warehouses
que, com sua arquitetura que separa armazenamento e computação, tornam o ELT
viável. Eles servem como repositório central para dados brutos e, ao mesmo tempo,
como o motor de processamento para a etapa de transformação.

**Ferramentas:** Snowflake, Google BigQuery, Amazon Redshift, Databricks (Lakehouse).

**Adotado neste trabalho:** Delta Lake + DuckDB — implementação local da arquitetura Lakehouse. O Delta Lake (via biblioteca `delta-rs`) provê a camada transacional sobre arquivos Parquet, enquanto o DuckDB atua como engine analítica, lendo tabelas Delta nativamente via extensão. Essa combinação é funcionalmente análoga à plataforma Databricks, com custo zero e reproduzível em qualquer máquina.

### 2.3.3 Transformação (O "T" do ELT)

Após os dados brutos serem carregados no DW, as ferramentas desta camada entram
em ação para limpá-los, modelá-los e prepará-los para análise. É aqui que o
Engenheiro de Analytics aplica a lógica de negócio. A ferramenta **dbt** (data build tool)
tornou-se o padrão incontestável nesta camada, permitindo que as transformações
sejam escritas em SQL e gerenciadas com as melhores práticas de engenharia de
software, como controle de versão (Git), testes automatizados e documentação.

**Ferramenta principal:** dbt (Core e Cloud).

**Adotado neste trabalho:** dbt Core com adapter `dbt-duckdb`, responsável pelas transformações nas camadas bronze, silver e gold sobre o ambiente Delta Lake + DuckDB.

### 2.3.4 Orquestração

Um pipeline de dados consiste em uma série de tarefas que precisam ser executadas
em uma ordem específica e com tratamento de dependências. Os orquestradores são
responsáveis por agendar, executar e monitorar esses fluxos de trabalho (também
conhecidos como **DAGs** - Directed Acyclic Graphs). Eles garantem que a
transformação só comece após a conclusão da carga, por exemplo.

**Ferramentas:** Apache Airflow, Mage (open-source), Dagster, Prefect.

**Adotado neste trabalho:** Apache Airflow com Docker Compose (LocalExecutor) — os spiders rodam como subprocessos dentro do próprio container do Airflow, eliminando a necessidade de Kubernetes. A inicialização do ambiente se reduz a `docker compose up`.

### 2.3.5 Análise e Visualização (BI e Analytics)

A camada final, onde o valor dos dados é consumido pelos usuários de negócio.
Ferramentas modernas de Business Intelligence se conectam diretamente ao Data
Warehouse para permitir a exploração dos dados modelados, a criação de dashboards
e a geração de relatórios.

**Ferramentas:** Looker, Metabase (open-source), Tableau, Microsoft Power BI.

A força do Modern Data Stack reside na sua sinergia: uma empresa pode, por exemplo,
combinar Fivetran para ingestão, Snowflake como Data Warehouse, dbt para
transformação e Metabase para visualização, criando um pipeline poderoso e coeso
sem ficar refém de um único fornecedor, e com a agilidade necessária para responder
rapidamente às novas demandas do negócio. A proposta procedural deste TCC se
encaixa precisamente na organização das etapas de trabalho dentro deste
ecossistema, utilizando um stack equivalente voltado para execução local: Scrapy para
extração, Delta Lake + DuckDB como Lakehouse local, dbt para transformação e
Apache Airflow com Docker Compose para orquestração.

### 2.3.6 O Data Lakehouse

A ascensão do Modern Data Stack, com o Cloud Data Warehouse em seu cerne,
resolveu muitos dos desafios da análise de dados em escala. Contudo, essa
arquitetura frequentemente resultava em um ecossistema dual: o Data Warehouse era
utilizado para análises de BI e SQL com dados estruturados, enquanto um Data Lake
separado era mantido para armazenar dados brutos, semiestruturados e não
estruturados, servindo a casos de uso de data science e machine learning. Essa
dualidade gera redundância de dados, custos de armazenamento duplicados e a
necessidade de complexos pipelines de ETL apenas para mover e sincronizar dados
entre os dois sistemas.

Para solucionar essa fragmentação, surge o conceito de **Data Lakehouse**. Proposta
originalmente por um grupo de pesquisadores e engenheiros da Databricks, a
arquitetura Lakehouse visa unificar as capacidades de Data Lakes e Data Warehouses
em uma única plataforma. O objetivo é criar um sistema que possa:

1. Armazenar grandes volumes de dados de qualquer tipo (estruturados ou não) em
   formatos de arquivo abertos (como Apache Parquet) sobre uma camada de
   armazenamento de objetos de baixo custo (como Amazon S3 ou Google Cloud
   Storage).

2. Implementar uma camada de metadados e gerenciamento de transações
   diretamente sobre os arquivos no Data Lake, trazendo funcionalidades antes
   exclusivas dos Data Warehouses, como transações ACID, versionamento de
   dados (time travel) e governança de esquema.

Essa camada transacional é viabilizada por formatos de tabela abertos como o **Delta
Lake** (criado pela Databricks), o **Apache Iceberg** (criado pelo Netflix) e o **Apache Hudi**
(criado pelo Uber). Essas tecnologias transformam um simples repositório de arquivos
em um sistema de armazenamento confiável e performático.

Dessa forma, o Lakehouse permite que uma única cópia dos dados seja utilizada para
múltiplas cargas de trabalho: analistas de BI podem executar consultas SQL de alta
performance, enquanto cientistas de dados podem utilizar bibliotecas como Spark ou
Pandas para treinar modelos de machine learning sobre os mesmos dados, eliminando
silos e simplificando drasticamente a arquitetura de dados corporativa. Para o
paradigma ELT, isso significa que a carga (L) e a transformação (T) podem ocorrer em
um ambiente unificado, flexível e mais econômico.

---

## 2.4 Governança e Qualidade de Dados

A transição para o paradigma ELT e a flexibilidade do Modern Data Stack, ao mesmo
tempo que democratizam o acesso e a manipulação dos dados, introduzem um desafio
crítico: o risco de transformar um Data Warehouse em um **"data swamp"** (pântano de
dados) — um repositório de dados de baixa qualidade, sem documentação e,
consequentemente, sem confiabilidade (Data Lake vs Data Swamp: Differences &
Cautionary Steps). A liberdade conferida pelo Schema-on-Read exige uma contrapartida
de disciplina e controle. É neste contexto que as práticas de Governança e Qualidade
de Dados se tornam não apenas relevantes, mas fundamentais para o sucesso de
qualquer projeto de dados.

### 2.4.1 Governança de Dados no Modern Data Stack

Governança de Dados é o conjunto de processos, políticas, padrões e métricas que
garantem o gerenciamento eficaz e seguro dos ativos de dados de uma organização.
Em um ecossistema modular como o MDS, a governança não é uma ferramenta única,
mas uma disciplina implementada através de várias práticas integradas ao longo do
pipeline. As mais relevantes para um modelo procedural ELT são:

- **Catalogação de Dados (Data Catalog):** Um catálogo de dados funciona como
  um inventário centralizado de todos os ativos de dados (Data Quality Fundamentals).
  Ele responde a perguntas fundamentais como: "Quais dados possuímos?", "Onde eles
  estão localizados?", "O que cada coluna significa?" e "Quem é o responsável por
  eles?". Ferramentas de catalogação se integram ao Data Warehouse e documentam
  metadados técnicos (tipos de dados, schemas) e de negócio (descrições, regras de
  cálculo), tornando os dados mais detectáveis e compreensíveis para toda a
  organização.

- **Linhagem de Dados (Data Lineage):** A linhagem de dados oferece uma trilha de
  auditoria visual de todo o ciclo de vida dos dados. Ela mostra a origem de cada
  campo, desde a fonte bruta, passando por todas as etapas de transformação, até
  sua apresentação em um dashboard final (What Is Data Lineage? | IBM). No contexto
  do ELT, onde transformações complexas ocorrem em múltiplos estágios dentro do
  Data Warehouse, a linhagem é crucial para depurar erros, entender o impacto de
  mudanças e, acima de tudo, construir confiança nos dados apresentados. Ferramentas
  como o dbt geram automaticamente gráficos de linhagem a partir das dependências
  entre os modelos de dados.

- **Gestão de Acesso e Propriedade (Access Control & Stewardship):** Com os dados
  centralizados no Data Warehouse, é vital definir políticas claras sobre quem pode
  visualizar, alterar ou criar modelos de dados. A governança estabelece controles de
  acesso baseados em funções (role-based access control), garantindo que dados
  sensíveis sejam protegidos (Fundamentals of Data Access Management - DATAVERSITY).
  Além disso, promove o conceito de **Data Stewardship**, designando "proprietários" ou
  "guardiões" para conjuntos de dados específicos, que se tornam responsáveis por sua
  qualidade, documentação e conformidade.

### 2.4.2 As Dimensões da Qualidade de Dados

Qualidade de dados não é um conceito subjetivo; ela pode ser medida e gerenciada
através de um conjunto de dimensões bem estabelecidas na literatura (Data Quality
Fundamentals). Um pipeline de dados confiável deve ser projetado para garantir que os
dados entregues atendam a esses critérios:

- **Acurácia:** O grau em que os dados representam corretamente o objeto ou evento
  do mundo real que descrevem.

- **Completude:** A proporção de dados armazenados em relação ao potencial de
  estarem 100% completos. Refere-se à ausência de valores nulos ou faltantes.

- **Consistência:** A ausência de contradições nos dados. Por exemplo, um cliente não
  pode ter uma data de cancelamento de serviço anterior à data de assinatura.

- **Validade:** O grau em que os dados estão em conformidade com o formato, tipo ou
  intervalo definido por suas regras de negócio (ex: um campo de CEP deve conter
  apenas números e ter um formato específico).

- **Unicidade:** Garante que não haja duplicidade de registros que deveriam ser únicos
  (ex: um mesmo cliente não deve aparecer duas vezes na tabela de clientes).

- **Pontualidade:** O grau em que os dados estão disponíveis no momento em que são
  necessários. Em um pipeline de dados, isso se traduz em "freshness", ou seja, quão
  recentes são os dados.

### 2.4.3 Testes de Dados como Ferramenta Prática

Se a Qualidade de Dados define "o que" é um dado confiável, os testes de dados são
"como" essa confiabilidade é garantida na prática. No paradigma ELT, o Engenheiro de
Analytics é o principal responsável por implementar testes diretamente na camada de
transformação. Ferramentas como o dbt permitem a prática de tratar os testes durante
o desenvolvimento de pipelines, permitindo a automação de verificações essenciais
(Add data tests to your DAG | dbt Developer Hub):

- **Testes Genéricos:** São testes pré-construídos que podem ser aplicados a qualquer
  coluna, como `not_null` (garante completude), `unique` (garante unicidade),
  `accepted_values` (garante validade) e `relationships` (garante consistência
  referencial entre tabelas, por exemplo, que todo id_cliente na tabela de fatos exista
  na tabela de dimensão de clientes).

- **Testes Customizados:** São testes escritos em SQL para validar regras de negócio
  complexas e específicas que não são cobertas pelos testes genéricos.

- **Testes de Frescor e Volume:** São testes operacionais que monitoram a saúde do
  pipeline. O teste de "freshness" verifica se uma fonte de dados foi atualizada dentro
  do esperado, enquanto testes de volume podem alertar para anomalias, como uma
  queda brusca no número de registros carregados, o que pode indicar uma falha no
  processo de extração.

Em conclusão, a implementação de um modelo procedural para ELT só é completa
quando incorpora os princípios de Governança e Qualidade em seu núcleo. A
governança fornece o mapa e as regras de trânsito, a qualidade define o que é um
"veículo" seguro, e os testes são a inspeção contínua que garante que apenas veículos
seguros trafeguem pelo pipeline.

---

## 2.5 Análise de Fontes de Dados Comuns em Cenários de ELT

A partir da definição do problema e dos KPIs, a análise exploratória das fontes de
dados disponíveis busca responder três perguntas fundamentais: quantas são as
fontes? Quais seus tipos de dados? Quais as suas limitações?

A primeira etapa de qualquer pipeline de dados, a Extração (E), é inteiramente ditada
pelas características da fonte de origem. A natureza, estrutura e limitações dos dados
no ponto de origem definem a complexidade, a frequência e a robustez necessárias
para os processos de extração e carregamento (L) no ambiente de destino.
Compreender esses cenários é, portanto, crucial para o desenho de um modelo
procedural eficaz.

### 2.5.1 Fontes via API (Application Programming Interface)

APIs são interfaces que permitem que sistemas de software se comuniquem e troquem
dados de forma padronizada. APIs REST (comumente usando JSON) e GraphQL são
as mais prevalentes para a extração de dados de serviços de terceiros (SaaS), redes
sociais ou microsserviços internos.

**Tipos de Dados:** Predominantemente semi-estruturados (JSON, XML).

**Estrutura Comum:** A estrutura é definida pelo provedor da API. Geralmente é bem
documentada, mas pode sofrer alterações (versionamento de API).

**Métodos de Extração:** Requisições HTTP (ex: GET, POST) a endpoints específicos. A
extração geralmente envolve lidar com mecanismos de autenticação (tokens, chaves
de API) e paginação para buscar grandes volumes de dados.

**Limitações:**

- **Rate Limiting:** A maioria das APIs impõe limites no número de requisições que
  podem ser feitas em um intervalo de tempo, exigindo um controle cuidadoso no
  processo de extração para evitar bloqueios.

- **Dependência de Terceiros:** O pipeline é vulnerável a mudanças na API (campos
  obsoletos, alterações na estrutura), instabilidade ou descontinuação do serviço.

- **Complexidade de Paginação:** Extrair todos os dados pode exigir uma lógica
  complexa para navegar por múltiplas "páginas" de resultados.

A estratégia de extração deve ser resiliente, contemplando pausas para respeitar o rate
limiting e uma lógica robusta de paginação. No carregamento, é uma boa prática
carregar o JSON bruto em uma coluna do tipo VARIANT ou JSON no Data Warehouse,
deixando a análise e a quebra da estrutura para a etapa de Transformação.

### 2.5.2 Bancos de Dados (Relacionais e NoSQL)

Fontes de dados operacionais que sustentam aplicações de negócio. Podem ser
bancos de dados relacionais (SQL) como PostgreSQL, MySQL e SQL Server, ou
NoSQL como MongoDB e DynamoDB.

**Tipos de Dados:** Estruturados em bancos relacionais (tabelas com esquema definido);
semi-estruturados em bancos NoSQL (documentos JSON/BSON).

**Métodos de Extração:**

- **Query Direta:** Execução de consultas SQL para extrair dados.
- **Change Data Capture (CDC):** Abordagem moderna que captura alterações
  (inserções, atualizações, exclusões) em tempo real a partir dos logs de transação do
  banco, sem sobrecarregar a base de produção.

**Limitações:**

- **Impacto na Produção:** Consultas pesadas e frequentes podem degradar a
  performance do sistema transacional que atende aos usuários finais.

- **Acesso e Segurança:** Requer credenciais de acesso direto ao banco, o que pode
  apresentar riscos de segurança e desafios de conectividade de rede.

A utilização de CDC é a abordagem preferencial para a extração, pois é eficiente e de
baixo impacto. A carga geralmente envolve a replicação dos dados para o Data
Warehouse de forma incremental, mantendo um espelho das tabelas de origem. As
transformações ocorrem depois, unindo dados de diferentes fontes e aplicando regras
de negócio.

### 2.5.3 Websites (Web Scraping)

Extração de informações diretamente do conteúdo HTML de páginas da web, quando
não há uma API disponível.

**Tipos de Dados:** Não-estruturados ou semi-estruturados (HTML, texto livre).

**Métodos de Extração:** Uso de bibliotecas de programação (ex: BeautifulSoup, Scrapy
em Python) para analisar o código HTML e extrair os dados desejados.

**Limitações:**

- **Fragilidade Extrema:** O processo de extração é altamente acoplado à estrutura
  visual do site. Qualquer alteração no layout ou no HTML do site pode quebrar o
  scraper.

- **Questões Legais e Bloqueios:** Muitos sites proíbem a prática em seus termos de
  serviço e implementam tecnologias anti-scraping (ex: CAPTCHAs) para bloquear o
  acesso automatizado.

Esta é frequentemente a fonte mais instável e de maior manutenção. A etapa de
extração deve ser projetada para ser robusta a falhas e, idealmente, o dado extraído
deve ser carregado em seu formato mais bruto possível (JSON ou até mesmo o HTML
completo) para um Data Lake, permitindo reprocessamento futuro sem a necessidade
de acessar o site novamente. A etapa de Transformação será invariavelmente
complexa, envolvendo muita limpeza e parseamento.

### 2.5.4 Fontes Manuais e Arquivos Estruturados (CSV, Excel)

Dados fornecidos por usuários ou exportados de outros sistemas em formatos de
arquivo, como CSV, TSV, XLSX ou planilhas Google Sheets.

**Tipos de Dados:** Geralmente estruturados (organizados em linhas e colunas), mas
com qualidade variável.

**Métodos de Extração:** O processo geralmente envolve o upload do arquivo para um
local de armazenamento em nuvem (como Amazon S3 ou Google Cloud Storage), que
serve como área de staging. O pipeline é então acionado para ler o arquivo a partir
desse local.

**Limitações:**

- **Erro Humano:** A maior fonte de problemas. Inclui inconsistências de formato
  (datas como DD/MM/AAAA vs. MM-DD-YY), erros de digitação, colunas renomeadas
  ou reordenadas, e uso de caracteres especiais que quebram o parser.

- **Falta de Padronização:** Cada novo arquivo pode ter pequenas variações no
  esquema, exigindo uma lógica de transformação flexível. Pode ser necessário
  conversão de tipo antes do carregamento.

A etapa de carregamento deve ser simples: mover o arquivo para o Data
Lake/Warehouse. A etapa de Transformação deve ser extremamente robusta, incluindo
muitos passos de validação de dados, limpeza (remoção de espaços extras,
padronização de maiúsculas/minúsculas) e tratamento de erros para lidar com a
imprevisibilidade dos dados.

### 2.5.5 Webhooks

Um padrão de "API reversa". Em vez de seu sistema puxar os dados (pull), o sistema
de origem empurra os dados (push) para um endpoint que você expõe, sempre que um
evento ocorre.

**Tipos de Dados:** Semi-estruturados (geralmente um payload JSON).

**Métodos de Extração:** Não há extração ativa. O processo consiste em construir um
serviço "ouvinte" (listener) que recebe requisições HTTP POST e processa o corpo da
requisição.

**Limitações:**

- **Perda de Dados:** Se o serviço listener estiver fora do ar no momento em que o
  evento é enviado, o dado pode ser perdido permanentemente, a menos que o sistema
  de origem tenha um mecanismo robusto de retentativas.

- **Gerenciamento de Volume:** Um pico de eventos pode sobrecarregar o serviço
  receptor se ele não for escalável.

É uma excelente abordagem para dados de baixa latência. A função do listener (a
etapa "E/L") deve ser a mais simples possível: receber o JSON, talvez adicionar um
metadado (como o timestamp de recebimento), e imediatamente armazená-lo em um
local bruto (uma fila de mensagens ou um Data Lake). A transformação é realizada
posteriormente por um processo assíncrono.

### 2.5.6 Streams de Eventos (Kafka, Google Pub/Sub)

Plataformas projetadas para lidar com fluxos contínuos de dados (eventos) em tempo
real e em alto volume. Os dados são publicados por "produtores" em "tópicos", e
consumidos por "consumidores".

**Tipos de Dados:** Semi-estruturados (os eventos são geralmente payloads em JSON,
Avro ou Protobuf).

**Métodos de Extração:** Construção de uma aplicação "consumidora" que se inscreve
em um ou mais tópicos e processa as mensagens à medida que chegam.

**Limitações:**

- **Complexidade de Gerenciamento:** Especialmente com tecnologias como o Apache
  Kafka, a configuração, manutenção e escalabilidade da infraestrutura podem ser
  complexas.

- **Paradigma de Processamento:** Requer uma mentalidade de processamento de
  streams em vez de batch, o que impacta o design de todo o pipeline.

- **Considerações para ELT:** Este é o cenário de ELT em tempo real ou near real-time.
  A extração é contínua. O carregamento é geralmente feito em micro-lotes
  (micro-batches), onde o consumidor acumula eventos por um curto período (ex:
  1 minuto) e os carrega de uma vez no Data Warehouse para otimizar a escrita. As
  transformações podem então ser executadas também em micro-lotes.

---

## 2.6 Evidências e Aplicações de Modelos Procedurais Semelhantes em Análise de Dados

A proposição de um modelo procedural para ELT, embora possa ser apresentada como
uma estruturação teórica formal, encontra forte validação empírica nas práticas
adotadas por algumas das maiores empresas de tecnologia do mundo. Gigantes como
Uber, Airbnb e Netflix, ao lidarem com ecossistemas de dados em escala de exabytes,
desenvolveram organicamente frameworks e plataformas internas que espelham os
princípios fundamentais de um processo procedural: modularidade, padronização,
testabilidade e orquestração. Esta seção visa apresentar evidências extraídas de
estudos de caso da indústria e trabalhos acadêmicos que demonstram a aplicação e os
benefícios de abordagens procedurais para a análise de dados.

Um dos principais motivadores para a adoção de modelos procedurais é a necessidade
de gerenciar a complexidade e a falta de padronização em ambientes de dados em
crescimento. Na Uber, antes da implementação de uma solução estruturada, o ciclo de
desenvolvimento de dados era heterogêneo, resultando em milhões de linhas de
código repetitivas e dificultando o foco dos engenheiros na lógica de negócio (Sparkle:
Standardizing Modular ETL at Uber | Uber Blog). A resposta foi a criação do **Sparkle**,
um framework para padronizar o desenvolvimento de ETL modular. O Sparkle permite
que a lógica de negócio seja expressa de forma modular em SQL, Java/Scala ou
Python, enquanto a orquestração do fluxo de trabalho é gerenciada por meio de
configurações declarativas em YAML.

Um modelo procedural robusto integra a garantia de qualidade como parte intrínseca
de seu fluxo, em vez de uma etapa posterior e isolada. A experiência da Uber ilustra
drasticamente esse ponto: antes do Sparkle, mais de 90% dos pipelines de dados não
possuíam testes unitários (Sparkle: Standardizing Modular ETL at Uber | Uber Blog). O
framework foi projetado para suportar o desenvolvimento orientado a testes, facilitando
a criação de testes unitários e de ponta a ponta e almejando 100% de cobertura. Além
disso, o Sparkle nativamente suporta validações pré e pós-processamento, verificando
a qualidade dos dados em aspectos como duplicatas, chaves nulas e frequência.

A plataforma **Minerva** do Airbnb segue uma filosofia similar, com um estágio mandatório
de Verificação de Dados (Data Check Stage) em seu fluxo de computação (How
Airbnb Standardized Metric Computation at Scale | The Airbnb Tech Blog | Medium).
Antes de qualquer transformação ou junção, os dados de entrada são validados para
garantir que não estejam malformados, verificando, por exemplo, se chaves primárias
são únicas e se timestamps estão em conformidade. Adicionalmente, a consistência é
garantida por um mecanismo de versionamento que dispara backfills automáticos
sempre que uma lógica de negócio é alterada, mantendo os dados sempre atualizados
e corretos.

A transição do padrão ETL para o ELT habilita a flexibilidade dos fluxos modernos. A
Netflix, ao enfrentar o crescimento exponencial no volume de dados e a complexidade
de requisitos analíticos, identificou o ETL tradicional como um gargalo (ETL vs ELT for
Scalable Data Workflows | by Samir Pandya | Medium). A migração para uma
abordagem ELT foi uma resposta direta, aproveitando a capacidade de processamento
elástica das plataformas em nuvem para realizar as transformações de dados somente
após o seu carregamento no sistema de destino.

Essa abordagem é formalizada e implementada em contextos acadêmicos e
institucionais. Um estudo de caso na Universidade de Trás-os-Montes e Alto Douro
(UTAD) detalha a implementação de um sistema de Business Intelligence usando uma
arquitetura ELT na Azure Synapse Analytics. Este estudo realiza a ingestão de diversas
fontes distintas, carregadas em seu formato bruto. Somente após o carregamento,
pipelines de transformação são executados para organizar, limpar, conjugar e
incrementar os dados, construindo o modelo analítico que será consumido pela
ferramenta de visualização.

A eficácia de um pipeline de dados procedural no padrão ELT não se restringe a
grandes corporações de tecnologia e possui aplicações práticas em diferentes
domínios. Um estudo no campo da Jurimetria demonstrou a aplicação bem-sucedida
desses princípios para analisar decisões de processos do Tribunal de Justiça de São
Paulo (TJSP) (JURIMETRIA E VISUALIZACAO DE DADOS: ANALISE DE DECISOES
DE PROCESSOS DO TJSP COM BASE EM DATA PIPELINES). O processo
implementado seguiu uma sequência procedural clara: coleta de dados públicos via
Web Scraping, dada a ausência de APIs; carga dos dados brutos em um banco de
dados NoSQL (MongoDB); transformação com scripts Python e expressões regulares
para analisar textos de decisões, classificar resultados e estruturar os dados; carga
final em um banco de dados relacional (PostgreSQL) com modelo dimensional
star-schema; e análise com visualização dos dados via ferramenta de BI.

Este caso evidencia como um modelo procedural ELT, mesmo com um conjunto de
ferramentas open-source, permite estruturar um problema complexo de análise de
dados, transformando dados não estruturados em insights acionáveis.

Em suma, as evidências da indústria e da academia convergem para a validação dos
princípios de um modelo procedural. A padronização, a modularidade, a qualidade
embarcada e a adoção do padrão ELT, observadas em empresas como Uber, Airbnb e
Netflix, demonstram ser uma resposta eficaz aos desafios de escala e complexidade
dos ecossistemas de dados modernos. O modelo proposto neste trabalho busca,
portanto, formalizar e estruturar essas melhores práticas em um guia coeso e aplicável.

---

# 3 Modelo Procedural Proposto

O modelo procedural proposto neste trabalho estrutura o desenvolvimento de pipelines
ELT em seis etapas sequenciais e interdependentes. A lógica central é transformar
uma necessidade de negócio em um pipeline analítico funcional, confiável e
reproduzível, com base nos princípios do Modern Data Stack.

A proposta foi construída com foco em execução local e em ferramentas de baixa
barreira de entrada, posicionando cada componente não como solução definitiva, mas
como instância de um conceito mais amplo — substituível por alternativas equivalentes
conforme o contexto do projeto. A validação do modelo é realizada por meio de um
estudo de caso no domínio cinematográfico, descrito no Capítulo 4.

## 3.1 Etapa 0: Identificação do Problema

O ponto de partida de qualquer projeto de dados é a definição clara do problema de
negócio a ser resolvido. Antes de qualquer decisão técnica, é necessário compreender:
qual decisão precisa ser apoiada pelos dados? Quem são os consumidores finais da
informação? Qual é o nível de granularidade e a frequência de atualização necessários?

Esta etapa determina se a construção de um pipeline de dados é de fato a solução
adequada. Um problema mal definido gera pipelines superdimensionados ou que não
atendem às necessidades reais dos usuários de negócio.

## 3.2 Etapa 1: Definição de KPIs

Com o problema claramente definido, a etapa seguinte consiste em traduzir as
necessidades de negócio em métricas mensuráveis — os **KPIs** (Key Performance
Indicators). Os KPIs determinam quais dados precisam ser extraídos, quais
transformações são necessárias e como o modelo analítico final deverá ser estruturado.

Esta etapa é crítica pois orienta todas as decisões subsequentes: a seleção das fontes
de dados, o esquema do modelo dimensional e os critérios de qualidade a serem
validados pelos testes automatizados.

## 3.3 Etapa 2: Análise e Seleção de Fontes

Com os KPIs definidos, é possível identificar quais fontes de dados são capazes de
fornecer as informações necessárias. A análise exploratória de fontes — detalhada na
seção 2.5 — busca responder: quantas fontes serão necessárias? Quais os tipos de
dados disponíveis? Quais as limitações de cada fonte?

As características das fontes selecionadas definem diretamente a complexidade e a
arquitetura das etapas de Extração e Carga. A escolha de uma API pública, por
exemplo, implica lidar com rate limiting e paginação; a escolha de arquivos CSV implica
uma etapa de transformação mais robusta para tratar inconsistências de qualidade.

## 3.4 Etapa 3: Planejamento de Arquitetura

De posse do problema, dos KPIs e das fontes disponíveis, é possível planejar a
arquitetura completa do pipeline. O planejamento deve contemplar:

- O ambiente de armazenamento analítico (Cloud Data Warehouse ou solução local
  equivalente);
- A ferramenta de ingestão e o mecanismo de extração adequado ao tipo de fonte;
- A ferramenta de transformação e a estrutura de camadas de modelos
  (`staging → intermediate → mart`);
- O mecanismo de orquestração das dependências entre as etapas;
- A camada de consumo (BI, queries ad hoc, exportações).

O resultado desta etapa é um diagrama de arquitetura e a decisão formal sobre o stack
tecnológico a ser utilizado, justificando cada escolha em função do problema e das
restrições do projeto.

## 3.5 Etapa 4: Implementação

Com a arquitetura planejada, inicia-se a implementação nas três camadas do ELT:

**Extração e Carga (E e L):** Implementação dos scripts ou conectores que extraem os
dados das fontes e os carregam no ambiente de destino em formato bruto, sem
transformações. O objetivo é preservar o dado original para fins de auditoria e
reprocessamento futuro.

**Transformação (T):** Desenvolvimento dos modelos de transformação, organizados em
camadas progressivas:

- **Camada de Staging:** modelos que replicam fielmente as tabelas brutas, realizando
  apenas conversões de tipo e renomeação de colunas para padronização;
- **Camada Intermediária:** modelos que limpam, enriquecem e preparam os dados para
  a modelagem dimensional;
- **Camada de Marts:** modelos dimensionais (tabelas fato e dimensão no padrão de
  Kimball) prontos para consumo analítico.

Os testes automatizados são escritos em paralelo com os modelos, integrando a
verificação de qualidade ao próprio desenvolvimento.

## 3.6 Etapa 5: Validação

A validação é executada de forma contínua ao longo do desenvolvimento, sendo
formalizada ao final da implementação. Ela contempla a execução dos testes
automatizados — genéricos e customizados — descritos na seção 2.4.3, verificando as
dimensões de qualidade de acurácia, completude, consistência, validade e unicidade
dos dados entregues.

Testes de frescor e volume complementam a validação operacional, monitorando a
saúde do pipeline ao longo do tempo e sinalizando falhas silenciosas no processo de
extração.

## 3.7 Etapa 6: Ajustes e Iteração

Com base nos resultados da validação, ajustes são realizados nos modelos de
transformação, nos critérios de qualidade ou, quando necessário, na arquitetura. O
caráter iterativo do modelo permite que o pipeline evolua de forma incremental. Novas
perguntas de negócio podem ser respondidas sem a necessidade de reprocessar a
extração, aproveitando o histórico bruto preservado na etapa de Carga — uma das
principais vantagens do paradigma ELT em relação ao ETL tradicional.
