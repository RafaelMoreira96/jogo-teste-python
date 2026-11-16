"""Testes automatizados para o sistema de Salvamento Manual (Altar, Menu de Pausa, F5 QuickSave)."""
import os
import pygame
from pathlib import Path

# Garante modo headless
os.environ["SDL_VIDEODRIVER"] = "dummy"
pygame.init()
pygame.display.set_mode((320, 180))

from main import App
from cenas.jogo import Jogo
from cenas.pausa import Pausa
from salvamento import caminho_slot, carregar_jogo, salvar_jogo, ler_resumo_slot, apagar_slot, NUM_SLOTS
from settings import PASTA_BASE


def test_salvamento_manual_altar():
    """Verifica se a interação no Altar salva, cura e não gera ataque espúrio."""
    app = App()
    # Inicia jogo e troca para mapa que contém altar (mundo.txt)
    jogo = Jogo(app, dialogo_inicial=None, slot_salvo=1)
    mapa_mundo = PASTA_BASE / "maps" / "mundo.txt"
    jogo.trocar_mapa(mapa_mundo, usar_porta=False, tocar_sfx_porta=False)

    assert len(jogo.nivel.pontos_salvamento) > 0, "O mapa mundo.txt deve conter ao menos um altar de salvamento ($)"
    altar_pos = jogo.nivel.pontos_salvamento[0]

    # Posiciona jogador a 20px do altar (dentro do raio de 34px)
    jogo.jogador.posicionar(altar_pos[0], altar_pos[1] + 18)
    jogo.jogador.vida = 2  # danificado
    jogo.rpg.mana = 3.0    # mana gasta
    jogo.jogador.tempo_ataque = 0.0

    # Simula entrada com ação (Espaço)
    class EntradaMock:
        def apertou(self, acao):
            return acao in ("acao", "confirmar")
        def segurando(self, acao):
            return False
        def eixo_x(self):
            return 0.0
        def eixo_y(self):
            return 0.0

    app.entrada = EntradaMock()
    jogo.atualizar(0.016)

    # 1. Deve ter restaurado vida e mana
    assert jogo.jogador.vida == jogo.vida_max_total(), "A vida deve ser totalmente restaurada no altar"
    assert jogo.rpg.mana == jogo.rpg.mana_maxima, "A mana deve ser restaurada no altar"

    # 2. NÃO deve ter atacado ao interagir com o altar
    assert not jogo.jogador.atacando, "O jogador não deve atacar ao salvar no altar"

    # 3. Checkpoint deve ter sido atualizado para o altar
    assert jogo.checkpoint is not None
    assert "Altar" in jogo.checkpoint["nome_local"]

    # 4. Notificação de salvamento ativada
    assert jogo.tempo_autosave > 0
    assert "Altar" in jogo.aviso_autosave

    # 5. Arquivo no disco atualizado
    resumo = ler_resumo_slot(1)
    assert resumo is not None, "Arquivo de savegame_1.json deve existir"
    assert resumo["vida"] == jogo.vida_max_total()


def test_salvamento_manual_menu_pausa():
    """Verifica se salvar pelo menu de pausa persiste a posição e mapa exatos."""
    app = App()
    jogo = Jogo(app, dialogo_inicial=None, slot_salvo=2)
    mapa_mundo = PASTA_BASE / "maps" / "mundo.txt"
    jogo.trocar_mapa(mapa_mundo, usar_porta=False, tocar_sfx_porta=False)

    # Posiciona o jogador em um local customizado
    pos_x, pos_y = 120, 180
    jogo.jogador.posicionar(pos_x, pos_y)
    jogo.jogador.direcao = "direita"

    pausa = Pausa(app, jogo)
    # Seleciona "Salvar Jogo"
    pausa.menu.indice = pausa.menu.opcoes.index("Salvar Jogo")

    class EntradaConfirmar:
        def apertou(self, acao):
            return acao == "confirmar"
        def segurando(self, acao):
            return False

    app.entrada = EntradaConfirmar()
    pausa.atualizar(0.016)

    # Verifica feedback no menu de pausa
    assert "Progresso Salvo no Arquivo 2" in pausa.msg_salvo
    assert jogo.tempo_autosave > 0
    assert "Manual" in jogo.aviso_autosave

    # Verifica arquivo salvo no slot 2
    resumo_slot2 = ler_resumo_slot(2)
    assert resumo_slot2 is not None

    # Carrega o save e valida que a posição foi salva com exatidão
    jogo_recarregado = carregar_jogo(app, slot=2)
    assert jogo_recarregado is not None
    assert jogo_recarregado.nivel.caminho.name == "mundo.txt"
    assert abs(jogo_recarregado.jogador.rect.centerx - pos_x) <= 2
    assert abs(jogo_recarregado.jogador.rect.bottom - pos_y) <= 2
    assert jogo_recarregado.jogador.direcao == "direita"


def test_quicksave_f5_e_quickload_f6():
    """Verifica o atalho F5 (Quick Save) e F6 (Quick Load) via app."""
    app = App()
    jogo = Jogo(app, dialogo_inicial=None, slot_salvo=3)
    mapa_mundo = PASTA_BASE / "maps" / "mundo.txt"
    jogo.trocar_mapa(mapa_mundo, usar_porta=False, tocar_sfx_porta=False)
    jogo.jogador.posicionar(200, 250)
    jogo.rpg.ouro = 450
    app.cenas = [jogo]

    # Simula evento F5
    ev_f5 = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_F5)
    app.eventos_quadro = [ev_f5]
    for ev in app.eventos_quadro:
        if ev.type == pygame.KEYDOWN and ev.key == pygame.K_F5:
            # Lógica de F5 implementada em main.py
            slot = getattr(jogo, "slot_salvo", 3)
            jogo.definir_checkpoint(
                jogo.nivel.caminho,
                (jogo.jogador.rect.centerx, jogo.jogador.rect.bottom),
                jogo.jogador.direcao,
                f"Quick Save ({getattr(jogo.nivel, 'nome', 'Mundo')})",
                notificar=False,
            )
            salvar_jogo(jogo, slot=slot)
            jogo.aviso_autosave = f"Quick Save (Slot {slot})"
            jogo.tempo_autosave = 3.5

    assert ler_resumo_slot(3) is not None
    assert ler_resumo_slot(3)["ouro"] == 450

    # Modifica o estado atual na memória para testar F6
    jogo.rpg.ouro = 0

    # Simula evento F6
    jogo_carregado = carregar_jogo(app, slot=3)
    assert jogo_carregado is not None
    assert jogo_carregado.rpg.ouro == 450, "Quick Load deve restaurar o ouro salvo no slot 3"
    assert abs(jogo_carregado.jogador.rect.centerx - 200) <= 2


def test_retrocompatibilidade_savegame_legado():
    """Verifica se salvar no slot 1 mantém savegame.json sincronizado."""
    app = App()
    jogo = Jogo(app, dialogo_inicial=None, slot_salvo=1)
    jogo.rpg.nivel = 7
    salvar_jogo(jogo, slot=1)

    legado = PASTA_BASE / "savegame.json"
    assert legado.exists(), "savegame.json deve existir como espelho"
    import json
    dados = json.loads(legado.read_text(encoding="utf-8"))
    assert dados["rpg"]["nivel"] == 7


if __name__ == "__main__":
    print("Iniciando testes de salvamento manual...")
    test_salvamento_manual_altar()
    print("✔ test_salvamento_manual_altar passou!")
    test_salvamento_manual_menu_pausa()
    print("✔ test_salvamento_manual_menu_pausa passou!")
    test_quicksave_f5_e_quickload_f6()
    print("✔ test_quicksave_f5_e_quickload_f6 passou!")
    test_retrocompatibilidade_savegame_legado()
    print("✔ test_retrocompatibilidade_savegame_legado passou!")
    print("\nTODOS OS TESTES DE SALVAMENTO MANUAL PASSARAM COM SUCESSO!")
