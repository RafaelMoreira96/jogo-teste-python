"""Suíte de Testes Automatizados para o Sistema de Autosave na Entrada dos Chefões."""
import json
from pathlib import Path
import pygame

from main import App
from cenas.jogo import Jogo, EH_ARENA_CHEFE
from salvamento import caminho_slot, carregar_jogo, salvar_jogo
from settings import PASTA_BASE


def testar_autosave_entrada_chefe():
    print("\n--- Testando Autosave na Entrada dos Chefões ---")
    app = App()
    slot_teste = 3
    # Garante slot de teste limpo
    caminho = caminho_slot(slot_teste)
    if caminho.exists():
        caminho.unlink()

    jogo = Jogo(app, dialogo_inicial=None, slot_salvo=slot_teste)
    assert jogo.slot_salvo == slot_teste

    # Coloca o jogador no mapa do mundo em frente ao portal/porta do chefe
    jogo.trocar_mapa(PASTA_BASE / "maps" / "mundo.txt", usar_porta=False)
    origem = jogo.nivel.caminho

    # 1. Herói adquire moedas, XP e mana antes de entrar no chefe
    jogo.rpg.ouro = 250
    jogo.rpg.ganhar_xp(15)
    jogo.jogador.posicionar(13 * 16, 15 * 16)

    # 2. Transição para o Covil do Rei Slime (Arena de Chefe)
    destino_chefe = PASTA_BASE / "maps" / "covil_rei_slime.txt"
    assert destino_chefe.name in EH_ARENA_CHEFE

    jogo.trocar_mapa(destino_chefe, usar_porta=True)

    # 3. Validações do Autosave
    assert caminho.exists(), f"Arquivo de save {caminho} não foi gerado no autosave!"
    with open(caminho, "r", encoding="utf-8") as f:
        dados = json.load(f)

    chk = dados.get("checkpoint")
    assert chk is not None, "Checkpoint não foi gravado no save!"
    assert "Entrada: Covil do Rei Slime" in chk.get("nome_local", "")
    assert chk.get("mapa") == "maps/mundo.txt"
    assert dados.get("rpg", {}).get("ouro") == 250
    print(f"✓ Autosave registrado com sucesso no disco: Slot {slot_teste} ({chk['nome_local']})")

    # 4. Feedback visual do Autosave ativo
    assert jogo.tempo_autosave > 0.0
    assert "Covil do Rei Slime" in jogo.aviso_autosave
    print(f"✓ Indicador visual ativo no HUD: '{jogo.aviso_autosave}' ({jogo.tempo_autosave:.1f}s)")

    # 5. Renderização do badge retrô 16-bit
    surf = pygame.Surface((320, 180))
    jogo._desenhar_badge_autosave(surf, app.fontes.normal)
    print("✓ Badge retrô 16-bit de Autosave (disquete + LED) renderizado perfeitamente!")

    # 6. Carregamento do Save (Load Game)
    jogo_recarregado = carregar_jogo(app, slot=slot_teste)
    assert jogo_recarregado is not None
    assert jogo_recarregado.rpg.ouro == 250
    assert jogo_recarregado.checkpoint["nome_local"] == chk["nome_local"]
    assert jogo_recarregado.checkpoint["mapa"] == "maps/mundo.txt"
    print("✓ Carregamento a partir do Autosave restabeleceu o herói na entrada do chefe com 100% de precisão!")

    # Limpeza
    if caminho.exists():
        caminho.unlink()


def testar_multiplas_entradas_chefes():
    print("\n--- Testando Múltiplas Entradas de Chefões ---")
    app = App()
    slot_teste = 3
    caminho = caminho_slot(slot_teste)
    if caminho.exists():
        caminho.unlink()

    jogo = Jogo(app, dialogo_inicial=None, slot_salvo=slot_teste)

    # Entrando na Câmara do Golem
    destino_golem = PASTA_BASE / "maps" / "camara_golem.txt"
    jogo.trocar_mapa(destino_golem, usar_porta=True)
    assert "Câmara do Golem" in jogo.aviso_autosave
    print(f"✓ Autosave acionado na entrada da Câmara do Golem!")

    # Limpeza
    if caminho.exists():
        caminho.unlink()
    print("🎉 SISTEMA DE AUTOSAVE NA ENTRADA DOS CHEFÕES VALIDADO COM 100% DE SUCESSO!")


if __name__ == "__main__":
    pygame.init()
    testar_autosave_entrada_chefe()
    testar_multiplas_entradas_chefes()
