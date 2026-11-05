def fator_recuperacao_capital(r: float, n: int) -> float:
    """Converte um valor presente em parcela anual equivalente (taxa r, n anos)."""
    if r == 0:
        return 1 / n
    return r * (1 + r) ** n / ((1 + r) ** n - 1)


def cae(vp_custos: float, valor_revenda: float, r: float, n: int) -> float:
    """Custo Anual Equivalente: [VP(custos) - VP(revenda no ano n)] x FRC(r, n)."""
    vp_revenda = valor_revenda / (1 + r) ** n
    return (vp_custos - vp_revenda) * fator_recuperacao_capital(r, n)
