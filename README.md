# UAI MODO TURBO

Placar de gamificação (checkpoints) do Time Wags, publicado como site estático via GitHub Pages,
com estética de videogame anos 90. Identidade visual: só o mascote (pão de queijo cibernético do UAI).

**Competição válida apenas para setembro/2026.** O motor de pontos foi redesenhado (v3) com
fechamentos semanais (toda segunda-feira) para Excelência, tNPS e Engajamento, e resultado final
do mês para Skip, Unanswered Calls, Transfer indevido, Expired jobs e Time Spent.

## Como funciona

O site abre com uma tela estilo arcade ("INSERT PERFORMANCE TO CONTINUE_") onde o agente digita
o nome, recebe uma saudação ("Oi, [nome]. Que bom que ocê tá aqui, sô!") e então vê o placar.
O nome fica salvo no navegador (localStorage).

O topo da página sempre mostra **até que data os dados são** ("Dados até DD/MM") — importante
porque nem toda métrica fecha no mesmo ritmo (semanal vs. mensal), e o ETL do Databricks tem um
dia de atraso natural.

## Regras do jogo (v3) — setembro/2026

### Geral (quem atua em chat e phone)

- **Excelência** (semanal): sem apontamento de qualidade/complaint/erro operacional = +10 pts.
  **Streak**: semana 2 = 15, semana 3 = 20, semana 4+ = 25 (cap 25). Um apontamento zera a sequência.
- **tNPS Chat** e **tNPS Phone** (semanal, fecha toda segunda): 70–74,99 = +5; 75–80 = +10;
  80,01–85 = +15; 85–100 = +20 (vale a maior faixa da semana, não cumulativo).
- **Skip** (resultado final do mês): <5% = +10; 5,01–7% = +5; 7,01–9% = +2; >9% = -2.
- **Unanswered Calls** (mês, só quem atua em phone): <2% = +10; 2,01–5% = +5; 5,01–8% = +2; >8% = 0.
- **Transfer indevido** (mês): <3% = +10. **Expired jobs** (mês): <3% = +10.

### Quem não atua em phone (só chat)

Desconsidera Unanswered Calls e tNPS Phone. Recebe faixa elevada de **tNPS Chat** (70–74,99=+6;
75–80=+11; 80,01–85=+16; 85–100=+25) e de **Skip** (<5%=+11; 5,01–7%=+6; 7,01–9%=+3; >9%=-5), como
compensação por operar em um único canal. Transfer indevido e Expired seguem a regra geral.

### Quem não atua em chat nem phone (backoffice)

**Excelência** em +20 pts/semana (streak igual). Desconsidera tNPS e Unanswered Calls. Skip segue a
regra geral. **Time Spent** (novo, semanal): média de tempo de atendimento abaixo de 7 minutos =
+10 pts/semana. Transfer indevido e Expired seguem a regra geral.

### Para todos

- **WoW**: +10 pts por WoW aprovada. **Chama do Encantamento**: 3+ WoWs no mês = +40, +10/extra.
- **Engajamento nos canais** (semanal): quem mais comentou e incentivou o time na semana nos canais
  #os_incríveis_csi, #copa_canguru_wow2026 e #cx-csi-informa ganha +10 pts.
- **Boss Battle da semana**: Top Performer da semana com tNPS chat e phone ≥85 na semana: +20 pts.
  **Boss Battle do mês**: mesma lógica, apurada no mês: +50 pts.

### Badges e prêmios

- **Estreia Top**: 1ª vez na carreira do agente como Top Performer (evento único, sem pontos).
- **Prêmio UAI de Qualidade**: quem não tiver apontamento de qualidade na semana e tiver alta volumetria.
- **Desbravador de Desafios**: menor Skip da semana.
- **Prêmio UAI Sô** ("a gente gosta é de conversar"): menor Unanswered Calls da semana.

## Fontes de dados

| Métrica | Fonte | Granularidade |
|---|---|---|
| Excelência / streak | Planilha "Central de Inteligência de CSI 2026" (abas Qualidade, Reclamações, Erros Ops) | Semanal |
| tNPS Chat / Phone | `etl.br__dataset.cx_metrics_tnps_resolutivity` + `cx_canonical_activities` (mesma query da skill `tnps-weekly-dm-time-wags`), filtrado por `channel` | Semanal (fecha segunda) |
| Skip / Transfer indevido / Expired / Time Spent | `etl.br__dataset.cx_canonical_activities` (`status`, `is_transfer_indevido`, `mount_time_spent`, `net_time_spent`) | Mensal (acumulado até hoje) |
| Unanswered Calls | `usr.cx_golden_layer.unanswered_calls` (`queue_event__actor`, `ringing`, `no_answer`) | Mensal (acumulado até hoje) |
| WoW | Planilha "Base Faísca H22026" | Mensal (acumulado) |
| Engajamento nos canais | Slack — #os_incríveis_csi (`C0AK68688EQ`), #copa_canguru_wow2026 (`C0B6H07JLEA`), #cx-csi-informa (`C0209GG9GQ7`) | Semanal |

## Limitações conhecidas e decisões em aberto

- **Classificação de canal por agente** (geral / só chat / backoffice) é baseada no histórico de
  agosto/26 (quem tinha ou não linhas em `unanswered_calls`/tNPS phone). Hoje: andresa.britto,
  caren.paraiso e lucrecia.santos = só chat; nenhum agente identificado como backoffice puro ou
  só phone. Revalidar mensalmente — se alguém mudar de canal, atualizar as listas em
  `scripts/generate_scoreboard.py` (`CHAT_ONLY`, `PHONE_ONLY`, `NO_CHANNEL`).
- **"Quem não atua em chat" (só phone)** não teve uma tabela elevada de tNPS/Skip especificada por
  Wagner (ele só detalhou o caso "só chat"). Por ora esse grupo usa as tabelas gerais. Avisar se
  precisar de valores elevados simétricos.
- **"Top Performer da semana"** não existe como campo oficial no Databricks (só há Top Performer
  mensal em `usr.csinnovation.csiagentsmetricsoficial`). Para o Boss Battle da semana, uso como
  proxy quem está em 1º lugar no placar acumulado daquela semana — avisar se quiser outra definição.
- **"Alta volumetria"** (critério do Prêmio UAI de Qualidade) ainda não tem um limite numérico
  definido — hoje o badge fica pendente até definirmos o corte (ex: acima da mediana de atendimentos
  do time na semana).
- **Engajamento nos canais**: a contagem de mensagens do Slack é feita pela tarefa agendada diária
  (roda dentro do Cowork, com acesso ao Slack) e grava em `data/engagement_override.json`; o script
  Python autônomo não tem acesso a essas ferramentas, então só lê esse arquivo se ele existir.
- **Níveis (Bronze/Prata/Ouro/Diamante)** foram recalibrados para o teto de pontos mais alto da v3
  (Diamante ≥300, Ouro ≥180, Prata ≥90), mas são provisórios — vamos ajustar depois dos primeiros
  fechamentos semanais reais de setembro.
- **01/09/2026**: dia de início da competição. O ETL do Databricks ainda não tinha processado o
  dia quando este snapshot foi gerado, e a 1ª segunda-feira de fechamento é 07/09/2026 — por isso
  o placar começa zerado para todo mundo.

## Automação

A atualização diária às 9h roda como uma **tarefa agendada no Cowork** (não GitHub Actions): um
agente Claude executa o pipeline (Databricks via fetch autenticado, Google Sheets, Slack, e o push
pro GitHub) usando as credenciais já usadas pela skill `daily-briefing-wags` (mesmo host/token/
warehouse). O script `scripts/generate_scoreboard.py` documenta as fórmulas e pode ser usado como
referência ou rodado manualmente/via GitHub Actions se os secrets abaixo forem configurados —
mas ele não tem acesso a Slack, por isso o campo de Engajamento depende do arquivo
`data/engagement_override.json` gerado pela tarefa agendada.

| Secret (uso opcional/manual) | O que é |
|---|---|
| `DATABRICKS_HOST` | host do workspace Databricks (sem `https://`) |
| `DATABRICKS_TOKEN` | personal access token ou service principal token com leitura na tabela |
| `DATABRICKS_WAREHOUSE_ID` | id do SQL warehouse a usar nas queries |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | conteúdo JSON de uma service account do Google com acesso de leitor nas planilhas |
| `XFORCE_EMAIL` | (opcional) email do xforce a filtrar; default `wagner.santos@nubank.com.br` |

## Como habilitar o site (uma vez)

1. Vá em **Settings > Pages** deste repositório.
2. Em **Build and deployment > Source**, escolha **Deploy from a branch**.
3. Branch: `main`, pasta: `/ (root)`.
4. Salve. O site fica em `https://wagnerhssantos.github.io/wags-checkpoints-arcade/`.

## Identidade visual

- `assets/uai-mascot.b64.txt`: mascote (pão de queijo cibernético) em base64, carregado via
  `data:` URI no navegador.
- `assets/emblem.svg`: emblema original da v1, não é mais usado na tela (mantido no repo por
  histórico). A identidade visual atual usa só o mascote.
