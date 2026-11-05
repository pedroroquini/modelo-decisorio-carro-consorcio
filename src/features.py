"""Atributos extraídos do nome do modelo na FIPE (regex).

Adaptado de `extrair_atributos_regex` do notebook antigo (referencia/Fipe_Carros.ipynb), com:
- um único dicionário de padrões, usado tanto para extrair quanto para limpar o nome;
- fronteiras que funcionam com tokens terminados em ponto ("AUT.", "TIP.", "SED.");
- cache em parquet que é refeito sozinho quando os padrões mudam.

As funções rodam sobre os NOMES ÚNICOS (alguns milhares), nunca sobre o dataset inteiro.
O resultado é juntado de volta ao dataset por `nome_modelo`.
"""
import hashlib
import re
import json
from pathlib import Path

import pandas as pd

# Fronteiras de token. Usamos (?<!\w) e (?!\w) em vez de \b porque \b falha depois de
# um ponto: em "TIP. FLEX", \b entre "." e " " não existe, e "TIP\." nunca casaria.
_INI, _FIM = r"(?<!\w)", r"(?!\w)"


def _token(alternativas: str) -> str:
    """Envolve as alternativas num grupo de captura com fronteiras de token."""
    return f"{_INI}({alternativas}){_FIM}"


# Ordem importa só para a leitura; cada padrão é aplicado de forma independente.
# Texto já vem em MAIÚSCULAS.
PADROES: dict[str, str] = {
    "motorizacao": r"(?<!\d)(\d\.\d)(?!\d)",
    "cilindros": _token(r"V6|V8|V10|V12|I6|H6"),
    "valvulas": _token(r"\d{1,2}V"),
    "portas": _token(r"[2-5]P"),
    "tracao": _token(r"4X4|4X2|AWD|FWD|4WD|QUATTRO|4MATIC|XDRIVE"),
    "transmissao": _token(r"AUT\.?|MEC\.?|TIPTRONIC|TIP\.?|S-TRONIC|TRONIC|DUALOGIC|DUALO\.?|CVT|AUTOMATIC[OA]?|MANUAL"),
    "turbo": _token(r"BI-TURBO|BI-TB|TURBO|TB|T\.B\.?"),
    "combustivel_token": _token(r"TOTAL\s?FLEX|FLEX|FLEXPOWER|FLEXONE|FLEXSTART|F\.FLEX|T\.FLEX|HI-FLEX|ECONO\.?FLEX|"
                                r"DIESEL|DIES\.?|DIE\.?|H[IÍ]BRIDO|HÍB\.?|HYBRID|EL[EÉ]T\w*\.?"),
    "injecao": _token(r"MPFI|MPI|MI|TFSI|TSI|TDI|DCI|CGI|FSI|SFI"),
    "potencia_cv": r"(?<!\w)(\d{2,3})\s?CV(?!\w)",
    "carroceria_explicita": _token(r"SEDAN|SED\.?|HATCHBACK|HATCH|COUPE|CUP[EÊÉ]|CABRIOLET|CABRIO|WAGON|SW|"
                                   r"BREAK|VARIANT|ROADSTER|SPIDER|MINIBUS|VAN|FURG[AÃ]O|PICK-UP|P-UP|PICAPE|CHASSI"),
    "cabine": _token(r"CD|CS|CE|CAB\.?\s?DUPLA|CAB\.?\s?SIMPLES|CAB\.?\s?ESTENDIDA"),
}

# Colunas devolvidas por extrair_atributos (além de nome_modelo).
COLUNAS_ATRIBUTOS = list(PADROES) + ["flag_eletrico", "nome_modelo_limpo"]


def versao_padroes() -> str:
    """Hash curto dos padrões. Se qualquer regex mudar, o hash muda e o cache é refeito."""
    texto = json.dumps(PADROES, sort_keys=True, ensure_ascii=False)
    return hashlib.sha1(texto.encode("utf-8")).hexdigest()[:10]


def extrair_atributos(nomes_modelo: pd.Series) -> pd.DataFrame:
    """Extrai os atributos técnicos de cada nome de modelo.

    Recebe uma Series de nomes (de preferência únicos) e devolve um DataFrame com
    uma linha por nome: `nome_modelo`, uma coluna por padrão de PADROES,
    `flag_eletrico` e `nome_modelo_limpo` (nome sem os tokens técnicos).
    Atributo não encontrado fica nulo (NaN), nunca vazio ou zero.
    """
    nomes = nomes_modelo.reset_index(drop=True)
    texto = nomes.str.upper()
    out = pd.DataFrame({"nome_modelo": nomes})

    for coluna, padrao in PADROES.items():
        # expand=False devolve uma Series (1 coluna) em vez de um DataFrame
        valor = texto.str.extract(padrao, expand=False)
        out[coluna] = valor.str.rstrip(".")   # "AUT." e "AUT" viram o mesmo valor

    # Elétrico: token ELÉT... sem DIESEL (evita "injeção eletrônica" de motores diesel)
    # (?:...) é um grupo que não captura: aqui só queremos saber se casa, não extrair.
    out["flag_eletrico"] = (
        texto.str.contains(rf"{_INI}EL[EÉ]T\w*", regex=True, na=False)
        & ~texto.str.contains(rf"{_INI}DIESEL{_FIM}", regex=True, na=False)
    )

    limpo = texto
    for padrao in PADROES.values():
        limpo = limpo.str.replace(padrao, " ", regex=True)
    limpo = limpo.str.replace(r"[./]", " ", regex=True).str.replace(r"\s+", " ", regex=True).str.strip()
    out["nome_modelo_limpo"] = limpo
    return out


def atributos_com_cache(nomes_modelo: pd.Series, caminho_cache: Path) -> pd.DataFrame:
    """Devolve os atributos dos nomes pedidos, reaproveitando o cache em parquet.

    - Cache inexistente ou feito com outros padrões: processa tudo e regrava.
    - Cache válido: processa só os nomes novos e acrescenta ao cache.
    """
    caminho_cache = Path(caminho_cache)
    nomes = pd.Series(pd.unique(nomes_modelo.dropna()), name="nome_modelo")
    versao = versao_padroes()

    cache = None
    if caminho_cache.exists():
        cache = pd.read_parquet(caminho_cache)
        if cache.get("versao_padroes", pd.Series(dtype=str)).ne(versao).any() or cache.empty:
            print(f"Cache com padrões antigos: reprocessando {len(nomes):,} nomes.")
            cache = None

    if cache is None:
        cache = extrair_atributos(nomes)
    else:
        novos = nomes[~nomes.isin(cache["nome_modelo"])]
        print(f"Cache válido com {len(cache):,} nomes; {len(novos):,} novos para processar.")
        if len(novos) > 0:
            cache = pd.concat([cache.drop(columns="versao_padroes"), extrair_atributos(novos)],
                              ignore_index=True)
        else:
            cache = cache.drop(columns="versao_padroes")

    cache["versao_padroes"] = versao
    caminho_cache.parent.mkdir(parents=True, exist_ok=True)
    cache.to_parquet(caminho_cache, index=False)
    return cache[cache["nome_modelo"].isin(nomes)].drop(columns="versao_padroes").reset_index(drop=True)


def cobertura(atributos: pd.DataFrame) -> pd.DataFrame:
    """% de nomes em que cada atributo foi encontrado (não nulo), do maior para o menor."""
    cols = [c for c in PADROES if c in atributos]
    pct = atributos[cols].notna().mean().mul(100).round(1)
    return pct.sort_values(ascending=False).rename("pct_preenchido").to_frame()


def definir_modelo_base(nomes_modelo: pd.Series, excecoes: pd.DataFrame) -> pd.Series:
    """Nome do modelo sem versão, ex.: "Onix Hatch LT 1.0..." -> "ONIX".

    Regra: primeiro token do nome em maiúsculas (cortando em "/" e tirando "." ou "," do fim).
    Exceções: se o nome começar com um `prefixo` da tabela de exceções
    (data/ref/modelo_base_excecoes.csv), usa o `modelo_base` da tabela.
    Prefixos mais longos têm prioridade.
    """
    texto = nomes_modelo.str.upper().str.strip()
    base = texto.str.split().str[0].str.split("/").str[0].str.rstrip(".,")

    ordenadas = excecoes.assign(tam=excecoes["prefixo"].str.len()).sort_values("tam")
    for prefixo, modelo in zip(ordenadas["prefixo"], ordenadas["modelo_base"]):
        # o prefixo precisa terminar numa fronteira: "XC 60" casa com "XC 60 T5", não com "XC 600"
        casa = texto.str.match(re.escape(prefixo.upper()) + r"(?![A-Z0-9])")
        base = base.mask(casa, modelo.upper())   # o mais longo é aplicado por último e prevalece
    return base
