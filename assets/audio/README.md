# Arquitetura Híbrida de Áudio - PyMystic

Este diretório permite carregar faixas de áudio pré-renderizadas de alta qualidade (.ogg, .wav, .mp3) criadas em estúdio ou DAW, substituindo automaticamente os geradores procedurais.

## Estrutura de Pastas:
- `bgm/`: Músicas de fundo. Ex: `vila.ogg`, `mundo.ogg`, `chefe.ogg`, `chefe_final.ogg`, `santuario.ogg`, `castelo.ogg`, etc.
- `sfx/`: Efeitos sonoros. Ex: `espada.wav`, `parry_perfeito.wav`, `passo_pedra.wav`, `passo_grama.wav`, `exaustao.wav`, etc.

## Comportamento Inteligente:
1. Se um arquivo de áudio estiver presente neste diretório com o nome correspondente, o motor do jogo o carrega diretamente.
2. Se o arquivo não existir, o sintetizador procedural 16-bits integrado gera o som em tempo real em memória, garantindo 100% de funcionamento autônomo sem dependências externas.
