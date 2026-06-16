# -*- coding: utf-8 -*-
"""
Gera dados SINTÉTICOS para a demo do projeto (portfólio).

Tudo aqui é FICTÍCIO: valores, números de OB, processos e datas são aleatórios.
A única referência real é a lista PÚBLICA de municípios/CNPJ (data/municipios.csv) —
CNPJ de prefeitura é informação pública. Nenhum dado operacional real é usado.

Saída: exemplos/seed_exemplo.csv (mesmo formato do export "Página2"), pronto para
importar na aba Configurações → "Recarregar razão inicial (seed)".

Uso:  python exemplos/gerar_dados_fake.py
"""
import csv
import random
from datetime import date, timedelta
from pathlib import Path

random.seed(42)  # reprodutível

BASE = Path(__file__).resolve().parent.parent
MUNICIPIOS = BASE / "data" / "municipios.csv"
SAIDA = BASE / "exemplos" / "seed_exemplo.csv"

CAB = ["PROCESSO", "OB", "STATUS OB", "DATA DE PAGAMENTO", "", "VALOR", "OBJETO",
       "CREDOR", "DESCRIÇÃO", "CATEGORIA", "MUNICÍPIO", "PARCELA", "CAT_MUN"]

DATAS = [date(2026, 3, 19), date(2026, 4, 16), date(2026, 5, 20), date(2026, 6, 10)]


def brl(v):
    return "R$ " + f"{v:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")


def main():
    with open(MUNICIPIOS, encoding="utf-8") as f:
        muns = [(r["cnpj"], r["municipio"]) for r in csv.DictReader(f)]
    muns = random.sample(muns, 40)  # 40 municípios fictícios na demo

    seq = 5000
    linhas = [CAB]

    def nova(cnpj, nome, prog, parcela, dt, valor, status="ENVIADO", compl=False):
        nonlocal seq
        seq += 1
        ob = f"2026160101OB{seq:05d}"
        proc = f"2026{random.randint(1000000, 9999999)}"
        desc = f"{parcela}ª PARCELA DO {prog}/2026" + (" (COMPLEMENTO)" if compl else "")
        credor = f"PREFEITURA MUNICIPAL DE {nome} - {cnpj}"
        cat_mun = prog + nome
        linhas.append([proc, ob, status, dt.strftime("%d/%m/%Y"), "",
                       brl(valor), "", credor, desc, prog, nome, parcela, cat_mun])

    for cnpj, nome in muns:
        base_pete = random.randint(5_000, 900_000)
        for p in range(1, random.randint(2, 5)):           # PETE: 1..(1-4) parcelas
            nova(cnpj, nome, "PETE", p, DATAS[p - 1], base_pete)
        base_peae = random.randint(20_000, 300_000)
        for p in range(1, random.randint(2, 4)):           # PEAE: 1..(1-3) parcelas
            nova(cnpj, nome, "PEAE", p, DATAS[p - 1], base_peae)

    # casos especiais para demonstrar recursos do sistema:
    c0, n0 = muns[0]
    nova(c0, n0, "PETE", 2, DATAS[1], 45_000.00, compl=True)        # complemento
    c1, n1 = muns[1]
    nova(c1, n1, "PETE", 1, DATAS[0], 88_000.00)                    # 1ª OB normal
    nova(c1, n1, "PETE", 1, DATAS[1], 88_000.00)                    # 2ª OB normal -> ANOMALIA
    c2, n2 = muns[2]
    nova(c2, n2, "PEAE", 1, DATAS[0], 70_000.00, status="ANULADO")  # anulada -> descartada

    SAIDA.parent.mkdir(exist_ok=True)
    with open(SAIDA, "w", encoding="utf-8-sig", newline="") as f:
        csv.writer(f).writerows(linhas)
    print(f"Gerado: {SAIDA}  ({len(linhas) - 1} lançamentos fictícios)")


if __name__ == "__main__":
    main()
