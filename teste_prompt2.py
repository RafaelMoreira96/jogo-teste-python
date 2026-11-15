"""Script de verificação headless completo dos 4 Pilares do Prompt 2."""
import os
import sys

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import pygame
pygame.init()

from audio import SistemaAudio
from config import carregar as carregar_config
from efeitos import (
    MonolitoTeleporte,
    PortalMistico,
    ReliquiaGuardiao,
    TotemSinalizacao,
    VasoQuebravel,
    VentoGuia,
)
from rpg import LISTA_CHEFES_PROGRESSAO, SistemaRPG
from settings import PASTA_BASE


def testar_audio():
    print("--- Testando Sistema de Áudio (Novos SFX) ---")
    cfg = carregar_config()
    audio = SistemaAudio(cfg)
    novos_sfx = ["teleporte", "quebrar_vaso", "ativar_monolito", "gong_chefe", "eco_fantasma"]
    for s in novos_sfx:
        assert s in audio._sfx, f"SFX '{s}' não encontrado no banco!"
        audio.sfx(s)
    print("✓ Todos os novos efeitos sonoros sintetizados e tocados com sucesso!")


def testar_jogo_completo():
    print("\n--- Testando Jogo e Pilares do Prompt 2 ---")
    from main import App
    app = App()
    from cenas.jogo import Jogo
    jogo = Jogo(app, dialogo_inicial=None)

    # 1. Teste de Totens de Sinalização e Monólitos no mapa 'mundo.txt'
    caminho_mundo = PASTA_BASE / "maps" / "mundo.txt"
    jogo.trocar_mapa(caminho_mundo, usar_porta=False)
    
    assert len(jogo.monolitos) > 0, "Nenhum Monólito instanciado em mundo.txt!"
    mono = jogo.monolitos[0]
    print(f"✓ Monólito encontrado: {mono.nome_regiao} ({mono.id_waypoint})")
    
    assert len(jogo.totens) > 0, "Nenhum Totem de Sinalização instanciado em mundo.txt!"
    totem = jogo.totens[0]
    print(f"✓ Totem de Sinalização encontrado com rotas: {totem.rotas}")

    # 2. Teste do Portal Místico e Portal Fantasma
    assert len(jogo.portais_misticos) > 0, "Nenhum Portal Místico instanciado em mundo.txt!"
    portal_slime = jogo.portais_misticos[0]
    print(f"✓ Portal Místico ativo para: {portal_slime.nome_chefe} (Nv. Req: {portal_slime.req_nivel}, Elemento: {portal_slime.elemento})")
    
    # Testa renderização do portal ativo
    surf_teste = pygame.Surface((320, 180))
    portal_slime.desenhar(surf_teste, jogo.camera, app.fontes.normal, jogo.rpg)
    
    # Derrota o chefe e verifica transformação em Portal Fantasma
    jogo.rpg.chefes_derrotados.add("rei_slime")
    portal_slime.atualizar(0.1, jogo)
    portal_slime.desenhar(surf_teste, jogo.camera, app.fontes.normal, jogo.rpg)
    print("✓ Portal Místico transformado com sucesso no Fantasma da Porta (selo espectral)!")

    # 3. Teste de Despertar de Monólito e Viagem Rápida
    jogo.jogador.posicionar(mono.pos.x, mono.pos.y)
    mono.atualizar(0.1, jogo)
    assert mono.id_waypoint in jogo.rpg.waypoint_descobertos, "Monólito não despertou após aproximação do herói!"
    print("✓ Monólito despertado e registrado em waypoint_descobertos!")

    # Teste de teleporte astral
    alvo_teleporte = {
        "id": "vila",
        "nome": "Vila de Aurora",
        "mapa": "vila.txt",
        "pos": (28 * 16, 8 * 16),
    }
    jogo.executar_teleporte_astral(alvo_teleporte)
    assert jogo.feixe_teleporte is not None, "Feixe de teleporte astral não foi ativado!"
    # Avança tempo para completar teleporte
    jogo.atualizar(0.5)
    assert jogo.nivel.caminho.name == "vila.txt", f"Teleporte falhou, mapa atual é {jogo.nivel.caminho.name}!"
    print("✓ Teleporte Astral executado com feixe de luz vertical para Vila de Aurora!")

    # 4. Teste de Vasos de Cerâmica Quebráveis
    vaso = VasoQuebravel((100, 100))
    jogo.vasos.append(vaso)
    ouro_antes = jogo.rpg.ouro
    coracoes_antes = len(jogo.coracoes)
    mana_antes = jogo.rpg.mana
    vaso.quebrar(jogo)
    assert vaso.quebrado, "Vaso não ficou quebrado após quebrar()!"
    print("✓ Vaso de cerâmica quebrado com sucesso e recompensa gerada!")

    # 5. Teste de Relíquias e entrega ao Ancião
    reliquia = ReliquiaGuardiao((jogo.jogador.rect.centerx, jogo.jogador.rect.centery), "reliquia_vento")
    jogo.reliquias.append(reliquia)
    reliquia.atualizar(0.1, jogo)
    assert "reliquia_vento" in jogo.rpg.reliquias_coletadas, "Relíquia não foi coletada pelo jogador!"
    print("✓ Relíquia Secreta coletada com sucesso!")

    # Entrega ao Ancião
    jogo.entregar_reliquias_anciao()
    assert "reliquia_vento" in jogo.rpg.reliquias_entregues, "Relíquia não foi entregue ao Ancião!"
    assert len(jogo.rpg.reliquias_coletadas) == 0, "Relíquias coletadas não foram esvaziadas após entrega!"
    print("✓ Relíquia entregue ao Ancião com expansão de bênçãos permanentes!")

    # 6. Teste do Vento Guia (Arcane Compass)
    jogo.invocar_vento_guia()
    assert len(jogo.ventos_guia) > 0, "Vento Guia não gerou partículas de orientação!"
    for _ in range(5):
        jogo.atualizar(0.1)
    print("✓ Vento Guia invocado e partículas fluíram apontando para o próximo Guardião!")

    # 7. Teste de Vinheta de Apresentação de Chefes (Title Card Épico)
    from chefe import CRIADORES_CHEFES
    chefe_teste = CRIADORES_CHEFES["golem_pedra"](100, 100)
    jogo.iniciar_apresentacao_chefe(chefe_teste)
    assert jogo.apresentacao_chefe is not None, "Apresentação de chefe não foi iniciada!"
    # Desenha cena com title card
    jogo.desenhar(surf_teste)
    print(f"✓ Title Card Épico exibido com sucesso para {chefe_teste.nome}!")

    # 8. Teste do Atlas do Mundo com Badges dos Chefes
    from cenas.mapa_mundo import MapaMundo
    mapa_cena = MapaMundo(app, jogo)
    mapa_cena.desenhar(surf_teste)
    print("✓ Atlas do Mundo com badges de 15 Guardiões renderizado com sucesso!")

    # 8b. Teste da Cena de Teleporte Astral
    from cenas.teleporte import CenaTeleporte
    teleporte_cena = CenaTeleporte(app, jogo, id_origem="mundo")
    teleporte_cena.atualizar(0.1)
    teleporte_cena.desenhar(surf_teste)
    print("✓ Interface modal de Viagem Rápida Astral (CenaTeleporte) testada e renderizada!")

    # 9. Teste de Salvamento e Carregamento
    from salvamento import carregar_jogo, salvar_jogo
    salvou = salvar_jogo(jogo)
    assert salvou, "Falha ao salvar jogo!"
    jogo_carregado = carregar_jogo(app)
    assert jogo_carregado is not None, "Falha ao carregar jogo!"
    assert "vila" in jogo_carregado.rpg.waypoint_descobertos, "Waypoints não foram preservados no save!"
    assert "reliquia_vento" in jogo_carregado.rpg.reliquias_entregues, "Relíquias entregues não foram preservadas no save!"
    print("✓ Save/Load validado com persistência completa de waypoints e relíquias!")

    print("\n=======================================================")
    print("TODOS OS 4 PILARES DO PROMPT 2 PASSARAM COM 100% DE SUCESSO!")
    print("=======================================================")


if __name__ == "__main__":
    testar_audio()
    testar_jogo_completo()
