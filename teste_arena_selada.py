import os
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

from pathlib import Path
import pygame

pygame.init()
pygame.display.set_mode((256, 144))

from main import App
from cenas.jogo import Jogo
from cenas.mapa_mundo import MapaMundo
from entrada import Entrada


def testar_arena_selada():
    print("=== TESTE: ARENA DE CHEFÃO SELADA ATÉ A VITÓRIA OU MORTE ===")
    app = App()
    jogo = Jogo(app, dialogo_inicial=None)
    app.cenas = [jogo]

    # 1. Carrega o mapa do mundo e anda até o portal do Rei Slime
    caminho_mundo = Path("maps/mundo.txt")
    caminho_arena = Path("maps/covil_rei_slime.txt")
    jogo.trocar_mapa(caminho_mundo, usar_porta=False)

    pos_fora = (jogo.jogador.rect.centerx, jogo.jogador.rect.centery)
    print(f"[1] Fora da arena em {caminho_mundo.name}: pos={pos_fora}")

    # 2. Entra na arena do Rei Slime
    jogo.trocar_mapa(caminho_arena, usar_porta=True)
    jogo.atualizar(0.016)
    print(f"[2] Entrou em {jogo.nivel.caminho.name}")

    # Verifica checkpoint salvo na entrada exterior
    chk = getattr(jogo, "checkpoint", None)
    assert chk is not None, "Checkpoint não foi definido!"
    assert "mundo.txt" in chk["mapa"], f"Checkpoint esperado em mundo.txt, obtido: {chk['mapa']}"
    assert "Entrada:" in chk["nome_local"], f"Nome do checkpoint esperado 'Entrada: ...', obtido: {chk['nome_local']}"
    print(f"    ✔ Checkpoint gravado corretamente fora da arena: {chk['nome_local']} em {chk['mapa']}")

    # Verifica se o chefe está ativo e a arena está selada
    assert len(jogo.chefes) > 0, "Rei Slime não foi instanciado!"
    chefe = jogo.chefes[0]
    assert jogo.chefe_ativo is chefe, "chefe_ativo deve apontar para o chefe vivo!"
    assert jogo.arena_selada is True, "arena_selada deve ser True enquanto chefe estiver vivo!"
    print(f"    ✔ Chefe ativo detectado: {chefe.nome} (HP: {chefe.vida}/{chefe.vida_max})")
    print("    ✔ Propriedade jogo.arena_selada == True")

    # Verifica se as portas da arena são barreiras nos obstáculos
    for rect_p, _ in jogo.nivel.portas:
        assert rect_p in jogo.nivel.obstaculos, "Porta deve estar nos obstáculos enquanto arena selada!"
    print("    ✔ Portas de saída adicionadas a nivel.obstaculos (bloqueio físico ativo)")

    # 3. Tenta sair pela porta enquanto o chefe está vivo
    porta_saida, destino_saida = jogo.nivel.portas[0]
    print(f"[3] Testando tentativa de fuga pela porta para {destino_saida.name}...")
    jogo.jogador.posicionar(porta_saida.centerx, porta_saida.centery)

    # Executa um ciclo de atualização
    jogo.tempo_alerta_selo = 0.0
    jogo.atualizar(0.016)

    assert jogo.fade_destino is None, "ERRO: O jogador conseguiu iniciar transição pela porta com o chefe vivo!"
    assert "Arena Selada" in jogo.aviso_mapa, f"Aviso de arena selada esperado, recebido: {jogo.aviso_mapa}"
    print(f"    ✔ Fuga impedida com sucesso! Aviso: '{jogo.aviso_mapa}'")
    print(f"    ✔ Jogador empurrado: tempo_empurrao={jogo.jogador.tempo_empurrao:.2f}")

    # 4. Tenta usar o mapa do mundo para fugir
    print("[4] Testando tentativa de teleporte / fast-travel...")
    mapa_mundo = MapaMundo(app, jogo)
    app.entrada.apertadas.clear()
    app.entrada.apertadas.add("confirmar")
    mapa_mundo.atualizar(0.016)
    assert "Arena Selada" in jogo.aviso_mapa, "Viagem rápida pelo mapa não foi bloqueada!"
    print(f"    ✔ Viagem rápida bloqueada: '{jogo.aviso_mapa}'")
    app.entrada.apertadas.clear()

    # 5. Renderiza um snapshot do visual com barreira selada
    tela = pygame.Surface((256, 144))
    jogo.desenhar(tela)
    caminho_snap = Path("/home/rafael/.gemini/antigravity/brain/dccdf99b-6810-4991-9700-047c54c4cd94/snapshot_arena_selada.png")
    pygame.image.save(tela, caminho_snap)
    print(f"[5] Snapshot da arena selada salvo em {caminho_snap}")

    # 6. Teste de Game Over: Morre dentro da arena
    print("[6] Testando Morte (Game Over) dentro da arena...")
    jogo.jogador.posicionar(jogo.nivel.largura_px // 2, jogo.nivel.altura_px // 2)
    jogo.jogador.vida = 0
    jogo.atualizar(0.016)
    assert jogo.estado == "derrota", f"Estado esperado 'derrota', obtido: {jogo.estado}"

    # Revive no checkpoint
    jogo.renascer_no_checkpoint()
    assert jogo.estado == "jogando"
    assert jogo.nivel.caminho.name == "mundo.txt", f"Esperado renascer fora da arena em mundo.txt, renasceu em: {jogo.nivel.caminho.name}"
    assert jogo.jogador.vida == jogo.vida_max_total(), "Vida deve ser restaurada após renascer no checkpoint!"
    print(f"    ✔ Renascimento no checkpoint exterior executado com sucesso: renasceu em {jogo.nivel.caminho.name} com HP {jogo.jogador.vida}")

    # 7. Re-entra na arena e DERROTA o chefe
    print("[7] Re-entrando na arena para derrotar o chefe...")
    jogo.trocar_mapa(caminho_arena, usar_porta=True)
    chefe = jogo.chefes[0]
    chefe.vida = 0
    chefe.morrendo = True
    chefe.tempo_morte = 0.0

    # Atualiza jogo para processar a morte do chefe
    jogo.atualizar(0.016)

    assert len(jogo.chefes) == 0, "Chefes vivos ainda presentes após morte!"
    assert jogo.arena_selada is False, "arena_selada deve ser False após derrotar o chefe!"
    assert "Arena Aberta" in jogo.aviso_mapa, f"Esperado aviso de arena aberta, obtido: {jogo.aviso_mapa}"
    print(f"    ✔ Chefe derrotado! {jogo.aviso_mapa}")
    print("    ✔ jogo.arena_selada == False")

    # 8. Testa saída livre pela porta agora que o chefe foi derrotado
    print("[8] Testando saída pela porta com chefe derrotado...")
    jogo.jogador.posicionar(porta_saida.centerx, porta_saida.centery)
    jogo.atualizar(0.016)

    assert jogo.fade_destino is not None, "ERRO: Jogador não conseguiu sair pela porta após derrotar o chefe!"
    assert jogo.fade_destino.name == "mundo.txt", f"Destino de saída esperado mundo.txt, obtido: {jogo.fade_destino.name}"
    print(f"    ✔ Transição de saída iniciada com sucesso para {jogo.fade_destino.name}!")

    # Completa a transição
    jogo.fade_alfa = 1.0
    jogo.fade_estado = "out"
    jogo.atualizar(0.016)
    assert jogo.nivel.caminho.name == "mundo.txt", f"Esperado estar em mundo.txt, está em {jogo.nivel.caminho.name}"
    print("    ✔ Jogador retornou com sucesso para o mundo aberto!")

    # 9. Tenta reentrar no covil do chefe já derrotado (deve estar permanentemente selado)
    print("[9] Testando bloqueio permanente de reentrada no covil do chefe purificado...")
    porta_covil = [r for r, d in jogo.nivel.portas if d.name == "covil_rei_slime.txt"][0]
    jogo.jogador.posicionar(porta_covil.centerx, porta_covil.centery)
    jogo.atualizar(0.016)
    print(f"    DEBUG: aviso_mapa='{jogo.aviso_mapa}', fade_destino={jogo.fade_destino}, pos={jogo.jogador.rect.center}, porta={porta_covil}")
    assert jogo.fade_destino is None, "Não deve permitir reentrar no covil de chefe derrotado!"
    assert "Área Selada" in jogo.aviso_mapa
    print(f"    ✔ Área selada para sempre confirmada: '{jogo.aviso_mapa}'")

    print("\n>>> TODOS OS TESTES PASSARAM COM 100% DE SUCESSO! <<<")

if __name__ == "__main__":
    testar_arena_selada()
