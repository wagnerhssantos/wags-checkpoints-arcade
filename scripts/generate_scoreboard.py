#!/usr/bin/env python3
"""
Gera data/scoreboard.json para o site UAI MODO TURBO (Time Wags).

MOTOR DE PONTOS v7 -- competicao valida SOMENTE para setembro/2026.
Fechamentos semanais sempre na segunda-feira (semana de referencia = a que
acabou de fechar). Metricas mensais (Skip/Unanswered/Expired/Time Spent) usam
o resultado acumulado do mes corrente ate hoje.

## v7 -- Transfer sai da pontuacao e Skip vira chat+backoffice (09/09/2026)

Decisao do Wagner em 09/09/2026, duas mudancas independentes:

1. **Transfer indevido nao pontua mais durante o mes.** Continua sendo apurado
   e publicado (ops.transferIndevido.pct) para acompanhamento individual, mas
   com pts=0, applicable=False e monitoringOnly=True -- o site renderiza a
   coluna como "--". A metrica volta a pontuar no FECHAMENTO do mes, quando o
   resultado final estiver consolidado. Pra retomar: colocar TRANSFER_PTS=10 e
   EXPIRED_PTS=10 (ver item 2).

2. **Skip conta apenas atendimentos de chat e backoffice** -- numerador E
   denominador (SKIP_ACTIVITY_TYPES). email e inbound_call ficam fora da conta.
   Motivo: na apuracao de 01-07/09 nenhum skip do time aconteceu em
   inbound_call, e um volume relevante estava em email. No caso da
   lucrecia.santos, 25 dos 28 skips do mes eram de e-mail -- o Skip dela
   aparecia como 8,46% quando o numero real de chat+backoffice e 1,63%.
   Restringir tambem o denominador evita diluir o percentual de quem atende
   muito fone.

Pra manter o teto mensal de 40 pts da v4 sem redesenhar nada, os 10 pts que o
Transfer deixou vago foram para o Expired, que passou de +10 para +20 (mesmo
corte de <3%). Tetos mensais continuam identicos nos tres grupos:

  GERAL:       Skip 10 + Unanswered 10 + Expired 20 = 40
  SO CHAT:     Skip 20 (dobrado)        + Expired 20 = 40
  BACKOFFICE:  Skip 20 (dobrado)        + Expired 20 = 40

ATENCAO -- interacao nao resolvida: com o Skip restrito a chat+backoffice, um
agente classificado como "so phone" (PHONE_ONLY) ficaria sem base de calculo de
Skip. O grupo esta vazio hoje; resolver antes de classificar alguem nele.

## v6 -- Engajamento deixa de ser "quem mais postou leva tudo" (07/09/2026)

Regra: **+10 pts por semana para quem engajou de QUALQUER forma** -- mensagem
no canal, resposta em thread OU reacao/curtida em post de colega. Basta uma
dessas coisas. Nao e ranking, nao e winner-takes-all. Quem nao teve nenhum
registro na semana fica com 0. O teto continua 10 pts/semana.

Diagnostico da semana 36 que motivou a mudanca: 13 dos 14 agentes engajaram nos
canais e apenas 1 pontuava. A agente mais engajada do time (2 mensagens, 19
respostas em thread e reacoes em 43 posts distintos) tirava ZERO por nao abrir
topicos novos. O podio era artefato da metrica, nao do comportamento.

Trade-off assumido: a v6 nao distingue intensidade. Foi deliberado (metrica de
participacao). O campo "score" no engagement_override.json preserva a
intensidade caso a gente queira um bonus graduado depois.

## v5 -- Boss Battle com criterio por media de canais (01/09/2026)

Boss Battle (semana +20, mes +50) usa criterio de qualidade por MEDIA dos
canais aplicaveis ao grupo do agente, em vez de exigir os dois:
- GERAL: media(tNPS chat, tNPS phone) da semana/mes >= 85.
- SO CHAT: tNPS chat >= 85. SO PHONE: tNPS phone >= 85.
- BACKOFFICE: sem tNPS -- usa a faixa maxima de Time Spent (<5min).

"Top Performer da semana" nao existe oficialmente no Databricks; o proxy e o
agente com maior soma de Excelencia+tNPS naquela semana. Engajamento fica FORA
do calculo do Boss Battle. Empate: desempate alfabetico (deterministico).

## v4 -- recalibracao de justica entre grupos (01/09/2026)

Principio: "redistribuicao de canal" -- cada agente tem uma cota FIXA de pontos
por metrica-familia e, se ele so opera em UM canal daquela familia, o canal que
ele tem passa a valer o DOBRO.

Tetos unificados (todos os grupos):
  SEMANAL: Excelencia (25 max) + tNPS (40 max) + Engajamento (10) = 75.
  MENSAL: ver tabela da v7 acima = 40 pts/mes.

## Fontes de dados

- Excelencia / streak: planilha "Central de Inteligencia de CSI 2026"
  (abas 4.Qualidade, 5.Reclamacoes, 6.Erros Ops).
- tNPS chat / phone (SEMANAL, fecha segunda): etl.br__dataset.cx_metrics_tnps_resolutivity
  join etl.br__dataset.cx_canonical_activities (last_agent), filtrando
  channel = 'chat' ou 'inbound_call', survey_type='Human',
  fl_nps_answered=1, actor_affiliation='nubank'.
- Skip (MENSAL, v7): etl.br__dataset.cx_canonical_activities filtrando
  activity_type IN ('chat','backoffice').
- Transfer indevido / Expired / Time Spent (MENSAL): mesma tabela, base
  completa (chat, email, inbound_call, backoffice).
- Unanswered Calls (MENSAL): usr.cx_golden_layer.unanswered_calls.
- WoW: planilha "Base Faisca H22026", aba "(Automatizacao) WoWs Faisca".
- Engajamento (SEMANAL, v6): Slack -- #os_incriveis_csi (C0AK68688EQ),
  #wow_csi (C090RS3739N) e #cx-csi-informa (C0209GG9GQ7). Este script NAO tem
  acesso as ferramentas MCP de Slack -- espera o arquivo
  `data/engagement_override.json` gerado pela tarefa agendada no Cowork.

## Classificacao de canal por agente (revalidar mensalmente)

Com base no historico de agosto/26: andresa.britto, caren.paraiso e
lucrecia.santos nao tem nenhuma linha em unanswered_calls nem tNPS phone
-- classificados como "so atua em chat". Nenhum agente identificado hoje
como "so atua em phone" ou backoffice puro.

Secrets/variaveis de ambiente esperadas (GitHub Secrets), caso rodado via
Actions (fluxo alternativo -- o fluxo principal e a tarefa agendada no
Cowork, que usa as ferramentas MCP diretamente):
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
PHONE_ONLY = set()          # nenhum agente hoje -- ver ATENCAO na secao v7
NO_CHANNEL = set()          # nenhum agente hoje (backoffice puro)

# Canais Slack usados no calculo de Engajamento
CHANNEL_TIME = "C0AK68688EQ"       # #os_incriveis_csi
CHANNEL_WOW = "C090RS3739N"        # #wow_csi
CHANNEL_INFORMA = "C0209GG9GQ7"    # #cx-csi-informa

# ---- Bandas de tNPS semanal (v4: tetos unificados em 75 pts/semana) ----
TNPS_BANDS_GERAL = [(70, 5), (75, 10), (80.01, 15), (85, 20)]
TNPS_BANDS_UM_CANAL = [(70, 10), (75, 20), (80.01, 30), (85, 40)]

STREAK_PTS = [10, 15, 20, 25]  # semana 1,2,3,4+ (cap) -- igual pra todo mundo
EXCELENCIA_BASE = 10

# ---- Bandas mensais (v7: familia skip + expired = 40 pts/mes) ----
SKIP_BANDS_GERAL = [(5, 10), (7, 5), (9, 2), (9, -2)]
SKIP_BANDS_DOBRADO = [(5, 20), (7, 10), (9, 4), (9, -4)]
UNANSWERED_BANDS = [(2, 10), (5, 5), (8, 2)]  # acima de 8% = 0 (sem penalidade)

# v7: Skip conta so chat e backoffice (numerador E denominador).
SKIP_ACTIVITY_TYPES = ("chat", "backoffice")

# v7: Transfer indevido congelado como monitoramento. Pra retomar no fechamento
# do mes: TRANSFER_PTS = 10 e EXPIRED_PTS = 10 (o teto de 40 se mantem nos dois
# cenarios).
TRANSFER_THRESHOLD = 3
TRANSFER_PTS = 0            # <-- v7: nao pontua
EXPIRED_THRESHOLD = 3
EXPIRED_PTS = 20            # <-- v7: herdou os 10 pts do Transfer

# Time Spent (so backoffice)
TIME_SPENT_BANDS = [(5, 40), (7, 25), (9, 10)]  # >=9min = 0

# ---- Engajamento (v6): binario, +10 por semana pra quem engajou ----
ENGAGEMENT_PTS = 10
ENGAGEMENT_FIELDS = ("msgs", "threads", "postsReagidos")

BOSS_WEEKLY_PTS = 20
BOSS_MONTHLY_PTS = 50
BOSS_TNPS_THRESHOLD = 85
BOSS_TIME_SPENT_MAX_MIN = TIME_SPENT_BANDS[0][0]

LEVELS = [(300, "DIAMANTE"), (180, "OURO"), (90, "PRATA"), (0, "BRONZE")]


def tnps_band_points(pct, bands):
    """Retorna os pontos da MAIOR faixa atingida (nao cumulativo)."""
    if pct is None:
        return 0
    pts = 0
    for lower, p in bands:
        if pct >= lower:
            pts = p
    return pts


def tiered_points(pct, bands):
    """bands: (limite, pts) do mais restrito pro mais frouxo, seguido
    opcionalmente de (limite_penalidade, pts_negativo)."""
    if pct is None:
        return 0
    for limit, pts in bands:
        if pts > 0 and pct < limit:
            return pts
    for limit, pts in bands:
        if pts < 0 and pct > limit:
            return pts
    return 0


def engajou_na_semana(entry):
    """v6: True se o agente teve QUALQUER forma de engajamento na semana."""
    if entry is None:
        return False
    if isinstance(entry, dict):
        return any((entry.get(f) or 0) > 0 for f in ENGAGEMENT_FIELDS)
    try:
        return float(entry) > 0
    except (TypeError, ValueError):
        return False


def load_engagement_override(path="data/engagement_override.json"):
    try:
        with open(path, encoding="utf-8") as f:
            raw = json.load(f)
    except FileNotFoundError:
        print("aviso: data/engagement_override.json nao encontrado -- "
              "Engajamento vai ficar zerado (rode a tarefa agendada no Cowork, "
              "que e quem tem acesso ao Slack)")
        return {}
    return {k: v for k, v in raw.items()
            if not k.startswith("_") and isinstance(v, dict)}


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


def week_quality_pct(grp, chat_entry, phone_entry):
    """Media de tNPS dos canais aplicaveis ao grupo, numa semana especifica."""
    vals = []
    if grp in ("geral", "chat_only") and chat_entry is not None:
        vals.append(chat_entry["tnps"])
    if grp in ("geral", "phone_only") and phone_entry is not None:
        vals.append(phone_entry["tnps"])
    if not vals:
        return None
    return sum(vals) / len(vals)


def month_quality_pct(grp, chat_entries, phone_entries):
    """Mesma logica, juntando todas as semanas do mes (cada semana pesa igual)."""
    vals = []
    if grp in ("geral", "chat_only"):
        vals += [e["tnps"] for e in chat_entries]
    if grp in ("geral", "phone_only"):
        vals += [e["tnps"] for e in phone_entries]
    if not vals:
        return None
    return sum(vals) / len(vals)


def compute_boss_battle(records, n_weeks):
    """Retorna (weekly_pts, weekly_won, monthly_pts, monthly_won)."""
    by_agent = {r["agent"]: r for r in records}
    weekly_pts = {r["agent"]: 0 for r in records}
    weekly_won = {r["agent"]: False for r in records}

    def quality_ok(rec, chat_entry, phone_entry):
        if rec["group"] == "backoffice":
            tsm = rec["time_spent_min"]
            return tsm is not None and tsm < BOSS_TIME_SPENT_MAX_MIN
        pct = week_quality_pct(rec["group"], chat_entry, phone_entry)
        return pct is not None and pct >= BOSS_TNPS_THRESHOLD

    def quality_ok_month(rec):
        if rec["group"] == "backoffice":
            tsm = rec["time_spent_min"]
            return tsm is not None and tsm < BOSS_TIME_SPENT_MAX_MIN
        pct = month_quality_pct(rec["group"], rec["tnps_chat_entries"], rec["tnps_phone_entries"])
        return pct is not None and pct >= BOSS_TNPS_THRESHOLD

    for i in range(n_weeks):
        scores = {}
        chat_by_agent = {}
        phone_by_agent = {}
        for r in records:
            chat_entry = next((e for e in r["tnps_chat_entries"] if e["week_index"] == i), None)
            phone_entry = next((e for e in r["tnps_phone_entries"] if e["week_index"] == i), None)
            chat_by_agent[r["agent"]] = chat_entry
            phone_by_agent[r["agent"]] = phone_entry
            exc = r["weekly_excelencia"][i] if i < len(r["weekly_excelencia"]) else 0
            cp = chat_entry["pts"] if chat_entry else 0
            pp = phone_entry["pts"] if phone_entry else 0
            scores[r["agent"]] = exc + cp + pp
        if not any(v > 0 for v in scores.values()):
            continue  # ninguem pontuou essa semana -- sem Boss Battle
        top_agent = max(sorted(scores.keys()), key=lambda a: scores[a])
        rec = by_agent[top_agent]
        if quality_ok(rec, chat_by_agent[top_agent], phone_by_agent[top_agent]):
            weekly_pts[top_agent] += BOSS_WEEKLY_PTS
            weekly_won[top_agent] = True

    monthly_pts = {r["agent"]: 0 for r in records}
    monthly_won = {r["agent"]: False for r in records}
    totals_with_weekly = {r["agent"]: r["base_total"] + weekly_pts[r["agent"]] for r in records}
    if any(v > 0 for v in totals_with_weekly.values()):
        top_agent = max(sorted(totals_with_weekly.keys()), key=lambda a: totals_with_weekly[a])
        rec = by_agent[top_agent]
        if quality_ok_month(rec):
            monthly_pts[top_agent] += BOSS_MONTHLY_PTS
            monthly_won[top_agent] = True

    return weekly_pts, weekly_won, monthly_pts, monthly_won


def main():
    today = datetime.date.today()
    month_start = f"{COMPETITION_MONTH}-01"
    year, month = (int(x) for x in COMPETITION_MONTH.split("-"))
    month_end = today.strftime("%Y-%m-%d")
    closed_mondays = [m for m in mondays_of_month(year, month) if m <= today]

    roster_emails = [f"{a}@nubank.com.br" for a in ROSTER]
    email_list_sql = ",".join(f"'{e}'" for e in roster_emails)
    skip_types_sql = ",".join(f"'{t}'" for t in SKIP_ACTIVITY_TYPES)

    # ---- 1) Metricas mensais (resultado do mes corrente ate hoje) ----
    ops_by_agent = {}
    skip_by_agent = {}
    unanswered_by_agent = {}
    try:
        # 1a) Transfer / Expired / Time Spent -- base COMPLETA de atendimentos.
        ops_rows = databricks_query(
            "SELECT agent, COUNT(dist_key) AS total_int, "
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
                "transfer_pct": round(int(r["transfer_indevido"] or 0) * 100.0 / total, 2) if total else None,
                "expired_pct": round(int(r["expired"] or 0) * 100.0 / total, 2) if total else None,
                "avg_time_spent_min": round(float(r["avg_time_spent"]) / 60.0, 2) if r.get("avg_time_spent") else None,
            }

        # 1b) Skip -- v7: SO chat e backoffice, numerador E denominador.
        skip_rows = databricks_query(
            "SELECT agent, COUNT(dist_key) AS total_int, "
            "SUM(CASE WHEN status='skipped' THEN 1 ELSE 0 END) AS skipped "
            "FROM etl.br__dataset.cx_canonical_activities "
            f"WHERE DATE(local_start_time) BETWEEN '{month_start}' AND '{month_end}' "
            "AND actor_affiliation='nubank' AND source_id NOT LIKE '%lineu%' "
            "AND NOT (activity_type IN ('email','backoffice') AND status='expired') "
            f"AND activity_type IN ({skip_types_sql}) "
            f"AND agent IN ({email_list_sql}) GROUP BY agent"
        )
        for r in skip_rows:
            agent = r["agent"].split("@")[0]
            total = int(r["total_int"] or 0)
            skip_by_agent[agent] = round(int(r["skipped"] or 0) * 100.0 / total, 2) if total else None

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
    tnps_weekly = {}
    for agent in ROSTER:
        tnps_weekly[agent] = {"chat": [], "phone": []}
    try:
        for week_index, monday in enumerate(closed_mondays):
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
                um_canal_so = (canal == "chat" and agent in CHAT_ONLY) or (canal == "phone" and agent in PHONE_ONLY)
                bands = TNPS_BANDS_UM_CANAL if um_canal_so else TNPS_BANDS_GERAL
                pts = tnps_band_points(tnps, bands)
                tnps_weekly.setdefault(agent, {"chat": [], "phone": []})[canal].append({"tnps": tnps, "pts": pts, "week_index": week_index})
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

    # ---- 4) Engajamento (override gerado pela tarefa agendada) ----
    engagement_override = load_engagement_override()

    # ---- 5) Montar dados intermediarios por agente ----
    records = []
    for agent in ROSTER:
        grp = group_of(agent)

        weekly_excelencia = []
        streak = 0
        for monday in closed_mondays:
            week_label = f"Semana de {(monday - datetime.timedelta(days=7)).strftime('%d/%m')} a {(monday - datetime.timedelta(days=1)).strftime('%d/%m')}"
            is_clean = week_label not in incidents_by_week.get(agent, set())
            if is_clean:
                streak += 1
                mult = STREAK_PTS[min(streak, 4) - 1] / STREAK_PTS[0]
                weekly_excelencia.append(round(EXCELENCIA_BASE * mult))
            else:
                streak = 0
                weekly_excelencia.append(0)
        excelencia_total = sum(weekly_excelencia)

        tnps_chat_entries = tnps_weekly.get(agent, {}).get("chat", [])
        tnps_phone_entries = tnps_weekly.get(agent, {}).get("phone", [])
        tnps_chat_pts = 0 if grp in ("backoffice", "phone_only") else sum(w["pts"] for w in tnps_chat_entries)
        tnps_phone_pts = 0 if grp in ("backoffice", "chat_only") else sum(w["pts"] for w in tnps_phone_entries)

        ops = ops_by_agent.get(agent, {})
        skip_pct = skip_by_agent.get(agent)          # v7: so chat+backoffice
        transfer_pct = ops.get("transfer_pct")
        expired_pct = ops.get("expired_pct")
        time_spent_min = ops.get("avg_time_spent_min")
        unanswered_pct = None if grp in ("chat_only", "backoffice") else unanswered_by_agent.get(agent)

        skip_bands = SKIP_BANDS_DOBRADO if grp in ("chat_only", "backoffice") else SKIP_BANDS_GERAL
        skip_pts = tiered_points(skip_pct, skip_bands)
        unanswered_pts = tiered_points(unanswered_pct, UNANSWERED_BANDS) if unanswered_pct is not None else 0
        # v7: TRANSFER_PTS = 0 -- a metrica e so monitoramento ate o fechamento.
        transfer_pts = TRANSFER_PTS if (transfer_pct is not None and transfer_pct < TRANSFER_THRESHOLD) else 0
        expired_pts = EXPIRED_PTS if (expired_pct is not None and expired_pct < EXPIRED_THRESHOLD) else 0
        time_spent_pts = 0
        if grp == "backoffice" and time_spent_min is not None:
            time_spent_pts = tiered_points(time_spent_min, TIME_SPENT_BANDS) * len(closed_mondays)

        wow_count = wow_total.get(agent, 0)
        chama = wow_count >= 3
        wow_pts = (40 + (wow_count - 3) * 10) if chama else wow_count * 10

        engagement_pts = 0
        engagement_detail = {}
        for week_key, counts in engagement_override.items():
            entry = counts.get(agent)
            if engajou_na_semana(entry):
                engagement_pts += ENGAGEMENT_PTS
            if isinstance(entry, dict):
                engagement_detail[week_key] = entry

        ops_total = skip_pts + unanswered_pts + transfer_pts + expired_pts + time_spent_pts
        base_total = excelencia_total + tnps_chat_pts + tnps_phone_pts + ops_total + wow_pts + engagement_pts

        records.append({
            "agent": agent,
            "group": grp,
            "weekly_excelencia": weekly_excelencia,
            "excelencia_total": excelencia_total,
            "tnps_chat_entries": tnps_chat_entries,
            "tnps_phone_entries": tnps_phone_entries,
            "tnps_chat_pts": tnps_chat_pts,
            "tnps_phone_pts": tnps_phone_pts,
            "skip_pct": skip_pct, "skip_pts": skip_pts,
            "unanswered_pct": unanswered_pct, "unanswered_pts": unanswered_pts,
            "transfer_pct": transfer_pct, "transfer_pts": transfer_pts,
            "expired_pct": expired_pct, "expired_pts": expired_pts,
            "time_spent_min": time_spent_min, "time_spent_pts": time_spent_pts,
            "wow_count": wow_count, "wow_pts": wow_pts, "chama": chama,
            "engagement_pts": engagement_pts,
            "engagement_detail": engagement_detail,
            "ops_total": ops_total,
            "base_total": base_total,
        })

    # ---- 6) Boss Battle (semana +20, mes +50) ----
    boss_weekly_pts, boss_weekly_won, boss_monthly_pts, boss_monthly_won = compute_boss_battle(
        records, len(closed_mondays)
    )

    # ---- 7) Montar resultado final por agente (base + Boss Battle) ----
    results = []
    for r in records:
        agent = r["agent"]
        grp = r["group"]
        total = r["base_total"] + boss_weekly_pts[agent] + boss_monthly_pts[agent]

        results.append({
            "agent": agent,
            "group": grp,
            "total": total,
            "level": level_of(total),
            "excelencia": {"weekly": r["weekly_excelencia"], "total": r["excelencia_total"]},
            "tnps": {
                "chat": r["tnps_chat_entries"],
                "chatPts": r["tnps_chat_pts"],
                "phone": r["tnps_phone_entries"],
                "phonePts": r["tnps_phone_pts"],
                "applicable": {"chat": grp not in ("backoffice", "phone_only"), "phone": grp not in ("backoffice", "chat_only")},
            },
            "ops": {
                "skip": {"pct": r["skip_pct"], "pts": r["skip_pts"], "scope": "+".join(SKIP_ACTIVITY_TYPES)},
                "unanswered": {"pct": r["unanswered_pct"], "pts": r["unanswered_pts"], "applicable": grp not in ("chat_only", "backoffice")},
                # v7: transfer entra so como monitoramento -- applicable=False faz
                # o site renderizar a coluna como "--".
                "transferIndevido": {
                    "pct": r["transfer_pct"],
                    "pts": r["transfer_pts"],
                    "applicable": TRANSFER_PTS > 0,
                    "monitoringOnly": TRANSFER_PTS == 0,
                },
                "expired": {"pct": r["expired_pct"], "pts": r["expired_pts"]},
                "timeSpent": {"minutes": r["time_spent_min"], "pts": r["time_spent_pts"], "applicable": grp == "backoffice"},
                "total": r["ops_total"],
            },
            "wow": {"count": r["wow_count"], "pts": r["wow_pts"], "chama": r["chama"]},
            "engagement": {"pts": r["engagement_pts"], "detail": r["engagement_detail"]},
            "bossBattle": {
                "weekly": boss_weekly_won[agent],
                "monthly": boss_monthly_won[agent],
                "weeklyPts": boss_weekly_pts[agent],
                "monthlyPts": boss_monthly_pts[agent],
            },
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
