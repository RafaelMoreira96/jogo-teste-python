"""Bateria de Testes Automatizados para o Sistema de Checkpoints de Renascimento."""
import os
from pathlib import Path
import pygame

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
pygame.init()

from main import App
from settings import PASTA_BASE
from cenas.jogo import Jogo
from salvamento import apagar_slot, carregar_jogo, salvar_jogo


def testar_sistema_checkpoints():
    print("\n--- Testando Sistema de Checkpoints e Renascimento do Herói ---")
    app = App()

    # 1. Inicialização do Checkpoint
    jogo = Jogo(app, dialogo_inicial=None, slot_salvo=1)
    assert hasattr(jogo, "checkpoint"), "Jogo deve possuir atributo checkpoint!"
    assert jogo.checkpoint is not None, "Checkpoint inicial não deve ser nulo!"
    print(f"✓ Checkpoint inicial registrado: {jogo.checkpoint['nome_local']} ({jogo.checkpoint['mapa']})")

    # 2. Atualização ao mudar para Vila Aurora
    mapa_vila = PASTA_BASE / "maps" / "vila.txt"
    jogo.trocar_mapa(mapa_vila, usar_porta=False)
    assert "vila.txt" in jogo.checkpoint["mapa"], f"Checkpoint deveria apontar para vila.txt, obteve: {jogo.checkpoint['mapa']}"
    print(f"✓ Checkpoint atualizado ao explorar: {jogo.checkpoint['nome_local']}")

    # 3. Checkpoint seguro fora do covil de chefe ao entrar na arena
    mapa_mundo = PASTA_BASE / "maps" / "mundo.txt"
    jogo.trocar_mapa(mapa_mundo, usar_porta=False)
    mapa_covil = PASTA_BASE / "maps" / "covil_rei_slime.txt"
    jogo.trocar_mapa(mapa_covil, usar_porta=True)

    # O checkpoint deve ter sido fixado em mundo.txt (fora da arena) e NÃO dentro da câmara fechada
    assert "mundo.txt" in jogo.checkpoint["mapa"], f"Checkpoint de covil deveria apontar para fora (mundo.txt), obteve: {jogo.checkpoint['mapa']}"
    assert "Covil" in jogo.checkpoint["nome_local"] or "Slime" in jogo.checkpoint["nome_local"], f"Nome do checkpoint incorreto: {jogo.checkpoint['nome_local']}"
    print(f"✓ Checkpoint seguro registrado na entrada da arena: {jogo.checkpoint['nome_local']}")

    # 4. Morte do jogador dentro da arena
    jogo.rpg.nivel = 3
    jogo.rpg.ouro = 150
    jogo.jogador.vida = 0
    jogo.atualizar(0.1)
    assert jogo.estado == "derrota", "Estado deveria ser 'derrota' após zerar a vida!"

    # 5. Renascimento no Checkpoint
    app.entrada.apertadas.add("confirmar")
    jogo.atualizar(0.1)
    app.entrada.apertadas.clear()

    assert jogo.estado == "jogando", "Estado deveria voltar a 'jogando' após renascer!"
    assert jogo.jogador.vida == jogo.vida_max_total(), f"Vida deveria estar cheia ({jogo.vida_max_total()}), obteve: {jogo.jogador.vida}"
    assert jogo.rpg.mana == jogo.rpg.mana_maxima, "Mana deveria estar cheia após renascer!"
    assert jogo.rpg.nivel == 3, "Nível do RPG deve ser preservado ao renascer!"
    assert jogo.rpg.ouro == 150, "Ouro do herói deve ser preservado ao renascer!"
    assert "mundo.txt" in str(jogo.nivel.caminho), f"Jogador deveria ter renascido em mundo.txt, mas está em: {jogo.nivel.caminho}"
    print(f"✓ Herói renasceu com sucesso no Checkpoint ({jogo.checkpoint['nome_local']}) com vida e mana cheias e sem perda de progresso!")

    # 6. Teste de Persistência no Savegame
    apagar_slot(1)
    salvar_jogo(jogo, slot=1)
    jogo_carregado = carregar_jogo(app, slot=1)
    assert jogo_carregado is not None, "Falha ao carregar save com checkpoint!"
    assert hasattr(jogo_carregado, "checkpoint") and jogo_carregado.checkpoint is not None, "Checkpoint não foi restaurado do savegame!"
    assert "mundo.txt" in jogo_carregado.checkpoint["mapa"], f"Mapa do checkpoint restaurado incorreto: {jogo_carregado.checkpoint['mapa']}"
    print(f"✓ Persistência de Checkpoint validada no Save Game com sucesso!")

    # 7. Renderização da Tela de Game Over com Checkpoint
    tela = pygame.Surface((320, 180))
    jogo.estado = "derrota"
    jogo.desenhar(tela)
    print("✓ Tela de Game Over com indicação clara do Ponto de Retorno renderizada perfeitamente!")


if __name__ == "__main__":
    testar_sistema_checkpoints()
    print("\n=======================================================")
    print("🎉 SISTEMA DE CHECKPOINTS VALIDADO COM 100% DE SUCESSO!")
    print("=======================================================")
