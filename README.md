# A Lenda Perdida

RPG 2D de ação e aventura em 16-bits, com gráficos pixel art detalhados, sistema de chefões, progressão de habilidades e trilha sonora procedural, feito em Python com pygame-ce.

## Como rodar

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python main.py
```

## Controles

| Ação | Teclado | Controle |
|---|---|---|
| Andar | Setas / WASD | Direcional / analógico |
| Correr / Dash | Shift / C | B / RB |
| Pular | V / K | Y / LB |
| Espada / falar | Espaço / Z / J | A / X |
| Confirmar | Enter / Espaço | A |
| Voltar | Esc / X | B |
| Pausar | Esc / P | Start |
| Editor Visual | F2 | |
| Recarregar História | F5 | |
| Tela cheia | F11 | |

Controles de Xbox, PlayStation, Switch etc. funcionam e podem ser conectados com o jogo aberto.
Os botões ficam em `entrada.py`.

## Motor de História e Direção de Cenas

Toda a história e a direção das cenas ficam em `historia/dialogos.txt`. Além de falas, escolhas (`@opcao`) e condições (`@se` / `@marcar`), você pode dirigir como as cenas acontecem usando comandos `@`:

```
@mapa casa.txt                  # troca o mapa atual (opcional: @mapa mundo.txt 5 14)
@clima noite                    # muda o clima: dia, noite, chuva, trevas
@pose heroi dormir              # poses: dormir (com Zzz), acordar, assustar, comemorar, tremer, poder, caido
@esperar 1.5                    # pausa o diálogo enquanto a cena acontece
@efeito poder heroi             # partículas: poder, fogo, fumaca, explosao, parar
@clarao branco                  # flash na tela: branco, vermelho, roxo, dourado
@cenario cidade                 # cutscene da Entidade Maligna despertando
@cenario cidade_destruicao      # a Entidade Maligna destrói a cidade inteira
@cenario normal                 # volta para o mapa do jogo
@tremer 4 1.0                   # treme a câmera (intensidade e duração) e vibra o controle
@pular heroi                    # faz qualquer personagem dar um pulo
@emocao heroi !                 # mostra balão de expressão: !, ?, ..., coracao
@olhar 1 heroi                  # vira um personagem para uma direção ou para outro ator
@mover heroi baixo 2            # faz o personagem andar (por direção/passos ou coordenada x y)
@posicionar 1 8 14              # posiciona um ator na coordenada (x, y)
@camera 1                       # foca a câmera em um personagem ou coordenada
```

## Editor Visual Integrado (`F2`)

Aperte **`F2`** a qualquer momento (ou escolha **"Editor de jogo"** no Menu Principal) para abrir o editor no próprio jogo:
- **Mouse Esquerdo**: pinta o tile/objeto selecionado no mapa.
- **Mouse Direito**: apaga (volta para o chão).
- **`Q` / `E` ou Roda do Mouse**: troca o pincel (grama, caminho, paredes, cama, mesa, portas, Slimes, Corações, NPCs...).
- **`Tab`**: alterna entre os arquivos de mapa (`maps/casa.txt`, `maps/mundo.txt`).
- **`T`**: abre a lista de cenas/diálogos de `historia/dialogos.txt` para testar qualquer cena na hora.
- **`Ctrl+S`**: salva o mapa no arquivo `.txt`.
- **`F2` / `Esc`**: salva e joga imediatamente no mapa atual.

## Estrutura

| Arquivo | O que faz |
|---|---|
| `main.py` | janela, loop principal, pilha de cenas |
| `cenas/` | menu principal, jogo, pausa, configurações |
| `entrada.py` | teclado + controle, por ações |
| `config.py` | configurações salvas em `config.json` |
| `historia.py` | lê e executa `historia/dialogos.txt` |
| `caixa_dialogo.py` | caixa de diálogo e escolhas |
| `npc.py` | personagens que conversam |
| `ui.py` | texto, menus |
| `settings.py` | constantes (resolução, velocidades, vida...) |
| `sprites.py` | tiles, itens e carregamento dos PNGs |
| `personagens.py` | pixel art dos personagens (32x32, em camadas) |
| `level.py` | lê o mapa de texto, colisão com tiles |
| `entidade.py` | movimento com colisão e knockback (base) |
| `player.py` | jogador: movimento, animação, espada, dano |
| `enemy.py` | slime: passeia e persegue |
| `efeitos.py` | corações coletáveis e partículas |
| `camera.py` | câmera que segue o jogador |
| `hud.py` | corações, contador, mensagens |
| `maps/mundo.txt` | o mapa |

## Editando

**Mapa**: edite `maps/mundo.txt`. Cada caractere é um tile de 16x16:

```
.  grama        ,  caminho      *  flores
T  árvore       #  pedra        ~  água         (sólidos)
B  arbusto (sólido, cortável)
P  jogador      S  slime        H  coração
1-9 NPC (veja [npcs] no fim do arquivo)
```

**Arte**: na primeira execução os sprites são gerados e salvos em `assets/sprites/`.
Edite os PNGs em qualquer editor de pixel art (LibreSprite, Pixelorama, Aseprite),
mantendo o tamanho. Apague um PNG para voltar à arte padrão.

- personagens (`heroi.png`, `aldea.png`, `mago.png`...): 128x96, quadros de 32x32; linhas baixo, cima e direita (esquerda é espelhada), 4 quadros de caminhada cada
- `slime.png`: 32x16, 2 quadros
- `espada.png`: 16x16, apontando para cima
- `coracoes.png`: 24x8 (cheio, metade, vazio)
- tiles: 16x16 cada
