"""Testes de Validação do Sistema de Audio Ducking Dinâmico (Fase 2)."""
import os
import pygame

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

from audio import SFX_DUCKING_REGRAS, SistemaAudio
from main import App
from cenas.jogo import Jogo


def testar_regras_ducking():
    print("--- Testando Regras de Ducking e Sintetizador ---")
    assert "rugido_chefe" in SFX_DUCKING_REGRAS
    assert "fanfarra_item" in SFX_DUCKING_REGRAS
    assert "impacto_pesado" in SFX_DUCKING_REGRAS
    assert "morte_inimigo" in SFX_DUCKING_REGRAS

    fator, dur = SFX_DUCKING_REGRAS["rugido_chefe"]
    assert fator <= 0.40, f"Rugido do chefe deve abaixar bem a BGM, atual: {fator}"
    assert dur >= 1.0
    print("✓ Regras de mapeamento e atenuação de SFX validadas com sucesso!")


def testar_transicao_ducking_sfx():
    print("\n--- Testando Transição Dinâmica de Ducking (Attack e Release) ---")
    cfg = {"volume_bgm": 80, "volume_sfx": 80}
    audio = SistemaAudio(cfg)

    if not audio.ativo:
        print("Mixer não inicializado (ambiente headless); testando lógica direta.")
        audio.ativo = True

    audio.fator_ducking = 1.0
    audio._duck_alvo = 1.0
    audio._tempo_duck = 0.0

    # Dispara um SFX que tem regra de ducking (ex: rugido_chefe)
    audio.sfx("rugido_chefe")
    assert audio._duck_alvo <= 0.35
    assert audio._tempo_duck > 1.0
    print("✓ Gatilho do SFX registrou ducking dinâmico!")

    # Fase de Attack (deve cair rápido)
    audio.atualizar(0.1)
    assert audio.fator_ducking < 0.60, f"Volume deveria ter caído no attack, atual: {audio.fator_ducking}"
    print(f"✓ Attack responsivo verificado: BGM atenuada para {audio.fator_ducking*100:.1f}%")

    # Sustentação durante o efeito
    audio.atualizar(0.5)
    assert audio.fator_ducking <= 0.35, f"BGM deveria se manter baixa durante o rugido, atual: {audio.fator_ducking}"

    # Fase de Release (passando do tempo de duração do rugido)
    audio.atualizar(1.2)  # expira o tempo
    # Deve recuperar suavemente em direção a 1.0
    for _ in range(20):
        audio.atualizar(0.05)

    assert audio.fator_ducking > 0.90, f"BGM deveria ter se recuperado no release, atual: {audio.fator_ducking}"
    print(f"✓ Release musical suave concluído: BGM recuperada para {audio.fator_ducking*100:.1f}%")


def testar_ducking_dialogo_e_integracao():
    print("\n--- Testando Ducking Suave em Diálogos com o Jogo ---")
    app = App()
    jogo = Jogo(app, dialogo_inicial=None)
    audio = app.audio

    if not audio.ativo:
        audio.ativo = True

    # Reseta temporizadores de ducking que foram disparados na abertura/conquistas
    audio.fator_ducking = 1.0
    audio._duck_alvo = 1.0
    audio._tempo_duck = 0.0
    audio._vol_bgm_base = 0.8
    assert not audio.duck_dialogo

    # Simula abertura de diálogo com NPC
    jogo.iniciar_dialogo("inicio", opcional=True)
    assert jogo.dialogo is not None

    # Atualiza jogo
    jogo.atualizar(0.05)
    assert audio.duck_dialogo is True
    print("✓ Diálogo ativado acionou audio.duck_dialogo automaticamente!")

    # Avança tempo para aplicar ducking de diálogo
    for _ in range(10):
        audio.atualizar(0.05)

    assert audio.fator_ducking < 0.75, f"BGM deveria ser atenuada para ~68% durante fala, atual: {audio.fator_ducking}"
    print(f"✓ BGM atenuada para {audio.fator_ducking*100:.1f}% permitindo foco total na fala do NPC!")

    # Fecha o diálogo
    jogo.dialogo = None
    jogo.atualizar(0.05)
    assert audio.duck_dialogo is False

    # Recuperação pós-diálogo
    for _ in range(15):
        audio.atualizar(0.05)

    assert audio.fator_ducking > 0.92, f"BGM deveria retornar a 100% após diálogo, atual: {audio.fator_ducking}"
    print("✓ BGM restaurada com sucesso após encerramento do diálogo!")
    print("\n🎉 SISTEMA DE AUDIO DUCKING DINÂMICO VALIDADO COM 100% DE SUCESSO!")


if __name__ == "__main__":
    testar_regras_ducking()
    testar_transicao_ducking_sfx()
    testar_ducking_dialogo_e_integracao()
