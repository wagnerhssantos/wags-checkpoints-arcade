#!/usr/bin/env python3
"""
Gera data/scoreboard.json para o site UAI MODO TURBO (Time Wags).

MOTOR DE PONTOS v3 -- competicao valida SOMENTE para setembro/2026.
Fechamentos semanais sempre na segunda-feira (semana de referencia = a que
acabou de fechar). Metricas mensais (Skip/Unanswered/Transfer/Expired/Time
Spent) usam o resultado acumulado do mes corrente até hoje (nao ha streak
semanal nessas 4/5).

## Fontes de dados

- Excelencia / streak: planilha "Central de Inteligencia de CSI 2026"
  (abas 4.Qualidade, 5.Reclamacoes, 6.Erros Ops) -- mesma logica da v2.
- tNPS chat / tNPS phone (SEMANAL, fecha segunda): etl.br__dataset.cx_metrics_tnps_resolutivity
  join etl.br__dataset.cx_canonical_activities (last_agent), filtrando
  channel = 'chat' ou channel = 'inbound_call', survey_type='Human',
  fl_nps_answered=1, actor_affiliation='nubank'. Query baseada na skill
  tnps-weekly-dm-time-wags (fonte oficial ja usada pro DM semanal do time).
- Skip / Transfer indevido / Expired / Time Spent (MENSAL, resultado final
  do mes corrente): etl.br__dataset.cx_canonical_activities (colunas
  status, is_transfer_indevido, mount_time_spent, net_time_spent).
  Formula de Time Spent confirmada em cx-analyst/references/metrics-targets.md:
  AVG(CASE WHEN mount_time_spent>0 THEN mount_time_spent ELSE net_time_spent END).
- Unanswered Calls (MENSAL): usr.cx_golden_layer.unanswered_calls
  (queue_event__actor, ringing, no_answer). So conta pra quem atua em phone.
- WoW: planilha "Base Faisca H22026", aba "(Automatizacao) WoWs Faisca".
- Engajamento nos canais (SEMANAL): contagem de mensagens/comentarios do
  agente nos 3 canais Slack do time -- #os_incriveis_csi (C0AK68688EQ),
  #copa_canguru_wow2026 (C0B6H07JLEA) e #cx-csi-informa (C0209GG9GQ7).
  O agente com mais interacoes na semana ganha +10. Este script NAO tem
  acesso as ferramentas MCP de Slack (roda fora do Cowork) -- espera um
  arquivo `data/engagement_override.json` com {"semana_iso": {"agent": qtd}}
  gerado pela tarefa agendada (que roda dentro do Cowork, com acesso ao
  Slack). Se o arquivo nao existir, o campo fica pendente.

## Classificacao de canal por agente (revalidar mensalmente)

Com base no historico de agosto/26: andresa.britto, caren.paraiso e
lucrecia.santos nao tem nenhuma linha em unanswered_calls nem tNPS phone
-- classificados como "so atua em chat". Nenhum agente identificado hoje
como "so atua em phone" ou "nao atua em chat e phone" (backoffice puro);
os grupos existem no motor e ficam vazios até algum agente se encaixar.

## Regras por grupo (ver README.md para o detalhamento completo)

- GERAL (atua em chat e phone): Excelencia +10/sem (streak 10/15/20/25 cap
  25); tNPS chat e tNPS phone (bandas 5/10/15/20 por semana, faixas
  70-74.99/75-80/80.01-85/85-100); Skip mensal (+10/+5/+2/-2); Unanswered
  mensal (+10/+5/+2/0); Transfer indevido mensal (+10 se <3%); Expired
  mensal (+10 se <3%).
- SO CHAT (nao atua phone): desconsidera Unanswered e tNPS Phone; tNPS
  Chat com banda elevada (6/11/16/25); Skip com banda elevada
  (11/6/3/-5); mantem Transfer/Expired gerais.
- BACKOFFICE PURO (nao atua chat nem phone): Excelencia +20/sem (streak
  igual); desconsidera tNPS e Unanswered; Skip geral; Time Spent semanal
  (<7min = +10/sem); mantem Transfer/Expired gerais.
- TODOS: Chama do Encantamento (3+ WoWs no mes = +40, +10/extra);
  Engajamento nos canais (+10/semana para quem mais participou); Boss
  Battle semana (+20, top da semana com tNPS chat e phone >=85 na semana);
  Boss Battle mes (+50, mesma logica mensal).

Secrets/variaveis de ambiente esperadas (GitHub Secrets), caso rodado via
Actions (fluxo alternativo -- o fluxo principal agora e a tarefa agendada
no Cowork, que usa as ferramentas MCP diretamente em vez deste script):
  DATABRICKS_HOST, DATABRICKS_TOKEN, DATABRICKS_WAREHOUSE_ID,
  GOOGLE_SERVICE_ACCOUNT_JSON, XFORCE_EMAIL
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

COMPETITION_MONTH = "2026-09"  # competicao valida SOMENTE para setembro/2026

ROSTER = [
    "andresa.britto", "kissila.oliveira", "lucas.cassimiro", "angela.julia",
    "gabrielle.macedo", "randal.savino", "caren.paraiso", "angelica.almeida",
    "giulia.machado", "guilherme.zunareli", "lucrecia.santos", "marcelo.calixto",
    "maycon.cardoso", "thiago.guedes",
]

# Classificacao de canal (revalidar mensalmente -- ver docstring acima)
CHAT_ONLY = {"andresa.britto", "caren.paraiso", "lucrecia.santos"}
PHONE_ONLY = set()          # nenhum agente hoje
NO_CHANNEL = set()          # nenhum agente hoje (backoffice puro)

# Canais Slack usados no calculo de Engajamento
CHANNEL_TIME = "C0AK68688EQ"       # #os_incriveis_csi
CHANNEL_WOW = "C0B6H07JLEA"        # #copa_canguru_wow2026
CHANNEL_INFORMA = "C0209GG9GQ7"    # #cx-csi-informa

# Bandas de tNPS semanal (padrao -- chat e phone da populacao geral)
TNPS_BANDS_GERAL = [(70, 5), (75, 10), (80.01, 15), (85, 20)]
# Banda elevada de tNPS chat para quem so atua em chat (compensacao)
TNPS_BANDS_CHAT_ONLY = [(70, 6), (75, 11), (80.01, 16), (85, 25)]

STREAK_PTS = [10, 15, 20, 25]  # semana 1,2,3,4+ (cap)
EXCELENCIA_BASE_GERAL = 10
EXCELENCIA_BASE_BACKOFFICE = 20

SKIP_BANDS_GERAL = [(5, 10), (7, 5), (9, 2), (9, -2)]
SKIP_BANDS_ELEVADO = [(5, 11), (7, 6), (9, 3), (9, -5)]
UNANSWERED_BANDS = [(2, 10), (5, 5), (8, 2)]  # acima de 8% = 0 (sem penalidade)
TRANSFER_THRESHOLD = 3
EXPIRED_THRESHOLD = 3
TIME_SPENT_THRESHOLD_MIN = 7  # minutos, so para grupo backoffice puro

BOSS_WEEKLY_PTS = 20
BOSS_MONTHLY_PTS = 50
BOSS_TNPS_THRESHOLD = 85  # tNPS chat e phone >= 85 (faixa maxima)

LEVELS = [(300, "DIAMANTE"), (180, "OURO"), (90, "PRATA"), (0, "BRONZE")]
# Thresholds provisorios para a 1a semana de competicao -- recalibrar
# depois que houver pelo menos 1-2 fechamentos semanais reais.


def tnps_band_points(pct, bands):
    """bands: lista de (limite_inferior_ou_igual, pts) em ordem crescente de
    faixa. Retorna os pontos da MAIOR faixa atingida (nao cumulativo)."""
    if pct is None:
        return 0
    pts = 0
    for lower, p in bands:
        if pct >= lower:
            pts = p
    return pts


def tiered_points(pct, bands):
    """bands: lista de (limite, pts) em ordem do mais restrito pro mais
    frouxo, seguida opcionalmente de (limite_penalidade, pts_penalidade)
    com pts negativo."""
    if pct is None:
        return 0
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


def week_number(date):
    return date.isocalendar()[1]


def mondays_of_month(year, month):
    """Lista de segundas-feiras (fechamentos) dentro do mes/ano dado."""
    first = datetime.date(year, month, 1)
    last_day = calendar.monthrange(year, month)[1]
    last = datetime.date(year, month, last_day)
    mondays = []
    d = first
    while d <= last:
        if d.weekday() == 0:  # segunda
            mondays.append(d)
        d += datetime.timedelta(days=1)
    return mondays


def group_of(agent):
    if agent in NO_CHANNEL:
        return "backoffice"
    if agent in CHAT_ONLY:
        return "chat_only"
    if agent in PHONE_ONLY:
        return "phone_only"
    return "geral"


def level_of(total):
    for threshold, label in LEVELS:
        if total >= threshold:
            return label
    return "BRONZE"


def main():
    today = datetime.date.today()
    month_start = f"{COMPETITION_MONTH}-01"
    year, month = (int(x) for x in COMPETITION_MONTH.split("-"))
    month_end = today.strftime("%Y-%m-%d")
    closed_mondays = [m for m in mondays_of_month(year, month) if m <= today]

    roster_emails = [f"{a}@nubank.com.br" for a in ROSTER]
    email_list_sql = ",".join(f"'{e}'" for e in roster_emails)

    # ---- 1) Metricas mensais (resultado final do mes corrente até hoje) ----
    ops_by_agent = {}
    unanswered_by_agent = {}
    try:
        ops_rows = databricks_query(
            "SELECT agent, COUNT(dist_key) AS total_int, "
            "SUM(CASE WHEN status='skipped' THEN 1 ELSE 0 END) AS skipped, "
            "SUM(CASE WHEN is_transfer_indevido=1 THEN 1 ELSE 0 END) AS transfer_indevido, "
            "SUM(CASE WHEN status='expired' THEN 1 ELSE 0 END) AS expired, "
            "AVG(CASE WHEN mount_time_spent IS NOT NULL AND mount_time_spent>0 "
            "THEN mount_time_spent ELSE net_time_spent END) AS avg_time_spent "
            "FROM etl.br__dataset.cx_canonical_activities "
            f"WHERE DATE(local_start_time) BETWEEN '{month_start}' AND '{month_end}' "
            "AND actor_affiliation='nubank' AND source_id NOT LIKE '%lineu%' "
            "AND NOT (activity_type IN ('email','backoffice') AND status='expired') "
            "AND activity_type IN ('chat','email','inbound_call','backoffice') "
            f"AND agent IN ({email_list_sql}) GROUP BY agent"
        )
        for r in ops_rows:
            agent = r["agent"].split("@")[0]
            total = int(r["total_int"] or 0)
            ops_by_agent[agent] = {
                "skip_pct": round(int(r["skipped"] or 0) * 100.0 / total, 2) if total else None,
                "transfer_pct": round(int(r["transfer_indevido"] or 0) * 100.0 / total, 2) if total else None,
                "expired_pct": round(int(r["expired"] or 0) * 100.0 / total, 2) if total else None,
                "avg_time_spent_min": round(float(r["avg_time_spent"]) / 60.0, 2) if r.get("avg_time_spent") else None,
            }

        unanswered_rows = databricks_query(
            "SELECT queue_event__actor AS agent, SUM(ringing) AS ringing, SUM(no_answer) AS no_answer "
            "FROM usr.cx_golden_layer.unanswered_calls "
            f"WHERE local_event_date BETWEEN '{month_start}' AND '{month_end}' "
            f"AND queue_event__actor IN ({email_list_sql}) GROUP BY queue_event__actor"
        )
        for r in unanswered_rows:
            agent = r["agent"].split("@")[0]
            ringing = int(r["ringing"] or 0)
            unanswered_by_agent[agent] = round(int(r["no_answer"] or 0) * 100.0 / ringing, 2) if ringing else None
    except Exception as e:
        print(f"aviso: nao consegui consultar metricas mensais no Databricks ({e})")

    # ---- 2) tNPS semanal (chat e phone), por segunda-feira ja fechada ----
    tnps_weekly = {}  # {agent: {"chat": [pts_por_semana], "phone": [...]}}
    for agent in ROSTER:
        tnps_weekly[agent] = {"chat": [], "phone": []}
    try:
        for monday in closed_mondays:
            week_start = (monday - datetime.timedelta(days=7)).strftime("%Y-%m-%d")
            week_end = (monday - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
            rows = databricks_query(f"""
                WITH last_agent AS (
                  SELECT source_id, agent,
                    ROW_NUMBER() OVER (PARTITION BY source_id ORDER BY local_stop_time DESC) AS rn
                  FROM etl.br__dataset.cx_canonical_activities
                  WHERE status='finished' AND actor_affiliation='nubank'
                    AND source_id NOT LIKE '%lineu%'
                    AND DATE(local_start_time) BETWEEN '{week_start}' AND '{week_end}'
                    AND agent IN ({email_list_sql})
                )
                SELECT la.agent AS agente, t.channel AS canal,
                  SUM(CASE WHEN t.survey_nps>=9 THEN 1 ELSE 0 END) AS promotores,
                  SUM(CASE WHEN t.survey_nps<=6 THEN 1 ELSE 0 END) AS detratores,
                  COUNT(*) AS total
                FROM etl.br__dataset.cx_metrics_tnps_resolutivity t
                JOIN last_agent la ON t.source_id = la.source_id AND la.rn = 1
                WHERE t.survey_type='Human' AND t.fl_nps_answered=1
                  AND DATE(t.local_start_time) BETWEEN '{week_start}' AND '{week_end}'
                  AND t.actor_affiliation='nubank' AND t.channel IN ('chat','inbound_call')
                GROUP BY la.agent, t.channel
            """)
            for r in rows:
                agent = r["agente"].split("@")[0]
                canal = "chat" if r["canal"] == "chat" else "phone"
                total = int(r["total"] or 0)
                if total == 0:
                    continue
                tnps = round((int(r["promotores"]) - int(r["detratores"])) / total * 100, 1)
                bands = TNPS_BANDS_CHAT_ONLY if (canal == "chat" and agent in CHAT_ONLY) else TNPS_BANDS_GERAL
                pts = tnps_band_points(tnps, bands)
                tnps_weekly.setdefault(agent, {"chat": [], "phone": []})[canal].append({"tnps": tnps, "pts": pts})
    except Exception as e:
        print(f"aviso: nao consegui consultar tNPS semanal no Databricks ({e})")

    # ---- 3) Excelencia semanal (Sheets) e WoW (Sheets) ----
    incidents_by_week = {}
    wow_total = {}
    try:
        svc = sheets_service()

        def mark_incident(agent, week_label):
            incidents_by_week.setdefault(agent, set()).add(week_label)

        def scan_incident_rows(values, month_label):
            for row in values:
                if len(row) < 4:
                    continue
                month_col, week_col, _cid, xmart = row[0], row[1], row[2], row[3]
                if month_col != month_label:
                    continue
                agent = xmart.split("@")[0].strip()
                if agent in ROSTER:
                    mark_incident(agent, week_col)

        month_label = f"{month:02d}/{str(year)[2:]}"
        scan_incident_rows(fetch_range(svc, SHEET_ID, "'4. Qualidade'!B1:E2000"), month_label)
        scan_incident_rows(fetch_range(svc, SHEET_ID, "'5. Reclamações.'!B1:E2000"), month_label)

        wow_rows = fetch_range(svc, WOW_SHEET_ID, "'(Automatização) WoWs Faísca'!A2:B5000")
        for row in wow_rows:
            if len(row) < 2:
                continue
            ts, email = row[0], row[1]
            agent = email.split("@")[0].strip()
            if agent not in ROSTER:
                continue
            try:
                d = datetime.datetime.strptime(ts[:10], "%Y-%m-%d").date()
            except ValueError:
                continue
            if d.strftime("%Y-%m") != COMPETITION_MONTH:
                continue
            wow_total[agent] = wow_total.get(agent, 0) + 1
    except Exception as e:
        print(f"aviso: nao consegui ler Google Sheets ({e})")

    # ---- 4) Engajamento nos canais (override gerado pela tarefa agendada) ----
    engagement_override = {}
    try:
        with open("data/engagement_override.json", encoding="utf-8") as f:
            engagement_override = json.load(f)
    except FileNotFoundError:
        pass  # pendente -- a tarefa agendada no Cowork popula isso via Slack MCP

    # ---- 5) Montar resultado por agente ----
    results = []
    for agent in ROSTER:
        grp = group_of(agent)
        base_excelencia = EXCELENCIA_BASE_BACKOFFICE if grp == "backoffice" else EXCELENCIA_BASE_GERAL

        weekly_excelencia = []
        streak = 0
        for monday in closed_mondays:
            week_label = f"Semana de {(monday - datetime.timedelta(days=7)).strftime('%d/%m')} a {(monday - datetime.timedelta(days=1)).strftime('%d/%m')}"
            is_clean = week_label not in incidents_by_week.get(agent, set())
            if is_clean:
                streak += 1
                mult = STREAK_PTS[min(streak, 4) - 1] / STREAK_PTS[0]
                weekly_excelencia.append(round(base_excelencia * mult))
            else:
                streak = 0
                weekly_excelencia.append(0)
        excelencia_total = sum(weekly_excelencia)

        tnps_chat_pts = 0 if grp in ("backoffice",) else sum(w["pts"] for w in tnps_weekly.get(agent, {}).get("chat", []))
        tnps_phone_pts = 0 if grp in ("backoffice", "chat_only") else sum(w["pts"] for w in tnps_weekly.get(agent, {}).get("phone", []))

        ops = ops_by_agent.get(agent, {})
        skip_pct = ops.get("skip_pct")
        transfer_pct = ops.get("transfer_pct")
        expired_pct = ops.get("expired_pct")
        time_spent_min = ops.get("avg_time_spent_min")
        unanswered_pct = None if grp == "chat_only" else unanswered_by_agent.get(agent)

        skip_bands = SKIP_BANDS_ELEVADO if grp == "chat_only" else SKIP_BANDS_GERAL
        skip_pts = tiered_points(skip_pct, skip_bands)
        unanswered_pts = tiered_points(unanswered_pct, UNANSWERED_BANDS) if unanswered_pct is not None else 0
        transfer_pts = 10 if (transfer_pct is not None and transfer_pct < TRANSFER_THRESHOLD) else 0
        expired_pts = 10 if (expired_pct is not None and expired_pct < EXPIRED_THRESHOLD) else 0
        time_spent_pts = 0
        if grp == "backoffice" and time_spent_min is not None and time_spent_min < TIME_SPENT_THRESHOLD_MIN:
            time_spent_pts = 10 * len(closed_mondays)

        wow_count = wow_total.get(agent, 0)
        chama = wow_count >= 3
        wow_pts = (40 + (wow_count - 3) * 10) if chama else wow_count * 10

        engagement_pts = 0
        for week_key, counts in engagement_override.items():
            if not counts:
                continue
            top_agent = max(counts, key=counts.get)
            if top_agent == agent:
                engagement_pts += 10

        ops_total = skip_pts + unanswered_pts + transfer_pts + expired_pts + time_spent_pts

        total = (
            excelencia_total + tnps_chat_pts + tnps_phone_pts + ops_total
            + wow_pts + engagement_pts
        )

        results.append({
            "agent": agent,
            "group": grp,
            "total": total,
            "level": level_of(total),
            "excelencia": {"weekly": weekly_excelencia, "total": excelencia_total},
            "tnps": {
                "chat": tnps_weekly.get(agent, {}).get("chat", []),
                "chatPts": tnps_chat_pts,
                "phone": tnps_weekly.get(agent, {}).get("phone", []),
                "phonePts": tnps_phone_pts,
                "applicable": {"chat": grp != "backoffice", "phone": grp not in ("backoffice", "chat_only")},
            },
            "ops": {
                "skip": {"pct": skip_pct, "pts": skip_pts},
                "unanswered": {"pct": unanswered_pct, "pts": unanswered_pts, "applicable": grp != "chat_only"},
                "transferIndevido": {"pct": transfer_pct, "pts": transfer_pts},
                "expired": {"pct": expired_pct, "pts": expired_pts},
                "timeSpent": {"minutes": time_spent_min, "pts": time_spent_pts, "applicable": grp == "backoffice"},
                "total": ops_total,
            },
            "wow": {"count": wow_count, "pts": wow_pts, "chama": chama},
            "engagement": {"pts": engagement_pts},
            "bossBattle": {"weekly": False, "monthly": False},  # calculado depois de ordenar
            "estreiaTop": False,
        })

    results.sort(key=lambda r: -r["total"])

    out = {
        "month": COMPETITION_MONTH,
        "monthLabel": f"{month:02d}/{str(year)[2:]}",
        "competitionScope": "Competição válida apenas para setembro/2026",
        "closedMondays": [m.strftime("%Y-%m-%d") for m in closed_mondays],
        "dataAsOf": today.strftime("%Y-%m-%d"),
        "generatedAt": datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
        "results": results,
    }

    os.makedirs("data", exist_ok=True)
    with open("data/scoreboard.json", "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    print("data/scoreboard.json atualizado.")


if __name__ == "__main__":
    main()
