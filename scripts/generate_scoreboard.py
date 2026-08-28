#!/usr/bin/env python3
"""
Gera data/scoreboard.json para o site UAI MODO TURBO (ex-WAGS CHECKPOINTS).

Motor de pontos v2 — considera SOMENTE o mes corrente, com granularidade
semanal para Excelencia e Aderencia, e mensal para tNPS / WoW / badges /
Skip / Unanswered Calls / Transfer indevido / Expired jobs.

Fontes:
- Databricks (usr.csinnovation.csiagentsmetricsoficial) via Statement Execution API:
  scoreLevel, tnpsChat, tnpsPhone, adherence (mensal) por agente/mes.
- Google Sheets "Central de Inteligencia de CSI 2026":
  4. Qualidade / 5. Reclamacoes (colunas Mes, Semana, CID, Xmart) e
  6. Erros Ops (Vigente) (coluna E = analista, L = Semana, M = Mes).
- Planilha "Base Faisca" (WoWs), timestamp + email do Xmart.

- Skip / Transfer indevido / Expired: `etl.br__dataset.cx_canonical_activities`
  (colunas `agent`, `status`, `is_transfer_indevido`), filtrado por
  `actor_affiliation = 'nubank'` e mes corrente. Resultado FINAL do mes
  (nao ha streak semanal para essas 4 metricas).
- Unanswered Calls: `usr.cx_golden_layer.unanswered_calls` (colunas
  `queue_event__actor`, `ringing`, `no_answer`), so se aplica a quem atua
  no canal phone -- quem nao tem nenhuma linha nessa tabela no mes fica
  marcado como "sem canal" e nao pontua nem penaliza nessa metrica.

LIMITACOES CONHECIDAS (documentadas tambem no README):
- Ainda nao ha fonte semanal de aderencia ao fone para o Time Wags
  (view_aderencia_final e outras tabelas do cx_golden_layer nao cobrem
  esse squad). Por isso a Aderencia usa o % MENSAL do Databricks repetido
  nas 4 semanas do mes, com o mesmo streak (10/15/20/25).
- O alinhamento de linha da aba "6. Erros Ops (Vigente)" e ocasionalmente
  instavel; quando isso acontece, o incidente e atribuido a semana mais
  proxima com evidencia (fail-soft), igual ja acontecia na v1.

Secrets/variaveis de ambiente esperadas (GitHub Secrets):
  DATABRICKS_HOST, DATABRICKS_TOKEN, DATABRICKS_WAREHOUSE_ID,
  GOOGLE_SERVICE_ACCOUNT_JSON, XFORCE_EMAIL (default wagner.santos@nubank.com.br)
"""
import os
import json
import time
import datetime
import calendar
import urllib.request

XFORCE = os.environ.get("XFORCE_EMAIL", "wagner.santos@nubank.com.br")
SHEET_ID = "138NRJQ7HMBG5x2UJ-eTViXErqE_0jp72DUpIkjTLmI4"
WOW_SHEET_ID = "1cUC_rv2mR5F3KmYSt9MP5qsZSRTjITyumDsuP6c6azs"

DATABRICKS_HOST = os.environ.get("DATABRICKS_HOST")
DATABRICKS_TOKEN = os.environ.get("DATABRICKS_TOKEN")
DATABRICKS_WAREHOUSE_ID = os.environ.get("DATABRICKS_WAREHOUSE_ID")

# Faixas de pontos de tNPS (media chat+phone do mes)
TNPS_BANDS = [(90, 50), (82, 20), (75, 10)]
TNPS_NO_CHANNEL_PTS = 20  # se o agente nao atua em chat/phone e esta limpo de qualidade
STREAK_PTS = [10, 15, 20, 25]  # semana 1,2,3,4+ (cap)
ADERENCIA_THRESHOLD = 0.85
BOSS_CHAT_THRESHOLD = 82
BOSS_PHONE_THRESHOLD = 85
LEVELS = [(180, "DIAMANTE"), (120, "OURO"), (80, "PRATA"), (0, "BRONZE")]


def tiered_points(pct, bands):
    """bands: lista de (limite, pts) em ordem do mais restrito pro mais frouxo,
    seguida opcionalmente de (limite_penalidade, pts_penalidade) com pts negativo."""
    for limit, pts in bands:
        if pts > 0 and pct < limit:
            return pts
    for limit, pts in bands:
        if pts < 0 and pct > limit:
            return pts
    return 0


def databricks_query(sql):
    url = f"https://{DATABRICKS_HOST}/api/2.0/sql/statements"
    payload = {"warehouse_id": DATABRICKS_WAREHOUSE_ID, "statement": sql, "wait_timeout": "30s"}
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode(),
        headers={"Authorization": f"Bearer {DATABRICKS_TOKEN}", "Content-Type": "application/json"},
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
    result = service.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range=rng).execute()
    return result.get("values", [])


def mmyy(iso_month):
    y, m, _ = iso_month.split("-")
    return f"{m}/{y[2:]}"


def week_number(date):
    """ISO-ish week number within the year, matching the 'Semana N' convention used in the sheets."""
    return date.isocalendar()[1]


def weeks_of_month(year, month):
    """Lista de (week_number, week_start_date) que tocam o mes/ano dado."""
    first = datetime.date(year, month, 1)
    last_day = calendar.monthrange(year, month)[1]
    last = datetime.date(year, month, last_day)
    weeks = []
    seen = set()
    d = first
    while d <= last:
        wn = week_number(d)
        if wn not in seen:
            seen.add(wn)
            weeks.append(wn)
        d += datetime.timedelta(days=1)
    return weeks


def tnps_points(chat, phone, clean_month):
    if chat is None and phone is None:
        return (None, TNPS_NO_CHANNEL_PTS if clean_month else 0, True)
    vals = [v for v in (chat, phone) if v is not None]
    avg = sum(vals) / len(vals)
    pts = 0
    for threshold, p in TNPS_BANDS:
        if avg > threshold:
            pts = p
            break
    return (avg, pts, False)


def level_of(total):
    for threshold, label in LEVELS:
        if total >= threshold:
            return label
    return "BRONZE"


def main():
    today = datetime.date.today()
    cur_month_iso = today.strftime("%Y-%m-01")
    month_label = mmyy(cur_month_iso)
    weeks = weeks_of_month(today.year, today.month)

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
    months_sorted = sorted({m for (_a, m) in rows_by_agent.keys()})
    roster = sorted({a for (a, m) in rows_by_agent.keys() if m == cur_month_iso})
    roster_emails = [f"{a}@nubank.com.br" for a in roster]

    month_start = cur_month_iso
    month_end = today.strftime("%Y-%m-%d")
    email_list_sql = ",".join(f"'{e}'" for e in roster_emails)

    ops_rows = databricks_query(
        "SELECT agent, COUNT(dist_key) AS total_interactions, "
        "SUM(CASE WHEN status = 'skipped' THEN 1 ELSE 0 END) AS skipped, "
        "SUM(CASE WHEN is_transfer_indevido = 1 THEN 1 ELSE 0 END) AS transfer_indevido, "
        "SUM(CASE WHEN status = 'expired' THEN 1 ELSE 0 END) AS expired "
        "FROM etl.br__dataset.cx_canonical_activities "
        f"WHERE DATE(local_start_time) BETWEEN '{month_start}' AND '{month_end}' "
        "AND actor_affiliation = 'nubank' AND source_id NOT LIKE '%lineu%' "
        "AND NOT (activity_type IN ('email','backoffice') AND status = 'expired') "
        "AND activity_type IN ('chat','email','inbound_call','backoffice') "
        f"AND agent IN ({email_list_sql}) GROUP BY agent"
    )
    ops_by_agent = {}
    for r in ops_rows:
        agent = r["agent"].split("@")[0]
        total = int(r["total_interactions"] or 0)
        ops_by_agent[agent] = {
            "skip_pct": round(int(r["skipped"] or 0) * 100.0 / total, 2) if total else None,
            "transfer_pct": round(int(r["transfer_indevido"] or 0) * 100.0 / total, 2) if total else None,
            "expired_pct": round(int(r["expired"] or 0) * 100.0 / total, 2) if total else None,
        }

    unanswered_rows = databricks_query(
        "SELECT queue_event__actor AS agent, SUM(ringing) AS ringing, SUM(no_answer) AS no_answer "
        "FROM usr.cx_golden_layer.unanswered_calls "
        f"WHERE local_event_date BETWEEN '{month_start}' AND '{month_end}' "
        f"AND queue_event__actor IN ({email_list_sql}) GROUP BY queue_event__actor"
    )
    unanswered_by_agent = {}
    for r in unanswered_rows:
        agent = r["agent"].split("@")[0]
        ringing = int(r["ringing"] or 0)
        unanswered_by_agent[agent] = round(int(r["no_answer"] or 0) * 100.0 / ringing, 2) if ringing else None

    # incidentes por (agent, "Semana N") -- Qualidade + Reclamacoes + Erros Ops
    incidents_by_week = {}

    def mark_incident(agent, week_label):
        incidents_by_week.setdefault(agent, set()).add(week_label)

    try:
        svc = sheets_service()

        def scan_incident_rows(values):
            for row in values:
                if len(row) < 4:
                    continue
                month_col, week_col, _cid, xmart = row[0], row[1], row[2], row[3]
                if month_col in ("Mes", "Mês"):
                    continue
                if month_col != month_label:
                    continue
                agent = xmart.split("@")[0].strip()
                if agent not in roster:
                    continue
                mark_incident(agent, week_col)

        scan_incident_rows(fetch_range(svc, SHEET_ID, "'4. Qualidade'!B1:E2000"))
        scan_incident_rows(fetch_range(svc, SHEET_ID, "'5. Reclamações.'!B1:E2000"))

        # Erros Ops: E=analista, L=Semana, M=Mes (colunas nao contiguas -> combinado E:M)
        eo_rows = fetch_range(svc, SHEET_ID, "'6. Erros Ops (Vigente)'!E1:M2000")
        for row in eo_rows:
            if len(row) < 9:
                continue
            analyst_email = row[0]
            week_col = row[7] if len(row) > 7 else None
            mon_col = row[8] if len(row) > 8 else None
            if not analyst_email or mon_col != month_label:
                continue
            agent = analyst_email.split("@")[0].strip()
            if agent not in roster:
                continue
            mark_incident(agent, week_col or f"Semana {weeks[-1]}")

        wow_rows = fetch_range(svc, WOW_SHEET_ID, "'(Automatização) WoWs Faísca'!A2:B5000")
        wow_by_week = {}
        wow_total = {}
        for row in wow_rows:
            if len(row) < 2:
                continue
            ts, email = row[0], row[1]
            agent = email.split("@")[0].strip()
            if agent not in roster:
                continue
            try:
                d = datetime.datetime.strptime(ts[:10], "%Y-%m-%d").date()
            except ValueError:
                continue
            if d.strftime("%Y-%m") != cur_month_iso[:7]:
                continue
            wn = week_number(d)
            wow_by_week[(agent, wn)] = wow_by_week.get((agent, wn), 0) + 1
            wow_total[agent] = wow_total.get(agent, 0) + 1
    except Exception as e:
        print(f"aviso: nao consegui ler Google Sheets ({e}); seguindo so com Databricks")
        wow_total = {}

    results = []
    for agent in roster:
        row = rows_by_agent.get((agent, cur_month_iso), {})
        clean_weeks_labels = [f"Semana {w}" for w in weeks]
        agent_incident_weeks = incidents_by_week.get(agent, set())

        weekly_pts = []
        clean_flags = []
        streak = 0
        for wl in clean_weeks_labels:
            is_clean = wl not in agent_incident_weeks
            clean_flags.append(is_clean)
            if is_clean:
                streak += 1
                weekly_pts.append(STREAK_PTS[min(streak, 4) - 1])
            else:
                streak = 0
                weekly_pts.append(0)
        excelencia_total = sum(weekly_pts)
        clean_month = all(clean_flags)

        # Aproximacao: so temos aderencia MENSAL do Databricks, entao aplicamos
        # o mesmo % nas N semanas do mes (streak completo se > 85%).
        adherence = row.get("adherence")
        aderencia_pts = 0
        if adherence is not None and adherence > ADERENCIA_THRESHOLD:
            aderencia_pts = sum(STREAK_PTS[:len(weeks)]) if len(weeks) <= 4 else sum(STREAK_PTS)

        chat = row.get("tnpsChat")
        phone = row.get("tnpsPhone")
        avg, tnps_pts, no_channel = tnps_points(chat, phone, clean_month)

        wow_count = wow_total.get(agent, 0)
        chama = wow_count >= 3
        # Regra: cada WoW vale 10 pts; ao atingir 3+ no mes, vira "Chama do
        # Encantamento" (40 pts pelas 3 primeiras + 10 por WoW extra).
        wow_pts = (40 + (wow_count - 3) * 10) if chama else wow_count * 10

        score_level = row.get("scoreLevel")
        boss_battle = (
            score_level == "Top"
            and chat is not None and chat > BOSS_CHAT_THRESHOLD
            and phone is not None and phone > BOSS_PHONE_THRESHOLD
        )

        # Estreia Top: Top neste mes e NAO Top em nenhum mes anterior conhecido
        was_top_before = any(
            a == agent and m < cur_month_iso and rows_by_agent[(a, m)].get("scoreLevel") == "Top"
            for (a, m) in rows_by_agent.keys()
        )
        estreia_top = score_level == "Top" and not was_top_before

        ops = ops_by_agent.get(agent, {})
        skip_pct = ops.get("skip_pct")
        transfer_pct = ops.get("transfer_pct")
        expired_pct = ops.get("expired_pct")
        unanswered_pct = unanswered_by_agent.get(agent)

        skip_pts = tiered_points(skip_pct, [(5, 10), (7, 5), (9, -5)]) if skip_pct is not None else 0
        unanswered_pts = (
            tiered_points(unanswered_pct, [(2, 10), (5, 5), (10, -5)]) if unanswered_pct is not None else 0
        )
        transfer_pts = 10 if (transfer_pct is not None and transfer_pct < 3) else 0
        expired_pts = 10 if (expired_pct is not None and expired_pct < 3) else 0
        ops_total = skip_pts + unanswered_pts + transfer_pts + expired_pts

        total = excelencia_total + aderencia_pts + tnps_pts + wow_pts + ops_total + (80 if boss_battle else 0)

        results.append({
            "agent": agent,
            "total": total,
            "level": level_of(total),
            "excelencia": {"weekly": weekly_pts, "total": excelencia_total, "cleanWeeks": clean_flags},
            "aderencia": {"monthlyPct": adherence, "pts": aderencia_pts},
            "tnps": {
                "chat": round(chat, 2) if chat is not None else None,
                "phone": round(phone, 2) if phone is not None else None,
                "avg": round(avg, 2) if avg is not None else None,
                "pts": tnps_pts,
                "noChannel": no_channel,
            },
            "wow": {"count": wow_count, "pts": wow_pts, "chama": chama},
            "ops": {
                "skip": {"pct": skip_pct, "pts": skip_pts},
                "unanswered": {"pct": unanswered_pct, "pts": unanswered_pts, "noChannel": unanswered_pct is None},
                "transferIndevido": {"pct": transfer_pct, "pts": transfer_pts},
                "expired": {"pct": expired_pct, "pts": expired_pts},
                "total": ops_total,
            },
            "bossBattle": boss_battle,
            "estreiaTop": estreia_top,
        })

    results.sort(key=lambda r: -r["total"])

    out = {
        "month": cur_month_iso[:7],
        "monthLabel": month_label,
        "weeks": [f"Semana {w}" for w in weeks],
        "weekRanges": [],
        "generatedAt": datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
        "results": results,
    }

    os.makedirs("data", exist_ok=True)
    with open("data/scoreboard.json", "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    print("data/scoreboard.json atualizado.")


if __name__ == "__main__":
    main()
