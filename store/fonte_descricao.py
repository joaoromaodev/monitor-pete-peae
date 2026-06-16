# -*- coding: utf-8 -*-
"""
Costura de migração: "de onde vem a descrição de uma OB".

HOJE  → bot Selenium (bot/bot_pete_peae.py), orquestrado pela UI via subprocess
        + status.json (console ao vivo). É a implementação `FonteBot`.

AMANHÃ → quando a SEFA liberar acesso ao PostgreSQL do SIAFE, basta uma nova
         implementação `FonteSQL.obter_descricoes(obs)` que faz um SELECT — o
         restante do sistema (core/*) não muda, pois só depende deste contrato.

Este módulo NÃO importa Streamlit. A orquestração do subprocess + console fica na
casca (app.py), que é a única peça descartável na migração.
"""
from typing import Protocol


class FonteDescricao(Protocol):
    """Contrato: dado um conjunto de OBs, devolve {ob: descricao}."""

    def obter_descricoes(self, obs: list[str]) -> dict[str, str]:
        ...


class FonteSQL:
    """
    Stub do futuro acesso direto ao PostgreSQL do SIAFE.
    Quando o acesso existir, implementar a query aqui e aposentar o bot.
    """

    def __init__(self, dsn: str):
        self.dsn = dsn

    def obter_descricoes(self, obs: list[str]) -> dict[str, str]:
        raise NotImplementedError(
            "Acesso direto ao SIAFE ainda não disponível — usando o bot Selenium."
        )
