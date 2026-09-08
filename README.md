# UAI MODO TURBO

Placar de gamificação (checkpoints) do Time Wags, publicado como site estático via GitHub Pages,
com estética de videogame anos 90. Identidade visual: só o mascote (pão de queijo cibernético do UAI).

**Competição válida apenas para setembro/2026.** O motor de pontos foi redesenhado (v3) com
fechamentos semanais (toda segunda-feira) para Excelência, tNPS e Engajamento, e resultado final
do mês para Skip, Unanswered Calls, Transfer indevido, Expired jobs e Time Spent. Na v4, os tetos
de pontos foram recalibrados pra ficarem iguais entre os grupos de agente (geral / só chat / só
phone / backoffice). Na v5, o Boss Battle passou a valer de verdade, com um critério de qualidade
por média dos canais de cada grupo. Na **v6**, o Engajamento deixou de ser "quem mais postou leva
tudo" e passou a contar as três formas de engajar — ver "Regras do jogo" abaixo.

## Como funciona

O site abre com uma tela estilo arcade ("INSERT PERFORMANCE TO CONTINUE_") onde o agente digita
o nome, recebe uma saudação ("Oi, [nome]. Que bom que ocê tá aqui, sô!") e então vê o placar.
O nome fica salvo no navegador (localStorage).

O topo da página sempre mostra **até que data os dados são** ("Dados até DD/MM") — importante
porque nem toda métrica fecha no mesmo ritmo (semanal vs. mensal), e o ETL do Databricks tem um
dia de atraso natural.

## Regras do jogo (v6) — setembro/2026

**v4 recalibra os tetos de pontos pra ficarem IGUAIS nos 3 grupos** — 75 pts/semana e 40 pts/mês
no máximo, não importa quantos canais o agente atende. Na v3, quem atendia só um canal (ou nenhum)
tinha um teto máximo mais baixo que quem atendia os dois, mesmo com nota perfeita — o que não é
justo numa competição de placar único. A regra é sempre a mesma: se você só tem UM canal disponível
numa família de métrica (tNPS, ou Skip/Unanswered), esse canal passa a valer o DOBRO, cobrindo
exatamente o espaço do canal que falta. Ver detalhamento e a matemática completa no topo do
`scripts/generate_scoreboard.py`.

### Geral (quem atua em chat e phone)

- **Excelência** (semanal): sem apontamento de qualidade/complaint/erro operacional = +10 pts.
  **Streak**: semana 2 = 15, semana 3 = 20, semana 4+ = 25 (cap 25). Um apontamento zera a sequência.
  Vale igual pra todo mundo, em qualquer grupo — Excelência mede conduta, não canal.
- **tNPS Chat** e **tNPS Phone** (semanal, fecha toda segunda): 70–74,99 = +5; 75–80 = +10;
  80,01–85 = +15; 85–100 = +20 (vale a maior faixa da semana, não cumulativo). Máximo 40 pts/semana
  somando os dois canais.
- **Skip** (resultado final do mês): <5% = +10; 5,01–7% = +5; 7,01–9% = +2; >9% = -2.
- **Unanswered Calls** (mês, só quem atua em phone): <2% = +10; 2,01–5% = +5; 5,01–8% = +2; >8% = 0.
  Máximo 20 pts/mês somando Skip + Unanswered.
- **Transfer indevido** (mês): <3% = +10. **Expired jobs** (mês): <3% = +10.

### Quem não atua em phone (só chat)

Desconsidera Unanswered Calls e tNPS Phone. **tNPS Chat em dobro** (70–74,99=+10; 75–80=+20;
80,01–85=+30; 85–100=+40 — mesmo teto de 40 pts/semana que geral tira de dois canais). **Skip em
dobro** (<5%=+20; 5,01–7%=+10; 7,01–9%=+4; >9%=-4 — cobre o espaço do Unanswered que não existe).
Transfer indevido e Expired seguem a regra geral.

### Quem não atua em chat (só phone)

Simétrico ao "só chat": desconsidera tNPS Chat. **tNPS Phone em dobro** (mesmas faixas do tNPS Chat
em dobro acima). Skip segue a regra geral (mantém Unanswered normal, já que atua em phone). Transfer
indevido e Expired seguem a regra geral. Hoje nenhum agente do time está classificado neste grupo —
mantido por simetria, caso alguém mude de canal.

### Quem não atua em chat nem phone (backoffice)

**Excelência** igual à regra geral (não é mais em dobro — ver nota da v4 acima). Desconsidera tNPS e
Unanswered Calls. **Skip em dobro** (mesma lógica do "só chat", cobre o espaço do Unanswered).
**Time Spent** (semanal) ocupa o espaço de 40 pts/semana que os outros tiram do tNPS, com faixas
graduadas: <5min = +40; <7min = +25; <9min = +10; ≥9min = 0. Transfer indevido e Expired seguem a
regra geral.

### Para todos

- **WoW**: +10 pts por WoW aprovada. **Chama do Encantamento**: 3+ WoWs no mês = +40, +10/extra.
- **Engajamento nos canais (v6 — semanal, fecha toda segunda): +10 pts para QUEM ENGAJOU DE
  QUALQUER FORMA na semana**, nos canais #os_incríveis_csi, #wow_csi e #cx-csi-informa. Conta
  igualmente: (a) mensagem de nível superior no canal, (b) resposta em thread, **(c) curtida /
  reação em post de colega**. Basta UMA dessas coisas para ganhar os 10 pts — não é ranking, não é
  "quem mais participou". Quem não teve nenhum registro na semana fica com 0. O teto continua sendo
  10 pts/semana (ninguém ganha 30 por fazer as três coisas), então os 75 pts/semana da v4 seguem
  válidos.
- **Boss Battle da semana**: Top Performer (proxy: maior soma de Excelência+tNPS na semana) que
  também cumpra o critério de qualidade daquele grupo: +20 pts. **Boss Battle do mês**: mesma
  lógica, mas com o agente de maior total acumulado no mês (incluindo Boss Battles semanais já
  ganhas): +50 pts. **Critério de qualidade (v5, por média dos canais do grupo)**: geral = média
  entre tNPS chat e tNPS phone ≥85; só chat = tNPS chat ≥85; só phone = tNPS phone ≥85; backoffice
  (sem tNPS) = Time Spent na faixa máxima (<5min). Se o Top Performer da vez não cumprir o critério,
  ninguém ganha o Boss Battle naquele período. Empate no placar é resolvido alfabeticamente.
  Engajamento fica de fora do cálculo do Boss Battle — é métrica de participação, não de qualidade
  de atendimento.

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
| Engajamento nos canais | Slack — #os_incríveis_csi (`C0AK68688EQ`), #wow_csi (`C090RS3739N`), #cx-csi-informa (`C0209GG9GQ7`). Mensagens via `slack_read_channel`, respostas via `slack_read_thread`, reações via `slack_get_reactions` | Semanal |

### Como coletar o Engajamento (v6) — passo a passo para a tarefa agendada

Para cada um dos 3 canais, na janela da semana fechada (segunda anterior 00:00 até domingo 23:59,
America/Sao_Paulo):

1. `slack_read_channel` com `response_format: "detailed"` — o detalhado é o que mostra
   `Thread: N replies` e `Reactions:` em cada mensagem. Anote o `Message TS` de cada uma.
2. Para cada mensagem com `Thread: N replies`, chame `slack_read_thread` e conte as respostas dos
   agentes do roster.
3. Para cada mensagem com `Reactions:`, chame `slack_get_reactions` e veja quais agentes do roster
   reagiram.
4. Grave em `data/engagement_override.json` no formato
   `{"semana_iso": {"agente": {"msgs": N, "threads": N, "emojis": N, "postsReagidos": N, "score": N}}}`.
   `score = 3*msgs + 2*threads + 1*postsReagidos` — serve só para ranquear intensidade no
   acompanhamento individual, **não** define pontos.
5. Pontuação: qualquer agente com `msgs`, `threads` ou `postsReagidos` > 0 ganha +10 na semana.

Excluir sempre das contagens: o Wagner (liderança) e os bots (UAI, Faísca, Claude).

## Limitações conhecidas e decisões em aberto

- **"Top Performer da semana" é um proxy**, não um campo oficial do Databricks (só existe Top
  Performer mensal em `usr.csinnovation.csiagentsmetricsoficial`). O proxy usado é o agente com
  maior soma de Excelência+tNPS naquela semana específica. Vale a pena revisar se um Top Performer
  oficial semanal passar a existir na fonte de dados.
- **Classificação de canal por agente** (geral / só chat / só phone / backoffice) é baseada no
  histórico de agosto/26 (quem tinha ou não linhas em `unanswered_calls`/tNPS phone). Hoje:
  andresa.britto, caren.paraiso e lucrecia.santos = só chat; nenhum agente identificado como
  backoffice puro ou só phone (grupos mantidos vazios por simetria). Revalidar mensalmente — se
  alguém mudar de canal, atualizar as listas em `scripts/generate_scoreboard.py` (`CHAT_ONLY`,
  `PHONE_ONLY`, `NO_CHANNEL`).
- **"Alta volumetria"** (critério do Prêmio UAI de Qualidade) ainda não tem um limite numérico
  definido — hoje o badge fica pendente até definirmos o corte (ex: acima da mediana de atendimentos
  do time na semana).
- **Teto de 50 usuários por emoji no Slack**: a API `slack_get_reactions` lista no máximo 50 pessoas
  por emoji (o total vem certo, a lista é que é truncada). Em posts CSI-wide muito curtidos isso
  subestima quem reagiu. **Não afeta a pontuação da v6**, que é binária (engajou ou não) — mas
  subestima os campos `emojis`/`postsReagidos` de quem mais reage. Só vira problema se um dia a
  regra voltar a ser graduada.
- **Engajamento não distingue intensidade (v6)**: como qualquer forma de engajar vale os mesmos 10
  pts, quem responde 19 threads e quem dá uma curtida na semana pontuam igual. Foi uma escolha
  deliberada — a métrica é de participação e serve pra puxar todo mundo pro canal, não pra
  ranquear. O campo `score` no `engagement_override.json` preserva a intensidade caso a gente
  queira usar num bônus separado depois.
- **Níveis (Bronze/Prata/Ouro/Diamante)** foram recalibrados para o teto de pontos mais alto da v3
  (Diamante ≥300, Ouro ≥180, Prata ≥90), mas são provisórios — vamos ajustar depois dos primeiros
  fechamentos semanais reais de setembro.
- **01/09/2026**: dia de início da competição. A 1ª segunda-feira de fechamento foi 07/09/2026.

### Resolvido na v4 (não é mais uma limitação)

- ~~Tetos de pontos desiguais entre grupos~~ — corrigido: 75 pts/semana e 40 pts/mês pros 3 grupos.
- ~~"Quem não atua em chat" (só phone) sem tabela elevada~~ — corrigido: tNPS Phone em dobro.
- ~~Excelência em dobro só pro backoffice, sem justificativa clara~~ — corrigido: Excelência agora
  vale igual pra todo mundo.

### Resolvido na v5 (não é mais uma limitação)

- ~~Boss Battle não implementado no motor de pontos~~ — corrigido: `compute_boss_battle()` calcula
  semana a semana (e o fechamento mensal) quem é o Top Performer e se cumpre o critério do grupo.
- ~~Critério "tNPS chat E phone ≥85" impossível pra quem só tem um canal~~ — corrigido: o critério
  agora é a MÉDIA dos canais aplicáveis ao grupo.

### Resolvido na v6 (não é mais uma limitação)

- ~~Engajamento contava só mensagens de nível superior~~ — corrigido: agora conta mensagem, resposta
  em thread E reação/curtida. A régua antiga media *quem posta*, não *quem engaja*.
- ~~"Quem mais comentou ganha tudo" concentrava 10 pts numa pessoa só~~ — corrigido: agora todo mundo
  que engajou de qualquer forma leva os 10 pts. **Diagnóstico que motivou a mudança (semana 36):**
  13 dos 14 agentes engajaram na semana e apenas 1 pontuou. A agente mais engajada do time
  (19 respostas em thread, reações em 43 posts distintos) tirava zero por não abrir tópicos novos,
  enquanto o vencedor liderava em mensagens mas era só o 8º em posts reagidos. O pódio era artefato
  da métrica, não do comportamento.

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
