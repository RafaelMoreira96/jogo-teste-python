"""Captura snapshots em alta fidelidade das novidades do Prompt 2."""
import os
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import pygame
pygame.init()

from main import App
from settings import PASTA_BASE
from cenas.jogo import Jogo
from cenas.mapa_mundo import MapaMundo
from cenas.teleporte import CenaTeleporte
from chefe import CRIADORES_CHEFES

app = App()
surf = pygame.Surface((320, 180))
pasta_artefatos = "/home/rafael/.gemini/antigravity/brain/dccdf99b-6810-4991-9700-047c54c4cd94"

# 1. Snapshot: Portal Místico Ativo e Totem de Sinalização em mundo.txt
jogo = Jogo(app, dialogo_inicial=None)
jogo.trocar_mapa(PASTA_BASE / "maps" / "mundo.txt", usar_porta=False)
# Posiciona herói perto do portal
for portal in jogo.portais_misticos:
    jogo.jogador.posicionar(portal.cx, portal.cy + 24)
    break
for _ in range(10):
    jogo.atualizar(0.05)
jogo.desenhar(surf)
pygame.image.save(surf, f"{pasta_artefatos}/snapshot_portal_mistico.png")
print("Salvo: snapshot_portal_mistico.png")

# 2. Snapshot: Portal Fantasma (Após Derrotar Guardião)
jogo.rpg.chefes_derrotados.add("rei_slime")
for _ in range(10):
    jogo.atualizar(0.05)
jogo.desenhar(surf)
pygame.image.save(surf, f"{pasta_artefatos}/snapshot_portal_fantasma.png")
print("Salvo: snapshot_portal_fantasma.png")

# 3. Snapshot: Vinheta Title Card Épico de Apresentação de Chefe
chefe_colosso = CRIADORES_CHEFES["colosso_solar"](160, 90)
jogo.iniciar_apresentacao_chefe(chefe_colosso)
jogo.apresentacao_chefe["tempo"] = 1.5
jogo.desenhar(surf)
pygame.image.save(surf, f"{pasta_artefatos}/snapshot_title_card_chefe.png")
print("Salvo: snapshot_title_card_chefe.png")

# 4. Snapshot: Atlas do Mundo com Badges dos Guardiões
atlas = MapaMundo(app, jogo)
atlas.desenhar(surf)
pygame.image.save(surf, f"{pasta_artefatos}/snapshot_atlas_chefes.png")
print("Salvo: snapshot_atlas_chefes.png")

# 5. Snapshot: Interface de Viagem Rápida Astral (Monólitos)
jogo.rpg.waypoint_descobertos.update(["vila", "mundo", "oasis", "bosque"])
teleporte = CenaTeleporte(app, jogo, id_origem="mundo")
teleporte.desenhar(surf)
pygame.image.save(surf, f"{pasta_artefatos}/snapshot_viagem_rapida.png")
print("Salvo: snapshot_viagem_rapida.png")
