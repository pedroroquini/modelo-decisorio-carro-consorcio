import pandas as pd

TOKENS_UTILITARIO = r"\b(?:Cab\.|CS|CD|Furg[aã]o|Pick-?up|Chassi|Van)\b"


def filtrar_universo(df: pd.DataFrame, p: dict, utilitarios: list[str]):
    """Aplica os filtros da etapa 01. Devolve (universo, excluidos).

    Espera as colunas: mesano_referencia, ano_modelo, valor, nome_modelo, modelo_base.
    """
    u = p["universo"]
    ref = df["mesano_referencia"].max()
    base = df[(df["mesano_referencia"] == ref)
              & (df["ano_modelo"] >= u["ano_modelo_min"])
              & (df["ano_modelo"] != u["codigo_ano_zero_km"])
              & (df["valor"].between(u["fipe_min"], u["fipe_max"]))].copy()
    mask = (base["nome_modelo"].str.contains(TOKENS_UTILITARIO, case=False, regex=True)
            | base["modelo_base"].str.upper().isin([m.upper() for m in utilitarios]))
    return base[~mask], base[mask]
