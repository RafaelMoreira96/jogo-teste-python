# ⚔️ A Lenda Perdida (The Lost Legend)

> Um RPG de Ação e Aventura 2D em 16-bits com estética retrô clássica (SNES / Mega Drive), combate em tempo real, 15 Guardiões Ancestrais, magias elementais, viagem rápida astral, atlas mundial e trilha sonora sintetizada proceduralmente. Desenvolvido em Python com [pygame-ce](https://pyga.me).

---

## 🌟 Principais Recursos

- 🗡️ **Combate de Ação Ágil**: Espada com combos, escudo com sistema de contra-ataque (*parry*), esquiva (*dash* com frames de invulnerabilidade) e arremesso de bombas para abrir passagens secretas.
- 🔮 **Magias Elementais & RPG**: Esfera de Fogo, Rajada Congelante, Lança de Trovão, Lâmina de Vento e Bênção de Luz, além de sistema de níveis, mana, atributos e árvore de habilidades (`[U]`).
- 🚪 **Portais Místicos & 15 Guardiões Ancestrais**: Cada grande chefe possui uma arena isolada com entrada mística monumental e efeitos de partículas. Ao derrotar um guardião, seu portal se transforma em um selo espectral eterno e sua relíquia é liberada.
- 💨 **Navegação & Vento Guia**: Nunca mais fique perdido! Invoque o **Vento Guia** (`[H]`) para que as brisas do mundo revelem a direção do próximo objetivo. Totens de madeira nas encruzilhadas apontam caminhos para vilas, templos e masmorras.
- 🗺️ **Atlas do Mundo & Badges de Chefes (`[M]`)**: Mapa geral detalhado indicando as regiões exploradas e o status de cada chefe (🔴 Ativo / 🟡 Pronto para lutar / ⚪ Conquistado).
- 🌌 **Rede de Monólitos Astrais (Fast Travel)**: Encontre e sintonize monólitos nas 6 grandes regiões do continente para viajar instantaneamente entre eles através de feixes de luz celestiais.
- 📜 **Missões & Conquistas**: Diário de missões secundárias, NPCs com diálogos e escolhas dinâmicas, e dezenas de conquistas desbloqueáveis com pop-ups animados.
- 🏺 **Exploração & Segredos**: Quebre vasos de cerâmica antigos, corte arbustos, descubra baús com equipamentos raros e colete as **6 Relíquias Ancestrais** para entregar ao Ancião da Vila Aurora.
- 🎵 **Áudio Sintetizado em Tempo Real**: Músicas de área e efeitos sonoros gerados por ondas procedurais sem depender de pacotes externos de áudio gravado.
- 🛠️ **Editor Visual de Fases Integrado (`[F2]`)**: Pinte e crie novos mapas diretamente no motor do jogo com o mouse e teclado.

---

## 🎮 Controles

O jogo conta com suporte total tanto para **Teclado** quanto para **Controles USB / Bluetooth** (Xbox, PlayStation, Nintendo Switch e genéricos):

| Ação | Teclado | Controle (Gamepad) |
|---|---|---|
| **Movimentação** | Setas direcionais / `W`, `A`, `S`, `D` | Analógico Esquerdo / D-Pad |
| **Atacar com Espada / Interagir** | `Espaço` / `Z` / `J` | Botão `A` / `X` |
| **Defender com Escudo (Parry)** | `Ctrl` / `E` | Gatilho Esquerdo (`LT` / `L2`) |
| **Esquiva (Dash / Correr)** | `Shift` / `C` | Botão `B` / `RB` |
| **Pular** | `V` / `K` | Botão `Y` / `LB` |
| **Lançar Magia Ativa** | `F` / `Q` | Gatilho Direito (`RT` / `R2`) |
| **Trocar Magia Elemental** | `R` / `E` | Botão `Y` |
| **Colocar Bomba** | `B` / `G` | Botão `X` |
| **Invocar Vento Guia** | `H` / `T` | Botão Direcional |
| **Atlas do Mundo / Mapa** | `M` | Botão `Back` / `Select` |
| **Árvore de Habilidades** | `U` / `Tab` | Botão Guia |
| **Pausar Jogo** | `Esc` / `P` | Botão `Start` |
| **Editor de Fases** | `F2` | — |
| **Tela Cheia** | `F11` | — |

---

## 🚀 Como Executar

### Pré-requisitos
- **Python 3.10** ou superior instalado no seu sistema.

### Instalação passo a passo

1. **Clone o repositório:**
   ```bash
   git clone https://github.com/RafaelMoreira96/jogo-teste-python.git
   cd jogo-teste-python
   ```

2. **Crie e ative um ambiente virtual:**
   ```bash
   # No Linux / macOS:
   python3 -m venv .venv
   source .venv/bin/activate

   # No Windows:
   python -m venv .venv
   .venv\Scripts\activate
   ```

3. **Instale as dependências:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Inicie a jornada:**
   ```bash
   python main.py
   ```

---

## 🗺️ As Grandes Regiões do Mundo

1. **Vila Aurora**: O refúgio inicial onde reside o Ancião, ferreiros, comerciantes e a fonte de água sagrada.
2. **Floresta Esmeralda & Covil do Rei Slime**: Bosques densos com fauna misteriosa, fungos e o primeiro guardião coroado.
3. **Lago Cristalino**: Águas serenas pontilhadas por ilhotas e espíritos das profundezas.
4. **Ruínas Antigas**: Estruturas de pedra milenares guardadas pelo temível Golem de Pedra Ancestral.
5. **Pântano Sombrio & Cemitério Esquecido**: Terrenos lamacentos e brumas onde repousam criaturas espectrais.
6. **Santuário das Trevas**: O epicentro da corrupção, onde as forças ancestrais aguardam o derradeiro confronto.

---

## 🏗️ Estrutura do Código-fonte

```text
├── assets/                     # Sprites, texturas procedurais e artes de tiles
├── audio.py                    # Sintetizador procedural de áudio (BGM e SFX em tempo real)
├── caixa_dialogo.py            # Caixa de texto clássica com suporte a paginação e opções
├── camera.py                   # Câmera cinemática suave com amortecimento e tremores (shake)
├── chefe.py                    # IA e estados dos 15 Chefões e Guardiões
├── conquistas.py               # Sistema de conquistas com persistência e alertas animados
├── efeitos.py                  # Partículas, iluminação, corações flutuantes e vasos quebráveis
├── enemy.py                    # Inimigos comuns (slimes, zumbis, arqueiros, morcegos)
├── entidade.py                 # Mecânica de física, colisão e knockback base
├── entrada.py                  # Mapeamento unificado de teclado e gamepads
├── equipamentos.py             # Armaduras, armas, escudos e relíquias
├── historia.py                 # Interpretador de roteiro e eventos direcionados
├── historia/dialogos.txt       # Roteiro completo do jogo e cutscenes (@comandos)
├── hud.py                      # Interface de usuário (Vida, Mana, XP, Alvo, Recursos, Minimapa)
├── level.py                    # Carregador de mapas em ASCII/tiles e colisões
├── main.py                     # Inicialização da janela SDL e ciclo do jogo
├── maps/                       # Arquivos .txt de cenários, vilas, cavernas e masmorras
├── missoes.py                  # Gerenciador de missões primárias e secundárias
├── player.py                   # Mecânicas do herói, ataques, magias, dash e animações
├── rpg.py                      # Atributos do personagem, progressão, inventário e magias
├── salvamento.py               # Serialização e persistência de dados (savegame)
├── ui.py                       # Fonte bitmap proporcional 16-bits e componentes de menus
└── cenas/                      # Telas e módulos de estado:
    ├── jogo.py                 # Ciclo principal do gameplay e mundo
    ├── menu.py                 # Tela de título e seleção de opções
    ├── mapa_mundo.py           # Atlas do mundo com sinalização de chefes
    ├── teleporte.py            # Viagem rápida entre Monólitos Astrais
    ├── arvore_habilidades.py   # Desbloqueio de poderes e melhorias
    ├── bestiario.py            # Enciclopédia de criaturas encontradas
    ├── diario_missoes.py       # Registro de missões em andamento e concluídas
    ├── conquistas.py           # Galeria de conquistas do jogador
    ├── loja.py                 # Comércio de itens, poções e aprimoramentos
    ├── pausa.py                # Menu de pausa
    └── editor.py               # Editor in-game de fases e posicionamento de entidades
```

---

## 🛠️ Editor de Fases (`F2`)

Pressione **`F2`** durante o jogo para editar qualquer mapa em tempo real:
- **Botão Esquerdo do Mouse**: Pinta o tile/objeto selecionado.
- **Botão Direito do Mouse**: Apaga para o solo base.
- **Roda do Mouse / Teclas `Q` e `E`**: Alterna entre os pincéis disponíveis (paredes, água, pontes, arbustos, tochas, vasos, totens, portais, NPCs e inimigos).
- **`Tab`**: Alterna entre mapas disponíveis.
- **`Ctrl + S`**: Salva as alterações diretamente no arquivo de mapa.
- **`F2` / `Esc`**: Salva e retorna instantaneamente para o jogo.

---

## 📜 Licença

Distribuído sob a licença MIT. Sinta-se à vontade para clonar, estudar, modificar e expandir esta aventura!
