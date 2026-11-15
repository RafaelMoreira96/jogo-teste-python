# 🛠️ PROMPT 3: Bateria de QA, Polimento para Lançamento Comercial e Novas Funcionalidades

> **Objetivo**: Elevar "A Lenda Perdida" ao padrão de lançamento comercial para plataformas como **Steam** e **Itch.io**. Este prompt abrange testes de controle de qualidade (QA), eliminação de bugs, acessibilidade, balanceamento econômico, novos recursos de engajamento (Speedrun, New Game+, Jukebox) e pipeline de empacotamento standalone.

---

## 📌 PILAR 1: Bateria de QA Rigoroso & Caça a Bugs Críticos

Realize uma varredura completa e aplique correções preventivas em todos os sistemas do jogo:

1. **Física, Colisão & Quinas**:
   - Elimine qualquer possibilidade de *tunneling* (atravessar paredes ou quinas em alta velocidade ao usar o Dash `[Shift]`).
   - Garanta que inimigos voadores ou de salto respeitem os limites do cenário e não fiquem presos dentro de blocos sólidos ou fora da tela.
   - Ao atacar com a espada próximo a paredes ou água, garanta que a animação e a caixa de colisão (*hitbox*) do ataque funcionem perfeitamente sem puxar o herói para dentro de tiles sólidos.

2. **Câmera, Transições & Cliping de Tela**:
   - Nas bordas extremas de mapas pequenos (ex.: interiores de cabanas ou cavernas estreitas), impeça que a câmera ultrapasse a área visível do mapa exibindo o fundo preto vazio.
   - Nas transições de mapas via portas e bordas, sincronize o fade-out/fade-in suave para que o jogador nunca visualize o mapa carregando sem iluminação ou inimigos sendo instanciados.

3. **Validação Cruzada dos 3 Slots de Salvamento**:
   - Teste exaustivo de persistência nos 3 slots (`savegame_1.json`, `savegame_2.json`, `savegame_3.json`):
     - Iniciar nova run no Slot 2 sem interferir no progresso do Slot 1.
     - Operação de duplicar/copiar um save para outro slot vazio sem corrupção de atributos de RPG ou mapa.
     - Apagar um slot e confirmar que o espaço volta ao estado `[ VAZIO ]` sem travar o motor.
     - Persistência das configurações globais em `config.json` (incluindo o status de `jogo_zerado` para desbloqueio do Modo Chefões).

4. **Normalização e Mixagem de Áudio**:
   - Ajuste as curvas de volume das ondas senoidais, quadradas e ruídos sintetizados em `audio.py`.
   - Evite picos de amplitude (clipping de áudio) quando múltiplos efeitos sonoros tocarem simultaneamente (ex.: quebrar 3 potes ao mesmo tempo em que uma bomba explode e um monstro é atingido).
   - O volume de BGM e SFX deve respeitar fidedignamente os seletores de 0 a 100 nas Configurações.

5. **Performance & Estabilidade a 60 FPS**:
   - Garanta que a taxa de quadros permaneça cravada em 60 FPS estáveis mesmo em batalhas cheias de projéteis, ondas de choque e partículas na tela.
   - Implemente um *delta time* (`dt`) clampado (máximo de 0.05s por quadro) para evitar que quedas momentâneas de desempenho façam o jogador atravessar objetos ou teleportar.

---

## 🎮 PILAR 2: Conforto do Jogador, Acessibilidade & Controles

1. **Remapeamento Completo de Teclas e Botões de Controle**:
   - Crie um submenu em `Configurações > Controles` onde o jogador pode redefinir livremente cada ação do jogo (Ataque, Pulo, Dash, Magia, Bomba, Mapa, Vento Guia, Pausa).
   - Suporte nativo tanto para teclado quanto para Gamepads (Xbox, PlayStation, Switch e genéricos), salvando o mapa de teclas personalizado diretamente em `config.json`.
   - Opção de "Restaurar Padrões de Fábrica" com um toque.

2. **Opções de Acessibilidade Visual e Sonora**:
   - **Tamanho do HUD**: Opção de alternar entre HUD Compacto, Normal ou Expandido para telas de diferentes tamanhos (monitores, Steam Deck e notebooks).
   - **Modo Alto Contraste para Dano**: Permite ativar um contorno brilhante nos projéteis inimigos e nas áreas de impacto perigosas no chão.
   - **Ajuste de Tremor de Tela (Screen Shake)**: Barra deslizante de intensidade do tremor (100%, 50%, Desativado) para jogadores sensíveis a movimentos bruscos de câmera.

3. **Menu de Pausa Ágil & Confirmação de Saída**:
   - No menu de pausa (`[Esc]` / `[Start]`), adicione a opção clara de "Voltar ao Menu Principal" acompanhada de uma janela de confirmação rápida para evitar que o jogador saia sem salvar acidentalmente.

---

## ⚖️ PILAR 3: Economia, Balanceamento & Curva de Aprendizado

1. **Sistema de Lojas & Economia Viva**:
   - No Mercador da Vila Aurora e no Bazar do Oásis, estruture uma loja com abas:
     - **Consumíveis**: Poção de Cura (restaura 4 corações), Frasco de Mana (recupera 50% da mana), Pacote de 3 Bombas e Chaves de Baú.
     - **Equipamentos & Amuletos**: Amuletos que concedem bônus passivos (ex.: *Amuleto da Rapidez* aumenta a velocidade de corrida em 15%, *Ímã de Ouro* atrai moedas a distâncias maiores).
     - **Melhorias de Armas**: Forja com o Ferreiro para aprimorar o dano da espada em troca de Ouro e Minérios encontrados pelo mundo.

2. **Tutorial Orgânico e Integrado no Prólogo**:
   - Em vez de tutoriais intrusivos com telas congeladas, use placas interativas de madeira e obstáculos simples no caminho inicial:
     - Uma fenda pequena no chão ensinando o Pulo (`[V]`).
     - Arbustos densos ensinando o golpe de espada (`[Espaço]`).
     - Uma rocha rachada ensinando o uso de bombas (`[B]`).
     - Um projétil disparado por um totem ensinando a defesa com escudo (`[Ctrl]`).

3. **Curva de Dificuldade dos Níveis 1 a 30**:
   - Rebalanceie a experiência (XP) dos monstros para que o jogador atinja naturalmente os níveis recomendados dos Guardiões ao explorar o mundo, sem a necessidade de derrotar slimes repetidamente por horas (anti-grind).

---

## 🏆 PILAR 4: Fator Replay & Conteúdo de Endgame (Lançamento)

1. **Modo Speedrun com Cronômetro Oficial Integrado**:
   - Opção em Configurações para ativar o **Cronômetro de Speedrun**:
     - Exibe no canto superior da tela o tempo exato em minutos, segundos e centésimos (`00:00.00`).
     - O relógio pausa automaticamente durante telas de carregamento e cutscenes.
     - Ao derrotar cada Guardião, exibe um *split* (tempo parcial) para que corredores possam comparar suas marcas.

2. **New Game+ (A Lenda Heróica)**:
   - Ao zerar o jogo e selecionar aquele slot no menu, o jogador recebe a opção de iniciar o **New Game+**:
     - Mantém os níveis, árvore de habilidades, moedas e relíquias coletadas.
     - Todos os inimigos e Guardiões ganham novos padrões de ataque mais rápidos, projéteis extras e comportamento mais agressivo.
     - Recompensas de Ouro e XP aumentadas em 2x.

3. **Jukebox / Sala de Música & Bestiário Interativo**:
   - No Menu Principal (ou em uma sala especial na Taverna da Vila), desbloqueie um Tocador de Música clássico para o jogador ouvir todas as faixas procedurais do jogo (Vila, Floresta, Lago, Ruínas, Santuário, Boss Fight, Vitória, Créditos).
   - O Bestiário ganha um contador de quantas vezes o jogador derrotou cada monstro, fraquezas elementais reveladas e animação do sprite em 360°.

---

## 📦 PILAR 5: Empacotamento & Script de Distribuição (Release Ready)

1. **Script de Geração de Executável (Build Automatizado)**:
   - Crie um script Python (`scripts/construir_executavel.py`) utilizando `pyinstaller`:
     - Empacota o jogo em um executável único e independente, incluindo todos os mapas (`maps/`), scripts, assets e fontes.
     - Gera o executável tanto para Windows (`.exe`) quanto para Linux sem depender de terminal ou de interpretador Python instalado na máquina do jogador.
     - Ícone do executável configurado com o brasão da espada dourada de *A Lenda Perdida*.
