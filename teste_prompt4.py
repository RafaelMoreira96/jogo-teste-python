"""Bateria de Testes Automatizados para o Prompt 4 (Narrativa, Hierarquia de Chefes e Cartografia)."""
import os
from pathlib import Path
import pygame

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
pygame.init()

from main import App
from historia import Conversa, Historia
from rpg import CATEGORIAS_CHEFES, LISTA_CHEFES_PROGRESSAO
from settings import PASTA_BASE
from level import Nivel


def testar_hierarquia_16_chefes():
    print("\n--- Parte 1: Hierarquia e Categorização dos 16 Chefes ---")
    assert len(LISTA_CHEFES_PROGRESSAO) == 16, f"Esperado 16 chefes na progressão, obteve {len(LISTA_CHEFES_PROGRESSAO)}!"
    assert len(CATEGORIAS_CHEFES) == 16, f"Esperado 16 categorias de chefes, obteve {len(CATEGORIAS_CHEFES)}!"

    guardioes_reliquias = [cid for cid, cat in CATEGORIAS_CHEFES.items() if "Guardião da Relíquia" in cat]
    arautos_eclipse = [cid for cid, cat in CATEGORIAS_CHEFES.items() if "Arauto do Eclipse" in cat]
    lendas_ocultas = [cid for cid, cat in CATEGORIAS_CHEFES.items() if "Lenda Oculta" in cat]
    soberano = [cid for cid, cat in CATEGORIAS_CHEFES.items() if "Soberano do Apocalipse" in cat]

    assert len(guardioes_reliquias) == 6, f"Esperado 6 Guardiões das Relíquias, obteve {len(guardioes_reliquias)}: {guardioes_reliquias}"
    assert len(arautos_eclipse) == 4, f"Esperado 4 Arautos do Eclipse, obteve {len(arautos_eclipse)}: {arautos_eclipse}"
    assert len(lendas_ocultas) == 5, f"Esperado 5 Lendas Ocultas, obteve {len(lendas_ocultas)}: {lendas_ocultas}"
    assert len(soberano) == 1, f"Esperado 1 Soberano do Apocalipse, obteve {len(soberano)}: {soberano}"

    print(f"✓ 6 Guardiões das Relíquias validados: {guardioes_reliquias}")
    print(f"✓ 4 Arautos do Eclipse validados: {arautos_eclipse}")
    print(f"✓ 5 Lendas Ocultas validadas: {lendas_ocultas}")
    print(f"✓ 1 Soberano do Apocalipse validado: {soberano}")


def testar_roteiro_tres_atos():
    print("\n--- Parte 2: Os 3 Atos Narrativos e Cutscenes ---")
    hist = Historia.carregar("historia/dialogos.txt")
    assert "inicio" in hist.dialogos, "Diálogo inicial não encontrado!"
    assert "cutscene_despertar_santuario" in hist.dialogos, "Cutscene do despertar do Santuário não encontrada!"
    assert "anciao_vila" in hist.dialogos, "Diálogo do Ancião não encontrado!"
    assert "anciao_reliquias" in hist.dialogos, "Diálogo de entrega de relíquias não encontrado!"

    # 1. Ato I (Herói sem marcas)
    flags_ato1 = set()
    conversa_ato1 = Conversa(hist, "anciao_vila", flags_ato1)
    passo = conversa_ato1.proximo()
    assert passo[0] == "fala" and "Bem-vindo à Vila Aurora" in passo[2], f"Ato I esperado, obteve: {passo}"
    print("✓ Ato I (O Despertar da Corrupção na Floresta) validado no Ancião!")

    # 2. Ato II (Rei Slime derrotado)
    flags_ato2 = {"rei_slime_derrotado"}
    conversa_ato2 = Conversa(hist, "anciao_vila", flags_ato2)
    passo = conversa_ato2.proximo()
    assert passo[0] == "fala" and "fratura mística" in passo[2], f"Ato II esperado, obteve: {passo}"
    print("✓ Ato II (Fratura dos Selos e Busca das 6 Relíquias) validado no Ancião!")

    # 3. Ato III (Santuário desperto / Eclipse)
    flags_ato3 = {"santuario_desperto"}
    conversa_ato3 = Conversa(hist, "anciao_vila", flags_ato3)
    passo = conversa_ato3.proximo()
    assert passo[0] == "fala" and "Eclipse do Apocalipse" in passo[2], f"Ato III esperado, obteve: {passo}"
    print("✓ Ato III (O Eclipse do Apocalipse e os 4 Arautos) validado no Ancião!")

    # 4. Cutscene do Santuário
    comandos_cutscene = hist.dialogos["cutscene_despertar_santuario"]
    tipos_comandos = [c[0] for c in comandos_cutscene]
    assert "cena" in tipos_comandos, "Cutscene deve conter comandos cinemáticos de cena (@clima, @tremer, etc)!"
    print("✓ Cutscene cinematográfica 'cutscene_despertar_santuario' compilada com comandos cênicos!")


def testar_cartografia_e_mapas(app):
    print("\n--- Parte 3: Cartografia e Conexão de Mapas ---")
    mapas_requeridos = [
        "mundo.txt",
        "vila.txt",
        "ruinas.txt",
        "santuario.txt",
        "lago.txt",
        "pantano.txt",
        "deserto.txt",
        "castelo.txt",
    ]
    for m in mapas_requeridos:
        caminho = PASTA_BASE / "maps" / m
        assert caminho.exists(), f"Mapa obrigatório {m} não encontrado!"
        nivel = Nivel(caminho, app.gfx)
        assert len(nivel.grade) > 5, f"Grade do mapa {m} está vazia ou corrompida!"
    print(f"✓ Todos os {len(mapas_requeridos)} mapas essenciais de cartografia validados e carregados com sucesso!")


if __name__ == "__main__":
    app = App()
    testar_hierarquia_16_chefes()
    testar_roteiro_tres_atos()
    testar_cartografia_e_mapas(app)
    print("\n=======================================================")
    print("🎉 EXECUÇÃO DO PROMPT 4 CONCLUÍDA COM 100% DE SUCESSO!")
    print("=======================================================")
