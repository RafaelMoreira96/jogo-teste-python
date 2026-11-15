"""Configurações do jogador, salvas em config.json."""
import json

from settings import ARQUIVO_CONFIG, PASTA_BASE

PADRAO = {
    "tela_cheia": False,
    "escala": 4,
    "velocidade_texto": "normal",
    "vibracao": True,
    "volume_bgm": 70,
    "volume_sfx": 80,
    "bussola": True,
    "jogo_zerado": False,
    "recordes_chefes": {},
    # QA & Polimento Comercial (Prompt 3)
    "tamanho_hud": "normal",  # "normal", "compacto", "expandido"
    "alto_contraste": False,
    "intensidade_tremor": 1.0,  # 1.0 (100%), 0.5 (50%), 0.0 (Desligado)
    "speedrun": False,
    "mapeamento_teclado": {},
    "mapeamento_controle": {},
}
ESCALAS = [2, 3, 4, 5, 6]
VELOCIDADES_TEXTO = {"lenta": 25, "normal": 50, "rapida": 120}  # letras por segundo
NOMES_VELOCIDADE = {"lenta": "Lenta", "normal": "Normal", "rapida": "Rápida"}
TAMANHOS_HUD = ["normal", "compacto", "expandido"]
INTENSIDADES_TREMOR = [1.0, 0.5, 0.0]


def carregar():
    cfg = dict(PADRAO)
    try:
        cfg.update(json.loads(ARQUIVO_CONFIG.read_text(encoding="utf-8")))
    except (OSError, ValueError):
        pass
    return cfg


def salvar(cfg):
    ARQUIVO_CONFIG.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")


def jogo_foi_zerado(app=None):
    """Verifica se o jogador já zerou o jogo ao menos uma vez."""
    if app and hasattr(app, "config") and app.config.get("jogo_zerado", False):
        return True
    cfg = carregar()
    if cfg.get("jogo_zerado", False):
        return True

    # Verifica se há save com vitória final ou conquista correspondente em qualquer slot
    from salvamento import NUM_SLOTS, caminho_slot
    for s in range(1, NUM_SLOTS + 1):
        c = caminho_slot(s)
        if c.exists():
            try:
                dados = json.loads(c.read_text(encoding="utf-8"))
                if dados.get("jogo_zerado") or "vitoria_final" in dados.get("flags", []) or "vitoria_final" in dados.get("conquistas", []):
                    return True
            except (OSError, ValueError):
                pass
    return False


def marcar_jogo_zerado(app=None):
    """Registra que o jogador zerou o jogo, persistindo no config.json."""
    if app and hasattr(app, "config"):
        app.config["jogo_zerado"] = True
        salvar(app.config)
    else:
        cfg = carregar()
        cfg["jogo_zerado"] = True
        salvar(cfg)
