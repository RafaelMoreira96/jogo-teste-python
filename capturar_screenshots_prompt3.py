"""Script para capturar snapshots de verificação visual do Prompt 3."""
import os
import pygame

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
pygame.init()

from main import App
from settings import LARGURA, ALTURA
from cenas.jogo import Jogo
from cenas.loja import CenaLoja
from cenas.bestiario import CenaBestiario
from cenas.jukebox import CenaJukebox
from cenas.remapeamento import CenaRemapeamento
from cenas.slots_save import CenaSlotsSave
from hud import desenhar_hud
from salvamento import salvar_jogo

app = App()
tela = pygame.Surface((LARGURA, ALTURA))

# 1. Snapshot do Novo HUD Limpo e Organizado com Modo Speedrun e Alvo
jogo = Jogo(app, dialogo_inicial=None, slot_salvo=1)
jogo.rpg.nivel = 3
jogo.rpg.ouro = 85
jogo.rpg.bombas = 3
jogo.rpg.chaves = 1
jogo.rpg.tempo_speedrun = 205.84  # 03:25.84
cfg = {"tamanho_hud": "normal", "speedrun": True}
# Atualiza jogo um frame para desenhar mundo
jogo.desenhar(tela)
# Garante HUD por cima
dados_mapa = jogo.mapas.get(jogo.nivel.caminho.resolve())
desenhar_hud(
    tela,
    app.gfx,
    app.fontes.normal,
    jogo.jogador.vida,
    jogo.jogador.vida_maxima,
    3,
    rpg=jogo.rpg,
    dados_mapa=dados_mapa,
    jogador_rect=jogo.jogador.rect,
    tempo=5.0,
    chefe_ativo=None,
    boss_rush_info=None,
    aviso_mapa=None,
    tempo_aviso_mapa=0.0,
    bussola=None,
    config=cfg,
    split_recente=("Rei Slime", 65.2),
    tempo_split_recente=4.0,
)
tela_escalada = pygame.transform.scale(tela, (LARGURA * 3, ALTURA * 3))
pygame.image.save(tela_escalada, "/home/rafael/.gemini/antigravity/brain/dccdf99b-6810-4991-9700-047c54c4cd94/snapshot_hud_prompt3.png")
print("Salvo: snapshot_hud_prompt3.png")

# 2. Snapshot da Loja com Abas
loja = CenaLoja(app, jogo)
loja.aba_idx = 0
loja.desenhar(tela)
tela_escalada = pygame.transform.scale(tela, (LARGURA * 3, ALTURA * 3))
pygame.image.save(tela_escalada, "/home/rafael/.gemini/antigravity/brain/dccdf99b-6810-4991-9700-047c54c4cd94/snapshot_loja_abas.png")
print("Salvo: snapshot_loja_abas.png")

# 3. Snapshot da Jukebox Retro
jukebox = CenaJukebox(app)
jukebox.desenhar(tela)
tela_escalada = pygame.transform.scale(tela, (LARGURA * 3, ALTURA * 3))
pygame.image.save(tela_escalada, "/home/rafael/.gemini/antigravity/brain/dccdf99b-6810-4991-9700-047c54c4cd94/snapshot_jukebox.png")
print("Salvo: snapshot_jukebox.png")

# 4. Snapshot do Menu de Remapeamento de Controles
remap = CenaRemapeamento(app)
remap.desenhar(tela)
tela_escalada = pygame.transform.scale(tela, (LARGURA * 3, ALTURA * 3))
pygame.image.save(tela_escalada, "/home/rafael/.gemini/antigravity/brain/dccdf99b-6810-4991-9700-047c54c4cd94/snapshot_remapeamento.png")
print("Salvo: snapshot_remapeamento.png")

# 5. Snapshot do Bestiário com Vitrine 360° e Abates
jogo.rpg.derrotas_monstros["slime"] = 18
bestiario = CenaBestiario(app, rpg=jogo.rpg)
bestiario.indice = 0
bestiario.t = 1.2
bestiario.desenhar(tela)
tela_escalada = pygame.transform.scale(tela, (LARGURA * 3, ALTURA * 3))
pygame.image.save(tela_escalada, "/home/rafael/.gemini/antigravity/brain/dccdf99b-6810-4991-9700-047c54c4cd94/snapshot_bestiario_prompt3.png")
print("Salvo: snapshot_bestiario_prompt3.png")
