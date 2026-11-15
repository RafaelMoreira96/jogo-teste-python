"""Tela da Loja e Forja da Vila em 16-bits para A Lenda Perdida."""
import pygame

from cenas.base import Cena
from settings import ALTURA, LARGURA
from ui import AMARELO, BRANCO, CINZA, ajustar_texto, desenhar_painel, quebrar_linhas, desenhar_rodape, desenhar_texto, escurecer

ITENS_LOJA = [
    {
        "id": "pocao_vida",
        "nome": "Poção de Vida",
        "preco": 15,
        "tipo": "consumivel",
        "desc": "Recupera 4 meios-corações instantaneamente.",
    },
    {
        "id": "pocao_mana",
        "nome": "Elixir de Mana",
        "preco": 15,
        "tipo": "consumivel",
        "desc": "Restaura 20 pontos de mana imediatamente.",
    },
    {
        "id": "bomba",
        "nome": "Bolsa de Bombas (+3)",
        "preco": 25,
        "tipo": "consumivel",
        "desc": "Adiciona 3 bombas para quebrar paredes e abrir passagens.",
    },
    {
        "id": "escudo_madeira",
        "nome": "Escudo de Carvalho",
        "preco": 30,
        "tipo": "escudo",
        "desc": "Equipamento: Segure [E / LCtrl] para bloquear flechas e projéteis.",
    },
    {
        "id": "lamina_vulcanica",
        "nome": "Lâmina Vulcânica",
        "preco": 60,
        "tipo": "arma",
        "desc": "Espada Dano 2: Queima os inimigos com fogo ardente.",
    },
    {
        "id": "sabre_tempestade",
        "nome": "Sabre da Tempestade",
        "preco": 90,
        "tipo": "arma",
        "desc": "Espada Dano 2: Ataques ágeis 40% mais velozes.",
    },
    {
        "id": "armadura_carmesim",
        "nome": "Armadura Carmesim",
        "preco": 75,
        "tipo": "tunica",
        "desc": "Armadura de Aço: Reduz todo dano recebido em 50%.",
    },
    {
        "id": "manto_astral",
        "nome": "Manto Astral",
        "preco": 95,
        "tipo": "tunica",
        "desc": "Manto Sagrado: Acelera regeneração de mana em +80%.",
    },
]


class CenaLoja(Cena):
    transparente = True

    def __init__(self, app, jogo):
        super().__init__(app)
        self.jogo = jogo
        self.indice = 0
        self.scroll = 0
        self.msg = ""
        self.timer_msg = 0.0

    def atualizar(self, dt):
        entrada = self.app.entrada
        audio = getattr(self.app, "audio", None)

        self.timer_msg = max(0.0, self.timer_msg - dt)

        ant = self.indice
        if entrada.apertou("cima"):
            self.indice = (self.indice - 1) % len(ITENS_LOJA)
        elif entrada.apertou("baixo"):
            self.indice = (self.indice + 1) % len(ITENS_LOJA)

        if self.indice != ant and audio:
            audio.sfx("menu_mover")

        if entrada.apertou("voltar") or entrada.apertou("pausa"):
            if audio:
                audio.sfx("menu_voltar")
            self.app.desempilhar()
            return

        if entrada.apertou("confirmar") or entrada.apertou("acao"):
            item = ITENS_LOJA[self.indice]
            rpg = self.jogo.rpg

            # Verifica se já possui equipamento único
            ja_tem = False
            if item["tipo"] == "arma" and rpg.arma_equipada == item["id"]:
                ja_tem = True
            elif item["tipo"] == "escudo" and rpg.escudo_equipado == item["id"]:
                ja_tem = True
            elif item["tipo"] == "tunica" and rpg.tunica_equipada == item["id"]:
                ja_tem = True

            if ja_tem:
                self.msg = "Você já possui este equipamento equipado!"
                self.timer_msg = 2.0
                if audio:
                    audio.sfx("bloqueio")
                return

            if rpg.ouro < item["preco"]:
                self.msg = "Ouro insuficiente para comprar este item!"
                self.timer_msg = 2.0
                if audio:
                    audio.sfx("bloqueio")
                return

            # Efetua compra
            rpg.ouro -= item["preco"]
            if item["id"] == "pocao_vida":
                self.jogo.jogador.curar(4)
                self.msg = "Vida restaurada em +4 corações!"
            elif item["id"] == "pocao_mana":
                rpg.mana = min(rpg.mana_maxima, rpg.mana + 20)
                self.msg = "Mana restaurada em +20 MP!"
            elif item["id"] == "bomba":
                rpg.bombas += 3
                self.msg = "Adquiridas +3 Bombas!"
            elif item["tipo"] == "arma":
                rpg.arma_equipada = item["id"]
                self.msg = f"{item['nome']} equipada com sucesso!"
            elif item["tipo"] == "escudo":
                rpg.escudo_equipado = item["id"]
                self.msg = f"{item['nome']} equipado! Segure [E] para defender."
            elif item["tipo"] == "tunica":
                rpg.tunica_equipada = item["id"]
                self.msg = f"{item['nome']} vestida com sucesso!"

            self.timer_msg = 2.5
            if audio:
                audio.sfx("compra")

        # Scroll suave
        alvo = max(0, min(len(ITENS_LOJA) - 4, self.indice - 1))
        self.scroll += (alvo - self.scroll) * 12.0 * dt

    def desenhar(self, tela):
        escurecer(tela, 220)
        fonte = self.app.fontes.normal

        painel = pygame.Rect(12, 8, LARGURA - 24, ALTURA - 16)
        desenhar_painel(tela, painel)

        # Topo com nome e carteira
        desenhar_texto(tela, fonte, "FORJA E MERCADO DA VILA", (20, 14), AMARELO)
        ouro_txt = f"Ouro: {self.jogo.rpg.ouro} G"
        desenhar_texto(tela, fonte, ouro_txt, (LARGURA - 20 - fonte.size(ouro_txt)[0], 14), (255, 230, 100))
        pygame.draw.line(tela, (65, 75, 110), (16, 26), (LARGURA - 16, 26))

        # Lista de itens com scroll
        base_y = 30
        item_alt = 26
        clip_rect = pygame.Rect(16, base_y, LARGURA - 32, 108)
        antigo_clip = tela.get_clip()
        tela.set_clip(clip_rect)

        for i, item in enumerate(ITENS_LOJA):
            y_pos = base_y + int((i - self.scroll) * item_alt)
            if y_pos < base_y - item_alt or y_pos > base_y + 108:
                continue

            eh_sel = (i == self.indice)
            rect_i = pygame.Rect(18, y_pos, LARGURA - 36, 23)

            cor_bg = (38, 50, 85) if eh_sel else (24, 28, 48)
            pygame.draw.rect(tela, cor_bg, rect_i, border_radius=3)
            cor_borda = AMARELO if eh_sel else (55, 65, 95)
            pygame.draw.rect(tela, cor_borda, rect_i, 1, border_radius=3)

            # Nome e preço
            desenhar_texto(tela, fonte, item["nome"], (24, y_pos + 3), AMARELO if eh_sel else BRANCO)
            desenhar_texto(tela, fonte, f"{item['preco']} G", (LARGURA - 64, y_pos + 3), (255, 215, 80))
            desenhar_texto(tela, fonte, ajustar_texto(fonte, item["desc"], LARGURA - 52), (24, y_pos + 13), (190, 200, 220) if eh_sel else CINZA)

        tela.set_clip(antigo_clip)

        # Descrição completa do item selecionado
        desc_sel = quebrar_linhas(fonte, ITENS_LOJA[self.indice]["desc"], LARGURA - 44)[:2]
        for li, linha in enumerate(desc_sel):
            desenhar_texto(tela, fonte, linha, (22, 142 + li * 10), (170, 190, 230))

        # Mensagem de feedback
        if self.timer_msg > 0 and self.msg:
            faixa = pygame.Surface((LARGURA - 40, 14), pygame.SRCALPHA)
            faixa.fill((16, 24, 46, 230))
            pygame.draw.rect(faixa, AMARELO, faixa.get_rect(), 1)
            tela.blit(faixa, (20, ALTURA - 37))
            desenhar_texto(tela, fonte, self.msg, (LARGURA // 2, ALTURA - 30), AMARELO, centro=True)

        rodape = "Enter / Espaço: Comprar | Esc / X: Voltar"
        desenhar_rodape(tela, fonte, rodape, CINZA)
