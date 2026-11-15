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
from ui import (
    CINZA,
    desenhar_barra,
    desenhar_icone,
    desenhar_painel,
    desenhar_tecla,
    desenhar_texto,
    escurecer,
    limpar_texto,
    quebrar_linhas,
)

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
    bussola=None,
):
    # =========================================================================
    # 1. QUADRO SUPERIOR ESQUERDO: STATUS DO HERÓI
    # =========================================================================
    max_coracoes = vida_maxima // 2
    linhas_coracoes = 1 if max_coracoes <= 6 else 2
    y_barras = 15 + (linhas_coracoes - 1) * 8
    larg_box = 86
    alt_box = (y_barras + 22) if rpg is not None else (y_barras + 2)
    desenhar_painel(tela, (2, 2, larg_box, alt_box), alfa=215)

    # 1.1 Corações (com leve pulso quando a vida está baixa)
    vida_baixa = vida <= 2 and vida > 0
    for i in range(max_coracoes):
        resto = vida - i * 2
        if resto >= 2:
            img = gfx.coracao_cheio
        elif resto == 1:
            img = gfx.coracao_metade
        else:
            img = gfx.coracao_vazio
        col = i % 6
        lin = i // 6
        dy = -1 if vida_baixa and i == (vida - 1) // 2 and int(tempo * 6) % 2 == 0 else 0
        tela.blit(img, (7 + col * 9, 6 + lin * 8 + dy))

    if rpg is not None:
        # 1.2 Nível (selo dourado à direita dos corações)
        txt_nv = f"Nv{rpg.nivel}"
        larg_nv = fonte.size(txt_nv)[0] + 4
        selo = pygame.Rect(larg_box - larg_nv - 2, 5, larg_nv, 10)
        pygame.draw.rect(tela, (8, 8, 16), selo.inflate(2, 2))
        pygame.draw.rect(tela, (120, 84, 30), selo)
        pygame.draw.line(tela, (236, 190, 90), selo.topleft, (selo.right - 1, selo.top))
        desenhar_texto(tela, fonte, txt_nv, selo.center, (255, 236, 150), centro=True)
        if rpg.pontos_habilidade > 0 and int(tempo * 2.5) % 2 == 0:
            desenhar_texto(tela, fonte, f"+{rpg.pontos_habilidade}", (selo.x - 1, selo.bottom + 1), (120, 255, 150))

        # 1.3 Mana (gota + barra) e XP (barra fina dourada)
        desenhar_icone(tela, "gota", (6, y_barras))
        prop_mp = rpg.mana / max(1.0, rpg.mana_maxima)
        desenhar_barra(tela, (15, y_barras + 1, 44, 4), prop_mp, (64, 160, 255))
        prop_xp = rpg.xp / max(1, rpg.xp_proximo)
        desenhar_barra(tela, (15, y_barras + 7, 44, 2), prop_xp, (246, 206, 70), brilho=False)
        desenhar_texto(tela, fonte, "XP", (62, y_barras + 2), (200, 180, 120))

        # 1.4 Feitiço equipado: tecla [F] + nome na cor do poder
        poder = rpg.poder_atual
        if poder is not None:
            tem_mana = rpg.mana >= poder["custo_mana"]
            cor_p = poder["cor"] if tem_mana else CINZA
            tag_poder = TAGS_PODERES.get(poder["id"], poder["nome"][:6])
            y_p = y_barras + 11
            larg_t = desenhar_tecla(tela, fonte, "F", (6, y_p))
            pygame.draw.rect(tela, (8, 8, 16), (8 + larg_t, y_p + 2, 6, 6))
            pygame.draw.rect(tela, cor_p, (9 + larg_t, y_p + 3, 4, 4))
            desenhar_texto(tela, fonte, tag_poder, (17 + larg_t, y_p), cor_p)
            custo = f"{poder['custo_mana']}"
            desenhar_texto(tela, fonte, custo, (larg_box - fonte.size(custo)[0] - 3, y_p), (110, 190, 255) if tem_mana else CINZA)

    # =========================================================================
    # 2. CENTRO SUPERIOR: FAIXA DE REGIÃO / OBJETIVO
    # =========================================================================
    if chefe_ativo is None:
        if tempo_aviso_mapa > 0 and aviso_mapa:
            texto = limpar_texto(aviso_mapa)
            larg_max = 2 * (LARGURA // 2 - 91)  # entre o painel de status e o minimapa
            larg_aviso = min(larg_max, fonte.size(texto)[0] + 12)
            linhas = quebrar_linhas(fonte, texto, larg_aviso - 10) if fonte.size(texto)[0] > larg_aviso - 10 else [texto]
            alt_aviso = 4 + 10 * len(linhas)
            # Sobe suavemente para fora da tela nos últimos instantes
            y0 = 3 - round((1 - min(1.0, tempo_aviso_mapa / 0.25)) * (alt_aviso + 6))
            desenhar_painel(tela, (LARGURA // 2 - larg_aviso // 2, y0, larg_aviso, alt_aviso + 2), "dourado", alfa=225, cantos=False)
            for i, linha in enumerate(linhas):
                desenhar_texto(tela, fonte, linha, (LARGURA // 2, y0 + 6 + i * 10), (255, 240, 160), centro=True)
        elif rpg is not None and hasattr(rpg, "proximo_chefe"):
            proximo = rpg.proximo_chefe()
            if proximo:
                _, nome_p, nv_p, _, _, _, _ = proximo
                nome_curto = (
                    nome_p.replace(" Ancestral", "")
                    .replace(" Coroado", "")
                    .replace(" Sombria", "")
                    .replace(" Corrompido", "")
                    .replace(" das Dunas", "")
                    .replace(" das Cavernas", "")
                )
                txt_obj = f"{nome_curto}"
                txt_nv = f"Nv{nv_p}"
                cor_nv = (120, 255, 150) if rpg.nivel >= nv_p else (255, 120, 110)
                larg_obj = min(150, fonte.size(txt_obj)[0] + fonte.size(txt_nv)[0] + 26)
                x0 = LARGURA // 2 - larg_obj // 2
                desenhar_painel(tela, (x0, 3, larg_obj, 14), "padrao", alfa=200, cantos=False)
                desenhar_icone(tela, "caveira", (x0 + 4, 6))
                desenhar_texto(tela, fonte, txt_obj, (x0 + 13, 5), (255, 235, 140))
                desenhar_texto(tela, fonte, txt_nv, (x0 + larg_obj - fonte.size(txt_nv)[0] - 3, 5), cor_nv)

    # =========================================================================
    # 3. QUADRO INFERIOR ESQUERDO: RECURSOS COM ÍCONES
    # =========================================================================
    if rpg is not None:
        itens = [("moeda", str(rpg.ouro), (255, 222, 110)), ("bomba", str(rpg.bombas), (255, 170, 100))]
        if rpg.chaves > 0:
            itens.append(("chave", str(rpg.chaves), (140, 230, 255)))
        if rpg.escudo_equipado != "nenhum":
            itens.append(("escudo", "", (140, 210, 255)))
        larg_rec = 6 + sum(9 + (fonte.size(v)[0] + 5 if v else 0) for _, v, _ in itens)
        desenhar_painel(tela, (2, ALTURA - 16, larg_rec, 14), alfa=215, cantos=False)
        cur_x = 6
        for nome_ic, valor, cor in itens:
            desenhar_icone(tela, nome_ic, (cur_x, ALTURA - 12))
            cur_x += 9
            if valor:
                desenhar_texto(tela, fonte, valor, (cur_x, ALTURA - 14), cor)
                cur_x += fonte.size(valor)[0] + 5

    # =========================================================================
    # 4. QUADRO SUPERIOR DIREITO: MINIMAPA EMOLDURADO
    # =========================================================================
    if dados_mapa is not None and not dados_mapa["nivel"].eh_interior:
        rect_mini = pygame.Rect(LARGURA - 52, 3, 49, 31)
        desenhar_miniatura_nivel(tela, dados_mapa, rect_mini, jogador_rect=jogador_rect, t=tempo)
        larg_t = fonte.size("Mapa")[0] + 12
        x_t = LARGURA - 3 - larg_t
        desenhar_tecla(tela, fonte, "M", (x_t, 36))
        desenhar_texto(tela, fonte, "Mapa", (x_t + 11, 36), CINZA)

    # =========================================================================
    # 4b. BÚSSOLA DE OBJETIVO (canto inferior direito)
    # =========================================================================
    if bussola is not None:
        desenhar_bussola(tela, fonte, bussola, tempo)

    # =========================================================================
    # 5. BARRA DE VIDA DE CHEFE / BOSS RUSH
    # =========================================================================
    if chefe_ativo is not None and getattr(chefe_ativo, "vivo", False):
        chefe_ativo.desenhar_barra_vida_hud(tela, fonte)
        if boss_rush_info:
            txt_rush = f"Onda {boss_rush_info['onda']}/{boss_rush_info['total']} - O Desafio das Sombras"
            desenhar_texto(tela, fonte, txt_rush, (LARGURA // 2, 24), (255, 120, 160), centro=True)


def desenhar_bussola(tela, fonte, bussola, tempo):
    """Rosa dos ventos 16-bits com agulha apontando o caminho e o nome do destino."""
    import math

    cx, cy, raio = LARGURA - 19, ALTURA - 20, 13
    desenhar_painel(tela, (cx - raio - 4, cy - raio - 4, raio * 2 + 8, raio * 2 + 8), "dourado", alfa=220, cantos=False)
    pygame.draw.circle(tela, (24, 20, 30), (cx, cy), raio)
    pygame.draw.circle(tela, (200, 160, 80), (cx, cy), raio, 1)
    for k in range(8):
        a = k * math.pi / 4
        r1 = raio - (3 if k % 2 == 0 else 2)
        pygame.draw.line(tela, (150, 120, 70), (cx + round(math.cos(a) * r1), cy + round(math.sin(a) * r1)), (cx + round(math.cos(a) * (raio - 1)), cy + round(math.sin(a) * (raio - 1))))
    desenhar_texto(tela, fonte, "N", (cx, cy - raio + 4), (230, 200, 140), centro=True)
    ang = bussola["angulo"]
    ponta = (cx + math.cos(ang) * (raio - 3), cy + math.sin(ang) * (raio - 3))
    cauda = (cx - math.cos(ang) * (raio - 5), cy - math.sin(ang) * (raio - 5))
    lado = (math.cos(ang + math.pi / 2) * 2.5, math.sin(ang + math.pi / 2) * 2.5)
    pygame.draw.polygon(tela, (230, 60, 60), [ponta, (cx + lado[0], cy + lado[1]), (cx - lado[0], cy - lado[1])])
    pygame.draw.polygon(tela, (220, 220, 230), [cauda, (cx + lado[0], cy + lado[1]), (cx - lado[0], cy - lado[1])])
    pygame.draw.circle(tela, (255, 220, 120), (cx, cy), 2)

    # Lembrete da tecla que mostra o objetivo
    desenhar_tecla(tela, fonte, "O", (cx - raio - 4, cy + raio - 6))

    # Painel do objetivo: escondido por padrão, aparece por 5 s ao apertar [O]
    visivel = bussola.get("tempo_visivel", 0.0)
    if visivel <= 0:
        return
    objetivo = limpar_texto(bussola.get("objetivo") or "")
    rotulo = limpar_texto(bussola.get("rotulo") or "")
    largura_max = 128

    def caber(texto):
        while texto and fonte.size(texto)[0] > largura_max:
            texto = texto[:-1]
        return texto

    linha1 = caber(objetivo)
    linha2 = caber(f"→ {rotulo}") if rotulo else ""
    larg = max(fonte.size(linha1)[0], fonte.size(linha2)[0]) + 10
    alt = 26 if linha2 else 14
    # Desliza para a direita e some no último meio segundo
    saida = max(0.0, 0.5 - visivel) / 0.5
    x0 = LARGURA - 2 - larg + round(saida * (larg + 4))
    y0 = cy - raio - 6 - alt
    destaque = bussola.get("destaque", 0.0) > 0 and int(tempo * 6) % 2 == 0
    desenhar_painel(tela, (x0, y0, larg, alt), "dourado" if destaque else "padrao", alfa=210, cantos=False)
    desenhar_texto(tela, fonte, linha1, (x0 + 5, y0 + 2), (255, 226, 140))
    if linha2:
        desenhar_texto(tela, fonte, linha2, (x0 + 5, y0 + 13), (190, 200, 225))


def desenhar_mensagem(tela, fonte, titulo, subtitulo):
    escurecer(tela)
    largura = max(fonte.size(titulo)[0], fonte.size(subtitulo)[0]) + 30
    desenhar_painel(tela, (LARGURA // 2 - largura // 2, ALTURA // 2 - 18, largura, 36), "dourado")
    desenhar_texto(tela, fonte, titulo, (LARGURA // 2, ALTURA // 2 - 6), (255, 236, 150), centro=True)
    desenhar_texto(tela, fonte, subtitulo, (LARGURA // 2, ALTURA // 2 + 7), CINZA, centro=True)
