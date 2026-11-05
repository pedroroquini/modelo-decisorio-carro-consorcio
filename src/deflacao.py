import pandas as pd


def fatores_reais(ipca: pd.DataFrame) -> pd.DataFrame:
    """Recebe colunas `mes` e `var_pct` (IPCA mensal, %) e devolve o fator
    que converte valores de cada mês para reais do último mês da série."""
    out = ipca.sort_values("mes").copy()
    out["indice"] = (1 + out["var_pct"] / 100).cumprod()
    out["fator_real"] = out["indice"].iloc[-1] / out["indice"]
    return out[["mes", "fator_real"]]
