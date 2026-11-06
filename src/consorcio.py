"""Regras da carta de consórcio: lance, crédito líquido e complemento no cartão.

Lógica conferida com a aba `simulação_aumento_credito` da planilha simulacao_consorcio.
"""


def decompor_lance(p: dict) -> dict:
    """Separa o lance total em parte embutida e parte com recurso próprio.

    - Lance total = carta × pct_lance_total (inclui o embutido).
    - Lance embutido = carta × pct_lance_embutido; sai da própria carta, reduzindo o crédito.
    - Lance com recurso próprio = lance total − lance embutido.
    - Crédito líquido = carta − lance embutido (o que sobra da carta para comprar o carro).
    - Sobra de recurso próprio = recurso próprio − lance com recurso próprio.
    """
    c, r = p["consorcio"], p["recursos"]
    carta = c["valor_carta"]
    lance_total = carta * c["pct_lance_total"]
    lance_embutido = carta * c["pct_lance_embutido"]
    lance_recurso_proprio = lance_total - lance_embutido
    return {
        "carta": carta,
        "lance_total": lance_total,
        "lance_embutido": lance_embutido,
        "lance_recurso_proprio": lance_recurso_proprio,
        "credito_liquido": carta - lance_embutido,
        "sobra_recurso_proprio": r["recurso_proprio"] - lance_recurso_proprio,
    }


def complemento_cartao(p: dict, preco_carro: float) -> dict:
    """Fecha a conta do preço do carro: cartão quando falta dinheiro, abatimento quando sobra.

    Disponível = crédito líquido + sobra de recurso próprio.
    - Carro mais caro que o disponível: a diferença vai para o cartão
      (complemento), com acréscimo de juros sobre o total, em parcelas iguais.
    - Carro mais barato: não há cartão, e a sobra abate o saldo devedor do
      consórcio (`abatimento_saldo_devedor`). O efeito nas parcelas é tratado na etapa 04.
    Os dois nunca são positivos ao mesmo tempo.
    """
    lance = decompor_lance(p)
    r = p["recursos"]
    disponivel = lance["credito_liquido"] + lance["sobra_recurso_proprio"]
    complemento = max(0.0, preco_carro - disponivel)
    total_com_juros = complemento * (1 + r["juros_complemento_cartao"])
    return {
        "preco_carro": preco_carro,
        "disponivel_sem_cartao": disponivel,
        "complemento": complemento,
        "complemento_com_juros": total_com_juros,
        "parcela_cartao": total_com_juros / r["parcelas_cartao"],
        "abatimento_saldo_devedor": max(0.0, disponivel - preco_carro),
    }
