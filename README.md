# Henriquix20 Encoder

Otimiza e prepara vídeos para upload no TikTok sem perda de qualidade.

Desenvolvido por **henriquix20**.

---

## O que faz

- Reencoda o vídeo com configurações otimizadas para a pipeline do TikTok (H.264 High, VBR 12/20 Mbps, 60fps constante, Rec.709)
- Aplica patch nos metadados do container MP4 (atoms `mvhd` e `mdhd`) para preservar o FPS durante o processamento do servidor
- Salva o arquivo de saída na mesma pasta do input com o sufixo `_hx20`

---

## Requisitos

- Python 3.x
- FFmpeg instalado e no PATH do sistema
  - Windows: [ffmpeg.org/download.html](https://ffmpeg.org/download.html)
  - Após instalar, adicione o executável ao PATH nas variáveis de ambiente

---

## Instalação

```bash
git clone https://github.com/henriquix20/henriquix20-encoder
cd henriquix20-encoder
pip install -r requirements.txt
```

---

## Como usar

```bash
python main.py
```

1. Arraste o arquivo `.mp4` para a janela ou clique para selecionar
2. Escolha o FPS do seu export (24, 30 ou 60)
3. Escolha o patch de metadados (recomendado: Nenhum para 60fps)
4. Clique em **Processar**
5. O arquivo `_hx20.mp4` será salvo na mesma pasta do original
6. Faça upload no [tiktok.com](https://tiktok.com) via desktop
7. Antes de publicar: **More options → Upload HD = ON**

---

## Opções de Patch de Metadados

| Opção | Quando usar |
|---|---|
| Nenhum (scale 1.0) | Vídeo já em 60fps — recomendado |
| 0.5× | 120fps reais → TikTok lê como 60fps |
| 0.25× | 120fps reais → TikTok lê como 30fps |

> **Atenção:** com patch 0.5× ou 0.25×, o vídeo vai parecer em câmera lenta em players de PC. Isso é esperado — no TikTok reproduz corretamente.

---

## Configurações

Todas as configurações estão centralizadas em `config.py`. Edite o arquivo para ajustar preset, bitrate, FPS padrão e outros parâmetros.

---

## Créditos

Criado por henriquix20.
