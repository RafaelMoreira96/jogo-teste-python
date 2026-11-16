"""Sistema de Salvamento e Carregamento de Progresso com Múltiplos Slots (Save Game)."""
from datetime import datetime
import json
from pathlib import Path

from settings import PASTA_BASE, VIDA_MAXIMA

NUM_SLOTS = 3


def caminho_slot(slot=1):
    slot = max(1, min(NUM_SLOTS, int(slot)))
    return PASTA_BASE / f"savegame_{slot}.json"


def _migrar_save_legado():
    """Migra savegame.json antigo para savegame_1.json de forma transparente."""
    legado = PASTA_BASE / "savegame.json"
    destino = caminho_slot(1)
    if legado.exists() and not destino.exists():
        try:
            destino.write_bytes(legado.read_bytes())
        except OSError:
            pass


_migrar_save_legado()
ARQUIVO_SAVE = caminho_slot(1)


def existe_save(slot=None):
    """Verifica se há savegame em um slot específico ou em qualquer um dos slots."""
    _migrar_save_legado()
    if slot is not None:
        return caminho_slot(slot).exists()
    return any(caminho_slot(s).exists() for s in range(1, NUM_SLOTS + 1))


def apagar_slot(slot):
    """Exclui o arquivo do slot especificado."""
    caminho = caminho_slot(slot)
    if caminho.exists():
        try:
            caminho.unlink()
            return True
        except OSError:
            return False
    return False


def apagar_save():
    """Apaga o slot 1 (compatibilidade com chamadas legadas)."""
    return apagar_slot(1)


def copiar_slot(origem, destino):
    """Duplica os dados de um save de um slot para outro."""
    c_origem = caminho_slot(origem)
    if not c_origem.exists():
        return False
    c_destino = caminho_slot(destino)
    try:
        dados = json.loads(c_origem.read_text(encoding="utf-8"))
        dados["slot"] = destino
        dados["data_salvamento"] = datetime.now().strftime("%d/%m %H:%M")
        temp_path = c_destino.with_suffix(".tmp")
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(dados, f, indent=2, ensure_ascii=False)
        temp_path.replace(c_destino)
        return True
    except (OSError, ValueError):
        return False


def ler_resumo_slot(slot):
    """Lê metadados resumidos de um slot para exibição rápida nos menus."""
    caminho = caminho_slot(slot)
    if not caminho.exists():
        return None
    try:
        dados = json.loads(caminho.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None

    rpg = dados.get("rpg", {})
    nome_mapa = "Lugar desconhecido"
    try:
        texto_mapa = (PASTA_BASE / dados.get("mapa", "")).read_text(encoding="utf-8")
        for linha in texto_mapa.splitlines():
            if linha.strip().startswith("nome") and "=" in linha:
                nome_mapa = linha.split("=", 1)[1].strip()
                break
    except OSError:
        pass

    chefes_derrotados = rpg.get("chefes_derrotados", [])
    reliquias = len(rpg.get("reliquias_coletadas", [])) + len(rpg.get("reliquias_entregues", []))
    flags = dados.get("flags", [])
    conquistas = dados.get("conquistas", [])
    jogo_zerado = bool(dados.get("jogo_zerado") or "vitoria_final" in flags or "vitoria_final" in conquistas)

    return {
        "slot": slot,
        "local": nome_mapa,
        "nivel": rpg.get("nivel", 1),
        "vida": dados.get("vida", 6),
        "vida_maxima": dados.get("vida_maxima", 6),
        "chefes": len(chefes_derrotados),
        "reliquias": reliquias,
        "ouro": rpg.get("ouro", 0),
        "jogo_zerado": jogo_zerado,
        "new_game_plus": bool(rpg.get("new_game_plus", False)),
        "ciclo_ng": rpg.get("ciclo_ng", 0),
        "tempo_speedrun": rpg.get("tempo_speedrun", 0.0),
        "data": dados.get("data_salvamento", "--/-- --:--"),
    }


def salvar_jogo(jogo, slot=None):
    """Salva o estado atual do jogador, atributos de RPG, chefes derrotados e mapa no slot especificado."""
    if slot is None:
        slot = getattr(jogo, "slot_salvo", 1)
    slot = max(1, min(NUM_SLOTS, int(slot)))
    jogo.slot_salvo = slot

    data_str = datetime.now().strftime("%d/%m %H:%M")

    dados = {
        "versao": 1,
        "slot": slot,
        "data_salvamento": data_str,
        "mapa": str(jogo.nivel.caminho.resolve().relative_to(PASTA_BASE.resolve())),
        "pos_x": jogo.jogador.rect.centerx,
        "pos_y": jogo.jogador.rect.bottom,
        "direcao": jogo.jogador.direcao,
        "vida": jogo.jogador.vida,
        "vida_maxima": jogo.jogador.vida_maxima,
        "checkpoint": getattr(jogo, "checkpoint", None),
        "mapas_visitados": list(jogo.mapas_visitados),
        "flags": list(jogo.flags),
        "jogo_zerado": "vitoria_final" in jogo.flags or "vitoria_final" in getattr(jogo.conquistas, "desbloqueadas", set()),
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
            "stamina": getattr(jogo.rpg, "stamina", 60.0),
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
            "amuletos": list(getattr(jogo.rpg, "amuletos", set())),
            "nivel_espada": getattr(jogo.rpg, "nivel_espada", 1),
            "tempo_speedrun": getattr(jogo.rpg, "tempo_speedrun", 0.0),
            "splits_speedrun": getattr(jogo.rpg, "splits_speedrun", {}),
            "derrotas_monstros": getattr(jogo.rpg, "derrotas_monstros", {}),
            "new_game_plus": getattr(jogo.rpg, "new_game_plus", False),
            "ciclo_ng": getattr(jogo.rpg, "ciclo_ng", 0),
        },
    }

    jogo.conquistas.desbloquear("salvador_ancestral", jogo)
    caminho = caminho_slot(slot)
    temp_path = caminho.with_suffix(".tmp")
    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=2, ensure_ascii=False)
    temp_path.replace(caminho)

    # Mantém savegame.json sincronizado para retrocompatibilidade
    if slot == 1:
        try:
            (PASTA_BASE / "savegame.json").write_text(caminho.read_text(encoding="utf-8"), encoding="utf-8")
        except OSError:
            pass

    return True


def carregar_jogo(app, slot=1):
    """Carrega o progresso salvo do slot e devolve uma instância pronta de Jogo."""
    _migrar_save_legado()
    slot = max(1, min(NUM_SLOTS, int(slot)))
    caminho = caminho_slot(slot)
    if not caminho.exists():
        return None

    try:
        with open(caminho, "r", encoding="utf-8") as f:
            dados = json.load(f)

        from cenas.jogo import Jogo

        jogo = Jogo(app, dialogo_inicial=None, slot_salvo=slot)
        jogo.slot_salvo = slot

        rpg_dados = dados.get("rpg", {})
        jogo.rpg.nivel = rpg_dados.get("nivel", 1)
        jogo.rpg.xp = rpg_dados.get("xp", 0)
        jogo.rpg.xp_proximo = rpg_dados.get("xp_proximo", 30)
        jogo.rpg.pontos_habilidade = rpg_dados.get("pontos_habilidade", 0)
        jogo.rpg.desbloqueadas = set(rpg_dados.get("desbloqueadas", ["esfera_fogo"]))
        jogo.rpg.poderes_ativos = list(rpg_dados.get("poderes_ativos", ["esfera_fogo"]))
        jogo.rpg.indice_poder = rpg_dados.get("indice_poder", 0)
        jogo.rpg.mana = rpg_dados.get("mana", 20.0)
        jogo.rpg.stamina = float(rpg_dados.get("stamina", jogo.rpg.stamina_maxima))
        jogo.rpg.stamina = min(jogo.rpg.stamina_maxima, jogo.rpg.stamina)
        jogo.jogador.rpg = jogo.rpg
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
        jogo.rpg.amuletos = set(rpg_dados.get("amuletos", []))
        jogo.rpg.nivel_espada = rpg_dados.get("nivel_espada", 1)
        jogo.rpg.tempo_speedrun = float(rpg_dados.get("tempo_speedrun", 0.0))
        jogo.rpg.splits_speedrun = dict(rpg_dados.get("splits_speedrun", {}))
        jogo.rpg.derrotas_monstros = dict(rpg_dados.get("derrotas_monstros", {}))
        jogo.rpg.new_game_plus = bool(rpg_dados.get("new_game_plus", False))
        jogo.rpg.ciclo_ng = int(rpg_dados.get("ciclo_ng", 0))

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
        jogo.jogador.definir_pose("normal")
        jogo.efeito_ativo = None
        jogo.alvo_camera = None
        jogo.jogador.vida = min(dados.get("vida", VIDA_MAXIMA), jogo.vida_max_total())
        jogo.camera.centralizar(jogo.jogador.rect)

        # Checkpoint restaurado da sessão
        chk = dados.get("checkpoint")
        if chk and isinstance(chk, dict):
            jogo.checkpoint = dict(chk)
        else:
            jogo.definir_checkpoint(caminho_mapa, (px, py), jogo.jogador.direcao, getattr(jogo.nivel, "nome", "Retorno Salvo"))

        # Transição fade-in suave ao carregar
        jogo.fade_estado = "in"
        jogo.fade_alfa = 1.0

        if dados.get("jogo_zerado") or "vitoria_final" in jogo.flags:
            from config import marcar_jogo_zerado
            marcar_jogo_zerado(app)

        return jogo
    except Exception as e:
        print(f"Erro ao carregar save slot {slot}: {e}")
        return None
