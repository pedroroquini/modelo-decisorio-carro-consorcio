"""Etapa 01: universo de carros candidatos (por exclusão do que não é carro de passeio)."""
import numpy as np
import pandas as pd

# Tokens no nome que indicam veículo de carga / não passeio, além dos atributos da regex.
TOKENS_NAO_PASSEIO = r"(?<!\w)(?:CAB\.|CARGO|CHASSI)(?!\w)"
# Versões PCD têm preço com isenção de impostos e distorcem a comparação.
TOKEN_PCD = r"(?<!\w)PCD(?!\w)"
# Valores de `carroceria_explicita` (src/features.py) que indicam utilitário.
CARROCERIAS_UTILITARIO = ["PICK-UP", "P-UP", "PICAPE", "FURGÃO", "FURGAO", "VAN", "CHASSI", "MINIBUS"]


def filtrar_universo(df: pd.DataFrame, p: dict, utilitarios: list[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Aplica os filtros da etapa 01. Devolve (universo, excluidos).

    Passo 1 (faixa): mês de referência mais recente, usado (não zero km), ano-modelo mínimo
    e FIPE dentro da faixa de premissas.yaml.
    Passo 2 (exclusão): marca o motivo de exclusão de cada linha da faixa; `excluidos` traz
    a coluna `motivo_exclusao` para revisão manual.

    Espera as colunas: mesano_referencia, zero_km, ano_modelo, valor, nome_modelo,
    modelo_base, carroceria_explicita, cabine.
    """
    u = p["universo"]
    ref = df["mesano_referencia"].max()
    faixa = df[(df["mesano_referencia"] == ref)
               & ~df["zero_km"]
               & (df["ano_modelo"] != u["codigo_ano_zero_km"])
               & (df["ano_modelo"] >= u["ano_modelo_min"])
               & df["valor"].between(u["fipe_min"], u["fipe_max"])].copy()

    nome = faixa["nome_modelo"].astype(str).str.upper()
    utilitarios_upper = [m.upper() for m in utilitarios]
    # A ordem das condições define o motivo registrado quando mais de uma vale.
    condicoes = [
        nome.str.contains(TOKEN_PCD, regex=True),
        faixa["modelo_base"].isin(utilitarios_upper),
        faixa["cabine"].notna(),
        faixa["carroceria_explicita"].isin(CARROCERIAS_UTILITARIO),
        nome.str.contains(TOKENS_NAO_PASSEIO, regex=True),
    ]
    motivos = ["PCD", "modelo utilitário (utilitarios.csv)", "cabine (CD/CS/CE)",
               "carroceria utilitária", "token de carga no nome"]
    faixa["motivo_exclusao"] = np.select(condicoes, motivos, default="")

    excluir = faixa["motivo_exclusao"] != ""
    universo = faixa[~excluir].drop(columns="motivo_exclusao")
    return universo, faixa[excluir]
