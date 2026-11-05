# CLAUDE.md — Modelo decisório para compra de bens duráveis (carro via consórcio)

## O projeto
Análise de custo do ciclo de vida (Life Cycle Cost), usada na engenharia para comprar e substituir
equipamentos, adaptada para bens duráveis de pessoa física. Primeiro caso: compra de um carro usado
com carta de consórcio. Responde: qual carro comprar, quanto pagar e por quanto tempo manter.

Dois objetivos: (1) apoiar uma compra real (o case da etapa 07); (2) ser um repositório de portfólio
com metodologia reutilizável. A metodologia completa está no README.md — leia antes de propor código.

## Sobre o autor (como trabalhar comigo)
- Analista de dados, forte em SQL e estatística, **iniciante em Python**. Quero entender o código, não só recebê-lo.
- Antes de escrever código de uma etapa, explique o plano em poucas linhas e espere meu ok.
- Explique o porquê das escolhas (boas práticas, alternativas descartadas). Equilibre intuição e rigor.
- Valide a lógica em uma amostra pequena antes de rodar no dataset completo.
- Mostre estatísticas de cobertura (% de match de regex, % de nulos) antes de confiar numa extração.
- Responda sempre em português; código, nomes de variáveis e comentários em português.
- Nunca faça push sem me perguntar. Commits pequenos, mensagens no imperativo em português.

## Decisões já tomadas (não mudar sem discutir)
- Universo: FIPE entre R$ 50 e 85 mil **no mês de referência mais recente**; ano-modelo >= 2017;
  excluir ano 32000 (zero km); só tipo "carro".
- Universo por **exclusão** do que não é carro de passeio (tokens no nome + `data/ref/utilitarios.csv`).
  Classificação de carroceria só para finalistas (etapa 07).
- Unidade de análise: par (código FIPE, ano-modelo).
- Só dados públicos e auditáveis no modelo geral; anúncios e cotações reais só para finalistas.
- Todas as premissas em `config/premissas.yaml`, com fonte. Nada hardcoded no código.
- Preferências do usuário (pesos, filtros) só na etapa 06.
- Segurança: guardar o **protocolo** do Latin NCAP (antigo x novo); "não testado" = nulo, nunca zero.
  Flag `esc_garantido_por_norma` para ano-modelo >= 2025 (Res. Contran 799/2020 e 954/2022).
- km/ano padrão 12.900 (KBB Brasil, 2019), editável.

## Etapa 03 (núcleo técnico)
- Alvo: y = ln(V(t+h) / V(t)), h = 1..6 anos, em **termos reais** (FIPE deflacionada pelo IPCA,
  série 433 do BCB; `src/deflacao.py`). Taxa de desconto real no CAE.
- Painel (código, ano-modelo, origem t, horizonte h); nenhuma feature usa informação posterior a t;
  h entra como feature de um modelo único.
- Escada: B0a (preço nominal constante = perda real igual ao IPCA), B0b (taxa real mediana do mercado),
  B1 (curva entre anos-modelo), B2 (curva histórica por idade e segmento — baseline a bater), M1 (LightGBM).
- Intervalos P10–P90 por regressão quantílica ou predição conformal.
- Backtest com origem móvel; reportar 2020–22 separadamente.
- Métricas: MAE, viés, cobertura P10–P90, Spearman do ranking de CAE, regret.
- Critério de aceitação (definido antes de rodar): M1 só é usado se superar B2 em MAE, viés e regret,
  com intervalos calibrados. Senão, usar B2 e documentar.

## Dados
- Dataset FIPE: `alanwgt/fipex-veiculos-brasil` (Hugging Face), ~19 milhões de linhas, split `train`.
- Colunas reais (vistas no notebook antigo): `tipo_veiculo`, `nome_marca`, `nome_modelo`, `ano_modelo`,
  `mes_referencia`, `ano_referencia`, `valor_centavos`, `sigla_combustivel`, `nome_combustivel`,
  `valor_formatado`. Confirmar o nome da coluna do código FIPE ao carregar (`df.info()`).
- ATENÇÃO 1: o valor vem em **centavos** (`valor_centavos`). Criar `valor = valor_centavos / 100`.
- ATENÇÃO 2: o notebook antigo montava `mesano_referencia` como texto "mes-ano" (ex.: "11-2026"),
  que não ordena corretamente (`.max()` daria o mês errado). Criar como inteiro AAAAMM:
  `ano_referencia * 100 + mes_referencia`.
- `src/universo.py` foi escrito esperando as colunas `valor`, `mesano_referencia` (AAAAMM) e
  `modelo_base`: adaptar a função ou criar essas colunas antes de chamá-la.
- O notebook antigo excluía versões **PCD** (`nome_modelo` contém "PCD"), porque têm preço com isenção
  e distorcem a comparação. Manter essa exclusão no universo (etapa 01) e documentar.
- Chave de série temporal: (código FIPE, ano_modelo).
- Memória: já houve estouro de RAM. Carregar só as colunas necessárias, filtrar `tipo_veiculo == "carro"`
  logo no início, converter texto repetido para `category`, evitar `.apply` linha a linha, salvar
  intermediários em parquet.
- Notebook antigo em `referencia/Fipe_Carros.ipynb` (não versionado). Reaproveitar em `src/features.py`:
  - `extrair_atributos_regex(nomes_modelo)`: roda só sobre os nomes únicos e extrai motorização,
    cilindros, válvulas, portas, tração, transmissão, turbo, combustível, injeção, potência,
    carroceria explícita, cabine (CD/CS) e `flag_elétrico`, além de `nome_modelo_limpo`.
  - O cache incremental em parquet dos nomes já processados.
  - As colunas `carroceria_explicita` (PICK-UP, FURGÃO, VAN...) e `cabine` (CD/CS) ajudam a etapa 01
    a excluir utilitários. `nome_modelo_limpo` ainda contém a versão (ex.: "ONIX LTZ"); o
    `modelo_base` precisa de uma regra adicional (ex.: primeiro token, com exceções revisadas).
- `data/raw` e `data/processed` não são versionados (.gitignore).

## Estrutura
- `config/premissas.yaml` — premissas editáveis
- `notebooks/00..07` — uma etapa por notebook; notebooks orquestram, lógica fica em `src/`
- `src/` — funções reutilizáveis e testáveis (config, universo, deflacao, custos; features e decisao a criar)
- `data/ref/` — tabelas pequenas mantidas à mão

## Convenções de código
- Funções pequenas com docstring em português; type hints.
- Nada de número mágico: tudo vem de `premissas.yaml`.
- Cada notebook termina com a seção "Decisões e observações" preenchida.
