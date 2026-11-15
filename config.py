"""Configurações do jogador, salvas em config.json."""
import json

from settings import ARQUIVO_CONFIG

PADRAO = {
    "tela_cheia": False,
    "escala": 4,
    "velocidade_texto": "normal",
    "vibracao": True,
    "volume_bgm": 70,
    "volume_sfx": 80,
    "bussola": True,
    "recordes_chefes": {},
}
ESCALAS = [2, 3, 4, 5, 6]
VELOCIDADES_TEXTO = {"lenta": 25, "normal": 50, "rapida": 120}  # letras por segundo
NOMES_VELOCIDADE = {"lenta": "Lenta", "normal": "Normal", "rapida": "Rápida"}


def carregar():
    cfg = dict(PADRAO)
    try:
        cfg.update(json.loads(ARQUIVO_CONFIG.read_text(encoding="utf-8")))
    except (OSError, ValueError):
        pass
    return cfg


def salvar(cfg):
    ARQUIVO_CONFIG.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")
