"""Download e carga do histórico FIPE (dataset fipeX)."""
from pathlib import Path

import pandas as pd
import requests

from src.config import RAIZ

# Só as colunas que o modelo usa. `valor_formatado` e `nome_combustivel` repetem informação.
COLUNAS_FIPE = [
    "codigo_fipe", "nome_marca", "nome_modelo", "sigla_combustivel", "ano_modelo",
    "zero_km", "valor_centavos", "mes_referencia", "ano_referencia",
]


def caminho_fipe(p: dict) -> Path:
    """Caminho local do arquivo FIPE definido nas premissas."""
    return RAIZ / p["dados"]["dir_raw"] / p["dados"]["arquivo_fipe"]


def baixar_fipe(p: dict, forcar: bool = False) -> Path:
    """Baixa o parquet do histórico FIPE para data/raw, se ainda não estiver lá.

    O download é feito em blocos para não carregar ~130 MB na memória de uma vez.
    """
    destino = caminho_fipe(p)
    if destino.exists() and not forcar:
        return destino
    destino.parent.mkdir(parents=True, exist_ok=True)
    url = f"{p['dados']['url_base_fipe']}/{p['dados']['arquivo_fipe']}"
    temporario = destino.with_suffix(".parcial")
    with requests.get(url, stream=True, timeout=60) as resposta:
        resposta.raise_for_status()
        with open(temporario, "wb") as f:
            for bloco in resposta.iter_content(chunk_size=1 << 20):
                f.write(bloco)
    temporario.replace(destino)   # só vira o arquivo final se o download terminou
    return destino


def carregar_fipe_carros(p: dict) -> pd.DataFrame:
    """Carrega o histórico FIPE só de carros, com as colunas derivadas.

    - Lê só COLUNAS_FIPE e já filtra o tipo de veículo na leitura (o pyarrow
      descarta as outras linhas antes de montar o DataFrame, poupando memória).
    - Remove linhas 100% repetidas (existem algumas centenas na fonte).
    - Cria `valor` (reais) e `mesano_referencia` (inteiro AAAAMM, ordena certo).
    - Converte textos repetidos para `category`.
    """
    df = pd.read_parquet(
        caminho_fipe(p),
        columns=COLUNAS_FIPE,
        filters=[("tipo_veiculo", "==", p["universo"]["tipo_veiculo"])],
    )
    df = df.drop_duplicates(ignore_index=True)
    df["valor"] = df["valor_centavos"] / 100
    df["mesano_referencia"] = df["ano_referencia"] * 100 + df["mes_referencia"]
    df["ano_modelo"] = df["ano_modelo"].astype("Int64")   # inteiro que aceita nulo (zero km)
    for col in ["codigo_fipe", "nome_marca", "nome_modelo", "sigla_combustivel"]:
        df[col] = df[col].astype("category")
    return df.drop(columns=["valor_centavos", "mes_referencia", "ano_referencia"])
