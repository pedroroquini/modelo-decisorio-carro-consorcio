# Modelo decisório para compra de bens duráveis — Carro via consórcio

Análise de **custo do ciclo de vida** (*Life Cycle Cost*), a mesma que a engenharia usa para comprar e substituir equipamentos, adaptada para bens duráveis de pessoa física. Primeiro caso: a compra de um carro usado com carta de consórcio.

O modelo responde três perguntas: **qual carro comprar, quanto pagar e por quanto tempo manter.**

> README completo (metodologia, métricas e limitações): substitua este arquivo pela versão exportada do documento do projeto.

## Etapas

| # | Notebook | Saída |
|---|---|---|
| 00 | Premissas | `config/premissas.yaml` |
| 01 | Universo | `data/processed/universo.parquet` |
| 02 | Features | `data/processed/features.parquet` + dicionário de dados |
| 03 | Valor residual | Curvas de valor residual com P10–P90 |
| 04 | Custos | CAE por horizonte, vida econômica |
| 05 | Monte Carlo | P90 do custo, pior ano de caixa |
| 06 | Decisão | Ranking (Pareto → TOPSIS → robustez) |
| 07 | Case real | Decisão documentada dos finalistas |

## Como rodar

1. Instale as dependências: `pip install -r requirements.txt`
2. Ajuste as premissas em `config/premissas.yaml`
3. Rode os notebooks em ordem, de `00` a `07`

## Fontes de dados

- Tabela FIPE histórica: dataset `alanwgt/fipex-veiculos-brasil` (Hugging Face)
- IPCA: série 433 do Sistema Gerenciador de Séries Temporais do Banco Central
- Km por ano: levantamento KBB Brasil (2019)
- Segurança: Latin NCAP; Resoluções Contran 799/2020 e 954/2022
