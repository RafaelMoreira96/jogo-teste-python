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


def desenhar_barra_soulslike(
    tela,
    x,
    y,
    largura,
    altura,
    prop_atual,
    prop_fantasma,
    cor_principal,
    cor_brilho,
    cor_fundo,
    cor_fantasma,
    cor_sombra,
    marcadores=True,
    pulso=False,
):
    """Renderiza uma barra elegante no estilo Soulslike (Dark Souls / Elden Ring).

    Possui fundo escuro com chanfro, trailing bar de dano/consumo recente,
    barra principal com gradiente de luz e marcadores de segmentação.
    """
    rect_calha = pygame.Rect(x, y, largura, altura)
    # Fundo escuro com borda de ardósia
    pygame.draw.rect(tela, (12, 12, 18), rect_calha.inflate(2, 2))
    pygame.draw.rect(tela, cor_fundo, rect_calha)

    # 1. Barra fantasma (trailing ghost bar de dano ou consumo recente)
    if prop_fantasma > prop_atual:
        larg_fantasma = max(0, min(largura, round(largura * prop_fantasma)))
        if larg_fantasma > 0:
            pygame.draw.rect(tela, cor_fantasma, (x, y, larg_fantasma, altura))

    # 2. Barra principal com brilho volumétrico
    larg_atual = max(0, min(largura, round(largura * prop_atual)))
    if larg_atual > 0:
        cor_base = cor_principal
        if pulso:
            cor_base = (
                min(255, cor_principal[0] + 50),
                max(0, cor_principal[1] - 30),
                max(0, cor_principal[2] - 30),
            )
        pygame.draw.rect(tela, cor_base, (x, y, larg_atual, altura))
        # Linha superior de iluminação/reflexo
        pygame.draw.line(tela, cor_brilho, (x, y), (x + larg_atual - 1, y))
        # Linha inferior de sombra
        if altura >= 3:
            pygame.draw.line(tela, cor_sombra, (x, y + altura - 1), (x + larg_atual - 1, y + altura - 1))
        # Ponto de brilho no topo da ponta
        if larg_atual >= 2:
            tela.set_at((x + larg_atual - 1, y), (255, 255, 255))

    # 3. Moldura externa metálica
    pygame.draw.rect(tela, (40, 42, 54), rect_calha.inflate(2, 2), 1)

    # 4. Marcadores verticais de graduação (ticks sutis estilo Dark Souls)
    if marcadores and largura >= 24:
        for mx in range(x + 16, x + largura - 4, 16):
            pygame.draw.line(tela, (16, 18, 26), (mx, y), (mx, y + altura - 1))


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
    config=None,
    split_recente=None,
    tempo_split_recente=0.0,
):
    cfg = config or {}
    tamanho_hud = cfg.get("tamanho_hud", "normal")
    modo_speedrun = cfg.get("speedrun", False)

    # =========================================================================
    # 1. QUADRO SUPERIOR ESQUERDO: STATUS DO HERÓI (ESTILO SOULSLIKE)
    # =========================================================================
    # 1.1 Proporções e comprimentos que escalam dinamicamente com os atributos
    # Barra de Vida (Vermelha)
    prop_hp = max(0.0, min(1.0, vida / max(1.0, float(vida_maxima))))
    vida_fantasma = getattr(rpg, "vida_fantasma", float(vida)) if rpg else float(vida)
    prop_hp_fantasma = max(0.0, min(1.0, vida_fantasma / max(1.0, float(vida_maxima))))
    larg_hp_base = 62 if tamanho_hud == "compacto" else (88 if tamanho_hud == "expandido" else 74)
    larg_hp = min(108, larg_hp_base + (vida_maxima - 6) * 3)

    # Barra de Magia (Azul)
    mana_atual = rpg.mana if rpg else 20.0
    mana_maxima = rpg.mana_maxima if rpg else 20.0
    prop_mp = max(0.0, min(1.0, mana_atual / max(1.0, float(mana_maxima))))
    mana_fantasma = getattr(rpg, "mana_fantasma", float(mana_atual)) if rpg else float(mana_atual)
    prop_mp_fantasma = max(0.0, min(1.0, mana_fantasma / max(1.0, float(mana_maxima))))
    larg_mp_base = 52 if tamanho_hud == "compacto" else (78 if tamanho_hud == "expandido" else 64)
    larg_mp = min(98, larg_mp_base + int((mana_maxima - 20) * 0.75)) if rpg else larg_mp_base

    # Barra de Stamina (Verde - escala com o nível do herói!)
    stamina_atual = getattr(rpg, "stamina", 60.0) if rpg else 60.0
    stamina_maxima = getattr(rpg, "stamina_maxima", 60.0) if rpg else 60.0
    prop_sp = max(0.0, min(1.0, stamina_atual / max(1.0, float(stamina_maxima))))
    stamina_fantasma = getattr(rpg, "stamina_fantasma", float(stamina_atual)) if rpg else float(stamina_atual)
    prop_sp_fantasma = max(0.0, min(1.0, stamina_fantasma / max(1.0, float(stamina_maxima))))
    larg_sp_base = 56 if tamanho_hud == "compacto" else (82 if tamanho_hud == "expandido" else 68)
    larg_sp = min(102, larg_sp_base + int((stamina_maxima - 60) * 0.35)) if rpg else larg_sp_base

    # Dimensões do Painel de Status
    x_barras = 25 if rpg is not None else 8
    larg_max_barras = max(larg_hp, larg_mp, larg_sp)
    larg_box = max(larg_max_barras + x_barras + 5, 84 if tamanho_hud == "compacto" else 102)
    alt_box = 39 if rpg is not None else 23
    desenhar_painel(tela, (2, 2, larg_box, alt_box), alfa=215)

    # 1.2 Brasão / Selo do Nível Soulslike (à esquerda das barras)
    if rpg is not None:
        selo_rect = pygame.Rect(5, 5, 17, 19)
        pygame.draw.rect(tela, (14, 14, 22), selo_rect)
        pygame.draw.rect(tela, (110, 80, 28), selo_rect, 1)
        pygame.draw.line(tela, (230, 190, 80), selo_rect.topleft, (selo_rect.right - 1, selo_rect.top))
        desenhar_texto(tela, fonte, "Nv", (selo_rect.centerx, selo_rect.y + 1), (200, 185, 140), centro=True)
        desenhar_texto(tela, fonte, str(rpg.nivel), (selo_rect.centerx, selo_rect.y + 9), (255, 235, 145), centro=True)
        if rpg.pontos_habilidade > 0 and int(tempo * 2.5) % 2 == 0:
            desenhar_texto(tela, fonte, f"+{rpg.pontos_habilidade}", (selo_rect.centerx, selo_rect.bottom), (120, 255, 150), centro=True)

    # 1.3 As 3 Barras Empilhadas no estilo Soulslike:
    # --- Barra 1: VIDA (HP - Vermelha) ---
    vida_baixa = vida <= 2 and vida > 0
    desenhar_barra_soulslike(
        tela,
        x=x_barras,
        y=5,
        largura=larg_hp,
        altura=5,
        prop_atual=prop_hp,
        prop_fantasma=prop_hp_fantasma,
        cor_principal=(212, 34, 42),
        cor_brilho=(255, 105, 115),
        cor_fundo=(45, 10, 14),
        cor_fantasma=(235, 170, 50),
        cor_sombra=(135, 16, 22),
        pulso=vida_baixa and int(tempo * 6) % 2 == 0,
    )
    if tamanho_hud == "expandido":
        desenhar_texto(tela, fonte, f"{vida}/{vida_maxima}", (x_barras + larg_hp + 3, 4), (255, 200, 200))

    # --- Barra 2: MAGIA (MP - Azul) ---
    desenhar_barra_soulslike(
        tela,
        x=x_barras,
        y=12,
        largura=larg_mp,
        altura=4,
        prop_atual=prop_mp,
        prop_fantasma=prop_mp_fantasma,
        cor_principal=(36, 130, 242),
        cor_brilho=(120, 205, 255),
        cor_fundo=(12, 22, 50),
        cor_fantasma=(135, 215, 255),
        cor_sombra=(18, 70, 160),
    )

    # --- Barra 3: STAMINA (SP - Verde) ---
    exaustao = getattr(rpg, "exaustao_stamina", False) if rpg else False
    desenhar_barra_soulslike(
        tela,
        x=x_barras,
        y=18,
        largura=larg_sp,
        altura=4,
        prop_atual=prop_sp,
        prop_fantasma=prop_sp_fantasma,
        cor_principal=(46, 200, 78),
        cor_brilho=(135, 248, 150),
        cor_fundo=(12, 38, 16),
        cor_fantasma=(195, 235, 95),
        cor_sombra=(22, 115, 42),
        pulso=exaustao and int(tempo * 6) % 2 == 0,
    )

    # 1.4 Barra fina de XP e Indicador de Feitiço / Habilidade
    if rpg is not None:
        prop_xp = rpg.xp / max(1, rpg.xp_proximo)
        larg_xp = max(larg_hp, larg_mp, larg_sp)
        desenhar_barra(tela, (x_barras, 24, larg_xp, 2), prop_xp, (246, 206, 70), brilho=False)

        poder = rpg.poder_atual
        if poder is not None:
            tem_mana = rpg.mana >= poder["custo_mana"]
            cor_p = poder["cor"] if tem_mana else CINZA
            tag_poder = TAGS_PODERES.get(poder["id"], poder["nome"][:5])
            if tamanho_hud == "compacto":
                tag_poder = tag_poder[:3]
            y_p = 28
            larg_t = desenhar_tecla(tela, fonte, "F", (5, y_p))
            pygame.draw.rect(tela, (8, 8, 16), (7 + larg_t, y_p + 2, 6, 6))
            pygame.draw.rect(tela, cor_p, (8 + larg_t, y_p + 3, 4, 4))
            desenhar_texto(tela, fonte, tag_poder, (16 + larg_t, y_p), cor_p)
            custo = f"{poder['custo_mana']} MP"
            desenhar_texto(
                tela,
                fonte,
                custo,
                (larg_box - fonte.size(custo)[0] - 3, y_p),
                (110, 190, 255) if tem_mana else CINZA,
            )

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
    # 4. QUADRO SUPERIOR DIREITO: MINIMAPA EMOLDURADO & MODO SPEEDRUN
    # =========================================================================
    tem_mapa = dados_mapa is not None and not dados_mapa["nivel"].eh_interior
    if tem_mapa:
        rect_mini = pygame.Rect(LARGURA - 52, 3, 49, 31)
        desenhar_miniatura_nivel(tela, dados_mapa, rect_mini, jogador_rect=jogador_rect, t=tempo)
        larg_t = fonte.size("Mapa")[0] + 12
        x_t = LARGURA - 3 - larg_t
        desenhar_tecla(tela, fonte, "M", (x_t, 36))
        desenhar_texto(tela, fonte, "Mapa", (x_t + 11, 36), CINZA)

    # 4.1 Cronômetro Oficial do Modo Speedrun (Pilar 4)
    if modo_speedrun and rpg is not None:
        t_sr = getattr(rpg, "tempo_speedrun", 0.0)
        minutos = int(t_sr // 60)
        segundos = int(t_sr % 60)
        centesimos = int((t_sr * 100) % 100)
        txt_cron = f"{minutos:02d}:{segundos:02d}.{centesimos:02d}"

        larg_cron = fonte.size(txt_cron)[0] + 8
        y_cron = 48 if tem_mapa else 4
        x_cron = LARGURA - larg_cron - 3
        desenhar_painel(tela, (x_cron, y_cron, larg_cron, 12), estilo="escuro", alfa=220, cantos=False)
        desenhar_texto(tela, fonte, txt_cron, (x_cron + 4, y_cron + 2), (120, 255, 170))

        # Notificação de Split ao derrotar um Guardião
        if tempo_split_recente > 0 and split_recente:
            nome_ch, tempo_split = split_recente
            m_s = int(tempo_split // 60)
            s_s = int(tempo_split % 60)
            c_s = int((tempo_split * 100) % 100)
            txt_split = f"★ Split: {m_s:02d}:{s_s:02d}.{c_s:02d}"
            larg_split = fonte.size(txt_split)[0] + 8
            x_sp = LARGURA // 2 - larg_split // 2
            y_sp = 20 if chefe_ativo is None else 28
            desenhar_painel(tela, (x_sp, y_sp, larg_split, 13), estilo="dourado", alfa=240, cantos=False)
            desenhar_texto(tela, fonte, txt_split, (x_sp + 4, y_sp + 2), (255, 240, 140))

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
