# UAI MODO TURBO

Placar de gamificação (checkpoints) do Time Wags, publicado como site estático via GitHub Pages,
com estética de videogame anos 90. Identidade visual: só o mascote (pão de queijo cibernético do UAI).

**Competição válida apenas para setembro/2026.** O motor de pontos foi redesenhado (v3) com
fechamentos semanais (toda segunda-feira) para Excelência, tNPS e Engajamento, e resultado final
do mês para Skip, Unanswered Calls, Expired jobs e Time Spent. Na v4, os tetos
de pontos foram recalibrados pra ficarem iguais entre os grupos de agente (geral / só chat / só
phone / backoffice). Na v5, o Boss Battle passou a valer de verdade, com um critério de qualidade
por média dos canais de cada grupo. Na v6, o Engajamento deixou de ser "quem mais postou leva
tudo". Na v7, o Transfer indevido saiu da pontuação e o Skip passou a contar só chat e
backoffice. Na v8, o Boss Battle do mês foi removido (ficou só o da semana) e o painel deixou
de exibir as colunas de Transfer indevido e Time Spent. Na **v9**, o Boss Battle da semana passou
a ser **compartilhado entre todos os empatados no topo** (acabou o desempate alfabético) e os
cortes de nível foram recalibrados para o teto real de um mês de 4 semanas — ver "Regras do jogo"
abaixo.

## Como funciona

O site abre com uma tela estilo arcade ("INSERT PERFORMANCE TO CONTINUE_") onde o agente digita
o nome, recebe uma saudação ("Oi, [nome]. Que bom que ocê tá aqui, sô!") e então vê o placar.
O nome fica salvo no navegador (localStorage).

O topo da página sempre mostra **até que data os dados são** ("Dados até DD/MM") — importante
porque nem toda métrica fecha no mesmo ritmo (semanal vs. mensal), e o ETL do Databricks tem um
dia de atraso natural.

## Mudanças da v9 — decidido pelo Wagner em 14/09/2026

### 1. Boss Battle da semana agora é compartilhado

O Boss Battle deixou de ter um único vencedor por semana. **Todos os agentes que empatarem no topo
do score da semana E cumprirem o critério de qualidade do seu grupo ganham o Boss Battle.**

- **1 vencedor sozinho: +20 pts** (valor da v8, inalterado).
- **2 ou mais vencedores: +10 pts para cada um.**

O desempate alfabético **foi eliminado**. Ele era o mecanismo que decidia de fato quem ganhava, e
tinha um viés permanente e indefensável: nomes começados em A (Andresa, Angela, Angelica) venciam
praticamente todo empate, para sempre.

**Por que a mudança:** empate no topo não é exceção, é a norma — e é estrutural, não azar. O score
do Boss Battle é Excelência (idêntica para todo mundo, 10/15/20/25 conforme o streak) + tNPS
convertido em faixas com teto de 40 pts/semana. O teto semanal é baixo e a granularidade é grossa,
então quanto melhor o time fica, mais gente encosta no teto.

Nas duas primeiras semanas de setembro, **8 pessoas-semana cumpriram integralmente o critério e só
2 recebiam os pontos**:

| Semana | Empatados no topo | Passaram no critério | Pagos na v8 | Pagos na v9 |
|---|---|---|---|---|
| 36 (teto 50) | Andresa, Angelica, Giulia | os 3 | só Andresa | os 3 (+10 cada) |
| 37 (teto 55) | Angelica, Caren, Gabrielle, Giulia, Guilherme | os 5 | só Angelica | os 5 (+10 cada) |

Repare na semana 37: o teto era 15 (Excelência) + 40 (tNPS) = **55**, e cinco pessoas cravaram 55.
Não foi empate apertado — foi **nota máxima batida por cinco agentes**.

Aplicado **retroativamente** a setembro inteiro. Efeito no placar de 14/09:

| Agente | v8 | v9 | Δ |
|---|---|---|---|
| angelica.almeida | 195 | 195 | — |
| giulia.machado | 160 | 180 | +20 |
| andresa.britto | 165 | 155 | -10 |
| caren.paraiso | 145 | 155 | +10 |
| guilherme.zunareli | 127 | 137 | +10 |
| gabrielle.macedo | 120 | 130 | +10 |

O badge "BOSS BATTLE DA SEMANA" passa a aparecer para 6 agentes em vez de 2 — o site já renderiza
isso automaticamente, um item por agente com `bossBattle.weekly = true`.

**Atenção ao ler o JSON:** `bossBattle.weeklyPts` agora pode ser 10, 20, 30 ou 40 no acumulado do
mês, dependendo de quantas semanas o agente venceu e se venceu sozinho ou dividido. `weekly` é
booleano e só indica "ganhou pelo menos uma vez no mês".

### 2. Níveis recalibrados para o teto real de 4 semanas

Os cortes antigos (Diamante ≥300, Ouro ≥180, Prata ≥90) foram calibrados no teto da v3 e o próprio
README já os marcava como provisórios. O problema que apareceu foi o oposto do previsto: em vez de
travar todo mundo no Bronze, **o placar dispara para o Ouro no meio do mês**. Na semana 2, 11 dos
14 agentes já estavam em Prata e o 1º lugar estava a 15 pts do Ouro.

A causa é o acúmulo semanal. Setembro tem 4 segundas de fechamento (07, 14, 21, 28) e cada uma
adiciona até 75 pts (Excelência até 25 + tNPS até 40 + Engajamento 10), fora o balde mensal de 40.
Projeção de um agente mantendo forma perfeita:

```
Excelência   10+15+20+25 =  70
tNPS         40 x 4      = 160
Engajamento  10 x 4      =  40
Ops (teto mensal)        =  40
WoW                      =  10
                          ----
                           320   <- Diamante SEM nenhum Boss Battle
```

Cortes novos, escalados para o teto realista de ~390 pts no mês fechado:

| Nível | Corte antigo | **Corte novo (v9)** |
|---|---|---|
| DIAMANTE | ≥300 | **≥320** |
| OURO | ≥180 | **≥240** |
| PRATA | ≥90 | **≥150** |
| BRONZE | <90 | **<150** |

Com isso, o placar de 14/09 (metade do mês) fica com 4 agentes em Prata e 10 em Bronze — e o nível
sobe conforme o mês avança, que é a progressão que um arcade deve dar. Os cortes são calculados no
`level_of()` a partir do `total`; **o site não tem os valores hardcoded**, ele só renderiza o campo
`level` do JSON.

## Mudanças da v8 — decidido pelo Wagner em 09/09/2026

### 1. Boss Battle agora é só o da semana

O **Boss Battle do mês (+50 pts) foi removido**. Fica valendo apenas o **Boss Battle da semana**,
com o mesmo critério de qualidade da v5 (média dos canais aplicáveis ao grupo ≥85). O valor do
prêmio semanal passou a variar na v9 (ver acima).

O efeito foi aplicado **retroativamente** no `scoreboard.json` de 09/09: a Angelica Almeida tinha
+50 de Boss Battle do mês e passou de 155 para **105 pts**.

Nos campos do JSON, `bossBattle.monthly` fica sempre `false` e `bossBattle.monthlyPts` sempre `0`.
O site não renderiza mais o badge "BOSS BATTLE DO MÊS".

### 2. O painel não mostra mais Transfer indevido nem Time Spent

As duas colunas saíram da tabela do placar no site:

- **Transfer indevido** está em modo monitoramento desde a v7 (0 pts até o fechamento do mês), então
  a coluna só exibia "—" para todo mundo.
- **Time Spent** só pontua para o grupo backoffice, que está vazio hoje — a coluna também era "—"
  para os 14 agentes.

As duas métricas **continuam sendo apuradas e publicadas** no `scoreboard.json`
(`ops.transferIndevido.pct` e `ops.timeSpent.minutes`) para o acompanhamento individual com a
liderança. Só a visualização do painel mudou; o cálculo de pontos não.

## Mudanças da v7 — decidido pelo Wagner em 09/09/2026

### 1. Transfer indevido sai da pontuação (vira só monitoramento)

O Transfer indevido **não vale mais pontos** durante o mês. O percentual continua sendo apurado e
publicado no `scoreboard.json` (campo `ops.transferIndevido.pct`) para acompanhamento individual
com a liderança, mas com `pts: 0`, `applicable: false` e `monitoringOnly: true`.

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

## Regras do jogo (v9) — setembro/2026

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
- **Transfer indevido** (mês): **0 pts — só monitoramento desde a v7**, retomado no fechamento do
  mês. Não aparece como coluna do painel (v8).

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
regra geral (+20). Transfer indevido não pontua. O grupo está vazio hoje, e por isso o Time Spent
também não aparece como coluna do painel (v8) — se alguém for classificado como backoffice, a
coluna precisa voltar.

### Para todos

- **WoW**: +10 pts por WoW aprovada. **Chama do Encantamento**: 3+ WoWs no mês = +40, +10/extra.
- **Engajamento nos canais (v6 — semanal, fecha toda segunda): +10 pts para QUEM ENGAJOU DE
  QUALQUER FORMA na semana**, nos canais #os_incríveis_csi, #wow_csi e #cx-csi-informa. Conta
  igualmente: (a) mensagem de nível superior no canal, (b) resposta em thread, **(c) curtida /
  reação em post de colega**. Basta UMA dessas coisas para ganhar os 10 pts — não é ranking, não é
  "quem mais participou". Quem não teve nenhum registro na semana fica com 0. O teto continua sendo
  10 pts/semana (ninguém ganha 30 por fazer as três coisas).
- **Boss Battle da semana (v9 — compartilhado)**: Top Performers da semana (proxy: maior soma de
  Excelência+tNPS na semana) que também cumpram o critério de qualidade do seu grupo.
  **+20 pts se houver um único vencedor; +10 pts para cada um se houver 2 ou mais.**
  **Critério de qualidade (v5, por média dos canais do grupo)**: geral = média entre tNPS chat e
  tNPS phone ≥85; só chat = tNPS chat ≥85; só phone = tNPS phone ≥85; backoffice (sem tNPS) = Time
  Spent na faixa máxima (<5min). Cada empatado no topo é avaliado **individualmente** no critério —
  quem passa leva, quem não passa fica de fora, e se ninguém do topo passar, ninguém ganha naquela
  semana. **Não existe mais desempate alfabético** (v9) nem Boss Battle do mês (v8).
- **Níveis (v9)**: DIAMANTE ≥320, OURO ≥240, PRATA ≥150, BRONZE <150. Calculados sobre o `total`
  acumulado do mês, então o nível sobe conforme as segundas vão fechando.

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

### Convenção da coluna de semana nas planilhas de Excelência

As abas `4. Qualidade` e `5. Reclamações.` usam o formato `"Semana N"` com a **numeração ISO da
semana do ano** (ex.: `"Semana 36"` = 31/08 a 06/09; `"Semana 37"` = 07/09 a 13/09). A aba
`6. Erros Ops (Vigente)` tem layout diferente e **não tem coluna de semana**: B = e-mail de quem
reportou, C = data do erro em `DD/MM/AAAA`, D = Customer ID/Ticket, **E = e-mail do analista que
cometeu o erro** (é essa coluna que deve ser cruzada com o roster).

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

- **`scripts/generate_scoreboard.py` está DEFASADO em relação à v7/v8/v9** e não deve ser executado
  como está: ele ainda implementa o Boss Battle do mês (+50), o Boss Battle da semana com vencedor
  único e desempate alfabético, o Transfer indevido valendo 10 pts, o Expired em 10 (não 20), o Skip
  sobre todos os canais e os níveis antigos (300/180/90). O workflow do GitHub Actions está em
  `workflow_dispatch` (manual) de propósito. Antes de rodar o script ou reativar o cron, atualizar:
  `BOSS_MONTHLY_PTS` → remover, `compute_boss_battle()` → premiar todos os empatados que passarem no
  critério (+20 solo / +10 compartilhado), `TRANSFER_THRESHOLD`/pts → 0, Expired → 20, o filtro de
  `activity_type` do Skip e `LEVELS` → 320/240/150. Quem manda no placar hoje é a tarefa agendada do
  Cowork, que segue este README.
- **Transfer indevido está congelado** (v7). Precisa ser retomado no fechamento de setembro: voltar
  Transfer para 10 pts e Expired para 10 pts, e devolver a coluna dele ao painel.
- **Colunas removidas do painel na v8**: se o Transfer voltar a pontuar, ou se algum agente for
  classificado como backoffice (Time Spent), as colunas correspondentes precisam voltar ao
  `index.html`.
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
  maior soma de Excelência+tNPS naquela semana.
- **O proxy do Boss Battle tem granularidade grossa** (v9 mitigou, não resolveu): o score usa os
  PONTOS de faixa do tNPS, não o tNPS bruto, então 88,9 e 100 valem os mesmos 20 pts. Somado à
  Excelência, que é idêntica para todos, o empate no teto é o resultado esperado — a v9 assume isso
  e premia todos os empatados em vez de sortear um. Se um dia a gente quiser Boss Battle exclusivo
  de novo, a alternativa é usar tNPS bruto no cálculo do Top Performer.
- **Classificação de canal por agente** (geral / só chat / só phone / backoffice) é baseada no
  histórico de agosto/26. Hoje: andresa.britto, caren.paraiso e lucrecia.santos = só chat; nenhum
  agente backoffice puro ou só phone. Revalidar mensalmente — se alguém mudar de canal, atualizar
  as listas em `scripts/generate_scoreboard.py` (`CHAT_ONLY`, `PHONE_ONLY`, `NO_CHANNEL`).
- **"Alta volumetria"** (critério do Prêmio UAI de Qualidade) ainda não tem um limite numérico
  definido — hoje o badge fica pendente até definirmos o corte.
- **Teto de 50 usuários por emoji no Slack**: a API `slack_get_reactions` lista no máximo 50 pessoas
  por emoji. **Não afeta a pontuação da v6**, que é binária — mas subestima os campos
  `emojis`/`postsReagidos` de quem mais reage. Na mesma linha, reações deixadas DENTRO de respostas
  de thread não são contabilizadas (só as de mensagens de nível superior).
- **Engajamento não distingue intensidade (v6)**: quem responde 19 threads e quem dá uma curtida na
  semana pontuam igual. Escolha deliberada — a métrica é de participação. O campo `score` no
  `engagement_override.json` preserva a intensidade caso a gente queira um bônus separado depois.
- **Agentes sem base de dados**: `maycon.cardoso` está sem nenhum registro no Databricks em setembro
  (sem atendimento, sem tNPS, sem unanswered) e sem engajamento no Slack — só pontua Excelência.
  `lucrecia.santos` está sem nenhuma pesquisa de tNPS no mês, o que a deixa sem os 40 pts/semana a
  que o grupo só-chat tem direito. Nos dois casos o placar reflete ausência de base, não performance
  ruim — confirmar situação cadastral antes do fechamento do mês.
- **01/09/2026**: dia de início da competição. A 1ª segunda-feira de fechamento foi 07/09/2026.
  Setembro tem 4 fechamentos: 07, 14, 21 e 28.

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

### Resolvido na v8

- ~~Boss Battle do mês (+50) concentrava meio nível de pontuação numa única pessoa~~ — removido;
  ficou só o da semana.
- ~~Painel com duas colunas que só mostravam "—" pra todo mundo (Transfer e Time Spent)~~ —
  removidas da visualização; as métricas seguem apuradas no `scoreboard.json`.

### Resolvido na v9

- ~~Desempate alfabético decidindo o Boss Battle, com viés permanente pra nomes em A~~ — eliminado;
  todos os empatados no topo que passam no critério de qualidade ganham.
- ~~8 pessoas-semana cumpriam o critério do Boss Battle e só 2 recebiam~~ — corrigido: na semana 36
  os 3 empatados levaram e na 37 os 5 levaram.
- ~~Níveis provisórios calibrados no teto da v3, com o time inteiro indo pro Ouro no meio do mês~~ —
  recalibrados pro teto real de 4 semanas: 320/240/150.
