#!/usr/bin/env python3
"""
Gera data/scoreboard.json para o site UAI MODO TURBO (Time Wags).

MOTOR DE PONTOS v5 -- competicao valida SOMENTE para setembro/2026.
Fechamentos semanais sempre na segunda-feira (semana de referencia = a que
acabou de fechar). Metricas mensais (Skip/Unanswered/Transfer/Expired/Time
Spent) usam o resultado acumulado do mes corrente até hoje (nao ha streak
semanal nessas 4/5).

## v5 -- Boss Battle implementado com criterio por media de canais (01/09/2026)

Boss Battle (semana +20, mes +50) estava documentado desde a v3 mas nunca
foi implementado (campo sempre False) -- e o criterio original ("tNPS chat
E phone >=85") so era atingivel por quem tem os dois canais, o que
recriaria a mesma injustica que a v4 corrigiu nos pontos normais.

v5 implementa o Boss Battle com um criterio de qualidade por MEDIA dos
canais aplicaveis ao grupo do agente, em vez de exigir os dois:
- GERAL: media(tNPS chat, tNPS phone) da semana/mes >= 85.
- SO CHAT: tNPS chat da semana/mes >= 85 (media de 1 valor = o proprio).
- SO PHONE: tNPS phone da semana/mes >= 85 (idem).
- BACKOFFICE: nao tem tNPS -- usa a faixa maxima de Time Spent (<5min,
  o mesmo corte que vale +40 pts/semana no motor normal) como equivalente.

"Top Performer da semana" continua sem existir oficialmente no Databricks
(so ha Top Performer mensal em usr.csinnovation.csiagentsmetricsoficial);
o proxy usado e o agente com maior soma de Excelencia+tNPS naquela semana
especifica (Engajamento fica de fora do calculo do Boss Battle -- e uma
metrica de participacao, nao de qualidade de atendimento, e ja e premiada
por si so). "Top Performer do mes" e o agente com maior total acumulado
(incluindo os pontos de Boss Battle da semana ja conquistados). Em caso de
empate, desempate alfabetico (deterministico, nao aleatorio).

## v4 -- recalibracao de justica entre grupos (01/09/2026)

A v3 dava a cada grupo (geral / so chat / backoffice) um teto MAXIMO de
pontos diferente por semana e por mes -- quem atuava nos dois canais podia
chegar a 75 pts/semana e 40 pts/mes, enquanto "so chat" parava em 60/31 e
"backoffice" em 55/30, mesmo com nota perfeita. Ou seja, o grupo que faz o
trabalho mais "invisivel" tinha o teto mais baixo, o que nao e justo se
todo mundo disputa o mesmo placar.

Principio da v4: "redistribuicao de canal" -- cada agente tem uma cota
FIXA de pontos por metrica-familia (qualidade de atendimento / skip) e,
se ele so opera em UM canal daquela familia, o canal que ele tem passa a
valer o DOBRO (equivalente a soma dos dois canais de quem atua nos dois).
Isso fecha o teto exatamente, sem inventar um "bonus" solto e sem mexer
na logica de Excelencia (que agora e igual pra todo mundo, pois nao tem
nada a ver com canal).

Tetos unificados (todos os grupos, mesmos valores):
  SEMANAL: Excelencia (25 max) + tNPS (40 max, dividido ou nao entre
  canais) + Engajamento (10) = 75 pts/semana.
  MENSAL: Skip (20 max, dividido ou nao com Unanswered) + Transfer (10)
  + Expired (10) = 40 pts/mes (+ Unanswered 10 max embutido no Skip pra
  quem nao atende phone).

- GERAL (chat + phone): tNPS chat (max 20) + tNPS phone (max 20) = 40.
  Skip (max 10) + Unanswered (max 10) = 20 "familia skip".
- SO CHAT (nao atua phone): tNPS chat DOBRADO (max 40, bandas
  10/20/30/40). Skip DOBRADO (max 20, bandas 20/10/4/-4) pra compensar a
  ausencia de Unanswered.
- SO PHONE (nao atua chat) [grupo hoje vazio, mantido por simetria]: tNPS
  phone DOBRADO (max 40). Skip padrao (mantem Unanswered normal).
- BACKOFFICE (nao atua chat nem phone): tNPS nao se aplica -- o espaco de
  40 pts/semana vira Time Spent com bandas graduadas (<5min=40,
  5-7min=25, 7-9min=10, >=9min=0). Skip DOBRADO (max 20) pra compensar a
  ausencia de Unanswered. Excelencia deixa de ser "em dobro" (agora e
  igual à geral -- Excelencia mede conduta, nao canal).

Badges (Estreia Top, Prêmio UAI de Qualidade, Desbravador de Desafios,
Prêmio UAI Sô) permanecem como estavam na v3 -- ainda nao implementados
no motor (ver README, secao "Limitacoes conhecidas").

## Fontes de dados

- Excelencia / streak: planilha "Central de Inteligencia de CSI 2026"
  (abas 4.Qualidade, 5.Reclamacoes, 6.Erros Ops) -- mesma logica da v2/v3.
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
  Time Spent so tem grao mensal (nao ha query semanal real ainda) -- o
  valor semanal e uma media do mes ate hoje, multiplicada pelo numero de
  segundas ja fechadas (mesma limitacao ja documentada na v3).
- Unanswered Calls (MENSAL): usr.cx_golden_layer.unanswered_calls
  (queue_event__actor, ringing, no_answer). So conta pra quem atua em phone.
- WoW: planilha "Base Faisca H22026", aba "(Automatizacao) WoWs Faisca".
- Engajamento nos canais (SEMANAL): contagem de mensagens/comentarios do
  agente nos 3 canais Slack do time -- #os_incriveis_csi (C0AK68688EQ),
  #wow_csi (C090RS3739N) e #cx-csi-informa (C0209GG9GQ7).
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
  Chat DOBRADO (10/20/30/40); Skip DOBRADO (20/10/4/-4); mantem
  Transfer/Expired gerais.
- SO PHONE (nao atua chat): desconsidera tNPS Chat; tNPS Phone DOBRADO
  (10/20/30/40); Skip padrao (mantem Unanswered normal); mantem
  Transfer/Expired gerais.
- BACKOFFICE PURO (nao atua chat nem phone): Excelencia igual a geral
  (streak 10/15/20/25); desconsidera tNPS e Unanswered; Skip DOBRADO
  (20/10/4/-4); Time Spent semanal com bandas graduadas
  (<5min=40, <7min=25, <9min=10, >=9min=0); mantem Transfer/Expired gerais.
- TODOS: Chama do Encantamento (3+ WoWs no mes = +40, +10/extra);
  Engajamento nos canais (+10/semana para quem mais participou); Boss
  Battle semana (+20) e mes (+50) -- criterio de qualidade por MEDIA dos
  canais do grupo (ver secao v5 acima), implementado a partir da v5.

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
CHANNEL_WOW = "C090RS3739N"        # #wow_csi
CHANNEL_INFORMA = "C0209GG9GQ7"    # #cx-csi-informa

# ---- Bandas de tNPS semanal (v4: tetos unificados em 75 pts/semana) ----
# Geral: tNPS chat (max 20) + tNPS phone (max 20) = 40 "familia tNPS".
TNPS_BANDS_GERAL = [(70, 5), (75, 10), (80.01, 15), (85, 20)]
# So chat / so phone: um unico canal cobre a familia inteira -> bandas em
# dobro (compensacao exata, nao um bonus solto).
TNPS_BANDS_UM_CANAL = [(70, 10), (75, 20), (80.01, 30), (85, 40)]

STREAK_PTS = [10, 15, 20, 25]  # semana 1,2,3,4+ (cap) -- igual pra todo mundo
EXCELENCIA_BASE = 10

# ---- Bandas de Skip mensal (v4: familia skip unificada em 20 pts/mes) ----
# Geral: Skip (max 10) + Unanswered (max 10) = 20 "familia skip".
SKIP_BANDS_GERAL = [(5, 10), (7, 5), (9, 2), (9, -2)]
# Quem nao tem Unanswered (so chat / backoffice): Skip cobre a familia
# inteira -> bandas em dobro.
SKIP_BANDS_DOBRADO = [(5, 20), (7, 10), (9, 4), (9, -4)]
UNANSWERED_BANDS = [(2, 10), (5, 5), (8, 2)]  # acima de 8% = 0 (sem penalidade)
TRANSFER_THRESHOLD = 3
EXPIRED_THRESHOLD = 3

# Time Spent (so backoffice): bandas graduadas que ocupam o espaco de 40
# pts/semana que os outros grupos tiram do tNPS. Minutos = media do mes
# corrente (proxy semanal -- ver limitacao na docstring).
TIME_SPENT_BANDS = [(5, 40), (7, 25), (9, 10)]  # >=9min = 0

BOSS_WEEKLY_PTS = 20
BOSS_MONTHLY_PTS = 50
BOSS_TNPS_THRESHOLD = 85  # media dos canais aplicaveis >= 85 (faixa maxima)
BOSS_TIME_SPENT_MAX_MIN = TIME_SPENT_BANDS[0][0]  # 5min -- equivalente pro backoffice (sem tNPS)

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


def week_quality_pct(grp, chat_entry, phone_entry):
    """Media de tNPS dos canais aplicaveis ao grupo, numa semana especifica.
    chat_entry/phone_entry: {"tnps": pct, "pts": ..., "week_index": i} ou None.
    Retorna None se o grupo nao tem nenhum canal com dado nessa semana
    (ex: backoffice, ou geral sem nenhuma survey na semana)."""
    vals = []
    if grp in ("geral", "chat_only") and chat_entry is not None:
        vals.append(chat_entry["tnps"])
    if grp in ("geral", "phone_only") and phone_entry is not None:
        vals.append(phone_entry["tnps"])
    if not vals:
        return None
    return sum(vals) / len(vals)


def month_quality_pct(grp, chat_entries, phone_entries):
    """Mesma logica de week_quality_pct, mas juntando todas as semanas do
    mes (cada semana pesa igual, sem ponderar por volume de atendimentos)."""
    vals = []
    if grp in ("geral", "chat_only"):
        vals += [e["tnps"] for e in chat_entries]
    if grp in ("geral", "phone_only"):
        vals += [e["tnps"] for e in phone_entries]
    if not vals:
        return None
    return sum(vals) / len(vals)


def compute_boss_battle(records, n_weeks):
    """records: lista de dicts intermediarios por agente (ver main()), com
    'agent', 'group', 'weekly_excelencia', 'tnps_chat_entries',
    'tnps_phone_entries', 'time_spent_min' e 'base_total'.
    Retorna (weekly_pts, weekly_won, monthly_pts, monthly_won), cada um
    {agent: valor}."""
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

    # ---- 4) Engajamento nos canais (override gerado pela tarefa agendada) ----
    engagement_override = {}
    try:
        with open("data/engagement_override.json", encoding="utf-8") as f:
            engagement_override = json.load(f)
    except FileNotFoundError:
        pass  # pendente -- a tarefa agendada no Cowork popula isso via Slack MCP

    # ---- 5) Montar dados intermediarios por agente (sem total nem Boss Battle ainda) ----
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
        skip_pct = ops.get("skip_pct")
        transfer_pct = ops.get("transfer_pct")
        expired_pct = ops.get("expired_pct")
        time_spent_min = ops.get("avg_time_spent_min")
        unanswered_pct = None if grp in ("chat_only", "backoffice") else unanswered_by_agent.get(agent)

        # Skip dobrado pra quem nao tem Unanswered (compensacao exata da familia "skip")
        skip_bands = SKIP_BANDS_DOBRADO if grp in ("chat_only", "backoffice") else SKIP_BANDS_GERAL
        skip_pts = tiered_points(skip_pct, skip_bands)
        unanswered_pts = tiered_points(unanswered_pct, UNANSWERED_BANDS) if unanswered_pct is not None else 0
        transfer_pts = 10 if (transfer_pct is not None and transfer_pct < TRANSFER_THRESHOLD) else 0
        expired_pts = 10 if (expired_pct is not None and expired_pct < EXPIRED_THRESHOLD) else 0
        time_spent_pts = 0
        if grp == "backoffice" and time_spent_min is not None:
            time_spent_pts = tiered_points(time_spent_min, TIME_SPENT_BANDS) * len(closed_mondays)

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
            "ops_total": ops_total,
            "base_total": base_total,
        })

    # ---- 6) Boss Battle (semana +20, mes +50) -- criterio por media de canais ----
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
                "skip": {"pct": r["skip_pct"], "pts": r["skip_pts"]},
                "unanswered": {"pct": r["unanswered_pct"], "pts": r["unanswered_pts"], "applicable": grp not in ("chat_only", "backoffice")},
                "transferIndevido": {"pct": r["transfer_pct"], "pts": r["transfer_pts"]},
                "expired": {"pct": r["expired_pct"], "pts": r["expired_pts"]},
                "timeSpent": {"minutes": r["time_spent_min"], "pts": r["time_spent_pts"], "applicable": grp == "backoffice"},
                "total": r["ops_total"],
            },
            "wow": {"count": r["wow_count"], "pts": r["wow_pts"], "chama": r["chama"]},
            "engagement": {"pts": r["engagement_pts"]},
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
