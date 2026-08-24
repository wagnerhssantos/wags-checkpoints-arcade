#!/usr/bin/env python3
"""
Gera data/scoreboard.json para o site WAGS CHECKPOINTS.

Fontes:
- Databricks (usr.csinnovation.csiagentsmetricsoficial) via Statement Execution API.
- Google Sheets "Central de Inteligencia de CSI 2026" (Qualidade, Reclamacoes, Erros Ops)
  e a planilha "Base Faisca" (WoWs), via Google Sheets API v4 com service account.

Secrets/variaveis de ambiente esperadas (configuradas como GitHub Secrets):
  DATABRICKS_HOST           ex: adb-xxxx.azuredatabricks.net (sem https://)
  DATABRICKS_TOKEN          personal access token ou service principal token
  DATABRICKS_WAREHOUSE_ID   id do SQL warehouse a usar
  GOOGLE_SERVICE_ACCOUNT_JSON   conteudo JSON da service account (precisa ter
                                 acesso de leitor nas planilhas abaixo -
                                 compartilhe as planilhas com o client_email dela)
  XFORCE_EMAIL              email do xforce a filtrar (default: wagner.santos@nubank.com.br)
"""
import os
import json
import time
import datetime
import urllib.request

XFORCE = os.environ.get("XFORCE_EMAIL", "wagner.santos@nubank.com.br")
SHEET_ID = "138NRJQ7HMBG5x2UJ-eTViXErqE_0jp72DUpIkjTLmI4"
WOW_SHEET_ID = "1cUC_rv2mR5F3KmYSt9MP5qsZSRTjITyumDsuP6c6azs"

DATABRICKS_HOST = os.environ.get("DATABRICKS_HOST")
DATABRICKS_TOKEN = os.environ.get("DATABRICKS_TOKEN")
DATABRICKS_WAREHOUSE_ID = os.environ.get("DATABRICKS_WAREHOUSE_ID")


def databricks_query(sql):
    url = f"https://{DATABRICKS_HOST}/api/2.0/sql/statements"
    payload = {
        "warehouse_id": DATABRICKS_WAREHOUSE_ID,
        "statement": sql,
        "wait_timeout": "30s",
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={
            "Authorization": f"Bearer {DATABRICKS_TOKEN}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read())

    statement_id = data["statement_id"]
    while data["status"]["state"] in ("PENDING", "RUNNING"):
        time.sleep(2)
        poll_req = urllib.request.Request(
            f"https://{DATABRICKS_HOST}/api/2.0/sql/statements/{statement_id}",
            headers={"Authorization": f"Bearer {DATABRICKS_TOKEN}"},
        )
        with urllib.request.urlopen(poll_req) as resp:
            data = json.loads(resp.read())

    if data["status"]["state"] != "SUCCEEDED":
        raise RuntimeError(f"Databricks query failed: {data['status']}")

    cols = [c["name"] for c in data["manifest"]["schema"]["columns"]]
    rows = []
    for r in data.get("result", {}).get("data_array", []):
        rows.append(dict(zip(cols, r)))
    return rows


def sheets_service():
    from google.oauth2 import service_account
    from googleapiclient.discovery import build

    info = json.loads(os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"])
    creds = service_account.Credentials.from_service_account_info(
        info, scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"]
    )
    return build("sheets", "v4", credentials=creds)


def fetch_range(service, spreadsheet_id, rng):
    result = (
        service.spreadsheets()
        .values()
        .get(spreadsheetId=spreadsheet_id, range=rng)
        .execute()
    )
    return result.get("values", [])


def mmyy(iso_month):
    y, m, _ = iso_month.split("-")
    return f"{m}/{y[2:]}"


def to_yyyymm(iso_month):
    return iso_month[:7]


def compute_month(agent, month, months, rows_by_agent, incidents, wow_counts):
    row = rows_by_agent.get((agent, month))
    if not row:
        return None
    idx = months.index(month)
    prev_iso = months[idx - 1] if idx > 0 else None
    prev_row = rows_by_agent.get((agent, prev_iso)) if prev_iso else None

    mm = mmyy(month)
    incident_count = incidents.get((agent, mm), 0)
    clean = incident_count == 0
    prev_clean = True
    if prev_row:
        prev_mm = mmyy(prev_iso)
        prev_clean = incidents.get((agent, prev_mm), 0) == 0

    ymm = to_yyyymm(month)
    wow = wow_counts.get((agent, ymm), 0)

    ever_topped_before = any(
        a == agent and m < month and r.get("scoreLevel") == "Top"
        for (a, m), r in rows_by_agent.items()
    )
    prev_adher_ok = prev_row and prev_row.get("adherence") is not None and prev_row["adherence"] > 0.85
    prev_high_or_top = prev_row and prev_row.get("scoreLevel") in ("Top", "High")

    pts = 0
    flags = {}
    if clean:
        pts += 15 if prev_clean else 10
        flags["excelencia"] = True
    if row.get("adherence") is not None and row["adherence"] > 0.85:
        pts += 15 if prev_adher_ok else 10
        flags["aderencia"] = True
    if row.get("tnpsChat") is not None and row["tnpsChat"] > 82:
        pts += 20
        flags["tnpsChat"] = True
    if row.get("tnpsPhone") is not None and row["tnpsPhone"] > 85:
        pts += 20
        flags["tnpsPhone"] = True
    if row.get("scoreLevel") == "Top":
        pts += 50
        flags["top"] = True
        if prev_high_or_top:
            pts += 15
        if not ever_topped_before:
            pts += 100
            flags["primeiroTop"] = True
    elif row.get("scoreLevel") == "High":
        pts += 30
        flags["high"] = True
        if prev_high_or_top:
            pts += 15
    if wow >= 3:
        pts += 40 + (wow - 3) * 10
        flags["chama"] = True
        flags["wowCount"] = wow

    boss_eligible = (
        row.get("scoreLevel") == "Top"
        and row.get("tnpsChat") is not None and row["tnpsChat"] > 82
        and row.get("tnpsPhone") is not None and row["tnpsPhone"] > 85
    )
    return {
        "pts": pts,
        "flags": flags,
        "bossEligible": boss_eligible,
        "scoreLevel": row.get("scoreLevel"),
        "tnpsChat": row.get("tnpsChat"),
        "tnpsPhone": row.get("tnpsPhone"),
        "adherence": row.get("adherence"),
    }


def main():
    db_rows_raw = databricks_query(
        "SELECT agent, month, scoreLevel, tnpsChat, tnpsPhone, adherence "
        "FROM usr.csinnovation.csiagentsmetricsoficial "
        f"WHERE xforce = '{XFORCE}' ORDER BY agent, month"
    )

    rows_by_agent = {}
    for r in db_rows_raw:
        agent = r["agent"].split("@")[0]
        month = r["month"]
        rows_by_agent[(agent, month)] = {
            "scoreLevel": r.get("scoreLevel"),
            "tnpsChat": float(r["tnpsChat"]) if r.get("tnpsChat") not in (None, "") else None,
            "tnpsPhone": float(r["tnpsPhone"]) if r.get("tnpsPhone") not in (None, "") else None,
            "adherence": float(r["adherence"]) if r.get("adherence") not in (None, "") else None,
        }

    months = sorted({m for (_, m) in rows_by_agent.keys()})
    cur_month = months[-1]
    prev_month = months[-2] if len(months) > 1 else None
    roster = sorted({a for (a, m) in rows_by_agent.keys() if m in (cur_month, prev_month)})

    incidents = {}
    wow_counts = {}

    try:
        svc = sheets_service()

        def add_incident_rows(values):
            for row in values:
                if len(row) < 4:
                    continue
                month_col, _week, _ticket, xmart = row[0], row[1], row[2], row[3]
                if month_col in ("Mes", "Mês"):
                    continue
                agent = xmart.split("@")[0].strip()
                if agent not in roster:
                    continue
                if month_col not in (mmyy(cur_month), mmyy(prev_month) if prev_month else None):
                    continue
                incidents[(agent, month_col)] = incidents.get((agent, month_col), 0) + 1

        add_incident_rows(fetch_range(svc, SHEET_ID, "'4. Qualidade'!B1:E2000"))
        add_incident_rows(fetch_range(svc, SHEET_ID, "'5. Reclamações.'!B1:E2000"))

        e_col = fetch_range(svc, SHEET_ID, "'6. Erros Ops (Vigente)'!E1:E2000")
        m_col = fetch_range(svc, SHEET_ID, "'6. Erros Ops (Vigente)'!M1:M2000")
        for e_row, m_row in zip(e_col, m_col):
            if not e_row or not m_row:
                continue
            agent = e_row[0].split("@")[0].strip() if e_row[0] else None
            month_col = m_row[0]
            if not agent or agent not in roster:
                continue
            if month_col not in (mmyy(cur_month), mmyy(prev_month) if prev_month else None):
                continue
            incidents[(agent, month_col)] = incidents.get((agent, month_col), 0) + 1

        wow_rows = fetch_range(svc, WOW_SHEET_ID, "'(Automatização) WoWs Faísca'!A2:B5000")
        for row in wow_rows:
            if len(row) < 2:
                continue
            ts, email = row[0], row[1]
            agent = email.split("@")[0].strip()
            if agent not in roster:
                continue
            ym = ts[:7]
            if ym not in (to_yyyymm(cur_month), to_yyyymm(prev_month) if prev_month else None):
                continue
            wow_counts[(agent, ym)] = wow_counts.get((agent, ym), 0) + 1
    except Exception as e:
        print(f"aviso: nao consegui ler Google Sheets ({e}); seguindo so com Databricks")

    results = []
    for agent in roster:
        cur = compute_month(agent, cur_month, months, rows_by_agent, incidents, wow_counts)
        prev = compute_month(agent, prev_month, months, rows_by_agent, incidents, wow_counts) if prev_month else None
        total = (cur["pts"] if cur else 0) + (prev["pts"] if prev else 0)
        results.append({"agent": agent, "total": total, "cur": cur, "prev": prev})

    results.sort(key=lambda r: -r["total"])

    out = {
        "curMonth": cur_month,
        "prevMonth": prev_month,
        "results": results,
        "generatedAt": datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
    }

    os.makedirs("data", exist_ok=True)
    with open("data/scoreboard.json", "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    print("data/scoreboard.json atualizado.")


if __name__ == "__main__":
    main()
