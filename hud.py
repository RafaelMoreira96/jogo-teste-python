"""HUD (Interface de Cabeça) 16-bits para A Lenda Perdida.

Design limpo, elegante e profissional no estilo 16-bits (Zelda ALttP / Minish Cap):
- Top-Left: Moldura compacta de Vitalidade (Corações), Mana/XP, Nível e Magia.
- Top-Center: Pílula única e centralizada para Região / Objetivo (sem nenhuma colisão).
- Top-Right: Minimapa emoldurado com atalho [M].
- Bottom-Left: Inventário compacto e dinâmico de recursos (Ouro, Bombas, Chaves, Escudo).
"""
import pygame

from cenas.mapa_mundo import desenhar_miniatura_nivel
from settings import ALTURA, LARGURA
from ui import AMARELO, BRANCO, CINZA, desenhar_texto, escurecer

TAGS_PODERES = {
    "esfera_fogo": "Fogo",
    "nova_gelo": "Gelo",
    "tempestade_raios": "Raio",
    "cura_celestial": "Cura",
    "corte_giratorio": "Giro",
    "golpe_vorpal": "Vorpal",
    "furia_escolhido": "Fúria",
}


def desenhar_hud(
    tela,
    gfx,
    fonte,
    vida,
    vida_maxima,
    inimigos_restantes,
    rpg=None,
    dados_mapa=None,
    jogador_rect=None,
    tempo=0.0,
    chefe_ativo=None,
    boss_rush_info=None,
    aviso_mapa=None,
    tempo_aviso_mapa=0.0,
):
    # =========================================================================
    # 1. QUADRO SUPERIOR ESQUERDO: STATUS DO HERÓI (COMPACTO: 76 x 33 px)
    # =========================================================================
    larg_box_heroi = 76
    alt_box_heroi = 33
    painel_status = pygame.Surface((larg_box_heroi, alt_box_heroi), pygame.SRCALPHA)
    pygame.draw.rect(painel_status, (14, 18, 32, 215), (0, 0, larg_box_heroi, alt_box_heroi))
    pygame.draw.rect(painel_status, (55, 70, 105, 230), (0, 0, larg_box_heroi, alt_box_heroi), 1)
    tela.blit(painel_status, (3, 3))

    # 1.1 Corações de Vida (até 5 por linha, cabem perfeitamente em 45px)
    max_corações = vida_maxima // 2
    for i in range(max_corações):
        resto = vida - i * 2
        if resto >= 2:
            img = gfx.coracao_cheio
        elif resto == 1:
            img = gfx.coracao_metade
        else:
            img = gfx.coracao_vazio
        col = i % 5
        lin = i // 5
        tela.blit(img, (6 + col * 9, 6 + lin * 8))

    # 1.2 Barras de Mana e XP + Nível
    if rpg is not None:
        y_barras = 16 if max_corações <= 5 else 22
        larg_barra = 34

        # Barra de Mana (Azul)
        pygame.draw.rect(tela, (10, 14, 26), (6, y_barras, larg_barra, 4))
        prop_mp = max(0.0, min(1.0, rpg.mana / max(1.0, rpg.mana_maxima)))
        if prop_mp > 0:
            pygame.draw.rect(tela, (65, 175, 255), (6, y_barras, round(larg_barra * prop_mp), 4))
        pygame.draw.rect(tela, (110, 205, 255), (6, y_barras, larg_barra, 4), 1)

        # Barra de XP (Dourada)
        pygame.draw.rect(tela, (10, 14, 26), (6, y_barras + 5, larg_barra, 2))
        prop_xp = max(0.0, min(1.0, rpg.xp / max(1, rpg.xp_proximo)))
        if prop_xp > 0:
            pygame.draw.rect(tela, (245, 215, 70), (6, y_barras + 5, round(larg_barra * prop_xp), 2))

        # Nível e PH
        txt_nv = f"Nv.{rpg.nivel}"
        if rpg.pontos_habilidade > 0:
            txt_nv += f"+{rpg.pontos_habilidade}U"
        cor_nv = (110, 255, 140) if rpg.pontos_habilidade > 0 else AMARELO
        desenhar_texto(tela, fonte, txt_nv, (43, y_barras - 1), cor_nv)

        # 1.3 Feitiço equipado
        poder = rpg.poder_atual
        if poder is not None:
            tem_mana = rpg.mana >= poder["custo_mana"]
            cor_p = poder["cor"] if tem_mana else CINZA
            tag_poder = TAGS_PODERES.get(poder["id"], poder["nome"][:5])
            txt_poder = f"[F] {tag_poder}"
            desenhar_texto(tela, fonte, txt_poder, (6, 25), cor_p)

    # =========================================================================
    # 2. CENTRO SUPERIOR: PÍLULA ELEGANTE (REGIÃO OU ALVO RECOMENDADO)
    # =========================================================================
    # Nunca colide: largura controlada entre X=85 e X=260
    if chefe_ativo is None:
        if tempo_aviso_mapa > 0 and aviso_mapa:
            # Letreiro de Chegada na Região
            larg_aviso = min(150, fonte.size(aviso_mapa)[0] + 16)
            faixa_r = pygame.Surface((larg_aviso, 13), pygame.SRCALPHA)
            alfa = int(min(1.0, tempo_aviso_mapa * 2.0) * 225)
            faixa_r.fill((14, 18, 34, alfa))
            pygame.draw.rect(faixa_r, (255, 220, 100, alfa), (0, 0, larg_aviso, 13), 1)
            tela.blit(faixa_r, (LARGURA // 2 - larg_aviso // 2, 4))
            desenhar_texto(tela, fonte, aviso_mapa, (LARGURA // 2, 6), (255, 240, 150), centro=True)
        elif rpg is not None and hasattr(rpg, "proximo_chefe"):
            proximo = rpg.proximo_chefe()
            if proximo:
                _, nome_p, nv_p, _, _, _, _ = proximo
                # Formato enxuto: "[Alvo: Golem de Pedra | Nv.2]"
                nome_curto = (
                    nome_p.replace(" Ancestral", "")
                    .replace(" Coroado", "")
                    .replace(" Sombria", "")
                    .replace(" Corrompido", "")
                    .replace(" das Dunas", "")
                    .replace(" das Cavernas", "")
                )
                txt_obj = f"Alvo: {nome_curto} | Nv.{nv_p}"
                larg_obj = min(154, fonte.size(txt_obj)[0] + 12)
                faixa_obj = pygame.Surface((larg_obj, 13), pygame.SRCALPHA)
                faixa_obj.fill((14, 18, 34, 195))
                pygame.draw.rect(faixa_obj, (215, 180, 75, 210), (0, 0, larg_obj, 13), 1)
                tela.blit(faixa_obj, (LARGURA // 2 - larg_obj // 2, 4))
                desenhar_texto(tela, fonte, txt_obj, (LARGURA // 2, 6), (255, 235, 130), centro=True)

    # =========================================================================
    # 3. QUADRO INFERIOR ESQUERDO: INVENTÁRIO DINÂMICO DE RECURSOS
    # =========================================================================
    if rpg is not None:
        str_ouro = f"{rpg.ouro}G"
        str_bomba = f"B:{rpg.bombas}"
        str_chave = f"K:{rpg.chaves}" if rpg.chaves > 0 else ""
        str_escudo = "[E]Def" if rpg.escudo_equipado != "nenhum" else ""

        w_ouro = fonte.size(str_ouro)[0]
        w_bomba = fonte.size(str_bomba)[0]
        w_chave = fonte.size(str_chave)[0] if str_chave else 0
        w_escudo = fonte.size(str_escudo)[0] if str_escudo else 0

        # Largura exata com margens seguras
        larg_rec = 10 + w_ouro + 8 + w_bomba
        if str_chave:
            larg_rec += 8 + w_chave
        if str_escudo:
            larg_rec += 8 + w_escudo
        larg_rec += 6

        painel_rec = pygame.Surface((larg_rec, 14), pygame.SRCALPHA)
        pygame.draw.rect(painel_rec, (14, 18, 32, 215), (0, 0, larg_rec, 14))
        pygame.draw.rect(painel_rec, (55, 70, 105, 230), (0, 0, larg_rec, 14), 1)
        tela.blit(painel_rec, (3, ALTURA - 17))

        cur_x = 7
        desenhar_texto(tela, fonte, str_ouro, (cur_x, ALTURA - 15), AMARELO)
        cur_x += w_ouro + 8

        desenhar_texto(tela, fonte, str_bomba, (cur_x, ALTURA - 15), (255, 165, 85))
        cur_x += w_bomba + 8

        if str_chave:
            desenhar_texto(tela, fonte, str_chave, (cur_x, ALTURA - 15), (120, 230, 255))
            cur_x += w_chave + 8

        if str_escudo:
            desenhar_texto(tela, fonte, str_escudo, (cur_x, ALTURA - 15), (140, 210, 255))

    # =========================================================================
    # 4. QUADRO SUPERIOR DIREITO: MINIMAPA EMOLDURADO
    # =========================================================================
    if dados_mapa is not None and not dados_mapa["nivel"].eh_interior:
        rect_mini = pygame.Rect(LARGURA - 52, 3, 49, 31)
        desenhar_miniatura_nivel(tela, dados_mapa, rect_mini, jogador_rect=jogador_rect, t=tempo)
        desenhar_texto(tela, fonte, "[M] Mapa", (LARGURA - 27, 36), CINZA, centro=True)

    # =========================================================================
    # 5. BARRA DE VIDA DE CHEFE / BOSS RUSH
    # =========================================================================
    if chefe_ativo is not None and getattr(chefe_ativo, "vivo", False):
        chefe_ativo.desenhar_barra_vida_hud(tela, fonte)
        if boss_rush_info:
            txt_rush = f"Onda {boss_rush_info['onda']}/{boss_rush_info['total']} - O Desafio das Sombras"
            desenhar_texto(tela, fonte, txt_rush, (LARGURA // 2, 24), (255, 120, 160), centro=True)


def desenhar_mensagem(tela, fonte, titulo, subtitulo):
    escurecer(tela)
    desenhar_texto(tela, fonte, titulo, (LARGURA // 2, ALTURA // 2 - 8), centro=True)
    desenhar_texto(tela, fonte, subtitulo, (LARGURA // 2, ALTURA // 2 + 8), CINZA, centro=True)
