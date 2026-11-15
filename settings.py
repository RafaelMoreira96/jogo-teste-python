"""Configurações gerais do jogo. Mexa aqui para ajustar o "feeling"."""
from pathlib import Path

TITULO = "A Lenda Perdida"

# Resolução interna: o jogo é desenhado nesse tamanho e depois ampliado.
LARGURA, ALTURA = 320, 180
ESCALA = 4  # 320x180 -> janela de 1280x720
FPS = 60
TILE = 16

# Jogador
VELOCIDADE_JOGADOR = 80  # pixels por segundo
VIDA_MAXIMA = 6  # em meios-corações (6 = 3 corações)
TEMPO_INVENCIVEL = 1.0  # segundos piscando depois de levar dano
TEMPO_ATAQUE = 0.25  # duração do golpe de espada

# Slimes
SLIME_VIDA = 3
SLIME_VEL_PASSEIO = 25
SLIME_VEL_PERSEGUIR = 42
SLIME_ALCANCE_VISAO = 80

# Chance de soltar coração
CHANCE_CORACAO_ARBUSTO = 0.2
CHANCE_CORACAO_SLIME = 0.4

COR_FUNDO = (20, 20, 30)

PASTA_BASE = Path(__file__).parent
PASTA_SPRITES = PASTA_BASE / "assets" / "sprites"
MAPA_CASA = PASTA_BASE / "maps" / "casa.txt"
MAPA_INICIAL = PASTA_BASE / "maps" / "mundo.txt"
ARQUIVO_HISTORIA = PASTA_BASE / "historia" / "dialogos.txt"
ARQUIVO_CONFIG = PASTA_BASE / "config.json"
