import re
from pathlib import Path
from typing import Any, Callable

import yaml

RAIZ = Path(__file__).resolve().parents[1]
CAMINHO_PREMISSAS = RAIZ / "config" / "premissas.yaml"

# Seções que o modelo espera encontrar no premissas.yaml.
SECOES_OBRIGATORIAS = [
    "universo", "consorcio", "recursos", "uso", "financeiro",
    "horizonte", "modelo_residual", "simulacao", "decisao", "dados",
]

# Marcador usado nos comentários do YAML para premissas ainda sem fonte.
MARCADOR_FONTE_PENDENTE = "FONTE PENDENTE"


def carregar_premissas(caminho: Path = CAMINHO_PREMISSAS, validar: bool = True) -> dict:
    """Lê o arquivo de premissas e devolve um dicionário.

    Com `validar=True` (padrão), confere o arquivo e levanta ValueError
    listando todos os problemas encontrados de uma vez.
    """
    with open(caminho, encoding="utf-8") as f:
        p = yaml.safe_load(f)
    if validar:
        erros = verificar_premissas(p)
        if erros:
            raise ValueError("Premissas inválidas:\n- " + "\n- ".join(erros))
    return p


def _obter(p: dict, caminho: str) -> Any:
    """Busca um valor aninhado pelo caminho com pontos, ex.: 'universo.fipe_min'.

    Levanta KeyError se alguma parte do caminho não existir.
    """
    valor = p
    for chave in caminho.split("."):
        valor = valor[chave]
    return valor


def _eh_numero(x: Any) -> bool:
    """True para int ou float (bool não conta como número aqui)."""
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def _eh_inteiro(x: Any) -> bool:
    """True para int (bool não conta)."""
    return isinstance(x, int) and not isinstance(x, bool)


def _eh_mes(x: Any) -> bool:
    """True para texto no formato 'AAAA-MM' com mês válido."""
    return isinstance(x, str) and re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", x) is not None


# Cada regra: (caminho no YAML, teste que deve ser verdadeiro, descrição do esperado).
# Os limites são de sanidade (pegar erro de digitação), não de mérito da premissa.
REGRAS: list[tuple[str, Callable[[Any], bool], str]] = [
    ("universo.fipe_min", lambda x: _eh_numero(x) and x > 0, "número > 0"),
    ("universo.fipe_max", _eh_numero, "número"),
    ("universo.ano_modelo_min", lambda x: _eh_inteiro(x) and 1990 <= x <= 2100, "ano inteiro"),
    ("universo.codigo_ano_zero_km", _eh_inteiro, "inteiro"),
    ("universo.tipo_veiculo", lambda x: isinstance(x, str) and x != "", "texto"),

    ("consorcio.valor_carta", lambda x: _eh_numero(x) and x > 0, "número > 0"),
    ("consorcio.pct_lance_total", lambda x: _eh_numero(x) and 0 <= x <= 1, "fração entre 0 e 1"),
    ("consorcio.pct_lance_embutido", lambda x: _eh_numero(x) and 0 <= x < 1, "fração entre 0 e 1"),
    ("consorcio.valor_ja_pago", lambda x: _eh_numero(x) and x >= 0, "número >= 0"),
    ("consorcio.parcelas_restantes", lambda x: _eh_inteiro(x) and x >= 0, "inteiro >= 0"),
    ("consorcio.fator_total_devedor", lambda x: _eh_numero(x) and 1 <= x <= 2, "entre 1 e 2"),

    ("recursos.recurso_proprio", lambda x: _eh_numero(x) and x >= 0, "número >= 0"),
    ("recursos.juros_complemento_cartao", lambda x: _eh_numero(x) and 0 <= x <= 1, "fração entre 0 e 1"),
    ("recursos.parcelas_cartao", lambda x: _eh_inteiro(x) and x >= 1, "inteiro >= 1"),

    ("uso.km_ano", lambda x: _eh_numero(x) and x > 0, "número > 0"),
    ("uso.aplicar_queda_km_idade", lambda x: isinstance(x, bool), "true ou false"),
    ("uso.queda_km_por_ano", lambda x: _eh_numero(x) and x >= 0, "número >= 0"),

    ("financeiro.taxa_desconto_real_aa", lambda x: _eh_numero(x) and -0.05 <= x <= 0.20, "fração entre -0,05 e 0,20"),
    ("financeiro.aliquota_ipva", lambda x: _eh_numero(x) and 0 <= x <= 0.10, "fração entre 0 e 0,10"),
    ("financeiro.desconto_mercado_sobre_fipe", lambda x: _eh_numero(x) and 0 <= x < 1, "fração entre 0 e 1"),
    ("financeiro.custo_mensal_referencia", lambda x: x is None or (_eh_numero(x) and x > 0), "vazio ou número > 0"),

    ("horizonte.anos_max", lambda x: _eh_inteiro(x) and x >= 1, "inteiro >= 1"),

    ("modelo_residual.horizontes_anos", lambda x: isinstance(x, list) and len(x) > 0 and all(_eh_inteiro(h) and h >= 1 for h in x), "lista de inteiros >= 1"),
    ("modelo_residual.quantis", lambda x: isinstance(x, list) and x == sorted(x) and all(_eh_numero(q) and 0 < q < 1 for q in x), "lista crescente de frações entre 0 e 1"),
    ("modelo_residual.janela_teste_meses", lambda x: _eh_inteiro(x) and x >= 1, "inteiro >= 1"),
    ("modelo_residual.regime_choque", lambda x: isinstance(x, list) and len(x) == 2 and all(_eh_mes(m) for m in x), "lista ['AAAA-MM', 'AAAA-MM']"),

    ("simulacao.n_cenarios", lambda x: _eh_inteiro(x) and x >= 100, "inteiro >= 100"),
    ("simulacao.semente", _eh_inteiro, "inteiro"),

    ("dados.dataset_fipe", lambda x: isinstance(x, str) and "/" in x, "texto 'dono/nome'"),
    ("dados.split", lambda x: isinstance(x, str) and x != "", "texto"),
    ("dados.serie_ipca_bcb", _eh_inteiro, "inteiro"),
    ("dados.arquivo_fipe", lambda x: isinstance(x, str) and x.endswith(".parquet"), "nome de arquivo .parquet"),
    ("dados.url_base_fipe", lambda x: isinstance(x, str) and x.startswith("https://"), "URL https"),
    ("dados.dir_raw", lambda x: isinstance(x, str) and x != "", "texto"),
    ("dados.dir_processed", lambda x: isinstance(x, str) and x != "", "texto"),
    ("dados.cache_regex", lambda x: isinstance(x, str) and x.endswith(".parquet"), "caminho .parquet"),
]


def verificar_premissas(p: dict) -> list[str]:
    """Confere o dicionário de premissas e devolve a lista de problemas.

    Lista vazia = tudo certo. Não para no primeiro erro: junta todos,
    para você corrigir o YAML de uma vez só.
    """
    erros: list[str] = []

    for secao in SECOES_OBRIGATORIAS:
        if not isinstance(p.get(secao), dict):
            erros.append(f"seção '{secao}' ausente")

    # Regras campo a campo.
    for caminho, teste, esperado in REGRAS:
        try:
            valor = _obter(p, caminho)
        except (KeyError, TypeError):
            if caminho.split(".")[0] in p:      # seção existe, falta só o campo
                erros.append(f"'{caminho}' ausente")
            continue
        if not teste(valor):
            erros.append(f"'{caminho}' = {valor!r}; esperado: {esperado}")

    # Regras que comparam campos entre si (só rodam se os campos passaram acima).
    if not erros:
        u, uso, h, mr = p["universo"], p["uso"], p["horizonte"], p["modelo_residual"]
        c, r = p["consorcio"], p["recursos"]
        if c["pct_lance_embutido"] > c["pct_lance_total"]:
            erros.append("consorcio.pct_lance_embutido não pode ser maior que pct_lance_total")
        lance_recurso_proprio = c["valor_carta"] * (c["pct_lance_total"] - c["pct_lance_embutido"])
        if r["recurso_proprio"] < lance_recurso_proprio:
            erros.append(
                f"recursos.recurso_proprio ({r['recurso_proprio']:,.2f}) não cobre a parte do lance "
                f"paga com recurso próprio ({lance_recurso_proprio:,.2f})"
            )
        if u["fipe_min"] >= u["fipe_max"]:
            erros.append("universo.fipe_min deve ser menor que universo.fipe_max")
        if uso["queda_km_por_ano"] >= uso["km_ano"]:
            erros.append("uso.queda_km_por_ano deve ser menor que uso.km_ano")
        if max(mr["horizontes_anos"]) > h["anos_max"]:
            erros.append("modelo_residual.horizontes_anos passa de horizonte.anos_max")
        inicio, fim = mr["regime_choque"]
        if inicio > fim:   # 'AAAA-MM' ordena corretamente como texto
            erros.append("modelo_residual.regime_choque: início depois do fim")

    return erros


def fontes_pendentes(caminho: Path = CAMINHO_PREMISSAS) -> list[str]:
    """Devolve as linhas do YAML marcadas com 'FONTE PENDENTE'.

    O PyYAML descarta comentários, por isso a leitura é do texto bruto.
    """
    linhas = caminho.read_text(encoding="utf-8").splitlines()
    return [linha.strip() for linha in linhas if MARCADOR_FONTE_PENDENTE in linha]
