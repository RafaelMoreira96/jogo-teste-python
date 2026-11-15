"""Tela da Loja e Forja da Vila em 16-bits para A Lenda Perdida.

Estrutura profissional com abas categorizadas (Pilar 3 do Prompt 3):
- Consumíveis: Poções de Vida, Elixir de Mana, Bombas e Chaves de Baú.
- Equipamentos & Amuletos: Amuleto da Rapidez, Ímã de Ouro, Escudos e Túnicas.
- Forja de Armas: Aprimoramento permanente de Dano e Espadas Lendárias.
"""
import pygame

from cenas.base import Cena
from settings import ALTURA, LARGURA
from ui import AMARELO, BRANCO, CINZA, ajustar_texto, desenhar_painel, desenhar_rodape, desenhar_texto, escurecer, quebrar_linhas

CATALOGO_LOJA = {
    "consumiveis": [
        {
            "id": "pocao_vida",
            "nome": "Poção de Vida",
            "preco": 15,
            "tipo": "consumivel",
            "desc": "Recupera 4 meios-corações de vida instantaneamente.",
        },
        {
            "id": "pocao_mana",
            "nome": "Elixir de Mana",
            "preco": 15,
            "tipo": "consumivel",
            "desc": "Recupera 50% da mana máxima imediatamente.",
        },
        {
            "id": "bomba",
            "nome": "Pacote de Bombas (+3)",
            "preco": 25,
            "tipo": "consumivel",
            "desc": "Adiciona 3 bombas para quebrar paredes e rochas rachadas.",
        },
        {
            "id": "chave",
            "nome": "Chave de Baú Ancestral",
            "preco": 30,
            "tipo": "consumivel",
            "desc": "Chave de bronze para abrir baús trancados em calabouços.",
        },
    ],
    "amuletos": [
        {
            "id": "amuleto_rapidez",
            "nome": "Amuleto da Rapidez",
            "preco": 50,
            "tipo": "amuleto",
            "desc": "Bônus Passivo: Aumenta a velocidade de movimento em +15%.",
        },
        {
            "id": "ima_ouro",
            "nome": "Ímã de Ouro",
            "preco": 45,
            "tipo": "amuleto",
            "desc": "Bônus Passivo: Atrai moedas e itens de 2x mais longe.",
        },
        {
            "id": "escudo_madeira",
            "nome": "Escudo de Carvalho",
            "preco": 30,
            "tipo": "escudo",
            "desc": "Equipamento: Segure [E / LCtrl] para bloquear flechas e projéteis.",
        },
        {
            "id": "armadura_carmesim",
            "nome": "Armadura Carmesim",
            "preco": 75,
            "tipo": "tunica",
            "desc": "Armadura de Aço: Reduz todo dano recebido pelo herói em 50%.",
        },
        {
            "id": "manto_astral",
            "nome": "Manto Astral",
            "preco": 95,
            "tipo": "tunica",
            "desc": "Manto Celestial: Acelera regeneração passiva de mana em +80%.",
        },
    ],
    "forja": [
        {
            "id": "aprimorar_espada",
            "nome": "Forjar Lâmina (+1 Dano)",
            "preco": 50,
            "tipo": "forja",
            "desc": "Aprimora o fio da sua espada atual com minérios da vila.",
        },
        {
            "id": "lamina_vulcanica",
            "nome": "Lâmina Vulcânica",
            "preco": 60,
            "tipo": "arma",
            "desc": "Espada Dano 2: Queima os inimigos com fogo das profundezas.",
        },
        {
            "id": "sabre_tempestade",
            "nome": "Sabre da Tempestade",
            "preco": 90,
            "tipo": "arma",
            "desc": "Espada Dano 2: Golpes reluzentes 40% mais ágeis.",
        },
        {
            "id": "lamina_lendaria",
            "nome": "Lâmina dos Guardiões",
            "preco": 150,
            "tipo": "arma",
            "desc": "Espada Sagrada Dano 3: Imbuída com o poder de todos os Guardiões.",
        },
    ],
}

ABAS = [
    ("consumiveis", "1. Consumíveis"),
    ("amuletos", "2. Amuletos & Equip."),
    ("forja", "3. Forja de Armas"),
]


class CenaLoja(Cena):
    transparente = True

    def __init__(self, app, jogo):
        super().__init__(app)
        self.jogo = jogo
        self.aba_idx = 0
        self.indice = 0
        self.scroll = 0
        self.msg = ""
        self.timer_msg = 0.0

    @property
    def chave_aba(self):
        return ABAS[self.aba_idx][0]

    @property
    def lista_itens(self):
        return CATALOGO_LOJA[self.chave_aba]

    def _preco_item(self, item):
        if item["id"] == "aprimorar_espada":
            nv = getattr(self.jogo.rpg, "nivel_espada", 1)
            return nv * 50
        return item["preco"]

    def atualizar(self, dt):
        entrada = self.app.entrada
        audio = getattr(self.app, "audio", None)

        self.timer_msg = max(0.0, self.timer_msg - dt)

        # Alternar abas com Esquerda/Direita ou Q/E
        ant_aba = self.aba_idx
        if entrada.apertou("esquerda"):
            self.aba_idx = (self.aba_idx - 1) % len(ABAS)
            self.indice = 0
            self.scroll = 0
        elif entrada.apertou("direita"):
            self.aba_idx = (self.aba_idx + 1) % len(ABAS)
            self.indice = 0
            self.scroll = 0

        if self.aba_idx != ant_aba and audio:
            audio.sfx("menu_mover")

        # Navegar itens da lista com Cima/Baixo
        ant_idx = self.indice
        itens = self.lista_itens
        if entrada.apertou("cima"):
            self.indice = (self.indice - 1) % len(itens)
        elif entrada.apertou("baixo"):
            self.indice = (self.indice + 1) % len(itens)

        if self.indice != ant_idx and audio:
            audio.sfx("menu_mover")

        if entrada.apertou("voltar") or entrada.apertou("pausa"):
            if audio:
                audio.sfx("menu_voltar")
            self.app.desempilhar()
            return

        if entrada.apertou("confirmar") or entrada.apertou("acao"):
            item = itens[self.indice]
            rpg = self.jogo.rpg
            preco = self._preco_item(item)

            # Verificações de compra
            if item["id"] == "aprimorar_espada":
                if rpg.nivel_espada >= 4:
                    self.msg = "Sua lâmina já está forjada ao nível máximo!"
                    self.timer_msg = 2.0
                    if audio:
                        audio.sfx("bloqueio")
                    return
            elif item["id"] == "amuleto_rapidez" and "rapidez" in getattr(rpg, "amuletos", set()):
                self.msg = "Você já possui o Amuleto da Rapidez!"
                self.timer_msg = 2.0
                if audio:
                    audio.sfx("bloqueio")
                return
            elif item["id"] == "ima_ouro" and "ima" in getattr(rpg, "amuletos", set()):
                self.msg = "Você já possui o Ímã de Ouro!"
                self.timer_msg = 2.0
                if audio:
                    audio.sfx("bloqueio")
                return
            elif item["tipo"] == "arma" and rpg.arma_equipada == item["id"]:
                self.msg = "Você já possui esta espada equipada!"
                self.timer_msg = 2.0
                if audio:
                    audio.sfx("bloqueio")
                return
            elif item["tipo"] == "escudo" and rpg.escudo_equipado == item["id"]:
                self.msg = "Você já possui este escudo equipado!"
                self.timer_msg = 2.0
                if audio:
                    audio.sfx("bloqueio")
                return
            elif item["tipo"] == "tunica" and rpg.tunica_equipada == item["id"]:
                self.msg = "Você já possui esta armadura vestida!"
                self.timer_msg = 2.0
                if audio:
                    audio.sfx("bloqueio")
                return

            if rpg.ouro < preco:
                self.msg = "Ouro insuficiente para comprar este item!"
                self.timer_msg = 2.0
                if audio:
                    audio.sfx("bloqueio")
                return

            # Efetua compra e consome ouro
            rpg.ouro -= preco
            if item["id"] == "pocao_vida":
                self.jogo.jogador.curar(4)
                self.msg = "Vida restaurada em +4 meios-corações!"
            elif item["id"] == "pocao_mana":
                rpg.mana = min(rpg.mana_maxima, rpg.mana + rpg.mana_maxima * 0.5)
                self.msg = "Mana restaurada em +50%!"
            elif item["id"] == "bomba":
                rpg.bombas += 3
                self.msg = "Adquiridas +3 Bombas!"
            elif item["id"] == "chave":
                rpg.chaves += 1
                self.msg = "Adquirida +1 Chave de Baú!"
            elif item["id"] == "amuleto_rapidez":
                rpg.amuletos.add("rapidez")
                self.msg = "Amuleto da Rapidez ativado! (+15% velocidade)"
            elif item["id"] == "ima_ouro":
                rpg.amuletos.add("ima")
                self.msg = "Ímã de Ouro ativado! (Alcance magnético ampliado)"
            elif item["id"] == "aprimorar_espada":
                rpg.nivel_espada += 1
                self.msg = f"Lâmina forjada para o Nv. {rpg.nivel_espada}! (+1 Dano)"
            elif item["tipo"] == "arma":
                rpg.arma_equipada = item["id"]
                self.jogo.jogador.arma_equipada = item["id"]
                self.msg = f"{item['nome']} equipada com sucesso!"
            elif item["tipo"] == "escudo":
                rpg.escudo_equipado = item["id"]
                self.jogo.jogador.escudo_equipado = item["id"]
                self.msg = f"{item['nome']} equipado! Segure [E / LCtrl] para defender."
            elif item["tipo"] == "tunica":
                rpg.tunica_equipada = item["id"]
                self.jogo.jogador.tunica_equipada = item["id"]
                self.msg = f"{item['nome']} vestida com sucesso!"

            self.timer_msg = 2.5
            if audio:
                audio.sfx("compra")

        # Scroll suave
        alvo = max(0, min(len(itens) - 4, self.indice - 1))
        self.scroll += (alvo - self.scroll) * 12.0 * dt

    def desenhar(self, tela):
        escurecer(tela, 220)
        fonte = self.app.fontes.normal

        painel = pygame.Rect(10, 6, LARGURA - 20, ALTURA - 12)
        desenhar_painel(tela, painel)

        # Topo: Título da Loja e Ouro atual
        desenhar_texto(tela, fonte, "MERCADO & FORJA DA VILA", (18, 11), AMARELO)
        ouro_txt = f"Ouro: {self.jogo.rpg.ouro} G"
        desenhar_texto(tela, fonte, ouro_txt, (LARGURA - 18 - fonte.size(ouro_txt)[0], 11), (255, 230, 100))

        # Abas de navegação no estilo clássico SNES
        y_aba = 24
        larg_aba = (LARGURA - 32) // len(ABAS)
        for i, (chave, rotulo) in enumerate(ABAS):
            eh_aba_sel = (i == self.aba_idx)
            rect_aba = pygame.Rect(16 + i * larg_aba, y_aba, larg_aba - 2, 14)
            cor_bg = (50, 65, 105) if eh_aba_sel else (22, 26, 44)
            pygame.draw.rect(tela, cor_bg, rect_aba, border_radius=2)
            cor_borda = AMARELO if eh_aba_sel else (55, 65, 95)
            pygame.draw.rect(tela, cor_borda, rect_aba, 1, border_radius=2)
            cor_txt = AMARELO if eh_aba_sel else CINZA
            desenhar_texto(tela, fonte, rotulo, rect_aba.center, cor_txt, centro=True)

        # Lista de itens com scroll suave
        base_y = 42
        item_alt = 24
        clip_rect = pygame.Rect(14, base_y, LARGURA - 28, 96)
        antigo_clip = tela.get_clip()
        tela.set_clip(clip_rect)

        itens = self.lista_itens
        for i, item in enumerate(itens):
            y_pos = base_y + int((i - self.scroll) * item_alt)
            if y_pos < base_y - item_alt or y_pos > base_y + 96:
                continue

            eh_sel = (i == self.indice)
            rect_i = pygame.Rect(16, y_pos, LARGURA - 32, 22)

            cor_bg = (38, 52, 90) if eh_sel else (24, 28, 48)
            pygame.draw.rect(tela, cor_bg, rect_i, border_radius=3)
            cor_borda = AMARELO if eh_sel else (55, 65, 95)
            pygame.draw.rect(tela, cor_borda, rect_i, 1, border_radius=3)

            preco = self._preco_item(item)
            preco_str = f"{preco} G"
            if item["id"] == "aprimorar_espada" and self.jogo.rpg.nivel_espada >= 4:
                preco_str = "MAX"

            # Nome e preço
            desenhar_texto(tela, fonte, item["nome"], (22, y_pos + 2), AMARELO if eh_sel else BRANCO)
            desenhar_texto(tela, fonte, preco_str, (LARGURA - 62, y_pos + 2), (255, 215, 80))
            desenhar_texto(tela, fonte, ajustar_texto(fonte, item["desc"], LARGURA - 46), (22, y_pos + 12), (190, 205, 225) if eh_sel else CINZA)

        tela.set_clip(antigo_clip)

        # Descrição e status do item selecionado
        item_sel = itens[self.indice]
        desc_sel = quebrar_linhas(fonte, item_sel["desc"], LARGURA - 40)[:2]
        for li, linha in enumerate(desc_sel):
            desenhar_texto(tela, fonte, linha, (18, 140 + li * 10), (170, 195, 235))

        # Mensagem flutuante de feedback
        if self.timer_msg > 0 and self.msg:
            faixa = pygame.Surface((LARGURA - 36, 14), pygame.SRCALPHA)
            faixa.fill((16, 24, 46, 235))
            pygame.draw.rect(faixa, AMARELO, faixa.get_rect(), 1)
            tela.blit(faixa, (18, ALTURA - 35))
            desenhar_texto(tela, fonte, self.msg, (LARGURA // 2, ALTURA - 28), AMARELO, centro=True)

        rodape = "←/→: Abas | ↑/↓: Itens | Enter: Comprar | Esc: Sair"
        desenhar_rodape(tela, fonte, rodape, CINZA)
