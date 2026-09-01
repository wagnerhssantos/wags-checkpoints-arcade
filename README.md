# UAI MODO TURBO

Placar de gamificação (checkpoints) do Time Wags, publicado como site estático via GitHub Pages,
com estética de videogame anos 90. Identidade visual: só o mascote (pão de queijo cibernético do UAI).

**Competição válida apenas para setembro/2026.** O motor de pontos foi redesenhado (v3) com
fechamentos semanais (toda segunda-feira) para Excelência, tNPS e Engajamento, e resultado final
do mês para Skip, Unanswered Calls, Transfer indevido, Expired jobs e Time Spent. Na v4, os tetos
de pontos foram recalibrados pra ficarem iguais entre os grupos de agente (geral / só chat / só
phone / backoffice) — ver "Regras do jogo" abaixo.

## Como funciona

O site abre com uma tela estilo arcade ("INSERT PERFORMANCE TO CONTINUE_") onde o agente digita
o nome, recebe uma saudação ("Oi, [nome]. Que bom que ocê tá aqui, sô!") e então vê o placar.
O nome fica salvo no navegador (localStorage).

O topo da página sempre mostra **até que data os dados são** ("Dados até DD/MM") — importante
porque nem toda métrica fecha no mesmo ritmo (semanal vs. mensal), e o ETL do Databricks tem um
dia de atraso natural.

## Regras do jogo (v4) — setembro/2026

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
- **Engajamento nos canais** (semanal): quem mais comentou e incentivou o time na semana nos canais
  #os_incríveis_csi, #wow_csi e #cx-csi-informa ganha +10 pts.
- **Boss Battle da semana**: Top Performer da semana com tNPS chat e phone ≥85 na semana: +20 pts.
  **Boss Battle do mês**: mesma lógica, apurada no mês: +50 pts. **Ainda não implementado** no motor
  de pontos (campo sempre `false` hoje) — e o critério como está escrito só é atingível por quem tem
  os dois canais. Antes de ligar, precisa virar um critério por grupo (ex: "só chat" cumpre com tNPS
  chat ≥85; backoffice cumpre com Time Spent na faixa máxima) pra não recriar o mesmo problema de
  teto desigual que a v4 acabou de corrigir nos pontos.

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
| Engajamento nos canais | Slack — #os_incríveis_csi (`C0AK68688EQ`), #wow_csi (`C090RS3739N`), #cx-csi-informa (`C0209GG9GQ7`) | Semanal |

## Limitações conhecidas e decisões em aberto

- **Boss Battle (semana e mês) ainda não está implementado** no motor de pontos — os campos
  `bossBattle.weekly`/`bossBattle.monthly` sempre retornam `false`. Além de implementar, o critério
  precisa ser adaptado por grupo (hoje exige tNPS chat E phone ≥85, o que "só chat", "só phone" e
  "backoffice" não conseguem cumprir de jeito nenhum — recriaria o mesmo problema de teto desigual
  que a v4 acabou de corrigir nos pontos). Próxima passada recomendada.
- **Classificação de canal por agente** (geral / só chat / só phone / backoffice) é baseada no
  histórico de agosto/26 (quem tinha ou não linhas em `unanswered_calls`/tNPS phone). Hoje:
  andresa.britto, caren.paraiso e lucrecia.santos = só chat; nenhum agente identificado como
  backoffice puro ou só phone (grupos mantidos vazios por simetria). Revalidar mensalmente — se
  alguém mudar de canal, atualizar as listas em `scripts/generate_scoreboard.py` (`CHAT_ONLY`,
  `PHONE_ONLY`, `NO_CHANNEL`).
- **"Alta volumetria"** (critério do Prêmio UAI de Qualidade) ainda não tem um limite numérico
  definido — hoje o badge fica pendente até definirmos o corte (ex: acima da mediana de atendimentos
  do time na semana).
- **Engajamento nos canais**: a contagem de mensagens do Slack é feita pela tarefa agendada diária
  (roda dentro do Cowork, com acesso ao Slack) e grava em `data/engagement_override.json`; o script
  Python autônomo não tem acesso a essas ferramentas, então só lê esse arquivo se ele existir. Como
  é "quem mais comentou ganha tudo" (não graduado), pode favorecer perfis mais falantes — avisar se
  quiser trocar por uma régua graduada.
- **Níveis (Bronze/Prata/Ouro/Diamante)** foram recalibrados para o teto de pontos mais alto da v3
  (Diamante ≥300, Ouro ≥180, Prata ≥90), mas são provisórios — vamos ajustar depois dos primeiros
  fechamentos semanais reais de setembro.
- **01/09/2026**: dia de início da competição. O ETL do Databricks ainda não tinha processado o
  dia quando este snapshot foi gerado, e a 1ª segunda-feira de fechamento é 07/09/2026 — por isso
  o placar começa zerado para todo mundo.

### Resolvido na v4 (não é mais uma limitação)

- ~~Tetos de pontos desiguais entre grupos~~ — corrigido: 75 pts/semana e 40 pts/mês pros 3 grupos
  (ver seção "Regras do jogo" acima e a docstring de `scripts/generate_scoreboard.py`).
- ~~"Quem não atua em chat" (só phone) sem tabela elevada~~ — corrigido: tNPS Phone em dobro,
  simétrico ao "só chat" (grupo ainda vazio hoje, mas a regra já existe caso alguém se encaixe).
- ~~Excelência em dobro só pro backoffice, sem justificativa clara~~ — corrigido: Excelência agora
  vale igual pra todo mundo; a compensação do backoffice vive inteira no Skip (dobrado) e no Time
  Spent (que ocupa o espaço do tNPS).

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
