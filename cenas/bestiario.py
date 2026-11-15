"""Bestiário e Códex de Monstros e Guardiões de A Lenda Perdida."""
import math
import pygame

from cenas.base import Cena
from settings import ALTURA, LARGURA
from ui import AMARELO, BRANCO, CINZA, desenhar_texto, escurecer

ENTRADAS_BESTIARIO = [
    {
        "id": "slime",
        "nome": "Slime Azul",
        "tipo": "Comum",
        "hp": 3,
        "dano": 1,
        "fraqueza": "Fogo / Espada",
        "lore": "Criatura gelatinosa pacífica que salta pelas planícies verdejantes.",
    },
    {
        "id": "slime_verde",
        "nome": "Slime Verde Tóxico",
        "tipo": "Comum",
        "hp": 4,
        "dano": 1,
        "fraqueza": "Fogo",
        "lore": "Slime infectado pelas brumas venenosas do Pântano Sombrio.",
    },
    {
        "id": "duende",
        "nome": "Duende Ladrão",
        "tipo": "Comum",
        "hp": 3,
        "dano": 1,
        "fraqueza": "Gelo / Ataque em Área",
        "lore": "Ladino ágil com adaga que corre em ziguezague emboscando viajantes.",
    },
    {
        "id": "zumbi_arqueiro",
        "nome": "Zumbi Arqueiro",
        "tipo": "Morto-Vivo",
        "hp": 4,
        "dano": 1,
        "fraqueza": "Luz / Fogo",
        "lore": "Antigo arqueiro imperial erguido pela magia sombria da Cripta.",
    },
    {
        "id": "troll",
        "nome": "Troll das Rochas",
        "tipo": "Bruto",
        "hp": 8,
        "dano": 2,
        "fraqueza": "Raio / Esquiva",
        "lore": "Monstro colossal das montanhas capaz de esmagar o solo com sua clava.",
    },
    {
        "id": "rei_slime",
        "nome": "Rei Slime Coroado",
        "tipo": "Guardião (Nv. 1)",
        "hp": 22,
        "dano": 1,
        "fraqueza": "Fogo",
        "lore": "O monarca ancestral de todas as geleias, coroado no Covil dos Slimes.",
    },
    {
        "id": "golem_pedra",
        "nome": "Golem de Pedra Ancestral",
        "tipo": "Guardião (Nv. 2)",
        "hp": 28,
        "dano": 2,
        "fraqueza": "Raio Celestial",
        "lore": "Esculpido em pedra viva para guardar as Ruínas Esquecidas do reino.",
    },
    {
        "id": "serpente_dunas",
        "nome": "Serpente das Dunas",
        "tipo": "Guardião (Nv. 3)",
        "hp": 34,
        "dano": 2,
        "fraqueza": "Gelo",
        "lore": "Réptil colossal que nada sob as areias escaldantes do Deserto.",
    },
    {
        "id": "colosso_solar",
        "nome": "Colosso Solar",
        "tipo": "Guardião (Nv. 4)",
        "hp": 40,
        "dano": 2,
        "fraqueza": "Gelo / Corte",
        "lore": "Bastião radiante consagrado ao Templo do Sol.",
    },
    {
        "id": "bruxa_brumas",
        "nome": "Bruxa das Brumas",
        "tipo": "Guardião (Nv. 5)",
        "hp": 46,
        "dano": 2,
        "fraqueza": "Fogo / Luz",
        "lore": "Misteriosa feiticeira que tece feitiços de veneno no Pântano.",
    },
    {
        "id": "ceifador_espectral",
        "nome": "Ceifador Espectral",
        "tipo": "Guardião (Nv. 6)",
        "hp": 52,
        "dano": 2,
        "fraqueza": "Luz Ancestral",
        "lore": "Espírito implacável que ceifa almas nas catacumbas da Cripta.",
    },
    {
        "id": "leviata_aquatico",
        "nome": "Leviatã Aquático",
        "tipo": "Guardião (Nv. 7)",
        "hp": 58,
        "dano": 2,
        "fraqueza": "Raio",
        "lore": "Ser primordial das profundezas abissais do Lago Sereno.",
    },
    {
        "id": "guardiao_diamante",
        "nome": "Guardião dos Cristais",
        "tipo": "Guardião (Nv. 8)",
        "hp": 64,
        "dano": 2,
        "fraqueza": "Impacto / Fogo",
        "lore": "Entidade de pura ressonância cristalina no Núcleo de Cristal.",
    },
    {
        "id": "troll_rochas",
        "nome": "Troll das Cavernas",
        "tipo": "Guardião (Nv. 9)",
        "hp": 70,
        "dano": 3,
        "fraqueza": "Fogo / Corte",
        "lore": "O maior e mais feroz de todos os trolls, senhor do desfiladeiro.",
    },
    {
        "id": "yeti_glacial",
        "nome": "Yeti Glacial",
        "tipo": "Guardião (Nv. 10)",
        "hp": 76,
        "dano": 3,
        "fraqueza": "Chama Astral",
        "lore": "Fera lendária das neves eternas no Pico Congelado.",
    },
    {
        "id": "valquiria_caida",
        "nome": "Valquíria Sombria",
        "tipo": "Guardião (Nv. 11)",
        "hp": 82,
        "dano": 3,
        "fraqueza": "Luz",
        "lore": "Antiga guerreira celeste corrompida no Santuário esquecido.",
    },
    {
        "id": "cavaleiro_negro",
        "nome": "Cavaleiro Negro",
        "tipo": "Guardião (Nv. 12)",
        "hp": 88,
        "dano": 3,
        "fraqueza": "Esquiva / Fogo",
        "lore": "Guarda de honra do castelo, agora amaldiçoado em sua armadura negra.",
    },
    {
        "id": "quimera_abissal",
        "nome": "Quimera Abissal",
        "tipo": "Guardião (Nv. 13)",
        "hp": 94,
        "dano": 3,
        "fraqueza": "Gelo",
        "lore": "Monstruosidade de três cabeças confinada no fosso da masmorra.",
    },
    {
        "id": "arquimago",
        "nome": "Arquimago Corrompido",
        "tipo": "Guardião (Nv. 14)",
        "hp": 100,
        "dano": 4,
        "fraqueza": "Lâmina Solar",
        "lore": "O sábio conselheiro que sucumbiu ao poder proibido das estrelas.",
    },
    {
        "id": "paladino_juizo",
        "nome": "Paladino do Juízo",
        "tipo": "Guardião (Nv. 15)",
        "hp": 110,
        "dano": 4,
        "fraqueza": "Chama Astral",
        "lore": "O juiz supremo que protege as portas do Salão do Trono.",
    },
    {
        "id": "entidade_maligna",
        "nome": "A Entidade Maligna",
        "tipo": "Chefe Final",
        "hp": 180,
        "dano": 4,
        "fraqueza": "Todas as Magias",
        "lore": "A fonte primordial de toda a corrupção que ameaça o destino de A Lenda Perdida.",
    },
]


class CenaBestiario(Cena):
    transparente = True

    def __init__(self, app, rpg=None):
        super().__init__(app)
        self.rpg = rpg
        self.indice = 0
        self.scroll = 0
        self.t = 0.0

    def atualizar(self, dt):
        self.t += dt
        entrada = self.app.entrada
        audio = getattr(self.app, "audio", None)

        ant = self.indice
        if entrada.apertou("cima"):
            self.indice = (self.indice - 1) % len(ENTRADAS_BESTIARIO)
        elif entrada.apertou("baixo"):
            self.indice = (self.indice + 1) % len(ENTRADAS_BESTIARIO)

        if self.indice != ant and audio:
            audio.sfx("menu_mover")

        if entrada.apertou("voltar") or entrada.apertou("pausa"):
            if audio:
                audio.sfx("menu_voltar")
            self.app.desempilhar()

        # Rolagem suave
        alvo_scroll = max(0, min(len(ENTRADAS_BESTIARIO) - 5, self.indice - 2))
        self.scroll += (alvo_scroll - self.scroll) * 12.0 * dt

    def desenhar(self, tela):
        escurecer(tela, 220)
        fonte = self.app.fontes.normal

        # Painel base
        painel = pygame.Rect(10, 8, LARGURA - 20, ALTURA - 16)
        pygame.draw.rect(tela, (16, 20, 36), painel, border_radius=4)
        pygame.draw.rect(tela, (215, 175, 65), painel, 1, border_radius=4)

        desenhar_texto(tela, fonte, "BESTIÁRIO DO REINO", (18, 14), AMARELO)
        pygame.draw.line(tela, (65, 75, 110), (14, 26), (LARGURA - 14, 26))

        # Lista de criaturas à esquerda (130px de largura)
        clip_lista = pygame.Rect(14, 30, 126, 118)
        antigo_clip = tela.get_clip()
        tela.set_clip(clip_lista)

        item_alt = 18
        for i, ent in enumerate(ENTRADAS_BESTIARIO):
            y_pos = 32 + int((i - self.scroll) * item_alt)
            if y_pos < 14 or y_pos > 150:
                continue

            eh_sel = (i == self.indice)
            # Verifica se já enfrentou
            eh_chefe = "Guardião" in ent["tipo"] or "Chefe" in ent["tipo"]
            conhecido = (ent["id"] in self.rpg.chefes_derrotados) if eh_chefe else True

            rect_item = pygame.Rect(16, y_pos, 120, 16)
            if eh_sel:
                pygame.draw.rect(tela, (38, 50, 85), rect_item, border_radius=2)
                pygame.draw.rect(tela, AMARELO, rect_item, 1, border_radius=2)

            cor_t = AMARELO if eh_sel else (BRANCO if conhecido else (110, 115, 130))
            nome_disp = ent["nome"] if conhecido else "??? [Desconhecido]"
            # Trunca nome se muito longo
            if len(nome_disp) > 17:
                nome_disp = nome_disp[:16] + "."
            desenhar_texto(tela, fonte, nome_disp, (20, y_pos + 3), cor_t)

        tela.set_clip(antigo_clip)

        # Divisor vertical
        pygame.draw.line(tela, (65, 75, 110), (146, 28), (146, 150))

        # Detalhes da criatura selecionada à direita (148 a 306)
        ent_sel = ENTRADAS_BESTIARIO[self.indice]
        eh_chefe_sel = "Guardião" in ent_sel["tipo"] or "Chefe" in ent_sel["tipo"]
        conhecido_sel = (ent_sel["id"] in self.rpg.chefes_derrotados) if eh_chefe_sel else True

        rx = 154
        if conhecido_sel:
            desenhar_texto(tela, fonte, ent_sel["nome"], (rx, 32), AMARELO)
            desenhar_texto(tela, fonte, f"Classe: {ent_sel['tipo']}", (rx, 46), (110, 220, 255))
            desenhar_texto(tela, fonte, f"HP: {ent_sel['hp']}   Dano: {ent_sel['dano']}", (rx, 58), BRANCO)
            desenhar_texto(tela, fonte, f"Fraqueza: {ent_sel['fraqueza']}", (rx, 70), (255, 140, 100))

            # Caixa de Lore
            rect_lore = pygame.Rect(rx, 84, 148, 58)
            pygame.draw.rect(tela, (22, 26, 46), rect_lore, border_radius=2)
            pygame.draw.rect(tela, (55, 65, 95), rect_lore, 1, border_radius=2)
            
            # Quebra descrição em 3 linhas
            palavras = ent_sel["lore"].split(" ")
            linhas, linha_atual = [], ""
            for p in palavras:
                if len(linha_atual + " " + p) < 26:
                    linha_atual = (linha_atual + " " + p).strip()
                else:
                    linhas.append(linha_atual)
                    linha_atual = p
            if linha_atual:
                linhas.append(linha_atual)

            for li, l_txt in enumerate(linhas[:4]):
                desenhar_texto(tela, fonte, l_txt, (rx + 4, 88 + li * 13), (200, 210, 230))
        else:
            desenhar_texto(tela, fonte, "??? DESCONHECIDO", (rx, 34), (140, 145, 160))
            desenhar_texto(tela, fonte, f"Classe: {ent_sel['tipo']}", (rx, 48), (90, 95, 110))
            desenhar_texto(tela, fonte, "Derrote este Guardião para", (rx, 70), CINZA)
            desenhar_texto(tela, fonte, "revelar suas fraquezas e lore.", (rx, 82), CINZA)

        # Rodapé
        rodape = "Setas: Escolher Criatura | Esc / X: Voltar"
        desenhar_texto(tela, fonte, rodape, (LARGURA // 2, ALTURA - 12), CINZA, centro=True)
