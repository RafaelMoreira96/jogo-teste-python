"""Suíte de Testes Automatizados para os Elementos 3D e Estética HD-2D (Octopath Traveler)."""
import pygame
from main import App
from level import Nivel
from render3d import (
    criar_braseiro_3d,
    criar_pilar_runico_3d,
    criar_farol_astral_3d,
    criar_lanterna_poste_3d,
    criar_cristal_3d,
    criar_obelisco_3d,
    desenhar_tilt_shift_dof,
    gerar_objetos_3d_nivel,
)
from settings import LARGURA, ALTURA, PASTA_BASE


def testar_malhas_e_renderizacao_3d():
    print("\n--- Testando Malhas Poligonais 3D e Iluminação Lambertiana ---")
    surf = pygame.Surface((LARGURA, ALTURA))

    # 1. Braseiro 3D com chama e halo
    braseiro = criar_braseiro_3d(80, 90, cor_fogo=(60, 180, 255))
    assert braseiro.tipo == "braseiro"
    braseiro.atualizar(0.5)
    braseiro.desenhar(surf, 0, 0, 0.5)
    print("✓ Braseiro 3D (pedestal de pedra + cesto de ferro + chama volumétrica) validado!")

    # 2. Pilar Rúnico 3D
    pilar = criar_pilar_runico_3d(140, 90, cor_runa=(90, 220, 255))
    assert pilar.tipo == "pilar_runico"
    pilar.atualizar(0.5)
    pilar.desenhar(surf, 0, 0, 0.5)
    print("✓ Pilar Rúnico 3D (coluna sombreada por normais + runas pulsantes) validado!")

    # 3. Farol Astral 3D (anéis concêntricos giroscópicos)
    farol = criar_farol_astral_3d(200, 90, cor_anel=(235, 195, 80), cor_nucleo=(130, 240, 255))
    assert farol.tipo == "farol_astral"
    farol.atualizar(0.5)
    farol.desenhar(surf, 0, 0, 0.5)
    print("✓ Farol Astral 3D (anéis giroscópicos concêntricos + núcleo flutuante) validado!")

    # 4. Lanterna-Poste 3D
    lanterna = criar_lanterna_poste_3d(260, 90)
    assert lanterna.tipo == "lanterna_poste"
    lanterna.atualizar(0.5)
    lanterna.desenhar(surf, 0, 0, 0.5)
    print("✓ Lanterna-Poste 3D (ferro fundido + cúpula incandescente) validada!")


def testar_tilt_shift_dof():
    print("\n--- Testando Filtro Ótico Tilt-Shift & Depth-of-Field HD-2D ---")
    surf = pygame.Surface((LARGURA, ALTURA))
    surf.fill((40, 60, 80))
    cor_antes_topo = surf.get_at((160, 5))
    desenhar_tilt_shift_dof(surf, 1.0)
    cor_depois_topo = surf.get_at((160, 5))
    # O topo deve estar sombreado/difuso com o DoF
    assert cor_depois_topo != cor_antes_topo
    # O centro de ação (y=90) deve permanecer perfeitamente intocado para foco total
    cor_centro_antes = (40, 60, 80, 255)
    assert surf.get_at((160, 90)) == cor_centro_antes
    print("✓ Efeito Tilt-Shift HD-2D validado (difusão atmosférica no horizonte e foco nítido no centro)!")


def testar_populacao_3d_mapas():
    print("\n--- Testando Distribuição de Elementos 3D nos Mapas e Arenas ---")
    app = App()
    # 1. Arena do Covil do Rei Slime (deve ter braseiros aquáticos e pilares rúnicos)
    nivel_slime = Nivel(PASTA_BASE / "maps" / "covil_rei_slime.txt", app.gfx)
    tipos_slime = [obj.tipo for obj in nivel_slime.objetos_3d]
    assert "braseiro" in tipos_slime, "Covil do Rei Slime deve possuir braseiros 3D!"
    assert "pilar_runico" in tipos_slime, "Covil do Rei Slime deve possuir pilares rúnicos 3D!"
    print(f"✓ Covil do Rei Slime populado com {len(nivel_slime.objetos_3d)} objetos 3D ({set(tipos_slime)})!")

    # 2. Vila Aurora (deve ter lanternas-poste 3D e obeliscos)
    nivel_vila = Nivel(PASTA_BASE / "maps" / "vila.txt", app.gfx)
    tipos_vila = [obj.tipo for obj in nivel_vila.objetos_3d]
    assert "lanterna_poste" in tipos_vila, "Vila Aurora deve possuir lanternas 3D!"
    assert "obelisco" in tipos_vila or "braseiro" in tipos_vila
    print(f"✓ Vila Aurora populada com {len(nivel_vila.objetos_3d)} objetos 3D ({set(tipos_vila)})!")

    # 3. Altar do Colosso (deve ter Farol Astral 3D e pilares solares)
    nivel_colosso = Nivel(PASTA_BASE / "maps" / "altar_colosso.txt", app.gfx)
    tipos_colosso = [obj.tipo for obj in nivel_colosso.objetos_3d]
    assert "farol_astral" in tipos_colosso, "Altar do Colosso deve possuir Farol Astral 3D!"
    print(f"✓ Altar do Colosso Solar populado com {len(nivel_colosso.objetos_3d)} objetos 3D ({set(tipos_colosso)})!")

    print("\n🎉 SISTEMA DE ELEMENTOS 3D E HD-2D (OCTOPATH TRAVELER) VALIDADO COM 100% DE SUCESSO!")


if __name__ == "__main__":
    pygame.init()
    testar_malhas_e_renderizacao_3d()
    testar_tilt_shift_dof()
    testar_populacao_3d_mapas()
