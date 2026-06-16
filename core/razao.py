# -*- coding: utf-8 -*-
"""
Regras do razão: definição do tipo de cada lançamento e montagem da grade
(município × parcelas) usada nos PDFs.

Tipo de um lançamento dentro de um (cnpj, programa, parcela):
  • COMPLEMENTO  — descrição traz "(COMPLEMENTO)"; é uma parcela extra (não soma)
  • NORMAL       — primeiro pagamento normal daquela parcela
  • EXTRA        — 2º pagamento NORMAL na mesma parcela → ANOMALIA: marca
                   `revisao` para conferência com a equipe de pagamento.

Sem dependência de Streamlit.
"""

# ordem das "faixas" de coluna na grade, dado um mesmo número de parcela
_ORDEM_TIPO = {"NORMAL": 0, "EXTRA": 1, "COMPLEMENTO": 2}


def definir_tipos(lancamentos: list[dict],
                  chaves_normais_existentes: set[tuple] | None = None) -> list[dict]:
    """
    Atribui `tipo` a cada lançamento (mutando uma cópia) considerando o que já
    existe no razão (`chaves_normais_existentes` = set de (cnpj,programa,parcela)
    com NORMAL) e os lançamentos anteriores do próprio lote.

    Preserva qualquer `revisao` que a classificação já tenha marcado
    (descrição fora do padrão, município fora do dicionário, etc.).
    """
    normais = set(chaves_normais_existentes or set())
    saida = []
    for orig in lancamentos:
        l = dict(orig)
        chave = (l.get("cnpj", ""), l.get("programa", ""), l.get("parcela"))

        if l.get("parcela") is None or not l.get("programa"):
            # sem parcela/programa resolvidos: não dá p/ tipar; já está em revisão
            l["tipo"] = ""
            l["revisao"] = True
        elif l.get("complemento"):
            l["tipo"] = "COMPLEMENTO"
        elif chave in normais:
            l["tipo"] = "EXTRA"
            l["revisao"] = True
            motivo = l.get("motivo_revisao", "")
            extra = "2ª OB normal na mesma parcela — conferir com a equipe de pagamento"
            l["motivo_revisao"] = (motivo + "; " + extra).lstrip("; ") if motivo else extra
        else:
            l["tipo"] = "NORMAL"
            normais.add(chave)

        saida.append(l)
    return saida


def rotulo_coluna(parcela: int, tipo: str) -> str:
    """Rótulo de coluna da grade. Ex.: (1,'NORMAL')->'1ª PARC'; (2,'COMPLEMENTO')->'2ª COMPL'."""
    sufixo = {"NORMAL": "PARC", "EXTRA": "EXTRA", "COMPLEMENTO": "COMPL"}.get(tipo, "PARC")
    return f"{parcela}ª {sufixo}"


def montar_grade(lancamentos: list[dict]) -> dict:
    """
    Monta a grade de um conjunto de lançamentos (já de um único programa).

    Devolve:
      {
        "colunas": [(parcela, tipo, rotulo), ...]  # ordenadas
        "linhas":  [{"municipio": str, "valores": {col_id: valor}, "total": float}, ...]
        "total_geral": float,
      }
    onde col_id = (parcela, tipo). Valores NÃO são somados entre parcelas
    distintas; só se houver, excepcionalmente, mais de uma OB na mesma célula
    (mesmo município+parcela+tipo) elas se somam.
    """
    colunas_set: set[tuple] = set()
    por_mun: dict[str, dict] = {}

    for l in lancamentos:
        parc, tipo, mun = l.get("parcela"), l.get("tipo"), l.get("municipio", "")
        valor = l.get("valor") or 0.0
        if parc is None or not tipo:
            continue
        col_id = (parc, tipo)
        colunas_set.add(col_id)
        cel = por_mun.setdefault(mun, {})
        cel[col_id] = round(cel.get(col_id, 0.0) + float(valor), 2)

    colunas = sorted(colunas_set, key=lambda c: (c[0], _ORDEM_TIPO.get(c[1], 9)))
    colunas_meta = [(p, t, rotulo_coluna(p, t)) for p, t in colunas]

    linhas = []
    for mun in sorted(por_mun):
        valores = por_mun[mun]
        total = round(sum(valores.values()), 2)
        linhas.append({"municipio": mun, "valores": valores, "total": total})

    total_geral = round(sum(lin["total"] for lin in linhas), 2)
    return {"colunas": colunas_meta, "linhas": linhas, "total_geral": total_geral}


def grade_consolidada(lancamentos: list[dict]) -> dict:
    """
    Grade compacta para o PDF (cabe em A4 paisagem mesmo com 10 parcelas):
      colunas = 1ª PARC … Nª PARC  +  uma única COMPL.  (sem colunas por parcela)

    • PARC = valor do lançamento NORMAL daquela parcela.
    • COMPL. = soma de TODOS os complementos do município (uma coluna só).
    • EXTRA (anomalias) NÃO entra no relatório — fica na aba Razão p/ conferência.

    Devolve {colunas:[(key,rotulo)], linhas:[{municipio,valores{key},total}], total_geral}
    onde key é ("P", n) para parcela e "C" para complemento.
    """
    max_parc = 0
    tem_compl = False
    por_mun: dict[str, dict] = {}

    for l in lancamentos:
        parc, tipo, mun = l.get("parcela"), l.get("tipo"), l.get("municipio", "")
        valor = float(l.get("valor") or 0.0)
        if parc is None or not tipo:
            continue
        cel = por_mun.setdefault(mun, {})
        if tipo == "COMPLEMENTO":
            cel["C"] = round(cel.get("C", 0.0) + valor, 2)
            tem_compl = True
        elif tipo == "NORMAL":
            cel[("P", parc)] = round(cel.get(("P", parc), 0.0) + valor, 2)
            max_parc = max(max_parc, parc)
        # EXTRA é ignorado de propósito (anomalia)

    colunas = [(("P", k), f"{k}ª PARC") for k in range(1, max_parc + 1)]
    if tem_compl:
        colunas.append(("C", "COMPL."))

    linhas = []
    for mun in sorted(por_mun):
        valores = por_mun[mun]
        total = round(sum(valores.values()), 2)
        linhas.append({"municipio": mun, "valores": valores, "total": total})

    total_geral = round(sum(lin["total"] for lin in linhas), 2)
    return {"colunas": colunas, "linhas": linhas, "total_geral": total_geral}
