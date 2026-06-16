# -*- coding: utf-8 -*-
"""
Classificação da descrição da OB.

Padrão esperado:
    Nª PARCELA DO {PETE|PEAE}/AAAA [(COMPLEMENTO)]
ex.:
    1ª PARCELA DO PETE/2026
    3ª PARCELA DO PEAE/2026 (COMPLEMENTO)

Extrai: programa (PETE/PEAE), número da parcela e se é complemento.
A definição do TIPO final (NORMAL/COMPLEMENTO/EXTRA) e a detecção de anomalia
(2ª OB normal na mesma parcela) dependem do que já existe no razão e ficam em
`core.razao` / camada de persistência — aqui é só o parsing puro + município.

Sem dependência de Streamlit.
"""
import re

from core.municipios import DicionarioMunicipios, sem_acento

# Nª PARCELA DO PETE/2026  — tolera º/ª/a, espaços, com ou sem barra
_RE_DESC = re.compile(
    r"(\d+)\s*[ºªoa]?\s*PARCELA\s+DO\s+(PETE|PEAE)\s*[/\-]?\s*(\d{4})?",
    re.I,
)

PROGRAMAS = ("PETE", "PEAE")


def parse_descricao(descricao: str) -> dict:
    """
    Faz o parsing da descrição. Devolve:
      {ok, programa, parcela, complemento, ano}
    `ok=False` quando a descrição não bate no padrão (precisa de revisão manual).
    """
    txt = sem_acento(descricao or "")
    m = _RE_DESC.search(txt)
    if not m:
        # ainda assim tenta detectar o programa solto p/ orientar a revisão
        prog = next((p for p in PROGRAMAS if p in txt), "")
        return {"ok": False, "programa": prog, "parcela": None,
                "complemento": "COMPLEMENTO" in txt, "ano": None}

    return {
        "ok": True,
        "programa": m.group(2).upper(),
        "parcela": int(m.group(1)),
        "complemento": "COMPLEMENTO" in txt,
        "ano": int(m.group(3)) if m.group(3) else None,
    }


def classificar(registro: dict, descricao: str,
                dic: DicionarioMunicipios) -> dict:
    """
    Junta um registro de OB (de `leitura.ler_relatorio_ob`) com a descrição
    capturada e o dicionário de municípios, produzindo um lançamento parcial
    (ainda SEM o tipo NORMAL/EXTRA e SEM o flag de anomalia).

    `revisao` já vem True quando: descrição fora do padrão, programa ausente,
    ou município não encontrado no dicionário.
    """
    p = parse_descricao(descricao)
    cnpj, municipio = dic.resolver(registro.get("credor", ""))

    motivos = []
    if not p["ok"]:
        motivos.append("descrição fora do padrão")
    if not p["programa"]:
        motivos.append("programa (PETE/PEAE) não identificado")
    if not dic.nome_por_cnpj(cnpj):
        motivos.append("município/CNPJ fora do dicionário")

    return {
        "ob":          registro.get("ob", ""),
        "processo":    registro.get("processo", ""),
        "status_ob":   registro.get("situacao", ""),
        "data_pagamento": registro.get("data", ""),
        "valor":       registro.get("valor"),
        "objeto":      registro.get("fonte", ""),
        "credor":      registro.get("credor", ""),
        "cnpj":        cnpj,
        "municipio":   municipio,
        "programa":    p["programa"],
        "parcela":     p["parcela"],
        "complemento": p["complemento"],
        "descricao":   (descricao or "").strip(),
        "revisao":     bool(motivos),
        "motivo_revisao": "; ".join(motivos),
    }


def eh_pete_peae(descricao: str) -> bool:
    """True se a descrição menciona PETE ou PEAE (filtro de entrada)."""
    txt = sem_acento(descricao or "")
    return any(p in txt for p in PROGRAMAS)
