# UAI MODO TURBO

Placar de gamificação (checkpoints) do Time Wags, publicado como site estático via GitHub Pages,
com estética de videogame anos 90. Identidade visual: só o mascote (pão de queijo cibernético do UAI).

**Competição válida apenas para setembro/2026.** O motor de pontos foi redesenhado (v3) com
fechamentos semanais (toda segunda-feira) para Excelência, tNPS e Engajamento, e resultado final
do mês para Skip, Unanswered Calls, Expired jobs e Time Spent. Na v4, os tetos
de pontos foram recalibrados pra ficarem iguais entre os grupos de agente (geral / só chat / só
phone / backoffice). Na v5, o Boss Battle passou a valer de verdade, com um critério de qualidade
por média dos canais de cada grupo. Na v6, o Engajamento deixou de ser "quem mais postou leva
tudo". Na **v7**, o Transfer indevido saiu da pontuação e o Skip passou a contar só chat e
backoffice — ver "Regras do jogo" abaixo.

## Como funciona

O site abre com uma tela estilo arcade ("INSERT PERFORMANCE TO CONTINUE_") onde o agente digita
o nome, recebe uma saudação ("Oi, [nome]. Que bom que ocê tá aqui, sô!") e então vê o placar.
O nome fica salvo no navegador (localStorage).

O topo da página sempre mostra **até que data os dados são** ("Dados até DD/MM") — importante
porque nem toda métrica fecha no mesmo ritmo (semanal vs. mensal), e o ETL do Databricks tem um
dia de atraso natural.

## Mudanças da v7 — decidido pelo Wagner em 09/09/2026

### 1. Transfer indevido sai da pontuação (vira só monitoramento)

O Transfer indevido **não vale mais pontos** durante o mês. O percentual continua sendo apurado e
publicado no `scoreboard.json` (campo `ops.transferIndevido.pct`) para acompanhamento individual
com a liderança, mas com `pts: 0`, `applicable: false` e `monitoringOnly: true` — o site renderiza
a coluna como "—".

**A métrica volta a pontuar no fechamento do mês**, quando o resultado final estiver consolidado.
Até lá é só termômetro.

### 2. Os 10 pts do Transfer foram para o Expired

Pra manter o teto mensal de 40 pts da v4 sem redesenhar nada, o **Expired jobs passou de +10 para
+20 pts** (mesmo corte: abaixo de 3%). Assim os tetos continuam idênticos nos três grupos:

| Grupo | Skip | Unanswered | Expired | Total/mês |
|---|---|---|---|---|
| Geral (chat + phone) | 10 | 10 | 20 | **40** |
| Só chat | 20 (dobrado) | — | 20 | **40** |
| Só phone (grupo vazio hoje) | 10 | 10 | 20 | **40** |
| Backoffice | 20 (dobrado) | — | 20 | **40** |

Quando o Transfer voltar a pontuar no fechamento, o Expired volta pra 10 e o Transfer retoma os
seus 10 — o teto de 40 não muda em nenhum dos dois cenários.

### 3. Skip conta apenas chat e backoffice

O Skip agora é calculado **só sobre atendimentos de `chat` e `backoffice`** — numerador E
denominador. Ou seja:

```
Skip % = skips em (chat + backoffice) / total de atendimentos em (chat + backoffice)
```

Atendimentos de `email` e `inbound_call` ficam completamente fora da conta. Isso importa mais do
que parece: na apuração de 01 a 07/09, **nenhum skip do time aconteceu em `inbound_call`**, e um
volume relevante deles estava em `email` — no caso da Lucrecia, 25 dos 28 skips do mês eram de
e-mail, o que jogava o Skip dela pra 8,46% quando o número real de chat+backoffice é 1,63%.
Manter o denominador restrito também evita diluir o percentual de quem atende muito fone.

## Regras do jogo (v7) — setembro/2026

**Tetos de pontos IGUAIS nos 3 grupos** — 75 pts/semana e 40 pts/mês no máximo, não importa
quantos canais o agente atende. A regra é sempre a mesma: se você só tem UM canal disponível numa
família de métrica (tNPS, ou Skip/Unanswered), esse canal passa a valer o DOBRO, cobrindo
exatamente o espaço do canal que falta. Ver detalhamento e a matemática completa no topo do
`scripts/generate_scoreboard.py`.

### Geral (quem atua em chat e phone)

- **Excelência** (semanal): sem apontamento de qualidade/complaint/erro operacional = +10 pts.
  **Streak**: semana 2 = 15, semana 3 = 20, semana 4+ = 25 (cap 25). Um apontamento zera a sequência.
  Vale igual pra todo mundo, em qualquer grupo — Excelência mede conduta, não canal.
- **tNPS Chat** e **tNPS Phone** (semanal, fecha toda segunda): 70–74,99 = +5; 75–80 = +10;
  80,01–85 = +15; 85–100 = +20 (vale a maior faixa da semana, não cumulativo). Máximo 40 pts/semana
  somando os dois canais.
- **Skip** (resultado final do mês, **só chat + backoffice**): <5% = +10; 5,01–7% = +5;
  7,01–9% = +2; >9% = -2.
- **Unanswered Calls** (mês, só quem atua em phone): <2% = +10; 2,01–5% = +5; 5,01–8% = +2; >8% = 0.
  Máximo 20 pts/mês somando Skip + Unanswered.
- **Expired jobs** (mês): <3% = **+20**.
- **Transfer indevido** (mês): **0 pts — só monitoramento na v7**, retomado no fechamento do mês.

### Quem não atua em phone (só chat)

Desconsidera Unanswered Calls e tNPS Phone. **tNPS Chat em dobro** (70–74,99=+10; 75–80=+20;
80,01–85=+30; 85–100=+40 — mesmo teto de 40 pts/semana que geral tira de dois canais). **Skip em
dobro** (<5%=+20; 5,01–7%=+10; 7,01–9%=+4; >9%=-4 — cobre o espaço do Unanswered que não existe),
também calculado só sobre chat + backoffice. Expired segue a regra geral (+20). Transfer indevido
não pontua.

### Quem não atua em chat (só phone)

Simétrico ao "só chat": desconsidera tNPS Chat. **tNPS Phone em dobro** (mesmas faixas do tNPS Chat
em dobro acima). Skip segue a regra geral (mantém Unanswered normal, já que atua em phone) — mas
repare que, com o Skip restrito a chat+backoffice, um agente 100% phone tende a ficar sem base de
cálculo de Skip. Hoje nenhum agente do time está classificado neste grupo — mantido por simetria,
caso alguém mude de canal. **Revisar essa interação antes de classificar alguém como só phone.**

### Quem não atua em chat nem phone (backoffice)

**Excelência** igual à regra geral. Desconsidera tNPS e Unanswered Calls. **Skip em dobro** (mesma
lógica do "só chat"). **Time Spent** (semanal) ocupa o espaço de 40 pts/semana que os outros tiram
do tNPS, com faixas graduadas: <5min = +40; <7min = +25; <9min = +10; ≥9min = 0. Expired segue a
regra geral (+20). Transfer indevido não pontua.

### Para todos

- **WoW**: +10 pts por WoW aprovada. **Chama do Encantamento**: 3+ WoWs no mês = +40, +10/extra.
- **Engajamento nos canais (v6 — semanal, fecha toda segunda): +10 pts para QUEM ENGAJOU DE
  QUALQUER FORMA na semana**, nos canais #os_incríveis_csi, #wow_csi e #cx-csi-informa. Conta
  igualmente: (a) mensagem de nível superior no canal, (b) resposta em thread, **(c) curtida /
  reação em post de colega**. Basta UMA dessas coisas para ganhar os 10 pts — não é ranking, não é
  "quem mais participou". Quem não teve nenhum registro na semana fica com 0. O teto continua sendo
  10 pts/semana (ninguém ganha 30 por fazer as três coisas).
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
| Skip | `etl.br__dataset.cx_canonical_activities`, **filtrando `activity_type IN ('chat','backoffice')`** (v7) | Mensal (acumulado até hoje) |
| Transfer indevido / Expired / Time Spent | `etl.br__dataset.cx_canonical_activities` (`is_transfer_indevido`, `status`, `mount_time_spent`, `net_time_spent`) — base completa | Mensal (acumulado até hoje) |
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

Se a janela da semana fechada não mudou desde a última execução, reaproveite o
`engagement_override.json` já publicado em vez de recontar o Slack.

Excluir sempre das contagens: o Wagner (liderança) e os bots (UAI, Faísca, Claude).

## Limitações conhecidas e decisões em aberto

- **Transfer indevido está congelado** (v7). Precisa ser retomado no fechamento de setembro: voltar
  `TRANSFER_PTS` para 10 e `EXPIRED_PTS` para 10 em `scripts/generate_scoreboard.py`.
- **Skip para agente "só phone"**: com o Skip restrito a chat+backoffice, um agente 100% phone
  ficaria sem base de cálculo. O grupo está vazio hoje, mas a interação precisa ser resolvida antes
  de classificar alguém nele.
- **Time Spent fura o teto mensal do backoffice**: `time_spent_pts` é multiplicado pelo número
  de segundas fechadas e depois somado ao `ops_total`, que é o balde mensal de 40 pts. Com 4
  semanas fechadas, um backoffice puro chegaria a 160 pts só de Time Spent. `NO_CHANNEL` está
  vazio, então ninguém é afetado hoje — mas resolver antes de classificar alguém no grupo.
  A raiz é conceitual: Time Spent é métrica SEMANAL (ocupa os 40 pts/semana do tNPS) e não
  deveria estar no balde mensal.
- **"Top Performer da semana" é um proxy**, não um campo oficial do Databricks (só existe Top
  Performer mensal em `usr.csinnovation.csiagentsmetricsoficial`). O proxy usado é o agente com
  maior soma de Excelência+tNPS naquela semana específica.
- **Classificação de canal por agente** (geral / só chat / só phone / backoffice) é baseada no
  histórico de agosto/26. Hoje: andresa.britto, caren.paraiso e lucrecia.santos = só chat; nenhum
  agente backoffice puro ou só phone. Revalidar mensalmente — se alguém mudar de canal, atualizar
  as listas em `scripts/generate_scoreboard.py` (`CHAT_ONLY`, `PHONE_ONLY`, `NO_CHANNEL`).
- **"Alta volumetria"** (critério do Prêmio UAI de Qualidade) ainda não tem um limite numérico
  definido — hoje o badge fica pendente até definirmos o corte.
- **Teto de 50 usuários por emoji no Slack**: a API `slack_get_reactions` lista no máximo 50 pessoas
  por emoji. **Não afeta a pontuação da v6**, que é binária — mas subestima os campos
  `emojis`/`postsReagidos` de quem mais reage.
- **Engajamento não distingue intensidade (v6)**: quem responde 19 threads e quem dá uma curtida na
  semana pontuam igual. Escolha deliberada — a métrica é de participação. O campo `score` no
  `engagement_override.json` preserva a intensidade caso a gente queira um bônus separado depois.
- **Níveis (Bronze/Prata/Ouro/Diamante)** foram recalibrados para o teto de pontos mais alto da v3
  (Diamante ≥300, Ouro ≥180, Prata ≥90), mas são provisórios.
- **01/09/2026**: dia de início da competição. A 1ª segunda-feira de fechamento foi 07/09/2026.

### Resolvido na v4

- ~~Tetos de pontos desiguais entre grupos~~ — corrigido: 75 pts/semana e 40 pts/mês pros 3 grupos.
- ~~"Quem não atua em chat" (só phone) sem tabela elevada~~ — corrigido: tNPS Phone em dobro.
- ~~Excelência em dobro só pro backoffice~~ — corrigido: Excelência agora vale igual pra todo mundo.

### Resolvido na v5

- ~~Boss Battle não implementado no motor de pontos~~ — corrigido: `compute_boss_battle()`.
- ~~Critério "tNPS chat E phone ≥85" impossível pra quem só tem um canal~~ — corrigido: agora é a
  MÉDIA dos canais aplicáveis ao grupo.

### Resolvido na v6

- ~~Engajamento contava só mensagens de nível superior~~ — corrigido: conta mensagem, resposta em
  thread E reação/curtida.
- ~~"Quem mais comentou ganha tudo" concentrava 10 pts numa pessoa só~~ — corrigido: todo mundo que
  engajou leva os 10 pts.

### Resolvido na v7

- ~~Skip contava skips de e-mail e inbound_call~~ — corrigido: só chat + backoffice, numerador e
  denominador. Skips de e-mail estavam distorcendo o número de quem faz muito backoffice.
- ~~Transfer indevido pontuando com dado ainda em movimento no meio do mês~~ — congelado como
  monitoramento até o fechamento.

## Automação

A atualização diária às 9h roda como uma **tarefa agendada no Cowork** (não GitHub Actions): um
agente Claude executa o pipeline (Databricks, Google Sheets, Slack, e o push pro GitHub) usando as
credenciais já usadas pela skill `daily-briefing-wags`. O script `scripts/generate_scoreboard.py`
documenta as fórmulas e pode ser rodado manualmente/via GitHub Actions se os secrets abaixo forem
configurados — mas ele não tem acesso a Slack, por isso o campo de Engajamento depende do arquivo
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
