# -*- coding: utf-8 -*-
"""
Dicionário de municípios — casa cada prefeitura pelo CNPJ.

O nome do credor no relatório do SIAFE vem com muitas variações
("PREFEITURA MUNICIPAL DE X", "PREFEITURA MUN. DE X", "...AÇÚ", com ponto final,
etc.), mas o CNPJ é único e estável. Por isso a chave é sempre o CNPJ; o nome
canônico (maiúsculo, sem acento — padrão dos relatórios atuais) sai daqui.

Sem dependência de Streamlit. A base é o CSV `data/municipios.csv` (cnpj,municipio).
"""
import csv
import re
import unicodedata
from pathlib import Path

# data/municipios.csv (uma pasta acima de core/)
_CSV_PADRAO = Path(__file__).resolve().parent.parent / "data" / "municipios.csv"


def sem_acento(texto: str) -> str:
    """Maiúsculas, sem acento — para comparação/normalização robusta."""
    nf = unicodedata.normalize("NFKD", str(texto))
    return "".join(c for c in nf if not unicodedata.combining(c)).upper().strip()


def extrair_cnpj(credor: str) -> str:
    """Extrai o CNPJ (14 dígitos) do sufixo do nome do credor. '' se não houver."""
    m = re.search(r"(\d{14})\s*$", str(credor).strip())
    if m:
        return m.group(1)
    # fallback: qualquer sequência de 14 dígitos no texto
    m = re.search(r"\b(\d{14})\b", str(credor))
    return m.group(1) if m else ""


class DicionarioMunicipios:
    """Carrega o CSV cnpj→município e resolve o nome canônico de um credor."""

    def __init__(self, caminho_csv: Path | str | None = None):
        self.caminho = Path(caminho_csv) if caminho_csv else _CSV_PADRAO
        self._por_cnpj: dict[str, str] = {}
        if self.caminho.exists():
            self.carregar()

    def carregar(self) -> None:
        self._por_cnpj.clear()
        with open(self.caminho, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                cnpj = str(row.get("cnpj", "")).strip()
                nome = str(row.get("municipio", "")).strip()
                if cnpj:
                    self._por_cnpj[cnpj] = nome

    def __len__(self) -> int:
        return len(self._por_cnpj)

    def nome_por_cnpj(self, cnpj: str) -> str:
        """Nome canônico do CNPJ, ou '' se desconhecido."""
        return self._por_cnpj.get(str(cnpj).strip(), "")

    def resolver(self, credor: str) -> tuple[str, str]:
        """
        Do nome do credor devolve (cnpj, municipio_canonico).
        Se o CNPJ não estiver no dicionário, devolve o nome 'limpo' do próprio
        credor como fallback (sem prefixo/acento) e sinaliza com municipio != ''.
        """
        cnpj = extrair_cnpj(credor)
        nome = self.nome_por_cnpj(cnpj)
        if not nome:
            nome = self._limpar_credor(credor)
        return cnpj, nome

    @staticmethod
    def _limpar_credor(credor: str) -> str:
        """Fallback p/ credor fora do dicionário: tira prefixo e CNPJ, normaliza."""
        s = re.sub(r"[\s-]+\d{14}\s*$", "", str(credor).strip())
        s = re.sub(r"^\s*PREFEIT\w*\.?\s*MUN\w*\.?\s*(DE|DO|DA)?\s+", "", s, flags=re.I)
        return sem_acento(s).rstrip(".").strip()
