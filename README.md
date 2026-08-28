# UAI MODO TURBO

Placar de gamificacao (checkpoints) do Time Wags, publicado como site estatico via GitHub Pages,
com estetica de videogame anos 90. Identidade visual: só o mascote (pão de queijo cibernético do UAI).

## Como funciona

O site abre com uma tela estilo arcade ("INSERT PERFORMANCE TO CONTINUE_") onde o agente digita
o nome, recebe uma saudação ("Oi, [nome]. Que bom que ocê tá aqui, sô!") e então vê o placar.
O nome fica salvo no navegador (localStorage) — dá pra trocar de jogador pelo link no rodapé.

**A partir desta versão, o placar considera SOMENTE o mês atual** (antes era uma janela rolante de
2 meses). O motor de pontos também mudou — ver "Regras do jogo" na própria página, ou o resumo abaixo.

## Regras do jogo (v2)

- **Excelência**: semana sem apontamento de qualidade/complaint/erro operacional = +10 pts. Semanal.
- **Streak Excelência**: semanas consecutivas limpas valem mais (10 → 15 → 20 → 25, cap 25). Um
  apontamento zera a sequência.
- **Aderência**: aderência ao fone > 85% = +10 pts, com o mesmo streak (10→15→20→25).
- **tNPS chat + phone**: média do mês > 75 = +10; > 82 = +20; > 90 = +50 (vale a maior faixa, não
  cumulativo). Quem não atua em chat/phone recebe +20 se estiver limpo de qualidade no mês.
- **Skip**: < 5% = +10; < 7% = +5; > 9% = -5. **Unanswered Calls**: < 2% = +10; < 5% = +5; > 10% =
  -5 (só conta pra quem atua em phone). **Transfer indevido**: < 3% = +10. **Expired jobs**: < 3% =
  +10. Todas as 4 usam o resultado FINAL do mês (não têm streak semanal).
- **Primeiro Top Performer**: 1ª vez na carreira do agente como Top — badge "Estreia Top" (evento
  único, sem pontos).
- **WoW**: +10 pts por WoW aprovada.
- **Chama do Encantamento**: 3+ WoWs no mês = +40, +10 por WoW extra. Mensal.
- **Boss Battle**: só para Top Performer com os dois tNPS (chat e phone) acima da meta no mês = +80
  pts + badge "Caçador de Chefões". Mensal.

## Limitações conhecidas (importante)

- **Skip / Transfer indevido / Expired jobs**: conectados via `etl.br__dataset.cx_canonical_activities`
  (mesma base usada em relatórios de performance do time — colunas `agent`, `status`,
  `is_transfer_indevido`), considerando o resultado final do mês (agosto/26).
- **Unanswered Calls**: conectado via `usr.cx_golden_layer.unanswered_calls`
  (`queue_event__actor`, `ringing`, `no_answer`). Só vale para quem atua no canal phone — quem não
  tem nenhuma linha nessa tabela no mês aparece como "sem canal" e não pontua nem penaliza nessa
  métrica (é o caso de andresa.britto, caren.paraiso e lucrecia.santos em agosto/26).
- **Aderência semanal**: não achei uma tabela de aderência ao fone com granularidade semanal para
  o Time Wags (`view_aderencia_final` não cobre esse squad). Por ora, uso a aderência **mensal** do
  Databricks (`usr.csinnovation.csiagentsmetricsoficial`) repetida nas semanas do mês.
- **Erros Ops por semana**: a aba "6. Erros Ops (Vigente)" às vezes tem instabilidade de alinhamento
  de linha; quando isso acontece, o incidente é atribuído com a melhor evidência disponível.
- **"Estreia Top"**: hoje só olho para os meses que já consultamos no Databricks (não a carreira
  inteira do agente), então pode haver falso positivo/negativo em casos muito antigos.

## Como habilitar o site (uma vez)

1. Vá em **Settings > Pages** deste repositório.
2. Em **Build and deployment > Source**, escolha **Deploy from a branch**.
3. Branch: `main`, pasta: `/ (root)`.
4. Salve. O site fica em `https://wagnerhssantos.github.io/wags-checkpoints-arcade/`.

## Como funciona a atualização dos dados

O arquivo `data/scoreboard.json` é o que o site lê. Ele é gerado por `scripts/generate_scoreboard.py`,
que busca dados no Databricks e nas planilhas Google Sheets (Central de Inteligência CSI 2026 e Base
Faísca), aplicando as regras v2 descritas acima.

Um workflow agendado (`.github/workflows/update-scoreboard.yml`) roda esse script automaticamente
em dias úteis e commita o `data/scoreboard.json` atualizado. Para isso funcionar, configure os
seguintes **Secrets** em Settings > Secrets and variables > Actions:

| Secret | O que é |
|---|---|
| `DATABRICKS_HOST` | host do workspace Databricks (sem `https://`) |
| `DATABRICKS_TOKEN` | personal access token ou service principal token com leitura na tabela |
| `DATABRICKS_WAREHOUSE_ID` | id do SQL warehouse a usar nas queries |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | conteúdo JSON de uma service account do Google com acesso de leitor nas planilhas (compartilhe as planilhas com o `client_email` dela) |
| `XFORCE_EMAIL` | (opcional) email do xforce a filtrar; default `wagner.santos@nubank.com.br` |

Sem esses secrets configurados, o workflow falha silenciosamente e o `data/scoreboard.json` fica no
último snapshot manual gerado nesta conversa (dados reais de agosto/26).

Você também pode rodar manualmente a qualquer momento em **Actions > Atualizar placar UAI MODO
TURBO > Run workflow**.

## Identidade visual

- `assets/uai-mascot.b64.txt`: mascote (pão de queijo cibernético) em base64, carregado via
  `data:` URI no navegador.
- `assets/emblem.svg`: emblema original da v1, não é mais usado na tela (mantido no repo por
  histórico). A identidade visual atual usa só o mascote.
