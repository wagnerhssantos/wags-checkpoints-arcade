# 🎮 UAI MODO TURBO — Fase Final

Vídeo em pixel art estilo videogame dos anos 90: os 14 heróis do Time Wags, de uniforme roxo e capa, caminham rumo ao castelo da **Fase Final**. Só o top 3 entra, e o vídeo termina com o pódio.

▶️ **[uai-modo-turbo-fase-final.mp4](uai-modo-turbo-fase-final.mp4)** (1920×1080, 27s, sem som)

## Como é gerado

- `gerar_video.py` lê o ranking de `data/scoreboard.json` (não recalcula nada) e desenha tudo em Python/Pillow + ffmpeg.
- O workflow `.github/workflows/render-video.yml` renderiza e commita o MP4 aqui em `media/`.
- Para gerar de novo com o placar do dia (ex.: resultado oficial de 29/09): **Actions → Render vídeo UAI MODO TURBO → Run workflow**.

Rodar localmente: `pip install pillow` + ffmpeg instalado → `python media/gerar_video.py`.
