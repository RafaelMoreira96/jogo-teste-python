"""Menu Principal de A Lenda Perdida.

Apresenta uma cena panorâmica épica em 16-bits com paralaxe em camadas:
- Céu de crepúsculo animado com estrelas cintilantes e estrelas cadentes periódicas;
- Lua gigante com halo místico pulsante;
- Nuvens de crepúsculo em múltiplas profundidades deslizando pelo vento;
- Cordilheira sombria e a Cidadela Ancestral com beacon de cristal mágico pulsante;
- Penhasco varrido pelo vento com a silhueta do Herói e sua capa esvoaçante ao vento;
- Partículas de poeira mágica dourada e folhas levadas pela brisa;
- Brasão de asas heráldicas douradas e o título 'A LENDA PERDIDA' com brilho especular itinerante.
"""
import math
import random
import pygame

from cenas.base import Cena
from settings import ALTURA, LARGURA, TITULO
from ui import CINZA, MenuLista, desenhar_cursor, desenhar_painel, desenhar_texto


class ParticulaVento:
    """Partículas douradas de poeira estelar e folhas levadas pelo vento."""
    def __init__(self):
        self.reset(random.uniform(0, LARGURA))

    def reset(self, x=None):
        self.x = -10 if x is None else x
        self.y = random.uniform(20, ALTURA - 15)
        self.vx = random.uniform(28, 55)
        self.vy = random.uniform(-6, 8)
        self.ondulacao = random.uniform(2.0, 5.0)
        self.fase = random.uniform(0, math.tau)
        self.tamanho = random.choice([1, 1, 2])
        self.cor = random.choice([
            (255, 235, 140),  # Ouro brilhante
            (240, 190, 80),   # Âmbar místico
            (220, 110, 60),   # Folha de outono
            (180, 240, 255),  # Centelha celeste
        ])

    def atualizar(self, dt, t):
        self.x += self.vx * dt
        self.y += math.sin(t * self.ondulacao + self.fase) * 0.45 + self.vy * dt * 0.2
        if self.x > LARGURA + 10 or self.y < 10 or self.y > ALTURA:
            self.reset()


class EstrelaCadente:
    """Meteoro que corta o céu do crepúsculo periodicamente."""
    def __init__(self):
        self.ativa = False
        self.tempo_espera = random.uniform(4.0, 9.0)
        self.x = 0
        self.y = 0
        self.vx = 0
        self.vy = 0
        self.vida = 0.0

    def atualizar(self, dt):
        if not self.ativa:
            self.tempo_espera -= dt
            if self.tempo_espera <= 0:
                self.ativa = True
                self.x = random.randint(60, 260)
                self.y = random.randint(10, 45)
                self.vx = random.uniform(160, 240)
                self.vy = random.uniform(70, 120)
                self.vida = random.uniform(0.35, 0.55)
                self.tempo_espera = random.uniform(7.0, 14.0)
        else:
            self.vida -= dt
            self.x += self.vx * dt
            self.y += self.vy * dt
            if self.vida <= 0:
                self.ativa = False

    def desenhar(self, tela):
        if not self.ativa:
            return
        # Rastro do meteoro
        for i in range(5):
            fator = 1.0 - (i / 5.0)
            px = int(self.x - self.vx * 0.025 * i)
            py = int(self.y - self.vy * 0.025 * i)
            if 0 <= px < LARGURA and 0 <= py < ALTURA:
                cor = (int(255 * fator), int(245 * fator), int(200 * fator))
                pygame.draw.line(tela, cor, (px, py), (px + 1, py), 1)


class MenuPrincipal(Cena):
    def __init__(self, app):
        super().__init__(app)
        self.t = 0.0

        from salvamento import existe_save
        opcoes = ["Novo jogo", "Modo Chefões", "Editor de jogo", "Configurações", "Sair"]
        if existe_save():
            opcoes.insert(0, "Continuar")
        self.menu = MenuLista(opcoes)

        if hasattr(app, "audio"):
            app.audio.tocar_bgm("menu")

        # Superfície pré-renderizada do gradiente de céu
        self.surf_ceu = pygame.Surface((LARGURA, 125))
        self._gerar_gradiente_ceu()

        # Estrelas cintilantes de fundo
        random.seed(42)
        self.estrelas = [
            (random.randint(4, LARGURA - 4), random.randint(4, 75), random.uniform(1.5, 4.0), random.uniform(0, math.tau))
            for _ in range(32)
        ]
        random.seed()

        # Estrela cadente
        self.meteoro = EstrelaCadente()

        # Nuvens de crepúsculo (2 camadas de profundidade)
        self.nuvens = [
            {"x": 20, "y": 38, "vel": 4.5, "tam": (48, 12), "cor": (55, 28, 52)},
            {"x": 160, "y": 24, "vel": 3.8, "tam": (64, 14), "cor": (48, 24, 46)},
            {"x": 270, "y": 48, "vel": 5.2, "tam": (52, 11), "cor": (65, 32, 58)},
            {"x": 80, "y": 62, "vel": 7.0, "tam": (70, 16), "cor": (88, 42, 60)},
            {"x": 220, "y": 68, "vel": 8.0, "tam": (58, 15), "cor": (95, 45, 62)},
        ]

        # Partículas de vento
        self.particulas = [ParticulaVento() for _ in range(22)]


    def _gerar_gradiente_ceu(self):
        cor_topo = (14, 10, 28)
        cor_meio = (48, 20, 42)
        cor_horiz = (130, 60, 48)
        for y in range(125):
            fator = y / 125.0
            if fator < 0.5:
                sub = fator * 2.0
                r = int(cor_topo[0] * (1 - sub) + cor_meio[0] * sub)
                g = int(cor_topo[1] * (1 - sub) + cor_meio[1] * sub)
                b = int(cor_topo[2] * (1 - sub) + cor_meio[2] * sub)
            else:
                sub = (fator - 0.5) * 2.0
                r = int(cor_meio[0] * (1 - sub) + cor_horiz[0] * sub)
                g = int(cor_meio[1] * (1 - sub) + cor_horiz[1] * sub)
                b = int(cor_meio[2] * (1 - sub) + cor_horiz[2] * sub)
            pygame.draw.line(self.surf_ceu, (r, g, b), (0, y), (LARGURA, y))

    def atualizar(self, dt):
        from cenas.configuracoes import Configuracoes
        from cenas.editor import Editor
        from cenas.jogo import Jogo

        if hasattr(self.app, "audio"):
            self.app.audio.tocar_bgm("menu")

        self.t += dt

        # Atualiza meteoro e nuvens
        self.meteoro.atualizar(dt)
        for n in self.nuvens:
            n["x"] += n["vel"] * dt
            if n["x"] > LARGURA + 30:
                n["x"] = -n["tam"][0] - 10

        # Atualiza partículas de vento
        for p in self.particulas:
            p.atualizar(dt, self.t)

        ant = self.menu.indice
        res = self.menu.atualizar(self.app.entrada)
        if self.menu.indice != ant and hasattr(self.app, "audio"):
            self.app.audio.sfx("menu_mover")

        if res != "confirmar":
            return

        if hasattr(self.app, "audio"):
            self.app.audio.sfx("menu_confirmar")

        escolha = self.menu.opcoes[self.menu.indice]
        if escolha == "Continuar":
            from salvamento import carregar_jogo
            salvo = carregar_jogo(self.app)
            if salvo:
                self.app.trocar(salvo)
            else:
                self.app.trocar(Jogo(self.app))
        elif escolha == "Novo jogo":
            self.app.trocar(Jogo(self.app))
        elif escolha == "Modo Chefões":
            from cenas.modo_chefes import SelecaoChefes
            self.app.trocar(SelecaoChefes(self.app))
        elif escolha == "Editor de jogo":
            self.app.trocar(Editor(self.app))
        elif escolha == "Configurações":
            self.app.empilhar(Configuracoes(self.app))
        elif escolha == "Sair":
            self.app.sair()

    def desenhar(self, tela):
        # 1. Céu em gradiente de crepúsculo
        tela.blit(self.surf_ceu, (0, 0))

        # 2. Estrelas cintilantes
        for ex, ey, freq, fase in self.estrelas:
            brilho = int(140 + 115 * math.sin(self.t * freq + fase))
            cor_est = (brilho, brilho, int(brilho * 0.9))
            tela.set_at((ex, ey), cor_est)

        # 3. Estrela cadente
        self.meteoro.desenhar(tela)

        # 4. Lua Mística Gigante com halo pulsante
        mx, my = 284, 30
        pulsar_halo = math.sin(self.t * 1.8) * 2.0
        halo = pygame.Surface((64, 64), pygame.SRCALPHA)
        for r in range(28 + int(pulsar_halo), 14, -2):
            alpha = int(16 * (1.0 - (r - 14) / 16.0))
            pygame.draw.circle(halo, (255, 235, 180, alpha), (32, 32), r)
        tela.blit(halo, (mx - 32, my - 32))
        
        # Disco da lua
        pygame.draw.circle(tela, (250, 242, 215), (mx, my), 15)
        # Crateras e sombreamento
        pygame.draw.circle(tela, (225, 212, 185), (mx - 4, my - 3), 3)
        pygame.draw.circle(tela, (225, 212, 185), (mx + 5, my + 4), 4)
        pygame.draw.circle(tela, (215, 200, 175), (mx - 2, my + 6), 2)
        # Sombra de crescente
        sombra_lua = pygame.Surface((30, 30), pygame.SRCALPHA)
        pygame.draw.circle(sombra_lua, (30, 18, 38, 110), (10, 15), 14)
        tela.blit(sombra_lua, (mx - 15, my - 15))

        # 5. Nuvens de crepúsculo em paralaxe
        for n in self.nuvens:
            nx, ny = int(n["x"]), int(n["y"])
            w, h = n["tam"]
            pygame.draw.ellipse(tela, n["cor"], (nx, ny, w, h))
            # Borda iluminada superior
            cor_borda = (min(255, n["cor"][0] + 35), min(255, n["cor"][1] + 20), min(255, n["cor"][2] + 25))
            pygame.draw.arc(tela, cor_borda, (nx, ny, w, h), 0, math.pi, 1)

        # 6. Cordilheira 1 (Montanhas distantes roxas)
        montanhas_1 = [
            (0, 110), (35, 82), (75, 105), (115, 78), (160, 98),
            (200, 72), (245, 96), (285, 76), (320, 102), (320, 130), (0, 130)
        ]
        pygame.draw.polygon(tela, (36, 18, 36), montanhas_1)
        for p1, p2 in [((35, 82), (55, 100)), ((115, 78), (135, 92)), ((200, 72), (220, 88)), ((285, 76), (300, 92))]:
            pygame.draw.line(tela, (85, 42, 65), p1, p2, 1)

        # 7. A Cidadela Ancestral / Castelo Proibido na colina (x=175 a 225)
        cx = 128
        # Torre central mais alta
        pygame.draw.polygon(tela, (22, 14, 28), [(cx + 10, 58), (cx + 7, 72), (cx + 13, 72)])
        pygame.draw.rect(tela, (22, 14, 28), (cx + 7, 72, 6, 26))
        # Farol de cristal mágico pulsante no topo
        brilho_cristal = int(200 + 55 * math.sin(self.t * 4.0))
        pygame.draw.circle(tela, (0, brilho_cristal, 255), (cx + 10, 56), 2)
        tela.set_at((cx + 10, 56), (255, 255, 255))

        # Torres laterais e baluartes
        pygame.draw.polygon(tela, (22, 14, 28), [(cx - 2, 68), (cx - 5, 78), (cx + 1, 78)])
        pygame.draw.rect(tela, (22, 14, 28), (cx - 5, 78, 6, 20))
        pygame.draw.polygon(tela, (22, 14, 28), [(cx + 22, 68), (cx + 19, 78), (cx + 25, 78)])
        pygame.draw.rect(tela, (22, 14, 28), (cx + 19, 78, 6, 20))
        pygame.draw.rect(tela, (22, 14, 28), (cx - 4, 82, 28, 18))
        
        # Janelas acesas piscando suavemente
        for wx, wy in [(cx + 9, 78), (cx + 9, 85), (cx - 2, 86), (cx + 21, 86), (cx + 5, 92), (cx + 14, 92)]:
            flicker = 220 + int(35 * math.sin(self.t * 5.0 + wx))
            tela.set_at((wx, wy), (flicker, flicker - 30, 90))

        # 8. Cordilheira 2 (Colinas próximas e pinheiros em silhueta)
        montanhas_2 = [
            (0, 126), (40, 114), (90, 122), (140, 108), (180, 116),
            (230, 106), (270, 118), (320, 112), (320, 180), (0, 180)
        ]
        pygame.draw.polygon(tela, (20, 15, 28), montanhas_2)
        for tx in [45, 52, 60, 125, 132, 155, 240, 248, 256, 305, 312]:
            ty = 114 if tx < 100 else (110 if tx < 200 else 112)
            pygame.draw.polygon(tela, (14, 10, 20), [(tx, ty - 6), (tx - 3, ty), (tx + 3, ty)])
            pygame.draw.line(tela, (14, 10, 20), (tx, ty), (tx, ty + 2), 1)

        # 9. Penhasco em primeiro plano à esquerda
        pontos_penhasco = [
            (0, 132), (32, 128), (56, 125), (78, 128), (92, 136), (82, 150),
            (90, 168), (80, 180), (0, 180)
        ]
        pygame.draw.polygon(tela, (15, 12, 22), pontos_penhasco)
        pygame.draw.lines(tela, (38, 48, 32), False, [(0, 132), (32, 128), (56, 125), (78, 128), (92, 136)], 2)
        for p1, p2 in [((30, 130), (25, 155)), ((60, 127), (55, 160)), ((80, 135), (72, 165))]:
            pygame.draw.line(tela, (28, 22, 36), p1, p2, 1)

        # 10. Silhueta do Herói solitário com capa esvoaçante ao vento
        hx, hy = 58, 125
        # Pernas e armadura
        pygame.draw.line(tela, (10, 8, 16), (hx - 2, hy), (hx - 3, hy - 8), 2)
        pygame.draw.line(tela, (10, 8, 16), (hx + 2, hy), (hx + 2, hy - 8), 2)
        pygame.draw.rect(tela, (12, 10, 18), (hx - 4, hy - 16, 7, 9))
        pygame.draw.circle(tela, (12, 10, 18), (hx, hy - 19), 3)

        # Capa vermelha real balançando dinamicamente com o vento
        onda_capa1 = math.sin(self.t * 7.5) * 3.0
        onda_capa2 = math.cos(self.t * 6.5) * 2.5
        cape_pts = [
            (hx - 4, hy - 14),
            (hx - 14 + int(onda_capa1 * 0.5), hy - 12 + int(onda_capa2)),
            (hx - 19 + int(onda_capa1), hy - 7 + int(onda_capa2 * 0.7)),
            (hx - 10, hy - 5),
            (hx - 2, hy - 8),
        ]
        pygame.draw.polygon(tela, (140, 32, 45), cape_pts)
        pygame.draw.polygon(tela, (185, 45, 60), [(p[0], p[1] - 1) for p in cape_pts[:3]] + [(hx - 4, hy - 14)])

        # Espada Sagrada cravada ou empunhada (com brilho especular na ponta)
        pygame.draw.line(tela, (200, 230, 255), (hx + 4, hy - 4), (hx + 4, hy - 22), 1)
        pygame.draw.line(tela, (255, 215, 0), (hx + 2, hy - 8), (hx + 6, hy - 8), 1)
        brilho_espada = int(220 + 35 * math.sin(self.t * 6.0))
        tela.set_at((hx + 4, hy - 23), (brilho_espada, brilho_espada, 255))

        # 11. Partículas de poeira dourada e folhas levadas pelo vento
        for p in self.particulas:
            pygame.draw.rect(tela, p.cor, (int(p.x), int(p.y), p.tamanho, p.tamanho))


        # 13. Brasão Heráldico Superior (Asas douradas e joia ciano)
        w_center_x = LARGURA // 2
        w_y = 15
        pontos_asa_esq = [(w_center_x - 8, w_y), (w_center_x - 35, w_y - 4), (w_center_x - 55, w_y + 2), (w_center_x - 25, w_y + 3)]
        pontos_asa_dir = [(w_center_x + 8, w_y), (w_center_x + 35, w_y - 4), (w_center_x + 55, w_y + 2), (w_center_x + 25, w_y + 3)]
        pygame.draw.polygon(tela, (215, 160, 40), pontos_asa_esq)
        pygame.draw.polygon(tela, (255, 230, 110), [(p[0], p[1] - 1) for p in pontos_asa_esq])
        pygame.draw.polygon(tela, (215, 160, 40), pontos_asa_dir)
        pygame.draw.polygon(tela, (255, 230, 110), [(p[0], p[1] - 1) for p in pontos_asa_dir])
        pygame.draw.polygon(tela, (0, 240, 255), [(w_center_x, w_y - 4), (w_center_x + 5, w_y), (w_center_x, w_y + 4), (w_center_x - 5, w_y)])
        tela.set_at((w_center_x, w_y), (255, 255, 255))

        # 14. Título Principal Majestoso: 'A LENDA PERDIDA' com brilho especular itinerante
        fontes = self.app.fontes
        
        # O brilho especular percorre o título a cada 3.5 segundos
        ciclo_brilho = (self.t % 3.5) / 1.2
        cor_titulo = (255, 235, 130)
        if 0.0 <= ciclo_brilho <= 1.0:
            # Pulso de brilho suave dourado/branco
            intensidade = math.sin(ciclo_brilho * math.pi)
            r = min(255, int(255 + 20 * intensidade))
            g = min(255, int(235 + 20 * intensidade))
            b = min(255, int(130 + 125 * intensidade))
            cor_titulo = (r, g, b)

        desenhar_texto(tela, fontes.titulo, TITULO, (w_center_x, 32), cor_titulo, centro=True)
        desenhar_texto(tela, fontes.normal, "- CRÔNICAS DO REINO ESQUECIDO -", (w_center_x, 48), (210, 185, 150), centro=True)

        # 15. Menu de Opções em painel 16-bits
        espaco = 15
        painel = pygame.Rect(194, 64, 112, len(self.menu.opcoes) * espaco + 10)
        desenhar_painel(tela, painel, alfa=205)
        menu_base_y = painel.y + 10
        for i, opc in enumerate(self.menu.opcoes):
            y_pos = menu_base_y + i * espaco
            if i == self.menu.indice:
                faixa = pygame.Surface((painel.width - 8, 11), pygame.SRCALPHA)
                faixa.fill((255, 200, 90, 46))
                tela.blit(faixa, (painel.x + 4, y_pos - 5))
                pulsar_sel = int(230 + 25 * math.sin(self.t * 5.0))
                desenhar_texto(tela, fontes.normal, opc, (painel.centerx + 4, y_pos), (255, pulsar_sel, 110), centro=True)
                desenhar_cursor(tela, painel.x + 7, y_pos - 3, t=self.t)
            else:
                desenhar_texto(tela, fontes.normal, opc, (painel.centerx + 4, y_pos), (170, 175, 195), centro=True)

        # 16. Rodapé com indicação de controles
        controle = self.app.entrada.nome_controle()
        rodape = f"Controle: {controle}" if controle else "Enter / Espaço: escolher"
        desenhar_texto(tela, fontes.normal, rodape, (w_center_x, ALTURA - 11), CINZA, centro=True)
