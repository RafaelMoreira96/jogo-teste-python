"""Testes de Validação do Sistema de Object Pooling (Fase 1)."""
import os
import pygame

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

from pooling import ListaParticulas, PoolParticulas, PoolProjeteis
from efeitos import Particula, explosao
from rpg import ProjetilMagico
from chefe import ProjetilChefe
from enemy import FlechaInimigo
from main import App
from cenas.jogo import Jogo


def testar_pool_particulas():
    print("--- Testando Pool de Partículas ---")
    PoolParticulas.limpar()

    p1 = PoolParticulas.obter((10, 20), (255, 0, 0), vel=(5, 5), vida=0.5)
    assert p1.pos.x == 10 and p1.pos.y == 20
    assert p1.vida == 0.5
    id_original = id(p1)

    PoolParticulas.liberar(p1)
    stats = PoolParticulas.stats()
    assert stats["em_espera"] == 1
    assert stats["liberadas"] == 1

    # Obter novamente deve reutilizar a mesma instância
    p2 = PoolParticulas.obter((30, 40), (0, 255, 0), vel=(-5, -5), vida=0.8)
    assert id(p2) == id_original
    assert p2.pos.x == 30 and p2.pos.y == 40
    assert p2.vida == 0.8
    assert p2.cor == (0, 255, 0)
    print("✓ Reutilização de instância de partícula confirmada (zero alocação)!")

    # Testar obter_explosao
    exp = PoolParticulas.obter_explosao((50, 50), [(255, 255, 0), (255, 100, 0)], quantidade=10)
    assert len(exp) == 10
    print(f"✓ Explosão gerada via Pool com {len(exp)} partículas!")


def testar_lista_particulas():
    print("\n--- Testando ListaParticulas e Reciclagem In-Place ---")
    PoolParticulas.limpar()
    lista = ListaParticulas()

    # Adiciona 20 partículas com tempos de vida diferentes
    for i in range(20):
        vida = 0.05 if i % 2 == 0 else 1.0
        lista.append(PoolParticulas.obter((0, 0), (255, 255, 255), vida=vida))

    assert len(lista) == 20
    # Avança tempo para matar metade
    lista.atualizar(0.1)
    assert len(lista) == 10, f"Deveriam sobrar 10 partículas, sobraram {len(lista)}"
    stats = PoolParticulas.stats()
    assert stats["em_espera"] == 10, f"Deveriam haver 10 liberadas na pool, há {stats['em_espera']}"
    print("✓ Reciclagem in-place com descarte e liberação automática para a pool validada!")

    # Clear devolve o resto
    lista.clear()
    assert len(lista) == 0
    assert PoolParticulas.stats()["em_espera"] == 20
    print("✓ clear() devolveu todas as partículas ativas para a pool com sucesso!")


def testar_pool_projeteis():
    print("\n--- Testando Pool de Projéteis ---")
    PoolProjeteis.limpar()

    # 1. Projétil Mágico
    pm1 = PoolProjeteis.obter_magico((100, 100), (1, 0), dano=3, cor=(255, 50, 50))
    id_pm = id(pm1)
    assert pm1.dano == 3
    PoolProjeteis.liberar(pm1)

    pm2 = PoolProjeteis.obter_magico((200, 200), (0, -1), dano=4, cor=(100, 100, 255))
    assert id(pm2) == id_pm
    assert pm2.pos.x == 200 and pm2.pos.y == 200
    assert pm2.dano == 4
    print("✓ Reutilização de Projétil Mágico validada com sucesso!")

    # 2. Projétil de Chefe
    pc1 = PoolProjeteis.obter_chefe((50, 50), (10, 0), dano=2, raio=6)
    id_pc = id(pc1)
    PoolProjeteis.liberar(pc1)

    pc2 = PoolProjeteis.obter_chefe((60, 60), (-10, 0), dano=5, raio=8)
    assert id(pc2) == id_pc
    assert pc2.dano == 5
    assert pc2.raio == 8
    print("✓ Reutilização de Projétil de Chefe validada com sucesso!")

    # 3. Flecha de Inimigo
    fl1 = PoolProjeteis.obter_flecha((10, 10), (100, 0), dano=1)
    id_fl = id(fl1)
    PoolProjeteis.liberar(fl1)

    fl2 = PoolProjeteis.obter_flecha((20, 20), (0, 100), dano=2)
    assert id(fl2) == id_fl
    assert fl2.dano == 2
    print("✓ Reutilização de Flecha de Inimigo validada com sucesso!")


def testar_integracao_jogo():
    print("\n--- Testando Integração com Loop do Jogo ---")
    app = App()
    jogo = Jogo(app, dialogo_inicial=None)

    # Dispara magia
    jogo.rpg.mana = 20.0
    jogo._usar_poder_ativo()
    assert len(jogo.projeteis) >= 1
    assert isinstance(jogo.particulas, ListaParticulas)

    # Simula 60 frames de jogo com combate
    for _ in range(60):
        jogo.atualizar(1 / 60)

    p_stats = PoolParticulas.stats()
    pr_stats = PoolProjeteis.stats()
    print(f"✓ Estatísticas de Partículas: {p_stats}")
    print(f"✓ Estatísticas de Projéteis: {pr_stats}")
    assert p_stats["reaproveitadas"] > 0, "Deveria haver reaproveitamento de partículas no gameplay!"
    print("🎉 INTEGRAÇÃO DE POOLING NO GAMEPLAY VALIDADA COM 100% DE SUCESSO!")


if __name__ == "__main__":
    testar_pool_particulas()
    testar_lista_particulas()
    testar_pool_projeteis()
    testar_integracao_jogo()
