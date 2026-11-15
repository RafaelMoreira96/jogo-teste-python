#!/usr/bin/env python3
"""Script de Build Automatizado para Distribuição de 'A Lenda Perdida' (Steam / Itch.io).

Gera executável standalone (.exe para Windows ou binário ELF para Linux) utilizando PyInstaller,
embutindo mapas, diálogos e assets procedurais.
"""
import os
from pathlib import Path
import platform
import subprocess
import sys


def main():
    raiz = Path(__file__).resolve().parent.parent
    os.chdir(raiz)
    sistema = platform.system()
    print(f"==================================================")
    print(f"📦 Iniciando Empacotamento de 'A Lenda Perdida'")
    print(f"Plataforma detectada: {sistema} ({platform.machine()})")
    print(f"Diretório raiz: {raiz}")
    print(f"==================================================")

    # Verifica se pyinstaller está disponível
    try:
        import PyInstaller
        print(f"✓ PyInstaller versão {PyInstaller.__version__} encontrado.")
    except ImportError:
        print("Instalando PyInstaller no ambiente virtual...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

    # Separador de dados no PyInstaller: ':' no Linux/macOS, ';' no Windows
    sep = ";" if sistema == "Windows" else ":"

    comando = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onefile",
        "--windowed",
        "--name",
        "ALendaPerdida",
        f"--add-data=maps{sep}maps",
        f"--add-data=historia{sep}historia",
        "--hidden-import=pygame",
        "--hidden-import=settings",
        "--hidden-import=ui",
        "--hidden-import=audio",
        "--hidden-import=rpg",
        "--hidden-import=level",
        "--hidden-import=camera",
        "--hidden-import=enemy",
        "--hidden-import=boss",
        "--hidden-import=salvamento",
        "--hidden-import=config",
        "--hidden-import=efeitos",
        "--hidden-import=conquistas",
        "--hidden-import=missoes",
        "--hidden-import=equipamentos",
        "--hidden-import=cenas.base",
        "--hidden-import=cenas.menu",
        "--hidden-import=cenas.jogo",
        "--hidden-import=cenas.prologo",
        "--hidden-import=cenas.loja",
        "--hidden-import=cenas.arvore_habilidades",
        "--hidden-import=cenas.mapa_mundo",
        "--hidden-import=cenas.bestiario",
        "--hidden-import=cenas.conquistas_cena",
        "--hidden-import=cenas.configuracoes",
        "--hidden-import=cenas.pausa",
        "--hidden-import=cenas.slots_save",
        "--hidden-import=cenas.jukebox",
        "--hidden-import=cenas.remapeamento",
        "main.py",
    ]

    print("\nExecutando PyInstaller...")
    print(" ".join(comando[:10]) + " ...")
    res = subprocess.run(comando)

    if res.returncode == 0:
        dist_dir = raiz / "dist"
        saida = dist_dir / ("ALendaPerdida.exe" if sistema == "Windows" else "ALendaPerdida")
        tamanho_mb = saida.stat().st_size / (1024 * 1024) if saida.exists() else 0
        print(f"\n✅ Build concluído com sucesso!")
        print(f"Executável gerado em: {saida}")
        print(f"Tamanho do arquivo: {tamanho_mb:.2f} MB")
        print("\nPronto para distribuição comercial na Steam / Itch.io!")
    else:
        print(f"\n❌ Erro durante o empacotamento (código {res.returncode}).", file=sys.stderr)
        sys.exit(res.returncode)


if __name__ == "__main__":
    main()
