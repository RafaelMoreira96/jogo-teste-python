"""Sintetizador 16-Bits de OST (BGM) e Efeitos Sonoros (SFX) estilo SNES / SPC700.

Gera proceduralmente em memória trilhas sonoras completas em 5 canais
(Melodia Principal expressiva, Contramelodia/Cordas, Harpa/Arpejos, Contrabaixo
e Percussão 16-bits) com filtro de Eco/Reverb multi-tap estilo SNES.
"""
import array
import math
from pathlib import Path
import random

import pygame

from settings import PASTA_BASE

TAXA_AMOSTRAGEM = 22050
DIR_AUDIO_ASSETS = PASTA_BASE / "assets" / "audio"


def _buscar_arquivo_audio(subpasta, nome):
    """Busca um arquivo de áudio (.ogg, .wav, .mp3) no diretório de assets se existir."""
    pasta = DIR_AUDIO_ASSETS / subpasta
    if not pasta.exists():
        return None
    for ext in (".ogg", ".wav", ".mp3"):
        candidato = pasta / f"{nome}{ext}"
        if candidato.is_file():
            return candidato
    return None

# Notas musicais em semitons (MIDI: C4 = 60, A4 = 69 -> 440 Hz)
_NOMES_NOTAS = {
    "C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3,
    "E": 4, "F": 5, "F#": 6, "Gb": 6, "G": 7, "G#": 8,
    "Ab": 8, "A": 9, "A#": 10, "Bb": 10, "B": 11,
}


def nota_para_midi(nome):
    """Converte 'C4', 'F#5', 'Bb3' em número MIDI (ou None para pausa '.' / '-')."""
    if not nome or nome in (".", "-", "_"):
        return None
    if len(nome) >= 3 and nome[1] in ("#", "b"):
        base, oitava = nome[:2], int(nome[2:])
    else:
        base, oitava = nome[:1], int(nome[1:])
    return 12 * (oitava + 1) + _NOMES_NOTAS[base]


def midi_para_freq(midi):
    return 440.0 * (2.0 ** ((midi - 69) / 12.0))


# Mapeamento automático de cada mapa para sua faixa da OST
MAPA_PARA_BGM = {
    "casa.txt": "vila",
    "vila.txt": "vila",
    "casa_anciao.txt": "vila",
    "casa_florista.txt": "vila",
    "taverna_vila.txt": "vila",
    "forja_vila.txt": "vila",
    "bosque_outono.txt": "vila",
    "cabana_druida.txt": "vila",
    "cabana_herbalista.txt": "vila",
    "cabana_cacador.txt": "vila",
    "cabana_lenhador.txt": "vila",
    "mundo.txt": "mundo",
    "lago.txt": "lago",
    "caverna_cristal.txt": "santuario",
    "santuario.txt": "santuario",
    "ruinas.txt": "ruinas",
    "pantano.txt": "ruinas",
    "cripta.txt": "abertura_sombria",
    "montanha.txt": "montanha",
    "pico_congelado.txt": "montanha",
    "deserto.txt": "deserto",
    "oasis.txt": "lago",
    "pousada_oasis.txt": "lago",
    "bazar_oasis.txt": "deserto",
    "templo_sol.txt": "deserto",
    "castelo.txt": "castelo",
    "castelo_patio.txt": "castelo",
    "castelo_masmorra.txt": "castelo",
    "castelo_biblioteca.txt": "santuario",
    "castelo_ante_camara.txt": "castelo",
    "castelo_sala_salvamento.txt": "abertura_sombria",
    "castelo_salao_trono.txt": "chefe_final",
}


# =====================================================================
# Composições da OST (Seções A + B com 5 Canais: Melodia, Contramelodia,
# Harpa/Arpejo, Baixo e Percussão)
# =====================================================================
PARTITURAS_OST = {
    # 1. ABERTURA SOMBRIA: Tocada nas cenas iniciais (sonho/pesadelo antes do controle)
    # Tom: Dó Menor Harmônico / Frígio — misteriosa, tensa e sinistra (estilo Chrono Trigger / Zelda ALttP Dark World Intro)
    "abertura_sombria": {
        "bpm": 82,
        "eco": 0.34,
        "timbre_melodia": "orgao_sombrio",
        "timbre_contra": "coral_sombrio",
        "timbre_harmonia": "cravo_sombrio",
        "melodia": [
            # Seção A: O sussurro nas sombras
            ("C4", 4), ("G4", 3), ("Ab4", 1), ("G4", 4), ("F4", 2), ("Eb4", 2),
            ("D4", 3), ("Eb4", 1), ("B3", 4), ("C4", 6), (".", 2),
            ("C5", 4), ("B4", 2), ("Ab4", 2), ("G4", 4), ("Eb4", 4),
            ("F4", 3), ("D4", 1), ("B3", 4), ("C4", 6), (".", 2),
            # Seção B: Presságio do despertar maligno
            ("Ab4", 3), ("G4", 1), ("F4", 4), ("Eb4", 3), ("D4", 1), ("C4", 4),
            ("Db4", 4), ("C4", 2), ("B3", 2), ("G3", 6), (".", 2),
            ("C4", 2), ("Eb4", 2), ("G4", 2), ("Ab4", 2), ("B4", 4), ("C5", 4),
            ("Ab4", 3), ("G4", 1), ("F#4", 4), ("G4", 6), (".", 2),
        ],
        "contra": [
            ("Eb3", 8), ("C3", 8), ("Ab2", 8), ("G2", 8),
            ("Eb4", 8), ("C4", 8), ("Ab3", 8), ("G3", 8),
            ("F3", 8), ("Eb3", 8), ("Db3", 8), ("B2", 8),
            ("C3", 8), ("Eb3", 8), ("D3", 8), ("B2", 8),
        ],
        "harmonia": [
            ("C3", 1), ("G3", 1), ("Eb4", 1), ("G3", 1), ("Ab2", 1), ("Eb3", 1), ("C4", 1), ("Eb3", 1),
            ("G2", 1), ("D3", 1), ("B3", 1), ("D3", 1), ("C3", 1), ("G3", 1), ("Eb4", 1), ("G3", 1),
            ("F2", 1), ("C3", 1), ("Ab3", 1), ("C3", 1), ("Eb2", 1), ("Bb2", 1), ("G3", 1), ("Bb2", 1),
            ("Db3", 1), ("Ab3", 1), ("F3", 1), ("Ab3", 1), ("G2", 1), ("D3", 1), ("B3", 1), ("D3", 1),
        ] * 2,
        "baixo": [
            ("C2", 6), ("G2", 2), ("Ab1", 6), ("Eb2", 2),
            ("G1", 6), ("D2", 2), ("C2", 6), ("G1", 2),
            ("Ab1", 6), ("Eb2", 2), ("C2", 6), ("G2", 2),
            ("F1", 4), ("G1", 4), ("C2", 8),
            ("F1", 6), ("C2", 2), ("Eb1", 6), ("Bb1", 2),
            ("Db2", 6), ("Ab1", 2), ("G1", 8),
            ("C2", 4), ("Eb2", 4), ("Ab1", 4), ("F#1", 4),
            ("G1", 6), ("D2", 2), ("G1", 8),
        ],
        "bateria": "B.......h...T...B.......h...T...",
    },

    # 2. APOCALIPSE: Tocada quando a Entidade Maligna destrói a cidade na visão inicial
    "apocalipse": {
        "bpm": 148,
        "eco": 0.25,
        "timbre_melodia": "orgao_sombrio",
        "timbre_contra": "trompa_real",
        "timbre_harmonia": "cravo_sombrio",
        "melodia": [
            ("D5", 2), ("F5", 2), ("E5", 2), ("Eb5", 2), ("D5", 3), ("A4", 1), ("Bb4", 4),
            ("C#5", 2), ("E5", 2), ("D5", 2), ("Bb4", 2), ("A4", 6), (".", 2),
            ("F5", 2), ("E5", 1), ("D5", 1), ("G#5", 4), ("G5", 2), ("F5", 2), ("E5", 2), ("D5", 2),
            ("C#5", 3), ("Bb4", 1), ("A4", 4), ("D5", 6), (".", 2),
        ],
        "contra": [
            ("A4", 4), ("F4", 4), ("G4", 4), ("Bb3", 4),
            ("E4", 4), ("G4", 4), ("F4", 4), ("C#4", 4),
            ("A4", 4), ("B4", 4), ("Bb4", 4), ("G4", 4),
            ("E4", 4), ("A3", 4), ("F4", 8),
        ],
        "harmonia": [
            ("D3", 1), ("A3", 1), ("D4", 1), ("F4", 1), ("Bb2", 1), ("F3", 1), ("Bb3", 1), ("D4", 1),
            ("G2", 1), ("D3", 1), ("G3", 1), ("Bb3", 1), ("A2", 1), ("E3", 1), ("A3", 1), ("C#4", 1),
        ] * 4,
        "baixo": [
            ("D2", 2), ("D3", 2), ("Bb1", 2), ("Bb2", 2), ("G1", 2), ("G2", 2), ("A1", 2), ("A2", 2),
        ] * 4,
        "bateria": "B.h.S.h.B.B.S.T.B.h.S.h.B.S.T.C.",
    },

    # 3. MENU PRINCIPAL: Tema épico e nostálgico em Lá Menor / Fá Lídio
    "menu": {
        "bpm": 112,
        "eco": 0.30,
        "timbre_melodia": "oboe_snes",
        "timbre_contra": "cordas_quentes",
        "timbre_harmonia": "harpa_celta",
        "melodia": [
            # Seção A
            ("E4", 2), ("A4", 2), ("C5", 3), ("B4", 1), ("A4", 2), ("G4", 2), ("E4", 4),
            ("F4", 2), ("A4", 2), ("D5", 3), ("C5", 1), ("B4", 6), ("E4", 2),
            ("C5", 2), ("E5", 2), ("D5", 3), ("B4", 1), ("C5", 2), ("A4", 2), ("F4", 4),
            ("E4", 2), ("G#4", 2), ("B4", 3), ("C5", 1), ("A4", 6), (".", 2),
            # Seção B
            ("F5", 3), ("E5", 1), ("D5", 2), ("C5", 2), ("B4", 3), ("C5", 1), ("D5", 4),
            ("E5", 3), ("D5", 1), ("C5", 2), ("B4", 2), ("A4", 6), ("G4", 2),
            ("F4", 2), ("A4", 2), ("C5", 2), ("F5", 2), ("E5", 3), ("D5", 1), ("B4", 4),
            ("C5", 3), ("B4", 1), ("G#4", 2), ("E4", 2), ("A4", 6), (".", 2),
        ],
        "contra": [
            ("C4", 8), ("A3", 8), ("D4", 8), ("G#3", 8),
            ("E4", 8), ("C4", 8), ("B3", 8), ("C4", 8),
            ("A4", 8), ("G4", 8), ("G4", 8), ("E4", 8),
            ("C4", 8), ("G#3", 8), ("E4", 8), ("C4", 8),
        ],
        "harmonia": [
            ("A3", 1), ("E4", 1), ("A4", 1), ("E4", 1), ("G3", 1), ("D4", 1), ("G4", 1), ("D4", 1),
            ("F3", 1), ("C4", 1), ("F4", 1), ("C4", 1), ("E3", 1), ("B3", 1), ("E4", 1), ("G#4", 1),
            ("A3", 1), ("E4", 1), ("C5", 1), ("E4", 1), ("F3", 1), ("C4", 1), ("A4", 1), ("C4", 1),
            ("E3", 1), ("B3", 1), ("G#4", 1), ("B3", 1), ("A3", 1), ("E4", 1), ("A4", 2),
        ] * 2,
        "baixo": [
            ("A2", 4), ("G2", 4), ("F2", 4), ("E2", 4),
            ("A2", 4), ("F2", 4), ("E2", 4), ("A2", 4),
            ("D2", 4), ("G2", 4), ("C2", 4), ("F2", 4),
            ("D2", 4), ("E2", 4), ("A2", 8),
        ],
        "bateria": "B...h...S...h.B.B...h...S...h.C.",
    },

    # 4. PRÓLOGO: Harpa cristalina e coro etéreo
    "prologo": {
        "bpm": 88,
        "eco": 0.36,
        "timbre_melodia": "sino_cristal",
        "timbre_contra": "coral_sombrio",
        "timbre_harmonia": "harpa_celta",
        "melodia": [
            ("E4", 4), ("B4", 3), ("C5", 1), ("B4", 4), ("A4", 2), ("G4", 2),
            ("F#4", 4), ("G4", 2), ("E4", 2), ("B3", 6), (".", 2),
            ("C5", 4), ("B4", 2), ("A4", 2), ("G4", 4), ("F#4", 4),
            ("E4", 4), ("D#4", 4), ("E4", 6), (".", 2),
        ],
        "contra": [
            ("G3", 8), ("E3", 8), ("D#3", 8), ("B2", 8),
            ("E4", 8), ("B3", 8), ("A3", 8), ("G3", 8),
        ],
        "harmonia": [
            ("E3", 1), ("B3", 1), ("G4", 1), ("B3", 1), ("C3", 1), ("G3", 1), ("E4", 1), ("G3", 1),
            ("A2", 1), ("E3", 1), ("C4", 1), ("E3", 1), ("B2", 1), ("F#3", 1), ("D#4", 1), ("F#3", 1),
        ] * 2,
        "baixo": [
            ("E2", 8), ("C2", 8), ("A1", 8), ("B1", 8),
            ("C2", 8), ("G1", 8), ("B1", 8), ("E2", 8),
        ],
        "bateria": "B.......h.......B.......C.......",
    },

    # 5. VILA / CASA / BOSQUE: Pastoral celta/SNES (estilo Secret of Mana / Legend of Mana)
    "vila": {
        "bpm": 104,
        "eco": 0.28,
        "timbre_melodia": "flauta_doce",
        "timbre_contra": "cordas_quentes",
        "timbre_harmonia": "harpa_celta",
        "melodia": [
            # Seção A
            ("G4", 2), ("A4", 1), ("B4", 1), ("D5", 3), ("E5", 1), ("D5", 2), ("B4", 2), ("G4", 4),
            ("E4", 2), ("G4", 2), ("A4", 3), ("B4", 1), ("A4", 6), (".", 2),
            ("B4", 2), ("D5", 2), ("G5", 3), ("F#5", 1), ("E5", 2), ("D5", 2), ("B4", 4),
            ("C5", 2), ("B4", 1), ("A4", 1), ("G4", 2), ("F#4", 2), ("G4", 6), (".", 2),
            # Seção B
            ("E5", 3), ("D5", 1), ("C5", 2), ("B4", 2), ("A4", 3), ("B4", 1), ("C5", 4),
            ("D5", 3), ("C5", 1), ("B4", 2), ("A4", 2), ("B4", 6), ("D5", 2),
            ("E5", 2), ("G5", 2), ("F#5", 3), ("D5", 1), ("E5", 2), ("C5", 2), ("A4", 4),
            ("B4", 2), ("G4", 2), ("A4", 3), ("F#4", 1), ("G4", 6), (".", 2),
        ],
        "contra": [
            ("B3", 8), ("G3", 8), ("C4", 8), ("F#3", 8),
            ("D4", 8), ("G3", 8), ("E3", 8), ("B3", 8),
            ("C4", 8), ("E4", 8), ("F#4", 8), ("G4", 8),
            ("C4", 8), ("A3", 8), ("D4", 8), ("B3", 8),
        ],
        "harmonia": [
            ("G3", 1), ("D4", 1), ("B4", 1), ("D4", 1), ("E3", 1), ("B3", 1), ("G4", 1), ("B3", 1),
            ("C3", 1), ("G3", 1), ("E4", 1), ("G3", 1), ("D3", 1), ("A3", 1), ("F#4", 1), ("A3", 1),
            ("G3", 1), ("D4", 1), ("B4", 1), ("D4", 1), ("C3", 1), ("G3", 1), ("E4", 1), ("G3", 1),
            ("A2", 1), ("E3", 1), ("C4", 1), ("D3", 1), ("G3", 1), ("D4", 1), ("B3", 2),
        ] * 2,
        "baixo": [
            ("G2", 4), ("E2", 4), ("C2", 4), ("D2", 4),
            ("B1", 4), ("E2", 4), ("C2", 2), ("D2", 2), ("G2", 4),
            ("C2", 4), ("A2", 4), ("D2", 4), ("G2", 4),
            ("C2", 4), ("A1", 4), ("D2", 4), ("G2", 4),
        ],
        "bateria": "B...h..hS...h..hB...h..hS...h...",
    },

    # 6. MUNDO (FLORESTA DE ESMERALDA): Aventura modal em Mi Dórico (estilo Chrono Trigger Corridors / Secret of Mana)
    "mundo": {
        "bpm": 126,
        "eco": 0.26,
        "timbre_melodia": "oboe_snes",
        "timbre_contra": "flauta_doce",
        "timbre_harmonia": "alaude_solo",
        "melodia": [
            # Seção A (Mi Dórico: Em - A - D - Bm - C#m7b5)
            ("E4", 2), ("B4", 2), ("C#5", 2), ("D5", 2), ("E5", 3), ("D5", 1), ("B4", 4),
            ("A4", 2), ("B4", 1), ("A4", 1), ("F#4", 2), ("D4", 2), ("E4", 6), (".", 2),
            ("E4", 2), ("B4", 2), ("C#5", 2), ("D5", 2), ("F#5", 3), ("E5", 1), ("C#5", 4),
            ("D5", 2), ("E5", 1), ("D5", 1), ("B4", 2), ("A4", 2), ("B4", 6), (".", 2),
            # Seção B
            ("G5", 3), ("F#5", 1), ("E5", 2), ("D5", 2), ("C#5", 3), ("D5", 1), ("E5", 4),
            ("F#5", 3), ("E5", 1), ("D5", 2), ("B4", 2), ("A4", 6), ("F#4", 2),
            ("G4", 2), ("B4", 2), ("E5", 2), ("D5", 2), ("C#5", 3), ("B4", 1), ("A4", 4),
            ("F#4", 2), ("A4", 2), ("B4", 2), ("D5", 2), ("E5", 6), (".", 2),
        ],
        "contra": [
            ("G4", 8), ("F#4", 8), ("F#4", 8), ("B3", 8),
            ("G4", 8), ("A4", 8), ("F#4", 8), ("D4", 8),
            ("B4", 8), ("A4", 8), ("A4", 8), ("F#4", 8),
            ("E4", 8), ("E4", 8), ("D4", 8), ("B3", 8),
        ],
        "harmonia": [
            ("E3", 1), ("B3", 1), ("G4", 1), ("B3", 1), ("A3", 1), ("E4", 1), ("C#4", 1), ("E4", 1),
            ("D3", 1), ("A3", 1), ("F#4", 1), ("A3", 1), ("E3", 1), ("B3", 1), ("G4", 1), ("B3", 1),
            ("E3", 1), ("B3", 1), ("G4", 1), ("B3", 1), ("A3", 1), ("E4", 1), ("C#4", 1), ("E4", 1),
            ("G3", 1), ("D4", 1), ("B3", 1), ("A3", 1), ("B2", 1), ("F#3", 1), ("D4", 2),
        ] * 2,
        "baixo": [
            ("E2", 3), ("E2", 1), ("A2", 4), ("D2", 3), ("D2", 1), ("E2", 4),
            ("E2", 3), ("E2", 1), ("A2", 4), ("G2", 2), ("A2", 2), ("B2", 4),
            ("G2", 4), ("A2", 4), ("B2", 4), ("F#2", 4),
            ("G2", 4), ("A2", 4), ("D2", 4), ("E2", 4),
        ],
        "bateria": "B.h.S.h.B.B.S.h.B.h.S.h.B.S.B.C.",
    },

    # 7. LAGO / OÁSIS: Sereno e aquático em Fá Lídio
    "lago": {
        "bpm": 100,
        "eco": 0.35,
        "timbre_melodia": "flauta_doce",
        "timbre_contra": "sino_cristal",
        "timbre_harmonia": "harpa_celta",
        "melodia": [
            ("C5", 3), ("B4", 1), ("A4", 2), ("G4", 2), ("E4", 4), ("C4", 4),
            ("F4", 2), ("A4", 2), ("C5", 2), ("E5", 2), ("D5", 6), (".", 2),
            ("E5", 3), ("D5", 1), ("C5", 2), ("A4", 2), ("G4", 4), ("E4", 4),
            ("F4", 2), ("G4", 2), ("A4", 2), ("B4", 2), ("C5", 6), (".", 2),
        ],
        "contra": [
            ("A4", 8), ("C4", 8), ("A3", 8), ("G3", 8),
            ("C5", 8), ("C4", 8), ("C4", 8), ("E4", 8),
        ],
        "harmonia": [
            ("F3", 1), ("C4", 1), ("E4", 1), ("A4", 1), ("C3", 1), ("G3", 1), ("C4", 1), ("E4", 1),
            ("D3", 1), ("A3", 1), ("D4", 1), ("F4", 1), ("G3", 1), ("B3", 1), ("D4", 1), ("G4", 1),
        ] * 2,
        "baixo": [
            ("F2", 8), ("C2", 8), ("D2", 4), ("G2", 4),
            ("F2", 8), ("C2", 8), ("G2", 4), ("C2", 4),
        ],
        "bateria": "B...h..hS...h..hB...h..hS...C...",
    },

    # 8. SANTUÁRIO / CAVERNA DE CRISTAL: Polifonia sacra e cristalina
    "santuario": {
        "bpm": 90,
        "eco": 0.38,
        "timbre_melodia": "sino_cristal",
        "timbre_contra": "coral_sombrio",
        "timbre_harmonia": "harpa_celta",
        "melodia": [
            ("F#5", 4), ("E5", 2), ("C#5", 2), ("D5", 4), ("A4", 4),
            ("B4", 3), ("C#5", 1), ("D5", 2), ("E5", 2), ("C#5", 6), (".", 2),
            ("F#5", 3), ("G#5", 1), ("A5", 4), ("E5", 4), ("C#5", 4),
            ("D5", 2), ("E5", 2), ("F#5", 2), ("G#5", 2), ("F#5", 6), (".", 2),
        ],
        "contra": [
            ("A4", 8), ("F#4", 8), ("D4", 8), ("E4", 8),
            ("C#5", 8), ("A4", 8), ("B4", 8), ("A4", 8),
        ],
        "harmonia": [
            ("F#3", 2), ("C#4", 2), ("A4", 2), ("C#4", 2), ("D3", 2), ("A3", 2), ("F#4", 2), ("A3", 2),
            ("B2", 2), ("F#3", 2), ("D4", 2), ("E3", 2), ("A2", 2), ("E3", 2), ("C#4", 4),
        ] * 2,
        "baixo": [
            ("F#2", 8), ("D2", 8), ("B1", 4), ("E2", 4), ("A1", 8),
            ("F#2", 8), ("C#2", 8), ("D2", 4), ("C#2", 4), ("F#2", 8),
        ],
        "bateria": "B.......C.......B.......C.......",
    },

    # 9. RUÍNAS / PÂNTANO: Mistério sincopado em Sol Menor Dórico
    "ruinas": {
        "bpm": 116,
        "eco": 0.32,
        "timbre_melodia": "oboe_snes",
        "timbre_contra": "coral_sombrio",
        "timbre_harmonia": "cravo_sombrio",
        "melodia": [
            ("G4", 2), ("Bb4", 2), ("D5", 3), ("C5", 1), ("Bb4", 2), ("A4", 2), ("G4", 4),
            ("E4", 2), ("G4", 2), ("Bb4", 2), ("A4", 2), ("F#4", 6), ("D4", 2),
            ("G4", 2), ("Bb4", 2), ("D5", 2), ("F5", 2), ("E5", 3), ("D5", 1), ("C5", 4),
            ("Bb4", 2), ("A4", 2), ("G4", 2), ("F#4", 2), ("G4", 6), (".", 2),
        ],
        "contra": [
            ("D4", 8), ("C4", 8), ("C4", 8), ("A3", 8),
            ("D4", 8), ("G4", 8), ("D4", 8), ("Bb3", 8),
        ],
        "harmonia": [
            ("G3", 1), ("D4", 1), ("Bb3", 1), ("D4", 1), ("Eb3", 1), ("Bb3", 1), ("G3", 1), ("Bb3", 1),
            ("C3", 1), ("G3", 1), ("E4", 1), ("G3", 1), ("D3", 1), ("A3", 1), ("F#4", 1), ("A3", 1),
        ] * 2,
        "baixo": [
            ("G2", 3), ("G2", 1), ("Eb2", 4), ("C2", 4), ("D2", 4),
            ("G2", 3), ("F2", 1), ("E2", 4), ("Eb2", 2), ("D2", 2), ("G2", 4),
        ],
        "bateria": "B.h.S..hB.h.S..hB.h.S..hB.S.T.C.",
    },

    # 10. MONTANHA / PICO CONGELADO: Épico de ventos alpinos em Lá Eólio
    "montanha": {
        "bpm": 134,
        "eco": 0.28,
        "timbre_melodia": "trompa_real",
        "timbre_contra": "cordas_quentes",
        "timbre_harmonia": "alaude_solo",
        "melodia": [
            ("A4", 2), ("E5", 3), ("D5", 1), ("C5", 2), ("B4", 2), ("C5", 2), ("D5", 2), ("E5", 2),
            ("G5", 3), ("F5", 1), ("E5", 2), ("D5", 2), ("E5", 6), (".", 2),
            ("F5", 2), ("E5", 1), ("D5", 1), ("C5", 2), ("A4", 2), ("G4", 2), ("B4", 2), ("D5", 4),
            ("C5", 2), ("B4", 1), ("A4", 1), ("G#4", 2), ("B4", 2), ("A4", 6), (".", 2),
        ],
        "contra": [
            ("C5", 8), ("A4", 8), ("B4", 8), ("G#4", 8),
            ("A4", 8), ("G4", 8), ("E4", 8), ("C4", 8),
        ],
        "harmonia": [
            ("A3", 1), ("E4", 1), ("A4", 1), ("E4", 1), ("F3", 1), ("C4", 1), ("F4", 1), ("C4", 1),
            ("G3", 1), ("D4", 1), ("G4", 1), ("D4", 1), ("E3", 1), ("B3", 1), ("E4", 1), ("G#4", 1),
        ] * 2,
        "baixo": [
            ("A2", 4), ("F2", 4), ("G2", 4), ("E2", 4),
            ("F2", 4), ("G2", 4), ("E2", 4), ("A2", 4),
        ],
        "bateria": "B.h.S.h.B.B.S.h.B.h.S.h.B.S.T.C.",
    },

    # 11. DESERTO / TEMPLO DO SOL: Escala Frígia Dominante Exótica (Ré, Mib, Fá#, Sol, Lá, Sib, Dó)
    "deserto": {
        "bpm": 122,
        "eco": 0.30,
        "timbre_melodia": "oboe_snes",
        "timbre_contra": "flauta_doce",
        "timbre_harmonia": "alaude_solo",
        "melodia": [
            ("D4", 2), ("Eb4", 2), ("F#4", 2), ("G4", 2), ("A4", 3), ("Bb4", 1), ("A4", 2), ("F#4", 2),
            ("G4", 2), ("F#4", 1), ("Eb4", 1), ("D4", 2), ("C4", 2), ("D4", 6), (".", 2),
            ("A4", 2), ("Bb4", 2), ("C5", 2), ("Bb4", 2), ("A4", 3), ("G4", 1), ("F#4", 4),
            ("G4", 2), ("Eb4", 2), ("F#4", 2), ("Eb4", 2), ("D4", 6), (".", 2),
        ],
        "contra": [
            ("A3", 8), ("C4", 8), ("Bb3", 8), ("F#3", 8),
            ("F#4", 8), ("D4", 8), ("Bb3", 8), ("A3", 8),
        ],
        "harmonia": [
            ("D3", 1), ("A3", 1), ("D4", 1), ("F#4", 1), ("Eb3", 1), ("Bb3", 1), ("Eb4", 1), ("G4", 1),
            ("C3", 1), ("G3", 1), ("C4", 1), ("Eb4", 1), ("D3", 1), ("A3", 1), ("D4", 1), ("F#4", 1),
        ] * 2,
        "baixo": [
            ("D2", 3), ("A2", 1), ("Eb2", 4), ("C2", 3), ("G2", 1), ("D2", 4),
            ("G2", 3), ("D2", 1), ("D2", 4), ("Eb2", 2), ("C2", 2), ("D2", 4),
        ],
        "bateria": "B..hS.h.B.B.S.h.B..hS.h.B.T.S.C.",
    },

    # 12. CASTELO DO ECLIPSE: Sinfonia Gótica em Ré Menor Harmônico (estilo Castlevania IV / Final Fantasy VI)
    "castelo": {
        "bpm": 144,
        "eco": 0.28,
        "timbre_melodia": "orgao_sombrio",
        "timbre_contra": "violino_solo",
        "timbre_harmonia": "cravo_sombrio",
        "melodia": [
            # Seção A
            ("D5", 2), ("A4", 1), ("D5", 1), ("F5", 3), ("E5", 1), ("D5", 2), ("C#5", 2), ("A4", 4),
            ("Bb4", 2), ("G4", 2), ("E5", 3), ("D5", 1), ("C#5", 6), ("A4", 2),
            ("D5", 2), ("F5", 2), ("A5", 3), ("G#5", 1), ("G5", 2), ("F5", 2), ("E5", 2), ("D5", 2),
            ("C#5", 2), ("E5", 2), ("A4", 2), ("C#5", 2), ("D5", 6), (".", 2),
            # Seção B
            ("F5", 3), ("E5", 1), ("D5", 2), ("C5", 2), ("Bb4", 3), ("D5", 1), ("G5", 4),
            ("E5", 3), ("D5", 1), ("C5", 2), ("Bb4", 2), ("A4", 6), ("C#5", 2),
            ("D5", 2), ("E5", 2), ("F5", 2), ("G5", 2), ("G#5", 3), ("A5", 1), ("F5", 4),
            ("E5", 2), ("D5", 2), ("C#5", 2), ("E5", 2), ("D5", 6), (".", 2),
        ],
        "contra": [
            ("F4", 8), ("E4", 8), ("G4", 8), ("E4", 8),
            ("A4", 8), ("Bb4", 8), ("E4", 8), ("F4", 8),
            ("A4", 8), ("Bb4", 8), ("G4", 8), ("E4", 8),
            ("F4", 8), ("B4", 8), ("A4", 8), ("F4", 8),
        ],
        "harmonia": [
            ("D3", 1), ("A3", 1), ("D4", 1), ("F4", 1), ("A2", 1), ("E3", 1), ("A3", 1), ("C#4", 1),
            ("Bb2", 1), ("F3", 1), ("Bb3", 1), ("D4", 1), ("A2", 1), ("E3", 1), ("A3", 1), ("C#4", 1),
        ] * 4,
        "baixo": [
            ("D2", 2), ("D3", 2), ("A1", 2), ("A2", 2), ("Bb1", 2), ("G1", 2), ("A1", 4),
            ("D2", 2), ("F2", 2), ("G2", 2), ("Bb2", 2), ("A2", 2), ("A1", 2), ("D2", 4),
            ("D2", 4), ("G2", 4), ("C2", 4), ("F2", 4),
            ("Bb1", 4), ("G#1", 4), ("A1", 4), ("D2", 4),
        ],
        "bateria": "B.h.S.h.B.B.S.h.B.h.S.h.B.S.T.C.",
    },

    # 13. DERROTA
    "derrota": {
        "bpm": 76,
        "eco": 0.38,
        "timbre_melodia": "oboe_snes",
        "timbre_contra": "cordas_quentes",
        "timbre_harmonia": "harpa_celta",
        "melodia": [
            ("E5", 4), ("D5", 4), ("C5", 4), ("B4", 4),
            ("A4", 6), ("G#4", 2), ("A4", 8),
        ],
        "contra": [
            ("C4", 8), ("E3", 8), ("C3", 8), ("C4", 8),
        ],
        "harmonia": [
            ("A2", 2), ("E3", 2), ("G2", 2), ("D3", 2),
            ("F2", 2), ("C3", 2), ("E2", 4),
            ("A2", 2), ("C3", 2), ("E3", 4), ("A2", 8),
        ],
        "baixo": [
            ("A1", 4), ("G1", 4), ("F1", 4), ("E1", 4), ("A1", 16),
        ],
        "bateria": "B.......B.......B...............",
    },

    # 14. BATALHA CONTRA CHEFE (Duelo Épico 16-Bits)
    "chefe": {
        "bpm": 150,
        "eco": 0.24,
        "timbre_melodia": "trompa_real",
        "timbre_contra": "orgao_sombrio",
        "timbre_harmonia": "cravo_sombrio",
        "melodia": [
            # Seção A: Fúria e Tensão
            ("D4", 2), ("D4", 1), ("F4", 1), ("A4", 2), ("G4", 2), ("F4", 2), ("E4", 2), ("D4", 4),
            ("Bb4", 3), ("A4", 1), ("G4", 2), ("F4", 2), ("E4", 4), ("C#4", 4),
            ("D4", 2), ("F4", 2), ("A4", 3), ("Bb4", 1), ("A4", 2), ("G4", 2), ("F4", 2), ("E4", 2),
            ("D4", 2), ("F4", 2), ("E4", 2), ("C#4", 2), ("D4", 6), (".", 2),
            # Seção B: Investida Heroica
            ("F4", 3), ("G4", 1), ("A4", 4), ("D5", 3), ("C5", 1), ("Bb4", 4),
            ("A4", 2), ("G4", 2), ("F4", 2), ("E4", 2), ("A4", 6), (".", 2),
            ("D5", 2), ("C#5", 2), ("D5", 2), ("E5", 2), ("F5", 3), ("E5", 1), ("D5", 4),
            ("Bb4", 2), ("A4", 2), ("G4", 2), ("E4", 2), ("D4", 6), (".", 2),
        ],
        "contra": [
            ("D3", 8), ("Bb2", 8), ("G2", 8), ("A2", 8),
            ("D3", 8), ("Bb2", 8), ("G2", 8), ("A2", 8),
            ("F3", 8), ("G3", 8), ("A3", 8), ("C#3", 8),
            ("D3", 8), ("Bb3", 8), ("G3", 8), ("A3", 8),
        ],
        "harmonia": [
            ("D3", 1), ("A3", 1), ("F4", 1), ("A3", 1), ("Bb2", 1), ("F3", 1), ("D4", 1), ("F3", 1),
            ("G2", 1), ("D3", 1), ("Bb3", 1), ("D3", 1), ("A2", 1), ("E3", 1), ("C#4", 1), ("E3", 1),
        ] * 4,
        "baixo": [
            ("D2", 2), ("D3", 2), ("Bb1", 2), ("Bb2", 2), ("G1", 2), ("G2", 2), ("A1", 2), ("A2", 2),
        ] * 4,
        "bateria": "B.h.S.h.B.B.S.T.B.h.S.h.B.S.T.C.",
    },

    # 15. CHEFE FINAL: O CLÍMAX DO APOCALIPSE (Soberano das Trevas)
    "chefe_final": {
        "bpm": 158,
        "eco": 0.28,
        "timbre_melodia": "orgao_sombrio",
        "timbre_contra": "coral_sombrio",
        "timbre_harmonia": "cravo_sombrio",
        "melodia": [
            # Seção A: O Juízo das Sombras
            ("C5", 2), ("G4", 2), ("Ab4", 2), ("Bb4", 2), ("C5", 3), ("D5", 1), ("Eb5", 4),
            ("D5", 2), ("C5", 2), ("B4", 2), ("G4", 2), ("Ab4", 4), ("G4", 4),
            ("Eb5", 3), ("D5", 1), ("C5", 2), ("Bb4", 2), ("Ab4", 3), ("G4", 1), ("F4", 4),
            ("G4", 2), ("Ab4", 2), ("B4", 2), ("D5", 2), ("C5", 6), (".", 2),
            # Seção B: O Confronto Cósmico
            ("C5", 4), ("Eb5", 4), ("G5", 3), ("F5", 1), ("Eb5", 4),
            ("D5", 3), ("C5", 1), ("B4", 4), ("C5", 6), (".", 2),
            ("Ab5", 2), ("G5", 2), ("F5", 2), ("Eb5", 2), ("D5", 3), ("Eb5", 1), ("C5", 4),
            ("B4", 2), ("D5", 2), ("G4", 2), ("B4", 2), ("C5", 6), (".", 2),
        ],
        "contra": [
            ("C4", 8), ("Eb4", 8), ("G4", 8), ("Ab4", 8),
            ("F4", 8), ("D4", 8), ("G4", 8), ("C4", 8),
            ("Ab4", 8), ("G4", 8), ("F4", 8), ("Eb4", 8),
            ("D4", 8), ("B3", 8), ("C4", 8), ("G3", 8),
        ],
        "harmonia": [
            ("C3", 1), ("G3", 1), ("Eb4", 1), ("G3", 1), ("Ab2", 1), ("Eb3", 1), ("C4", 1), ("Eb3", 1),
            ("F2", 1), ("C3", 1), ("Ab3", 1), ("C3", 1), ("G2", 1), ("D3", 1), ("B3", 1), ("D3", 1),
        ] * 4,
        "baixo": [
            ("C2", 2), ("C3", 2), ("Ab1", 2), ("Ab2", 2), ("F1", 2), ("F2", 2), ("G1", 2), ("G2", 2),
        ] * 4,
        "bateria": "B.h.S.h.B.B.S.T.B.B.S.h.B.S.T.C.",
    },

    # 16. VITÓRIA / FANFARRA HEROICA
    "vitoria": {
        "bpm": 128,
        "eco": 0.20,
        "timbre_melodia": "trompa_real",
        "timbre_contra": "cordas_quentes",
        "timbre_harmonia": "harpa_celta",
        "melodia": [
            ("C4", 2), ("E4", 2), ("G4", 2), ("C5", 4), ("G4", 2), ("C5", 6), (".", 2),
            ("D5", 2), ("C5", 2), ("B4", 2), ("A4", 2), ("B4", 4), ("G4", 4),
            ("A4", 2), ("B4", 2), ("C5", 2), ("D5", 2), ("E5", 6), ("D5", 2),
            ("C5", 8), (".", 8),
        ],
        "contra": [
            ("C3", 8), ("E3", 8), ("F3", 8), ("G3", 8),
            ("A3", 8), ("F3", 8), ("G3", 8), ("C3", 8),
        ],
        "harmonia": [
            ("C3", 1), ("G3", 1), ("E4", 1), ("G3", 1), ("F2", 1), ("C3", 1), ("A3", 1), ("C3", 1),
            ("G2", 1), ("D3", 1), ("B3", 1), ("D3", 1), ("C3", 1), ("G3", 1), ("E4", 1), ("G3", 1),
        ] * 2,
        "baixo": [
            ("C2", 4), ("G1", 4), ("F1", 4), ("G1", 4),
            ("A1", 4), ("F1", 4), ("G1", 4), ("C2", 8),
        ],
        "bateria": "B...S...B.B.S...B...S...B.S.T.C.",
    },

    # 17. ENCERRAMENTO / CRÉDITOS FINAIS (Tema nostálgico e festivo de final feliz)
    "encerramento": {
        "bpm": 120,
        "eco": 0.26,
        "timbre_melodia": "flauta_doce",
        "timbre_contra": "cordas_quentes",
        "timbre_harmonia": "harpa_celta",
        "melodia": [
            # Frase 1: Paz e alvorecer
            ("G4", 2), ("C5", 4), ("B4", 2), ("A4", 2), ("G4", 4), ("E4", 2),
            ("F4", 2), ("A4", 4), ("G4", 2), ("F4", 2), ("E4", 6), (".", 2),
            ("D4", 2), ("E4", 2), ("F4", 2), ("G4", 2), ("A4", 4), ("B4", 4),
            ("C5", 8), (".", 4), ("D5", 4),
            # Frase 2: Celebração heroica
            ("E5", 4), ("D5", 2), ("C5", 2), ("B4", 2), ("C5", 2), ("D5", 4),
            ("G4", 6), (".", 2), ("C5", 4), ("B4", 2), ("A4", 2),
            ("G4", 4), ("F4", 2), ("E4", 2), ("D4", 4), ("G4", 4),
            ("C4", 8), (".", 8),
        ],
        "contra": [
            ("C3", 8), ("G3", 8), ("F3", 8), ("C3", 8),
            ("F3", 8), ("G3", 8), ("C3", 8), ("G3", 8),
            ("C3", 8), ("G3", 8), ("F3", 8), ("G3", 8),
            ("F3", 8), ("G3", 8), ("C3", 16),
        ],
        "harmonia": [
            ("C4", 1), ("E4", 1), ("G4", 1), ("E4", 1), ("G3", 1), ("D4", 1), ("G4", 1), ("D4", 1),
            ("F3", 1), ("C4", 1), ("F4", 1), ("C4", 1), ("C3", 1), ("G3", 1), ("E4", 1), ("G3", 1),
        ] * 4,
        "baixo": [
            ("C2", 4), ("E2", 4), ("G2", 4), ("B1", 4),
            ("F2", 4), ("A2", 4), ("C3", 4), ("G2", 4),
            ("F2", 4), ("D2", 4), ("G2", 4), ("B1", 4),
            ("C2", 8), ("G1", 8),
        ] * 2,
        "bateria": "B...h.S...B...S.B...h.S...B.T.C.",
    },
}


# =====================================================================
# Síntese de Timbres 16-Bits e Percussão
# =====================================================================
_CACHE_NOTAS = {}
_CACHE_BATERIA = {}


def _sintetizar_nota(timbre, midi, n_amostras, ganho):
    """Sintetiza uma nota musical com harmônicos quentes estilo SNES SPC700."""
    chave = (timbre, midi, n_amostras, round(ganho, 2))
    if chave in _CACHE_NOTAS:
        return _CACHE_NOTAS[chave]

    if midi is None or n_amostras <= 0:
        arr = array.array("h", [0]) * max(1, n_amostras)
        _CACHE_NOTAS[chave] = arr
        return arr

    freq = midi_para_freq(midi)
    tau_f = math.tau * freq / TAXA_AMOSTRAGEM
    tau_vib = math.tau * 5.2 / TAXA_AMOSTRAGEM

    if timbre in ("cordas_quentes", "coral_sombrio", "cordas_orquestrais", "coral_mistico"):
        ataque = max(1, min(int(TAXA_AMOSTRAGEM * 0.045), n_amostras // 3))
    elif timbre in ("harpa_celta", "alaude_solo", "cravo_sombrio", "sino_cristal", "harpa_celestial"):
        ataque = max(1, int(TAXA_AMOSTRAGEM * 0.005))
    elif timbre == "timpano_epico":
        ataque = max(1, int(TAXA_AMOSTRAGEM * 0.003))
    else:
        ataque = max(1, min(int(TAXA_AMOSTRAGEM * 0.018), n_amostras // 4))

    release = max(1, min(int(TAXA_AMOSTRAGEM * 0.055), n_amostras // 3))
    inicio_rel = n_amostras - release

    amostras = array.array("h")
    ap = amostras.append

    for i in range(n_amostras):
        if i < ataque:
            env = i / ataque
        elif i > inicio_rel:
            env = (n_amostras - i) / release
        else:
            p = (i - ataque) / max(1, inicio_rel - ataque)
            if timbre in ("harpa_celta", "alaude_solo", "harpa_celestial"):
                env = math.exp(-p * 3.1)
            elif timbre == "cravo_sombrio":
                env = math.exp(-p * 2.5)
            elif timbre == "sino_cristal":
                env = math.exp(-p * 2.0)
            elif timbre == "timpano_epico":
                env = math.exp(-p * 3.8)
            else:
                env = 1.0 - 0.14 * p

        fase = i * tau_f
        vib = math.sin(i * tau_vib) * 0.11 if i > ataque * 2 else 0.0
        f = fase + vib

        if timbre == "flauta_doce":
            val = 0.80 * math.sin(f) + 0.14 * math.sin(2.0 * f) + 0.06 * math.sin(3.0 * f)
        elif timbre == "oboe_snes":
            val = (
                0.42 * math.sin(f)
                + 0.36 * math.sin(2.0 * f)
                + 0.16 * math.sin(3.0 * f)
                + 0.06 * math.sin(4.0 * f)
            )
        elif timbre == "violino_solo":
            val = (
                0.50 * math.sin(f)
                + 0.25 * math.sin(2.0 * f + 0.3)
                + 0.15 * math.sin(3.0 * f)
                + 0.10 * math.sin(4.0 * f)
            )
        elif timbre == "trompa_real":
            mod = 0.28 * math.sin(2.0 * f)
            val = (
                0.54 * math.sin(f + mod)
                + 0.26 * math.sin(2.0 * f)
                + 0.14 * math.sin(3.0 * f)
                + 0.06 * math.sin(5.0 * f)
            )
        elif timbre == "cordas_orquestrais":
            val = (
                0.46 * math.sin(fase)
                + 0.28 * math.sin(fase * 1.003 + 0.4)
                + 0.18 * math.sin(fase * 0.997 + 0.8)
                + 0.08 * math.sin(2.0 * fase)
            )
        elif timbre == "coral_mistico":
            val = (
                0.42 * math.sin(fase)
                + 0.30 * math.sin(fase * 1.005 + 0.6)
                + 0.18 * math.sin(fase * 0.995 + 1.2)
                + 0.10 * math.sin(3.0 * fase)
            )
        elif timbre == "harpa_celestial":
            val = (
                0.62 * math.sin(fase)
                + 0.24 * math.sin(2.0 * fase)
                + 0.14 * math.sin(4.0 * fase) * math.exp(-i / max(1, n_amostras * 0.28))
            )
        elif timbre == "timpano_epico":
            t_n = i / TAXA_AMOSTRAGEM
            val = (
                0.78 * math.sin(fase * (1.0 + 0.45 * math.exp(-t_n * 22.0)))
                + 0.22 * math.sin(0.5 * fase)
            )
        elif timbre == "orgao_sombrio":
            # Órgão de tubos gótico com sub-oitava e quinta
            val = (
                0.44 * math.sin(f)
                + 0.24 * math.sin(0.5 * f)
                + 0.18 * math.sin(2.0 * f)
                + 0.14 * math.sin(3.0 * f)
            )
        elif timbre == "coral_sombrio":
            # Vozes com leve detune (chorus natural)
            val = (
                0.46 * math.sin(fase)
                + 0.34 * math.sin(fase * 1.004 + 0.5)
                + 0.20 * math.sin(2.0 * fase)
            )
        elif timbre == "cordas_quentes":
            val = (
                0.52 * math.sin(fase)
                + 0.30 * math.sin(fase * 0.997 + 0.8)
                + 0.18 * math.sin(2.0 * fase)
            )
        elif timbre == "sino_cristal":
            val = (
                0.62 * math.sin(fase)
                + 0.24 * math.sin(2.0 * fase)
                + 0.14 * math.sin(5.0 * fase) * math.exp(-i / max(1, n_amostras * 0.35))
            )
        elif timbre == "harpa_celta":
            val = (
                0.68 * math.sin(fase)
                + 0.22 * math.sin(2.0 * fase)
                + 0.10 * math.sin(3.0 * fase) * math.exp(-i / max(1, n_amostras * 0.3))
            )
        elif timbre == "alaude_solo":
            val = (
                0.56 * math.sin(fase)
                + 0.28 * math.sin(2.0 * fase)
                + 0.16 * math.sin(3.0 * fase)
            )
        elif timbre == "cravo_sombrio":
            val = (
                0.45 * math.sin(fase)
                + 0.32 * math.sin(2.0 * fase)
                + 0.23 * math.sin(3.0 * fase)
            )
        elif timbre == "baixo":
            val = 0.70 * math.sin(fase) + 0.22 * math.sin(2.0 * fase) + 0.08 * math.sin(3.0 * fase)
        else:
            val = math.sin(fase)

        ap(int(val * env * ganho))

    _CACHE_NOTAS[chave] = amostras
    return amostras


def _sintetizar_percussao(tipo, n_amostras, ganho):
    """Sintetiza bateria 16-bits suave: B=Bumbo, S=Caixa, h=Shaker, T=Tímpano, C=Prato."""
    chave = (tipo, n_amostras, round(ganho, 2))
    if chave in _CACHE_BATERIA:
        return _CACHE_BATERIA[chave]

    if tipo not in ("B", "S", "h", "T", "C") or n_amostras <= 0:
        arr = array.array("h", [0]) * max(1, n_amostras)
        _CACHE_BATERIA[chave] = arr
        return arr

    rng = random.Random(ord(tipo) * 97)
    amostras = array.array("h")
    ap = amostras.append
    fase = 0.0
    ruido_ant = 0.0

    for i in range(n_amostras):
        t = i / TAXA_AMOSTRAGEM
        ruido_bruto = rng.uniform(-1.0, 1.0)
        # Filtro passa-baixa no ruído para soar quente como amostras de SNES
        ruido_suave = 0.55 * ruido_ant + 0.45 * ruido_bruto
        ruido_ant = ruido_suave

        if tipo == "B":
            env = math.exp(-t * 24.0)
            freq = 48.0 + 95.0 * math.exp(-t * 42.0)
            fase += math.tau * freq / TAXA_AMOSTRAGEM
            val = math.sin(fase) * env
        elif tipo == "T":
            # Tímpano orquestral grave
            env = math.exp(-t * 14.0)
            freq = 78.0 + 35.0 * math.exp(-t * 25.0)
            fase += math.tau * freq / TAXA_AMOSTRAGEM
            val = (0.82 * math.sin(fase) + 0.18 * ruido_suave) * env
        elif tipo == "S":
            env_ruido = math.exp(-t * 20.0)
            env_corpo = math.exp(-t * 34.0)
            fase += math.tau * 170.0 / TAXA_AMOSTRAGEM
            val = 0.65 * ruido_suave * env_ruido + 0.45 * math.sin(fase) * env_corpo
        elif tipo == "h":
            env = math.exp(-t * 48.0)
            val = (ruido_bruto - ruido_suave) * 0.65 * env
        else:  # "C"
            env = math.exp(-t * 8.5)
            val = (ruido_bruto - 0.5 * ruido_suave) * 0.55 * env

        ap(int(max(-1.0, min(1.0, val)) * ganho))

    _CACHE_BATERIA[chave] = amostras
    return amostras


def _montar_canal_notas(eventos, timbre, amostras_passo, total_amostras, ganho):
    canal = array.array("h")
    for nome_nota, passos in eventos:
        midi = nota_para_midi(nome_nota)
        dur = passos * amostras_passo
        canal.extend(_sintetizar_nota(timbre, midi, dur, ganho))
    while len(canal) < total_amostras:
        canal.extend(canal[: total_amostras - len(canal)])
    if len(canal) > total_amostras:
        del canal[total_amostras:]
    return canal


def sintetizar_bgm(nome_faixa):
    """Renderiza uma trilha completa da OST em 5 canais + Eco SPC700."""
    dados = PARTITURAS_OST.get(nome_faixa, PARTITURAS_OST["mundo"])
    bpm = dados["bpm"]
    amostras_passo = max(600, int(TAXA_AMOSTRAGEM * (60.0 / bpm) * 0.25))
    total_passos = sum(p for _, p in dados["melodia"])
    total_amostras = total_passos * amostras_passo

    c_melodia = _montar_canal_notas(
        dados["melodia"], dados["timbre_melodia"], amostras_passo, total_amostras, 7200
    )
    c_contra = _montar_canal_notas(
        dados["contra"], dados["timbre_contra"], amostras_passo, total_amostras, 4200
    )
    c_harmonia = _montar_canal_notas(
        dados["harmonia"], dados["timbre_harmonia"], amostras_passo, total_amostras, 4600
    )
    c_baixo = _montar_canal_notas(
        dados["baixo"], "baixo", amostras_passo, total_amostras, 5800
    )

    padrao_bat = dados["bateria"]
    c_bateria = array.array("h")
    while len(c_bateria) < total_amostras:
        for ch in padrao_bat:
            c_bateria.extend(_sintetizar_percussao(ch, amostras_passo, 3400))
            if len(c_bateria) >= total_amostras:
                break
    if len(c_bateria) > total_amostras:
        del c_bateria[total_amostras:]

    # Eco / Delay circular estilo SNES SPC700 (3 passos de semicolcheia = delay pontilhado)
    fator_eco = dados.get("eco", 0.28)
    atraso = 3 * amostras_passo
    if fator_eco > 0 and total_amostras > atraso:
        eco_mel = c_melodia[-atraso:] + c_melodia[:-atraso]
        eco_har = c_harmonia[-atraso:] + c_harmonia[:-atraso]
        mix = array.array(
            "h",
            (
                max(-32700, min(32700, m + c + h + b + d + int((em + eh) * fator_eco)))
                for m, c, h, b, d, em, eh in zip(
                    c_melodia, c_contra, c_harmonia, c_baixo, c_bateria, eco_mel, eco_har
                )
            ),
        )
    else:
        mix = array.array(
            "h",
            (
                max(-32700, min(32700, s))
                for s in map(sum, zip(c_melodia, c_contra, c_harmonia, c_baixo, c_bateria))
            ),
        )

    return pygame.mixer.Sound(buffer=mix)


# =====================================================================
# Síntese de Efeitos Sonoros (SFX) 16-Bits
# =====================================================================
def _gerar_sfx_varredura(f_ini, f_fim, duracao, forma="pulso", ruido=0.0, ganho=14000):
    n = max(1, int(TAXA_AMOSTRAGEM * duracao))
    arr = array.array("h")
    rng = random.Random(int(f_ini * 13 + f_fim * 7))
    fase = 0.0
    for i in range(n):
        p = i / n
        env = (1.0 - p) ** 1.35
        freq = f_ini + (f_fim - f_ini) * p
        fase += math.tau * freq / TAXA_AMOSTRAGEM
        if forma == "pulso":
            onda = 0.8 if math.sin(fase) >= 0 else -0.8
        elif forma == "tri":
            onda = (2.0 / math.pi) * math.asin(math.sin(fase))
        else:
            onda = math.sin(fase)
        if ruido > 0:
            onda = (1.0 - ruido) * onda + ruido * rng.uniform(-1.0, 1.0)
        arr.append(int(max(-1.0, min(1.0, onda * env)) * ganho))
    return pygame.mixer.Sound(buffer=arr)


def _gerar_sfx_notas(notas_dur, timbre="sino_cristal", ganho=13500):
    arr = array.array("h")
    for nome_nota, dur in notas_dur:
        n = max(1, int(TAXA_AMOSTRAGEM * dur))
        arr.extend(_sintetizar_nota(timbre, nota_para_midi(nome_nota), n, ganho))
    return pygame.mixer.Sound(buffer=arr)


def construir_banco_sfx():
    """Cria todos os efeitos sonoros 16-bits do jogo, integrando assets de áudio opcionais."""
    banco = {
        "espada": _gerar_sfx_varredura(540, 145, 0.11, "pulso", ruido=0.45, ganho=13500),
        "hit_inimigo": _gerar_sfx_varredura(240, 75, 0.12, "pulso", ruido=0.35, ganho=15000),
        "morte_inimigo": _gerar_sfx_varredura(380, 90, 0.22, "tri", ruido=0.40, ganho=14500),
        "dano_jogador": _gerar_sfx_varredura(310, 105, 0.20, "pulso", ruido=0.30, ganho=16000),
        "pulo": _gerar_sfx_varredura(210, 560, 0.13, "tri", ruido=0.0, ganho=12500),
        "pouso": _gerar_sfx_varredura(130, 55, 0.07, "tri", ruido=0.35, ganho=9500),
        "nado": _gerar_sfx_varredura(260, 420, 0.12, "seno", ruido=0.45, ganho=9500),
        "dash": _gerar_sfx_varredura(420, 160, 0.14, "tri", ruido=0.55, ganho=12500),
        "arbusto": _gerar_sfx_varredura(620, 220, 0.09, "seno", ruido=0.65, ganho=10500),
        "porta": _gerar_sfx_notas([("C4", 0.06), ("G4", 0.09)], "harpa_celta", ganho=12000),
        "coracao": _gerar_sfx_notas([("E5", 0.07), ("A5", 0.13)], "sino_cristal", ganho=13500),
        "level_up": _gerar_sfx_notas(
            [("C5", 0.09), ("E5", 0.09), ("G5", 0.09), ("C6", 0.24)],
            "trompa_real",
            ganho=14500,
        ),
        "magia_fogo": _gerar_sfx_varredura(480, 130, 0.24, "pulso", ruido=0.50, ganho=14500),
        "magia_gelo": _gerar_sfx_notas(
            [("E5", 0.06), ("B5", 0.06), ("E6", 0.14)], "sino_cristal", ganho=14000
        ),
        "magia_raio": _gerar_sfx_varredura(920, 140, 0.26, "pulso", ruido=0.60, ganho=15500),
        "magia_cura": _gerar_sfx_notas(
            [("F5", 0.08), ("A5", 0.08), ("C6", 0.18)], "sino_cristal", ganho=13500
        ),
        "magia_corte": _gerar_sfx_varredura(720, 180, 0.20, "pulso", ruido=0.40, ganho=14500),
        "menu_mover": _gerar_sfx_notas([("G5", 0.035)], "harpa_celta", ganho=9500),
        "menu_confirmar": _gerar_sfx_notas([("C5", 0.045), ("G5", 0.075)], "sino_cristal", ganho=11500),
        "menu_voltar": _gerar_sfx_notas([("G5", 0.045), ("C5", 0.075)], "harpa_celta", ganho=10500),
        "dialogo_bip": _gerar_sfx_notas([("E5", 0.022)], "flauta_doce", ganho=6500),
        "salvar": _gerar_sfx_notas(
            [("C5", 0.07), ("E5", 0.07), ("G5", 0.07), ("B5", 0.07), ("C6", 0.28)],
            "sino_cristal",
            ganho=14500,
        ),
        "rugido_chefe": _gerar_sfx_varredura(180, 50, 0.45, "pulso", ruido=0.75, ganho=16000),
        "laser": _gerar_sfx_varredura(980, 240, 0.28, "pulso", ruido=0.35, ganho=14500),
        "impacto_pesado": _gerar_sfx_varredura(140, 40, 0.35, "tri", ruido=0.65, ganho=16500),
        "cristal_quebra": _gerar_sfx_notas(
            [("G6", 0.04), ("D6", 0.05), ("A5", 0.07), ("E5", 0.12)],
            "sino_cristal",
            ganho=14000,
        ),
        "bloqueio": _gerar_sfx_varredura(190, 80, 0.18, "pulso", ruido=0.35, ganho=14000),
        "logo_bossbyte": _gerar_sfx_notas(
            [("D4", 0.05), ("A4", 0.05), ("D5", 0.07), ("F#5", 0.10), ("A5", 0.26)],
            "trompa_real",
            ganho=15000,
        ),
        "logo_pygame": _gerar_sfx_notas(
            [("C5", 0.06), ("E5", 0.06), ("G5", 0.06), ("C6", 0.22)],
            "sino_cristal",
            ganho=13000,
        ),
        "logo_antigravity": _gerar_sfx_notas(
            [("D5", 0.07), ("A5", 0.07), ("D6", 0.08), ("A6", 0.26)],
            "sino_cristal",
            ganho=14000,
        ),
        "logo_claude": _gerar_sfx_notas(
            [("E5", 0.07), ("G#5", 0.07), ("B5", 0.08), ("E6", 0.28)],
            "harpa_celta",
            ganho=14500,
        ),
        "moeda": _gerar_sfx_notas([("B5", 0.035), ("E6", 0.075)], "sino_cristal", ganho=13500),
        "bau_abrir": _gerar_sfx_notas([("C4", 0.04), ("E4", 0.05), ("A4", 0.12)], "harpa_celta", ganho=14000),
        "fanfarra_item": _gerar_sfx_notas(
            [("C5", 0.08), ("E5", 0.08), ("G5", 0.08), ("C6", 0.32)],
            "trompa_real",
            ganho=15000,
        ),
        "pedra_arrastar": _gerar_sfx_varredura(110, 85, 0.22, "tri", ruido=0.60, ganho=12000),
        "explosao_bomba": _gerar_sfx_varredura(160, 35, 0.35, "pulso", ruido=0.85, ganho=16500),
        "escudo_bloqueio": _gerar_sfx_notas([("G5", 0.04), ("D6", 0.09)], "sino_cristal", ganho=15000),
        "compra": _gerar_sfx_notas([("C5", 0.05), ("G5", 0.05), ("C6", 0.12)], "sino_cristal", ganho=13500),
        "teleporte": _gerar_sfx_notas(
            [("C5", 0.05), ("E5", 0.05), ("G5", 0.05), ("B5", 0.06), ("E6", 0.28)],
            "sino_cristal",
            ganho=14500,
        ),
        "quebrar_vaso": _gerar_sfx_varredura(780, 140, 0.15, "pulso", ruido=0.80, ganho=14500),
        "ativar_monolito": _gerar_sfx_notas(
            [("D5", 0.08), ("A5", 0.08), ("D6", 0.12), ("F#6", 0.32)],
            "sino_cristal",
            ganho=15000,
        ),
        "gong_chefe": _gerar_sfx_varredura(140, 42, 0.65, "pulso", ruido=0.55, ganho=17000),
        "eco_fantasma": _gerar_sfx_notas(
            [("E4", 0.12), ("B4", 0.14), ("E5", 0.30)],
            "harpa_celta",
            ganho=12000,
        ),
        # Micro-sonorização adaptativa por terreno (Passos)
        "passo_grama": _gerar_sfx_varredura(260, 110, 0.05, "seno", ruido=0.65, ganho=5400),
        "passo_pedra": _gerar_sfx_varredura(440, 150, 0.04, "pulso", ruido=0.40, ganho=6800),
        "passo_agua": _gerar_sfx_varredura(220, 390, 0.07, "seno", ruido=0.55, ganho=6200),
        "passo_areia": _gerar_sfx_varredura(310, 115, 0.06, "tri", ruido=0.75, ganho=5800),
        "passo_madeira": _gerar_sfx_varredura(210, 90, 0.05, "tri", ruido=0.30, ganho=6500),
        # Feedback de combate avançado & Soulslike
        "exaustao": _gerar_sfx_varredura(340, 130, 0.28, "seno", ruido=0.80, ganho=8500),
        "parry_perfeito": _gerar_sfx_notas(
            [("D6", 0.04), ("A6", 0.08), ("D7", 0.22)], "sino_cristal", ganho=16500
        ),
        "riposte": _gerar_sfx_varredura(540, 80, 0.32, "pulso", ruido=0.60, ganho=17000),
        "alerta_perigo": _gerar_sfx_notas(
            [("F#6", 0.06), ("F#6", 0.12)], "sino_cristal", ganho=14000
        ),
    }

    # Sobrescreve com arquivos de áudio dedicados de alta fidelidade se presentes
    pasta_sfx = DIR_AUDIO_ASSETS / "sfx"
    if pasta_sfx.exists():
        for arq in pasta_sfx.iterdir():
            if arq.is_file() and arq.suffix.lower() in (".ogg", ".wav", ".mp3"):
                try:
                    banco[arq.stem] = pygame.mixer.Sound(str(arq))
                except Exception:
                    pass

    return banco


# =====================================================================
# Regras de Audio Ducking Dinâmico (skills/game-audio/SKILL.md)
# Atenua dinamicamente a BGM para destacar eventos críticos e SFX pesados.
# Formato: {nome_sfx: (fator_volume_bgm, duracao_segundos)}
# =====================================================================
SFX_DUCKING_REGRAS = {
    # Rugidos de chefes e gongos épicos
    "rugido_chefe": (0.30, 1.25),
    "gong_chefe": (0.35, 1.10),
    "morte_inimigo": (0.50, 0.70),
    "impacto_pesado": (0.45, 0.50),
    "explosao_bomba": (0.40, 0.85),
    "quebrar_vaso": (0.65, 0.35),
    "cristal_quebra": (0.55, 0.40),
    # Fanfarras, teleporte e level up
    "fanfarra_item": (0.25, 2.20),
    "level_up": (0.35, 1.40),
    "ativar_monolito": (0.35, 1.50),
    "teleporte": (0.40, 1.20),
    # Magias e combate avançado
    "magia_raio": (0.50, 0.65),
    "magia_fogo": (0.60, 0.50),
    "magia_corte": (0.55, 0.45),
    "magia_gelo": (0.55, 0.50),
    "escudo_bloqueio": (0.60, 0.35),
    "parry_perfeito": (0.35, 0.65),
    "riposte": (0.28, 0.85),
    "alerta_perigo": (0.45, 0.40),
}


# =====================================================================
# Gerenciador Principal de Áudio (OST + SFX)
# =====================================================================
class SistemaAudio:
    def __init__(self, cfg):
        self.cfg = cfg
        self.ativo = False
        self.faixa_atual = None
        self.modo_jukebox = False
        self._cache_bgm = {}
        self._sfx = {}
        self._canal_bgm = None
        self._cooldown_sfx = {}
        self.fator_ducking = 1.0
        self._duck_alvo = 1.0
        self._tempo_duck = 0.0
        self.duck_dialogo = False
        self._vol_bgm_base = 0.7

        try:
            atual = pygame.mixer.get_init()
            if atual is None or atual[0] != TAXA_AMOSTRAGEM or atual[2] != 1:
                if atual is not None:
                    pygame.mixer.quit()
                pygame.mixer.init(frequency=TAXA_AMOSTRAGEM, size=-16, channels=1, buffer=1024)
            pygame.mixer.set_num_channels(16)
            self._canal_bgm = pygame.mixer.Channel(0)
            self._sfx = construir_banco_sfx()
            self.ativo = True
            self.aplicar_volumes()
        except pygame.error:
            self.ativo = False

    def aplicar_volumes(self):
        if not self.ativo:
            return
        self._vol_bgm_base = max(0.0, min(1.0, self.cfg.get("volume_bgm", 70) / 100.0))
        vol_sfx = max(0.0, min(1.0, self.cfg.get("volume_sfx", 80) / 100.0))
        if self._canal_bgm is not None:
            self._canal_bgm.set_volume(self._vol_bgm_base * self.fator_ducking)
        for som in self._sfx.values():
            som.set_volume(vol_sfx)

    def aplicar_ducking(self, fator=0.5, duracao=0.6):
        """Abaixa dinamicamente o volume da BGM para dar destaque a um evento/SFX."""
        self._duck_alvo = min(self._duck_alvo, fator)
        self._tempo_duck = max(self._tempo_duck, duracao)

    def atualizar(self, dt):
        """Atualiza a transição suave de ducking do canal de BGM."""
        if not self.ativo:
            return

        if self._tempo_duck > 0:
            self._tempo_duck = max(0.0, self._tempo_duck - dt)
            alvo = self._duck_alvo
            if self._tempo_duck <= 0:
                self._duck_alvo = 1.0
        else:
            alvo = 1.0

        if self.duck_dialogo:
            alvo = min(alvo, 0.68)

        # Attack rápido (15.0) para resposta imediata ao impacto, release suave (3.5)
        taxa = 15.0 if alvo < self.fator_ducking else 3.5
        self.fator_ducking += (alvo - self.fator_ducking) * min(1.0, dt * taxa)
        if self._canal_bgm is not None:
            self._canal_bgm.set_volume(self._vol_bgm_base * self.fator_ducking)

    def tocar_bgm(self, nome_faixa, forcar=False):
        """Inicia ou troca a música de fundo (BGM) com cache em memória."""
        if nome_faixa not in PARTITURAS_OST:
            nome_faixa = "mundo"
        if self.modo_jukebox and not forcar:
            return False
        if self.faixa_atual == nome_faixa and self._canal_bgm and self._canal_bgm.get_busy():
            return False

        self.faixa_atual = nome_faixa
        if not self.ativo or self._canal_bgm is None:
            return True

        if nome_faixa not in self._cache_bgm:
            arq_custom = _buscar_arquivo_audio("bgm", nome_faixa)
            if arq_custom is not None:
                try:
                    self._cache_bgm[nome_faixa] = pygame.mixer.Sound(str(arq_custom))
                except Exception:
                    self._cache_bgm[nome_faixa] = sintetizar_bgm(nome_faixa)
            else:
                self._cache_bgm[nome_faixa] = sintetizar_bgm(nome_faixa)

        som = self._cache_bgm[nome_faixa]
        self._vol_bgm_base = max(0.0, min(1.0, self.cfg.get("volume_bgm", 70) / 100.0))
        self._canal_bgm.set_volume(self._vol_bgm_base * self.fator_ducking)
        loops = 0 if nome_faixa == "derrota" else -1
        self._canal_bgm.play(som, loops=loops, fade_ms=380)
        return True

    def tocar_bgm_mapa(self, nome_arquivo_mapa):
        """Escolhe automaticamente a BGM correspondente ao mapa."""
        tema = MAPA_PARA_BGM.get(nome_arquivo_mapa, "mundo")
        return self.tocar_bgm(tema)

    def sfx(self, nome):
        """Toca um efeito sonoro 16-bits respeitando intervalo e disparando ducking."""
        # Aciona ducking dinâmico caso haja regra para este som
        if nome in SFX_DUCKING_REGRAS:
            fator, dur = SFX_DUCKING_REGRAS[nome]
            self.aplicar_ducking(fator, dur)

        if not self.ativo or nome not in self._sfx:
            return
        if self.cfg.get("volume_sfx", 80) <= 0:
            return
        agora = pygame.time.get_ticks() / 1000.0
        min_intervalo = 0.045 if nome == "dialogo_bip" else 0.03
        if agora - self._cooldown_sfx.get(nome, 0.0) < min_intervalo:
            return
        self._cooldown_sfx[nome] = agora

        canal = pygame.mixer.find_channel(False)
        if canal is not None and canal != self._canal_bgm:
            canal.play(self._sfx[nome])
        else:
            self._sfx[nome].play()
