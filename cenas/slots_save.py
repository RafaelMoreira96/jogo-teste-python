"""Tela de Seleção e Gerenciamento de Slots de Salvamento (Runs Independentes)."""
import math
import pygame

from cenas.base import Cena
from cenas.jogo import Jogo
from salvamento import (
    NUM_SLOTS,
    PASTA_BASE,
    apagar_slot,
    carregar_jogo,
    copiar_slot,
    existe_save,
    ler_resumo_slot,
    salvar_jogo,
)
from settings import ALTURA, LARGURA
from ui import CINZA, desenhar_icone, desenhar_painel, desenhar_texto, limpar_texto


class CenaSlotsSave(Cena):
    """Permite ao jogador escolher entre 3 slots para carregar ou iniciar novas runs, além de apagar ou duplicar."""

    def __init__(self, app, modo="carregar"):
        super().__init__(app)
        self.modo = modo  # "carregar" ou "novo"
        self.indice = 0
        self.t = 0.0
        self.modal = None  # {"tipo": "apagar"|"sobrescrever"|"duplicar", "slot": 1}
        self.msg_feedback = ""
        self.tempo_feedback = 0.0
        self.resumos = [ler_resumo_slot(s) for s in range(1, NUM_SLOTS + 1)]

    def _recarregar_resumos(self):
        self.resumos = [ler_resumo_slot(s) for s in range(1, NUM_SLOTS + 1)]

    def atualizar(self, dt):
        self.t += dt
        entrada = self.app.entrada
        audio = getattr(self.app, "audio", None)

        if self.tempo_feedback > 0:
            self.tempo_feedback = max(0.0, self.tempo_feedback - dt)

        # ------------------------------------------------------------ Modal ativo
        if self.modal is not None:
            if entrada.apertou("voltar"):
                if audio:
                    audio.sfx("menu_voltar")
                self.modal = None
                return

            if entrada.apertou("confirmar"):
                tipo = self.modal["tipo"]
                slot = self.modal["slot"]
                if tipo == "apagar":
                    apagar_slot(slot)
                    self._recarregar_resumos()
                    if audio:
                        audio.sfx("quebrar_vaso")
                    self.msg_feedback = f"Arquivo {slot} apagado com sucesso!"
                    self.tempo_feedback = 2.5
                    self.modal = None
                elif tipo == "sobrescrever":
                    if audio:
                        audio.sfx("menu_confirmar")
                    self.app.trocar(Jogo(self.app, slot_salvo=slot))
                elif tipo == "new_game_plus":
                    if audio:
                        audio.sfx("fanfarra_item")
                    jogo = carregar_jogo(self.app, slot)
                    if jogo:
                        jogo.rpg.new_game_plus = True
                        jogo.rpg.ciclo_ng = getattr(jogo.rpg, "ciclo_ng", 0) + 1
                        jogo.rpg.chefes_derrotados.clear()
                        jogo.flags.clear()
                        mapa_inicio = PASTA_BASE / "maps" / "mundo.txt"
                        jogo.trocar_mapa(mapa_inicio, usar_porta=False, tocar_sfx_porta=False)
                        salvar_jogo(jogo, slot)
                        self.app.trocar(jogo)
                    self.modal = None
                elif tipo == "duplicar":
                    destino = self.modal["destino"]
                    copiar_slot(slot, destino)
                    self._recarregar_resumos()
                    if audio:
                        audio.sfx("fanfarra_item")
                    self.msg_feedback = f"Arquivo {slot} copiado para o Arquivo {destino}!"
                    self.tempo_feedback = 2.5
                    self.modal = None
            return

        # ------------------------------------------------------------ Navegação
        ant = self.indice
        if entrada.apertou("cima"):
            self.indice = (self.indice - 1) % NUM_SLOTS
        if entrada.apertou("baixo"):
            self.indice = (self.indice + 1) % NUM_SLOTS
        if self.indice != ant and audio:
            audio.sfx("menu_mover")

        if entrada.apertou("voltar"):
            if audio:
                audio.sfx("menu_voltar")
            from cenas.menu import MenuPrincipal
            self.app.trocar(MenuPrincipal(self.app, pular_abertura=True))
            return

        slot_atual = self.indice + 1
        resumo_atual = self.resumos[self.indice]

        # Iniciar New Game+ com tecla N se o slot tiver jogo zerado
        apertou_n = any(ev.type == pygame.KEYDOWN and ev.key == pygame.K_n for ev in getattr(self.app, "eventos_quadro", []))
        if apertou_n and resumo_atual is not None and resumo_atual.get("jogo_zerado"):
            if audio:
                audio.sfx("menu_confirmar")
            self.modal = {"tipo": "new_game_plus", "slot": slot_atual}
            return

        # Apagar slot com tecla F/Q ou ação de exclusão
        if entrada.apertou("magia") or entrada.apertou("trocar_magia"):
            if resumo_atual is not None:
                if audio:
                    audio.sfx("bloqueio")
                self.modal = {"tipo": "apagar", "slot": slot_atual}
                return

        # Confirmar / Selecionar Slot
        if entrada.apertou("confirmar"):
            if self.modo == "novo":
                if resumo_atual is not None:
                    if audio:
                        audio.sfx("bloqueio")
                    self.modal = {"tipo": "sobrescrever", "slot": slot_atual}
                else:
                    if audio:
                        audio.sfx("menu_confirmar")
                    self.app.trocar(Jogo(self.app, slot_salvo=slot_atual))
            else:  # Modo carregar
                if resumo_atual is not None:
                    if audio:
                        audio.sfx("menu_confirmar")
                    jogo = carregar_jogo(self.app, slot_atual)
                    if jogo:
                        self.app.trocar(jogo)
                else:
                    if audio:
                        audio.sfx("bloqueio")
                    self.msg_feedback = "Arquivo vazio! Pressione Voltar e inicie um Novo Jogo."
                    self.tempo_feedback = 2.5

    def desenhar(self, tela):
        fonte = self.app.fontes.normal

        # Fundo escuro com gradiente noturno
        for y in range(ALTURA):
            p = y / ALTURA
            cor_linha = (int(10 + p * 15), int(14 + p * 18), int(28 + p * 25))
            tela.fill(cor_linha, (0, y, LARGURA, 1))

        # Cabeçalho
        titulo = "CARREGAR JORNADA" if self.modo == "carregar" else "NOVA JORNADA"
        sub = "Selecione o arquivo de save que deseja continuar" if self.modo == "carregar" else "Escolha um slot para gravar sua nova lenda"
        desenhar_texto(tela, fonte, titulo, (LARGURA // 2, 8), (255, 230, 130), centro=True)
        desenhar_texto(tela, fonte, sub, (LARGURA // 2, 20), (170, 180, 205), centro=True)

        # 3 Cartões de Save Slot
        for s in range(1, NUM_SLOTS + 1):
            idx = s - 1
            y_card = 34 + idx * 42
            card = pygame.Rect(18, y_card, LARGURA - 36, 38)
            sel = idx == self.indice

            r = self.resumos[idx]
            estilo = "magico" if sel else "padrao"
            desenhar_painel(tela, card, estilo=estilo, alfa=245)

            if sel:
                # Contorno pulsante e cursor
                pulso = int(math.sin(self.t * 8) * 20)
                pygame.draw.rect(tela, (255, 220 + pulso, 110), card, 1)
                desenhar_texto(tela, fonte, ">", (card.x + 6, card.y + 13), (255, 240, 140))

            rotulo_slot = f"[ ARQUIVO {s} ]"
            cor_rotulo = (255, 235, 140) if sel else (210, 215, 235)
            desenhar_texto(tela, fonte, rotulo_slot, (card.x + 18, card.y + 6), cor_rotulo)

            if r is not None:
                # Slot Ocupado
                desenhar_texto(tela, fonte, f"Nv.{r['nivel']}", (card.x + 110, card.y + 6), (180, 225, 255))

                # Corações
                for k in range(min(8, r["vida_maxima"] // 2)):
                    if r["vida"] >= (k + 1) * 2:
                        cor = self.app.gfx.coracao_cheio
                    elif r["vida"] == k * 2 + 1:
                        cor = self.app.gfx.coracao_metade
                    else:
                        cor = self.app.gfx.coracao_vazio
                    tela.blit(cor, (card.x + 145 + k * 8, card.y + 6))

                # Data do save no topo direito
                desenhar_texto(tela, fonte, r["data"], (card.right - 8 - fonte.size(r["data"])[0], card.y + 6), (150, 160, 180))

                # Linha inferior: Local, Chefes, Relíquias, Ouro
                local = limpar_texto(r["local"])
                if fonte.size(local)[0] > 75:
                    local = local[:10] + ".."
                desenhar_texto(tela, fonte, local, (card.x + 18, card.y + 20), (220, 225, 240))

                desenhar_icone(tela, "caveira", (card.x + 100, card.y + 20))
                desenhar_texto(tela, fonte, f"{r['chefes']}/16", (card.x + 110, card.y + 20), (255, 190, 130))

                desenhar_icone(tela, "estrela", (card.x + 144, card.y + 20))
                desenhar_texto(tela, fonte, f"{r['reliquias']}/6", (card.x + 154, card.y + 20), (255, 230, 140))

                desenhar_icone(tela, "moeda", (card.x + 182, card.y + 20))
                desenhar_texto(tela, fonte, f"{r['ouro']}G", (card.x + 192, card.y + 20), (255, 215, 100))

                if r.get("jogo_zerado"):
                    tag_z = "★ NG+" if r.get("new_game_plus") else "★ ZERADO"
                    desenhar_texto(tela, fonte, tag_z, (card.right - 8 - fonte.size(tag_z)[0], card.y + 20), (255, 215, 70))
            else:
                # Slot Vazio
                txt_vazio = "[ VAZIO - NOVO JOGO ]" if self.modo == "novo" else "[ VAZIO ]"
                cor_vazio = (120, 220, 140) if (self.modo == "novo" and sel) else CINZA
                desenhar_texto(tela, fonte, txt_vazio, (card.x + 110, card.y + 13), cor_vazio)

        # Rodapé / Mensagens
        if self.tempo_feedback > 0:
            desenhar_texto(tela, fonte, self.msg_feedback, (LARGURA // 2, ALTURA - 16), (255, 220, 100), centro=True)
        else:
            tem_zerado = any(r and r.get("jogo_zerado") for r in self.resumos)
            rodape = "Enter: Escolher  |  N: New Game+  |  F: Apagar  |  Esc: Voltar" if tem_zerado else "Enter: Escolher   |   F/Q: Apagar   |   Esc: Voltar"
            desenhar_texto(tela, fonte, rodape, (LARGURA // 2, ALTURA - 12), (180, 185, 210), centro=True)

        # Modal de Confirmação
        if self.modal is not None:
            surf_modal = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
            surf_modal.fill((4, 6, 14, 180))
            tela.blit(surf_modal, (0, 0))

            caixa = pygame.Rect(30, 52, LARGURA - 60, 74)
            desenhar_painel(tela, caixa, estilo="magico", alfa=250)
            pygame.draw.rect(tela, (230, 90, 90), caixa, 1)

            tipo = self.modal["tipo"]
            slot = self.modal["slot"]
            if tipo == "apagar":
                msg_m1 = f"Deseja APAGAR o Arquivo {slot}?"
                msg_m2 = "Todo o progresso desta run será perdido."
            elif tipo == "new_game_plus":
                msg_m1 = f"Iniciar New Game+ no Arquivo {slot}?"
                msg_m2 = "Inimigos 35% mais fortes! Mantém itens, armas e 2x Ouro/XP."
            else:
                msg_m1 = f"Sobrescrever o Arquivo {slot}?"
                msg_m2 = "O save existente será substituído pela nova run."

            desenhar_texto(tela, fonte, msg_m1, (LARGURA // 2, caixa.y + 12), (255, 120, 120), centro=True)
            desenhar_texto(tela, fonte, msg_m2, (LARGURA // 2, caixa.y + 26), (220, 220, 230), centro=True)
            desenhar_texto(tela, fonte, "Enter: Confirmar    Esc: Cancelar", (LARGURA // 2, caixa.y + 50), (255, 230, 140), centro=True)
