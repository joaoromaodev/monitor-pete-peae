# -*- coding: utf-8 -*-
"""
Gera o PDF de grade (município × parcelas) de um programa, acumulado do ano.
Visual SEDUC-PA (Azul Pará), A4 paisagem, zebrado — irmão do sistema de Diárias.

Recebe a grade de `core.razao.montar_grade` e devolve os bytes do PDF.
Sem dependência de Streamlit.
"""
from datetime import datetime
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER

# ── paleta SEDUC-PA ───────────────────────────────────────────────────────────
AZUL        = colors.HexColor("#0071CE")   # Azul Pará
AZUL_ESCURO = colors.HexColor("#004B8C")
AZUL_CLARO  = colors.HexColor("#E3F0FB")
VERMELHO    = colors.HexColor("#EB2939")   # faixa tricolor
ZEBRA       = colors.HexColor("#F1F7FD")
BORDA       = colors.HexColor("#DDE2E9")
TEXTO       = colors.HexColor("#161C24")

_NOME_PROGRAMA = {
    "PETE": "TRANSPORTE ESCOLAR - PETE",
    "PEAE": "ALIMENTAÇÃO ESCOLAR - PEAE",
}


def brl(valor) -> str:
    """1234.5 -> 'R$ 1.234,50'. Zero vira '—' para a grade ficar limpa."""
    try:
        v = float(valor)
    except (TypeError, ValueError):
        return ""
    if abs(v) < 0.005:
        return "—"
    s = f"{v:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")
    return f"R$ {s}"


def gerar_pdf(grade: dict, programa: str, ano: int = 2026,
              data_emissao: datetime | None = None) -> bytes:
    """
    grade: saída de montar_grade (colunas/linhas/total_geral) de UM programa.
    Devolve os bytes do PDF (A4 paisagem).
    """
    data_emissao = data_emissao or datetime.now()
    nome = _NOME_PROGRAMA.get(programa, programa)
    titulo = f"VISUALIZAÇÃO DE PARCELAS DO PROGRAMA ESTADUAL DE {nome} {ano}"

    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=landscape(A4),
        leftMargin=10 * mm, rightMargin=10 * mm,
        topMargin=10 * mm, bottomMargin=10 * mm,
        title=f"Relatorio {programa} {data_emissao:%d-%m-%Y}",
    )

    st_titulo = ParagraphStyle("t", fontName="Helvetica-Bold", fontSize=13,
                               textColor=colors.white, alignment=TA_CENTER, leading=16)
    st_sub = ParagraphStyle("s", fontName="Helvetica-Oblique", fontSize=8.5,
                            textColor=colors.HexColor("#434343"), alignment=TA_CENTER)

    # cabeçalhos da tabela — grade consolidada: colunas = [(key, rotulo), ...]
    rotulos = [rot for _key, rot in grade["colunas"]]
    head = ["MUNICÍPIO"] + rotulos
    dados = [head]
    for lin in grade["linhas"]:
        linha = [lin["municipio"]]
        for (key, _rot) in grade["colunas"]:
            linha.append(brl(lin["valores"].get(key, 0.0)))
        dados.append(linha)

    # larguras: município fixo, resto divide o espaço útil
    largura_util = landscape(A4)[0] - 20 * mm
    w_mun = 52 * mm
    n = max(len(rotulos), 1)
    w_col = max((largura_util - w_mun) / n, 16 * mm)
    col_widths = [w_mun] + [w_col] * len(rotulos)

    fonte = 7 if len(rotulos) <= 8 else 6
    pad = 4 if len(rotulos) <= 8 else 2
    tabela = Table(dados, colWidths=col_widths, repeatRows=1)

    estilo = [
        ("BACKGROUND", (0, 0), (-1, 0), AZUL),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), fonte),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("ALIGN", (0, 0), (0, -1), "LEFT"),
        ("ALIGN", (1, 0), (-1, 0), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 1), (-1, -1), fonte),
        ("TEXTCOLOR", (0, 1), (-1, -1), TEXTO),
        ("GRID", (0, 0), (-1, -1), 0.4, BORDA),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), pad),
        ("RIGHTPADDING", (0, 0), (-1, -1), pad),
    ]
    for i in range(1, len(dados)):
        if i % 2 == 0:
            estilo.append(("BACKGROUND", (0, i), (-1, i), ZEBRA))
    tabela.setStyle(TableStyle(estilo))

    # faixa de título (azul) + subtítulo, como um mini-cabeçalho institucional
    faixa = Table([[Paragraph(titulo, st_titulo)]],
                  colWidths=[largura_util], rowHeights=[12 * mm])
    faixa.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), AZUL),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LINEBELOW", (0, 0), (-1, -1), 3, VERMELHO),
    ]))

    sub = Paragraph(
        f"Relatório emitido em {data_emissao:%d/%m/%Y às %H:%M:%S}  ·  "
        f"{len(grade['linhas'])} municípios  ·  total {brl(grade['total_geral'])}",
        st_sub)

    doc.build([faixa, Spacer(1, 4 * mm), sub, Spacer(1, 4 * mm), tabela])
    return buf.getvalue()
