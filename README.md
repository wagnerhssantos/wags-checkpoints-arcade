# WAGS CHECKPOINTS

Placar de gamificacao (checkpoints) do Time Wags, publicado como site estatico via GitHub Pages,
com estetica de videogame anos 90.

## Como habilitar o site (uma vez)

1. Va em **Settings > Pages** deste repositorio.
2. Em **Build and deployment > Source**, escolha **Deploy from a branch**.
3. Branch: `main`, pasta: `/ (root)`.
4. Salve. O site fica em `https://wagnerhssantos.github.io/wags-checkpoints-arcade/`.

Como o repositorio e privado, o Pages so fica visivel para quem tem acesso de leitura ao
repositorio (isso pode exigir GitHub Pro/Team, dependendo do seu plano). Adicione os
colegas do time como colaboradores em **Settings > Collaborators** para eles conseguirem ver.

## Como funciona a atualizacao dos dados

O arquivo `data/scoreboard.json` e o que o site le. Ele e gerado por `scripts/generate_scoreboard.py`,
que busca dados no Databricks (tabela `usr.csinnovation.csiagentsmetricsoficial`) e nas planilhas
Google Sheets (Central de Inteligencia CSI 2026 e Base Faisca).

Um workflow agendado (`.github/workflows/update-scoreboard.yml`) roda esse script automaticamente
em dias uteis e commita o `data/scoreboard.json` atualizado. Para isso funcionar, configure os
seguintes **Secrets** em Settings > Secrets and variables > Actions:

| Secret | O que e |
|---|---|
| `DATABRICKS_HOST` | host do workspace Databricks (sem `https://`) |
| `DATABRICKS_TOKEN` | personal access token ou service principal token com leitura na tabela |
| `DATABRICKS_WAREHOUSE_ID` | id do SQL warehouse a usar nas queries |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | conteudo JSON de uma service account do Google com acesso de leitor nas planilhas (compartilhe as planilhas com o `client_email` dela) |
| `XFORCE_EMAIL` | (opcional) email do xforce a filtrar; default `wagner.santos@nubank.com.br` |

Sem esses secrets configurados, o workflow falha silenciosamente e o `data/scoreboard.json`
fica no ultimo snapshot manual gerado nesta conversa (dados reais de jul/ago 2026).

Voce tambem pode rodar manualmente a qualquer momento em **Actions > Atualizar placar WAGS
CHECKPOINTS > Run workflow**.

## Limitacoes conhecidas

- Julho foi calculado com os dados do Databricks (nao com o "tabelao com validacoes manuais",
  por conta de um bug na leitura da aba com "/" no nome).
- A leitura da aba "6. Erros Ops (Vigente)" no Google Sheets e ocasionalmente instavel; o script
  trata isso com tolerancia a falha (fonte tratada como zero quando indisponivel).
- O simbolo do time em `assets/emblem.svg` e um design original, para evitar usar marcas
  registradas de terceiros no material do time.
