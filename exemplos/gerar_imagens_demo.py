# -*- coding: utf-8 -*-
"""
Gera as imagens de demonstração do README a partir dos DADOS FICTÍCIOS
(exemplos/seed_exemplo.csv) — nunca dos dados reais.

Saídas em docs/:
  • dashboard_pete.png  — 1ª página do PDF da grade (renderizado via PyMuPDF)
  • whatsapp.png        — prévia da mensagem de WhatsApp (Pillow)

Uso:  python exemplos/gerar_imagens_demo.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # permite importar store/core

import fitz  # PyMuPDF
from PIL import Image, ImageDraw, ImageFont

from store.db import Razao, data_br
from store.seed import importar_seed
from core.razao import grade_consolidada
from core.pdf import gerar_pdf
from core.whatsapp import gerar_texto

BASE = Path(__file__).resolve().parent.parent
DOCS = BASE / "docs"
DOCS.mkdir(exist_ok=True)
SEED = BASE / "exemplos" / "seed_exemplo.csv"


def _fonte(sz, bold=False):
    nomes = (["arialbd.ttf", "DejaVuSans-Bold.ttf"] if bold
             else ["arial.ttf", "DejaVuSans.ttf"])
    for n in nomes:
        try:
            return ImageFont.truetype(n, sz)
        except Exception:
            pass
    return ImageFont.load_default()


def dashboard_png(razao):
    grade = grade_consolidada(razao.listar("PETE"))
    pdf = gerar_pdf(grade, "PETE")
    doc = fitz.open(stream=pdf, filetype="pdf")
    pix = doc[0].get_pixmap(dpi=130)
    pix.save(str(DOCS / "dashboard_pete.png"))
    doc.close()
    print("ok docs/dashboard_pete.png")


def whatsapp_png(razao):
    # escolhe uma data com lançamentos e monta o texto
    datas = razao.datas_disponiveis()
    d = datas[len(datas) // 2] if datas else datas[0]
    texto = gerar_texto(razao.do_dia(d), data_br(d))
    linhas = texto.splitlines()
    if len(linhas) > 16:
        linhas = linhas[:16] + ["…"]

    W = 720
    pad, lh = 26, 30
    H = 150 + lh * len(linhas) + 40
    img = Image.new("RGB", (W, H), (229, 221, 213))  # bege do WhatsApp
    d_ = ImageDraw.Draw(img)
    # barra superior verde
    d_.rectangle([0, 0, W, 64], fill=(7, 94, 84))
    d_.ellipse([16, 12, 56, 52], fill=(37, 211, 102))
    d_.text((70, 22), "Secretária  ·  Relatório do dia", font=_fonte(18, True), fill="white")
    # balão da mensagem
    bx0, by0, bx1, by1 = 24, 88, W - 24, H - 24
    d_.rounded_rectangle([bx0, by0, bx1, by1], radius=16, fill=(220, 248, 198))
    f = _fonte(16)
    fb = _fonte(16, True)
    y = by0 + 16
    for ln in linhas:
        bold = ln.startswith("📌") or "*" in ln
        # remove emojis (a fonte não os renderiza) só para a imagem de preview
        txt = ln
        for e in ("📌", "🚌", "🍎"):
            txt = txt.replace(e, "")
        txt = txt.replace("*", "").strip()
        d_.text((bx0 + 18, y), txt, font=(fb if bold else f), fill=(20, 30, 24))
        y += lh
    img.save(DOCS / "whatsapp.png")
    print("ok docs/whatsapp.png")


def main():
    tmp = BASE / "exemplos" / "_img_temp.db"
    if tmp.exists():
        tmp.unlink()
    razao = Razao(tmp)
    importar_seed(str(SEED), razao, substituir=True)
    try:
        dashboard_png(razao)
        whatsapp_png(razao)
    finally:
        razao.fechar()
        try:
            tmp.unlink()
        except Exception:
            pass


if __name__ == "__main__":
    main()
