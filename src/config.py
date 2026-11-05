from pathlib import Path
import yaml

RAIZ = Path(__file__).resolve().parents[1]


def carregar_premissas(caminho: Path = RAIZ / "config" / "premissas.yaml") -> dict:
    """Lê o arquivo de premissas e devolve um dicionário."""
    with open(caminho, encoding="utf-8") as f:
        return yaml.safe_load(f)
