import os
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import wave
from pathlib import Path
import pygame

pygame.init()
pygame.display.set_mode((256, 144))

from audio import (
    SistemaAudio,
    construir_banco_sfx,
    _sintetizar_nota,
    _buscar_arquivo_audio,
    SFX_DUCKING_REGRAS,
    DIR_AUDIO_ASSETS,
    TAXA_AMOSTRAGEM,
)
from player import Jogador
from level import Nivel
from rpg import SistemaRPG


class MockEntrada:
    def __init__(self, acoes_segurando=None, acoes_apertadas=None):
        self._segura = set(acoes_segurando or [])
        self._apertos = set(acoes_apertadas or [])

    def segurando(self, acao):
        return acao in self._segura

    def apertou(self, acao):
        return acao in self._apertos


class MockAudioCaptura:
    def __init__(self):
        self.sons_tocados = []

    def sfx(self, nome):
        self.sons_tocados.append(nome)


def testar_fase1_audio():
    print("=== TESTE DA FASE 1: ÁUDIO HI-FI, TIMBRES ORQUESTRAIS E MICRO-SONORIZAÇÃO ===")
    sis_audio = SistemaAudio({})
    banco = sis_audio._sfx
    novos_sons = [
        "passo_grama",
        "passo_pedra",
        "passo_agua",
        "passo_areia",
        "passo_madeira",
        "exaustao",
        "parry_perfeito",
        "riposte",
        "alerta_perigo",
    ]
    for nome in novos_sons:
        assert nome in banco, f"Efeito sonoro '{nome}' não encontrado no banco de SFX!"
        assert isinstance(banco[nome], pygame.mixer.Sound), f"'{nome}' deve ser uma instância de pygame.mixer.Sound"
    print(f"[1] Banco de SFX validado com sucesso ({len(banco)} efeitos sonoros disponíveis)")

    # 2. Regras de Audio Ducking dos Novos Efeitos
    assert "parry_perfeito" in SFX_DUCKING_REGRAS, "Ducking para parry_perfeito não configurado!"
    assert "riposte" in SFX_DUCKING_REGRAS, "Ducking para riposte não configurado!"
    assert "alerta_perigo" in SFX_DUCKING_REGRAS, "Ducking para alerta_perigo não configurado!"
    print("[2] Regras de Ducking Dinâmico validadas para Parry e Riposte")

    # 3. Timbres Orquestrais Sintetizados
    novos_timbres = ["cordas_orquestrais", "coral_mistico", "harpa_celestial", "timpano_epico"]
    for timbre in novos_timbres:
        amostras = _sintetizar_nota(timbre, 60, int(TAXA_AMOSTRAGEM * 0.25), 8000)
        assert len(amostras) == int(TAXA_AMOSTRAGEM * 0.25)
        assert max(map(abs, amostras)) > 0, f"Timbre {timbre} gerou silêncio!"
    print(f"[3] Novos timbres orquestrais sintetizados com sucesso: {novos_timbres}")

    # 4. Micro-sonorização Dinâmica de Passos por Terreno
    jogador = Jogador(100, 100)
    audio_mock = MockAudioCaptura()

    # Cria níveis mockados com caminhos diferentes para simular biomas
    class NivelMock:
        def __init__(self, nome_arquivo):
            self.caminho = Path(f"maps/{nome_arquivo}")
            self.eh_interior = False
            self.tema = None
            self.grade = [["." for _ in range(20)] for _ in range(20)]
            self.solidos = set()

        def solido(self, x, y):
            return False

        def colisoes(self, rect, pode_nadar=True):
            return []

        def eh_agua_em(self, x, y):
            return "agua" in self.caminho.name

        def dentro(self, x, y):
            return True

    # a) Passos na grama (mundo aberto padrão)
    entrada_mov = MockEntrada(acoes_segurando=["direita"])
    nivel_mundo = NivelMock("mundo.txt")
    audio_mock.sons_tocados.clear()
    jogador.timer_som_passo = 0.0
    jogador.atualizar(0.016, entrada_mov, nivel_mundo, audio=audio_mock)
    assert "passo_grama" in audio_mock.sons_tocados, f"Esperado passo_grama, obtido: {audio_mock.sons_tocados}"
    print("    ✔ Passo na grama detectado com sucesso!")

    # b) Passos na pedra (castelo/masmorra)
    audio_mock.sons_tocados.clear()
    jogador.timer_som_passo = 0.0
    nivel_castelo = NivelMock("castelo.txt")
    jogador.atualizar(0.016, entrada_mov, nivel_castelo, audio=audio_mock)
    assert "passo_pedra" in audio_mock.sons_tocados, f"Esperado passo_pedra, obtido: {audio_mock.sons_tocados}"
    print("    ✔ Passo na pedra detectado com sucesso!")

    # c) Passos na areia (deserto)
    audio_mock.sons_tocados.clear()
    jogador.timer_som_passo = 0.0
    nivel_deserto = NivelMock("deserto.txt")
    jogador.atualizar(0.016, entrada_mov, nivel_deserto, audio=audio_mock)
    assert "passo_areia" in audio_mock.sons_tocados, f"Esperado passo_areia, obtido: {audio_mock.sons_tocados}"
    print("    ✔ Passo na areia detectado com sucesso!")

    # d) Passos na madeira (taverna / casa)
    audio_mock.sons_tocados.clear()
    jogador.timer_som_passo = 0.0
    nivel_casa = NivelMock("casa.txt")
    jogador.atualizar(0.016, entrada_mov, nivel_casa, audio=audio_mock)
    assert "passo_madeira" in audio_mock.sons_tocados, f"Esperado passo_madeira, obtido: {audio_mock.sons_tocados}"
    print("    ✔ Passo na madeira detectado com sucesso!")

    # e) Passos na água rasa
    audio_mock.sons_tocados.clear()
    jogador.timer_som_passo = 0.0
    nivel_agua = NivelMock("lago_agua.txt")
    jogador.atualizar(0.016, entrada_mov, nivel_agua, audio=audio_mock)
    assert "passo_agua" in audio_mock.sons_tocados, f"Esperado passo_agua, obtido: {audio_mock.sons_tocados}"
    print("    ✔ Passo na água rasa detectado com sucesso!")

    # 5. Feedback Sonoro de Exaustão de Stamina
    audio_mock.sons_tocados.clear()
    rpg = SistemaRPG()
    jogador.rpg = rpg
    rpg.stamina = 5.0
    rpg.exaustao_stamina = True
    jogador.atualizar(0.016, MockEntrada(), nivel_mundo, audio=audio_mock)
    assert "exaustao" in audio_mock.sons_tocados, f"Esperado som de exaustao, obtido: {audio_mock.sons_tocados}"
    print("[5] Feedback sonoro de exaustão de stamina ativado e validado!")

    # 6. Teste de Arquitetura Híbrida de Áudio (Carregamento de arquivo externo .wav)
    pasta_bgm = DIR_AUDIO_ASSETS / "bgm"
    pasta_sfx = DIR_AUDIO_ASSETS / "sfx"
    pasta_bgm.mkdir(parents=True, exist_ok=True)
    pasta_sfx.mkdir(parents=True, exist_ok=True)

    arquivo_teste_wav = pasta_sfx / "teste_custom.wav"

    # Gera um pequeno arquivo WAV de 16-bits para teste
    with wave.open(str(arquivo_teste_wav), "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(TAXA_AMOSTRAGEM)
        silencio = (b"\x00\x00") * 1000
        wf.writeframes(silencio)

    try:
        busca = _buscar_arquivo_audio("sfx", "teste_custom")
        assert busca is not None and busca.name == "teste_custom.wav"
        banco_hibrido = construir_banco_sfx()
        assert "teste_custom" in banco_hibrido, "Arquivo WAV customizado não foi carregado dinamicamente no banco de SFX!"
        print("[6] Arquitetura Híbrida validada: arquivo customizado de estúdio carregado com prioridade!")
    finally:
        if arquivo_teste_wav.exists():
            arquivo_teste_wav.unlink()

    print("\n>>> TODOS OS TESTES DA FASE 1 PASSARAM COM 100% DE SUCESSO! <<<")


if __name__ == "__main__":
    testar_fase1_audio()
