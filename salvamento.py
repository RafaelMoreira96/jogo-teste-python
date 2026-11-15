"""Sistema de Salvamento e Carregamento de Progresso (Save Game)."""
import json
from pathlib import Path

from settings import PASTA_BASE, VIDA_MAXIMA


ARQUIVO_SAVE = PASTA_BASE / "savegame.json"


def existe_save():
    return ARQUIVO_SAVE.exists()


def apagar_save():
    if ARQUIVO_SAVE.exists():
        ARQUIVO_SAVE.unlink(missing_ok=True)


def salvar_jogo(jogo):
    """Salva o estado atual do jogador, atributos de RPG, chefes derrotados e mapa."""
    dados = {
        "versao": 1,
        "mapa": str(jogo.nivel.caminho.resolve().relative_to(PASTA_BASE.resolve())),
        "pos_x": jogo.jogador.rect.centerx,
        "pos_y": jogo.jogador.rect.bottom,
        "direcao": jogo.jogador.direcao,
        "vida": jogo.jogador.vida,
        "vida_maxima": jogo.jogador.vida_maxima,
        "mapas_visitados": list(jogo.mapas_visitados),
        "flags": list(jogo.flags),
        "conquistas": list(getattr(jogo.conquistas, "desbloqueadas", set())),
        "missoes": {
            "ativas": getattr(jogo.missoes, "ativas", {}),
            "concluidas": list(getattr(jogo.missoes, "concluidas", set())),
            "itens_quest": getattr(jogo.missoes, "itens_quest", {}),
        },
        "rpg": {
            "nivel": jogo.rpg.nivel,
            "xp": jogo.rpg.xp,
            "xp_proximo": jogo.rpg.xp_proximo,
            "pontos_habilidade": jogo.rpg.pontos_habilidade,
            "desbloqueadas": list(jogo.rpg.desbloqueadas),
            "poderes_ativos": list(jogo.rpg.poderes_ativos),
            "indice_poder": jogo.rpg.indice_poder,
            "mana": jogo.rpg.mana,
            "chefes_derrotados": list(getattr(jogo.rpg, "chefes_derrotados", set())),
            "ouro": getattr(jogo.rpg, "ouro", 0),
            "bombas": getattr(jogo.rpg, "bombas", 3),
            "chaves": getattr(jogo.rpg, "chaves", 0),
            "arma_equipada": getattr(jogo.rpg, "arma_equipada", "espada_ferro"),
            "escudo_equipado": getattr(jogo.rpg, "escudo_equipado", "nenhum"),
            "tunica_equipada": getattr(jogo.rpg, "tunica_equipada", "tunica_verde"),
            "waypoint_descobertos": list(getattr(jogo.rpg, "waypoint_descobertos", set())),
            "reliquias_coletadas": list(getattr(jogo.rpg, "reliquias_coletadas", set())),
            "reliquias_entregues": list(getattr(jogo.rpg, "reliquias_entregues", set())),
        },
    }

    jogo.conquistas.desbloquear("salvador_ancestral", jogo)
    temp_path = ARQUIVO_SAVE.with_suffix(".tmp")
    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=2, ensure_ascii=False)
    temp_path.replace(ARQUIVO_SAVE)
    return True


def carregar_jogo(app):
    """Carrega o progresso salvo e devolve uma instância pronta de Jogo."""
    if not existe_save():
        return None

    try:
        with open(ARQUIVO_SAVE, "r", encoding="utf-8") as f:
            dados = json.load(f)

        from cenas.jogo import Jogo

        jogo = Jogo(app, dialogo_inicial=None)
        rpg_dados = dados.get("rpg", {})
        jogo.rpg.nivel = rpg_dados.get("nivel", 1)
        jogo.rpg.xp = rpg_dados.get("xp", 0)
        jogo.rpg.xp_proximo = rpg_dados.get("xp_proximo", 30)
        jogo.rpg.pontos_habilidade = rpg_dados.get("pontos_habilidade", 0)
        jogo.rpg.desbloqueadas = set(rpg_dados.get("desbloqueadas", ["esfera_fogo"]))
        jogo.rpg.poderes_ativos = list(rpg_dados.get("poderes_ativos", ["esfera_fogo"]))
        jogo.rpg.indice_poder = rpg_dados.get("indice_poder", 0)
        jogo.rpg.mana = rpg_dados.get("mana", 20.0)
        jogo.rpg.chefes_derrotados = set(rpg_dados.get("chefes_derrotados", []))
        jogo.rpg.ouro = rpg_dados.get("ouro", 0)
        jogo.rpg.bombas = rpg_dados.get("bombas", 3)
        jogo.rpg.chaves = rpg_dados.get("chaves", 0)
        jogo.rpg.arma_equipada = rpg_dados.get("arma_equipada", "espada_ferro")
        jogo.rpg.escudo_equipado = rpg_dados.get("escudo_equipado", "nenhum")
        jogo.rpg.tunica_equipada = rpg_dados.get("tunica_equipada", "tunica_verde")
        jogo.rpg.waypoint_descobertos = set(rpg_dados.get("waypoint_descobertos", []))
        jogo.rpg.reliquias_coletadas = set(rpg_dados.get("reliquias_coletadas", []))
        jogo.rpg.reliquias_entregues = set(rpg_dados.get("reliquias_entregues", []))

        # Sincroniza equipamento no jogador
        jogo.jogador.arma_equipada = jogo.rpg.arma_equipada
        jogo.jogador.escudo_equipado = jogo.rpg.escudo_equipado
        jogo.jogador.tunica_equipada = jogo.rpg.tunica_equipada

        missoes_dados = dados.get("missoes", {})
        if hasattr(jogo, "missoes"):
            jogo.missoes.ativas = dict(missoes_dados.get("ativas", {}))
            jogo.missoes.concluidas = set(missoes_dados.get("concluidas", []))
            jogo.missoes.itens_quest = dict(missoes_dados.get("itens_quest", {}))

        jogo.mapas_visitados = set(dados.get("mapas_visitados", []))
        jogo.flags = set(dados.get("flags", []))
        jogo.conquistas.desbloqueadas = set(dados.get("conquistas", []))

        mapa_rel = dados.get("mapa", "maps/mundo.txt")
        caminho_mapa = PASTA_BASE / mapa_rel
        if not caminho_mapa.exists():
            caminho_mapa = PASTA_BASE / "maps" / "mundo.txt"

        jogo.trocar_mapa(caminho_mapa, usar_porta=False, tocar_sfx_porta=False)
        px = dados.get("pos_x", jogo.jogador.rect.centerx)
        py = dados.get("pos_y", jogo.jogador.rect.bottom)
        jogo.jogador.posicionar(px, py)
        jogo.jogador.direcao = dados.get("direcao", "baixo")
        jogo.jogador.vida = min(dados.get("vida", VIDA_MAXIMA), jogo.vida_max_total())
        jogo.camera.centralizar(jogo.jogador.rect)

        # Transição fade-in suave ao carregar
        jogo.fade_estado = "in"
        jogo.fade_alfa = 1.0

        return jogo
    except Exception as e:
        print(f"Erro ao carregar save: {e}")
        return None
