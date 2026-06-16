# -*- coding: utf-8 -*-
"""
Sincronização com o Google Sheets (Página1 = espelho do razão).

Autenticação por CONTA DE SERVIÇO (service account): um JSON de credenciais fica
em secrets/google_service_account.json e a planilha de destino é compartilhada
(Editor) com o e-mail da conta de serviço. Sem login interativo — serve local e,
no futuro, no servidor.

Faz um "full refresh": limpa a Página1 e regrava cabeçalho + todo o razão atual,
de forma que a planilha sempre reflita a base. Sem dependência de Streamlit.
"""
import json
from pathlib import Path

from store.db import data_br

_BASE = Path(__file__).resolve().parent.parent
CREDS_PATH = _BASE / "secrets" / "google_service_account.json"
_CONFIG = _BASE / "data" / "gsheet.json"

# ID da planilha de destino — fica em data/gsheet.json (fora do versionamento).
# Em branco aqui de propósito: o ID real é definido na aba Configurações do app.
DEFAULT_SHEET_ID = ""
ABA = "Página1"

CABECALHO = ["PROCESSO", "OB", "STATUS OB", "DATA DE PAGAMENTO", "", "VALOR",
             "OBJETO", "CREDOR", "DESCRIÇÃO", "CATEGORIA", "MUNICÍPIO", "PARCELA"]


# ── configuração (persistida em disco) ────────────────────────────────────────
def _load() -> dict:
    try:
        return json.loads(_CONFIG.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save(cfg: dict) -> None:
    _CONFIG.parent.mkdir(parents=True, exist_ok=True)
    _CONFIG.write_text(json.dumps(cfg, ensure_ascii=False), encoding="utf-8")


def get_sheet_id() -> str:
    return _load().get("sheet_id") or DEFAULT_SHEET_ID


def set_sheet_id(sheet_id: str) -> None:
    cfg = _load(); cfg["sheet_id"] = sheet_id.strip(); _save(cfg)


def get_auto_sync() -> bool:
    return bool(_load().get("auto_sync"))


def set_auto_sync(valor: bool) -> None:
    cfg = _load(); cfg["auto_sync"] = bool(valor); _save(cfg)


def credenciais_ok() -> bool:
    return CREDS_PATH.exists()


def email_conta_servico() -> str:
    """Lê o client_email do JSON (para o usuário saber com quem compartilhar)."""
    try:
        return json.loads(CREDS_PATH.read_text(encoding="utf-8")).get("client_email", "")
    except Exception:
        return ""


# ── escrita ───────────────────────────────────────────────────────────────────
def _linha(l: dict) -> list:
    """Converte um lançamento do razão para a linha da Página1 (12 colunas)."""
    return [
        l.get("processo", ""),
        l.get("ob", ""),
        l.get("status_ob", ""),
        data_br(l.get("data_pagamento", "")),
        "",                              # coluna em branco (layout da planilha)
        l.get("valor"),                  # número → permite SOMA/SUMIFS na planilha
        l.get("objeto", ""),
        l.get("credor", ""),
        l.get("descricao", ""),
        l.get("programa", ""),           # CATEGORIA
        l.get("municipio", ""),
        l.get("parcela"),
    ]


def atualizar_pagina1(lancamentos: list[dict], sheet_id: str | None = None) -> dict:
    """
    Full refresh da Página1: limpa e regrava cabeçalho + todos os lançamentos.
    Devolve {linhas, sheet_id, url}. Lança exceção com mensagem clara em caso de erro.
    """
    import gspread

    if not credenciais_ok():
        raise RuntimeError(
            "Credenciais do Google não encontradas. Coloque o JSON da conta de "
            f"serviço em: {CREDS_PATH}")

    sheet_id = (sheet_id or get_sheet_id()).strip()
    gc = gspread.service_account(filename=str(CREDS_PATH))
    try:
        sh = gc.open_by_key(sheet_id)
    except Exception as e:
        raise RuntimeError(
            f"Não consegui abrir a planilha. Confirme o ID e se ela foi compartilhada "
            f"(Editor) com {email_conta_servico() or 'a conta de serviço'}. Detalhe: {e}")

    try:
        ws = sh.worksheet(ABA)
    except gspread.WorksheetNotFound:
        ws = sh.add_worksheet(title=ABA, rows=max(len(lancamentos) + 10, 100), cols=12)

    valores = [CABECALHO]
    for l in sorted(lancamentos, key=lambda x: (x.get("data_pagamento", ""),
                                                x.get("municipio", ""),
                                                x.get("programa", ""),
                                                x.get("parcela") or 0)):
        valores.append(_linha(l))

    ws.clear()
    ws.update(values=valores, range_name="A1", value_input_option="USER_ENTERED")

    # VALOR (coluna F) como número com formato de moeda: exibe "R$ 428.264,70"
    # mas continua sendo número (permite SOMA/SUMIFS nos painéis).
    n = len(valores)
    if n > 1:
        try:
            ws.format(f"F2:F{n}", {"numberFormat": {"type": "NUMBER",
                                                    "pattern": "R$ #,##0.00"}})
            ws.format("A1:L1", {"textFormat": {"bold": True}})
        except Exception:
            pass  # formatação é cosmética; não falha a sincronização por causa dela

    return {"linhas": len(lancamentos), "sheet_id": sheet_id,
            "url": f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit"}
