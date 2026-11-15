"""Pixel art dos personagens em estilo 16-Bits JRPG (32x32).

Cada personagem é montado em camadas: pernas + corpo + cabeça + acessórios
(capas, ombreiras, chapéus, elmos, cajados, escudos).
O contorno escuro e o sombreamento de volume são aplicados automaticamente.
"""
import pygame

QUADRO = 32
QUADROS_POR_LINHA = 11
CONTORNO = (26, 18, 34)

# Paleta base expandida com tons de luz, meio-tom e sombra profunda 16-bits
PALETA_BASE = {
    ".": None,
    "k": CONTORNO,            # contorno / linhas escuras internas
    "s": (254, 218, 182),     # pele luz
    "S": (228, 172, 132),     # pele sombra
    "d": (196, 134, 96),      # pele sombra profunda (queixo/pescoço)
    "e": (32, 26, 48),        # cílios / pupila escura
    "u": (58, 128, 225),      # íris do olho (azul brilhante no herói)
    "w": (255, 255, 255),     # brilho especular (olhos / joias)
    "r": (246, 152, 148),     # rubor nas bochechas
    "R": (192, 92, 92),       # boca
    "h": (146, 84, 44),       # cabelo tom médio
    "H": (96, 50, 26),        # cabelo sombra
    "i": (208, 142, 78),      # cabelo brilho (mechas iluminadas)
    "c": (52, 98, 192),       # túnica / traje cor principal
    "C": (32, 60, 134),       # traje sombra
    "v": (96, 148, 235),      # traje luz
    "a": (244, 242, 232),     # tecido claro / barba / avental
    "A": (194, 198, 212),     # tecido claro sombra
    "b": (132, 78, 40),       # couro / cinto / bainha
    "B": (84, 48, 24),        # couro sombra
    "y": (248, 206, 72),      # ouro / fivela / bordado
    "Y": (188, 134, 34),      # ouro sombra
    "p": (64, 58, 92),        # calça
    "P": (42, 36, 62),        # calça sombra
    "o": (124, 72, 38),       # botas
    "O": (78, 44, 22),        # botas sombra
    "m": (192, 200, 218),     # aço / armadura
    "M": (124, 132, 156),     # aço sombra
    "n": (242, 248, 255),     # aço brilho intenso
    "f": (224, 54, 58),       # cachecol / capa / pluma vermelha
    "F": (152, 28, 38),       # cachecol / capa sombra
    "g": (88, 218, 255),      # cristal / gema de mana
    "G": (38, 128, 212),      # cristal sombra
    "t": (162, 104, 54),      # madeira / cajado
    "T": (104, 62, 30),       # madeira sombra
}


def _parte(linhas, x, y, atras=False, tipo="outro"):
    return {"linhas": linhas, "x": x, "y": y, "atras": atras, "tipo": tipo}


def cabeca(linhas, pad=0):
    """Cabeça de 16 de largura, com `pad` colunas extras à esquerda; queixo na linha 16."""
    return _parte(linhas, 8 - pad, 17 - len(linhas), tipo="cabeca")


def corpo(linhas):
    return _parte(linhas, 8, 17, tipo="corpo")


def pernas(linhas):
    return _parte(linhas, 8, 26)


def extra(linhas, x, y, atras=False):
    return _parte(linhas, x, y, atras)


# ================================================================ pernas e botas 16-bits
PERNAS_FRENTE_PARADO = [
    "...ppppP..Ppppp...",
    "...pppPP..PPppp...",
    "...yyyY....Yyyy...",
    "..ooooOO..OOoooo..",
    "..oOOOOO..OOOOOo..",
]
PERNAS_FRENTE_PASSO_E1 = [
    "...ppppP..Ppppp...",
    "..ppppP...PPppp...",
    "..ooooOO..Ppppp...",
    "..oOOOOO..OOoooo..",
    "..........OOOOOo..",
]
PERNAS_FRENTE_PASSO_E2 = [
    "...ppppP..Ppppp...",
    "...yyyY...PPppp...",
    "..ooooOO..Ppppp...",
    "..oOOOOO..OOoooo..",
    "..........OOOOOo..",
]
PERNAS_FRENTE_PASSO_D1 = [
    "...ppppP..Ppppp...",
    "...pppPP...Ppppp..",
    "...pppPP..OOoooo..",
    "..ooooOO..OOOOOo..",
    "..oOOOOO..........",
]
PERNAS_FRENTE_PASSO_D2 = [
    "...ppppP..Ppppp...",
    "...pppPP...yyyY...",
    "...pppPP..OOoooo..",
    "..ooooOO..OOOOOo..",
    "..oOOOOO..........",
]
PERNAS_LADO_PARADO = [
    ".....ppppPP.......",
    ".....ppppPP.......",
    ".....yyyyYY.......",
    ".....oooooOO......",
    ".....oOOOOOO......",
]
PERNAS_LADO_PASSO_A1 = [
    "....pppppppP......",
    "...pPpp..pppP.....",
    "...oooO...yyyY....",
    "..oOOO....oooooO..",
    "..........oOOOOO..",
]
PERNAS_LADO_PASSO_A2 = [
    "....pppppppP......",
    "...pPpp..pppP.....",
    "..yyyY....pppP....",
    ".ooooO....oooooO..",
    ".oOOOO....oOOOOO..",
]
PERNAS_LADO_PASSO_B1 = [
    "....pppppppP......",
    "...pppP..pPpp.....",
    "..yyyY...oooO.....",
    ".oooooO..oOOO.....",
    ".oOOOOO...........",
]
PERNAS_LADO_PASSO_B2 = [
    "....pppppppP......",
    "...pppP..pPpp.....",
    "..pppP....yyyY....",
    ".oooooO...ooooO...",
    ".oOOOOO...oOOOO...",
]

PERNAS_FRENTE = [
    PERNAS_FRENTE_PASSO_E1,
    PERNAS_FRENTE_PASSO_E2,
    PERNAS_FRENTE_PARADO,
    PERNAS_FRENTE_PASSO_D1,
    PERNAS_FRENTE_PASSO_D2,
    PERNAS_FRENTE_PARADO,
    PERNAS_FRENTE_PARADO,
    PERNAS_FRENTE_PARADO,
    PERNAS_FRENTE_PASSO_D1,
    PERNAS_FRENTE_PASSO_E2,
    PERNAS_FRENTE_PASSO_E1,
]
PERNAS_COSTAS = [
    PERNAS_FRENTE_PASSO_D1,
    PERNAS_FRENTE_PASSO_D2,
    PERNAS_FRENTE_PARADO,
    PERNAS_FRENTE_PASSO_E1,
    PERNAS_FRENTE_PASSO_E2,
    PERNAS_FRENTE_PARADO,
    PERNAS_FRENTE_PARADO,
    PERNAS_FRENTE_PARADO,
    PERNAS_FRENTE_PASSO_E1,
    PERNAS_FRENTE_PASSO_D2,
    PERNAS_FRENTE_PASSO_D1,
]
PERNAS_LADO = [
    PERNAS_LADO_PASSO_A1,
    PERNAS_LADO_PASSO_A2,
    PERNAS_LADO_PARADO,
    PERNAS_LADO_PASSO_B1,
    PERNAS_LADO_PASSO_B2,
    PERNAS_LADO_PARADO,
    PERNAS_LADO_PARADO,
    PERNAS_LADO_PARADO,
    PERNAS_LADO_PASSO_B1,
    PERNAS_LADO_PASSO_A2,
    PERNAS_LADO_PASSO_A1,
]

# Corrige largura para 16 colunas nas grades de pernas frontais
PERNAS_FRENTE = [[l[1:17] if len(l) == 18 else l for l in q] for q in PERNAS_FRENTE]
PERNAS_COSTAS = [[l[1:17] if len(l) == 18 else l for l in q] for q in PERNAS_COSTAS]
PERNAS_LADO = [[l[1:17] if len(l) == 18 else l for l in q] for q in PERNAS_LADO]


# ================================================================ 1. HERÓI (Aventureiro com bandana, cachecol rubro e ombreiras)
HEROI_FRENTE = [
    "...hhhiihhhhh...",
    "..hhiihhhhhihh..",
    ".hhiihhhhhhhhhH.",
    "hhhhhHhhhhHhhhHH",
    "hffffffffffFffHH",
    "hfyyfssssssffFHH",
    "hhHssHssssHssHHH",
    "hsssewsssssewsSh",
    "hssseessssseesSh",
    "hsssuusssssuusSh",
    ".ssrssssssssrss.",
    ".SsssssRRsssssS.",
    "..dSssssssssSd..",
]
HEROI_COSTAS = [
    "...hhhiihhhhh...",
    "..hhiihhhhhihh..",
    ".hhiihhhhhhhhhH.",
    "hhhhhhhhhhhhhhHH",
    "hffffffffffffFHH",
    "hFFFFFFFFFFFFfHH",
    "hhhhhhhhhhhhFFHH",
    "hHhhhhhhhhhhfFHH",
    "hHhhhHhhhhHhFFHH",
    "hHhhHHhhhhHHhHHH",
    ".hHhHHhhhhHHhHH.",
    ".sHHhHhhhhHhHHs.",
    "..dSssssssssSd..",
]
HEROI_LADO = [
    "..hhhhiihhhh....",
    ".hhhhiihhhhhh...",
    "hhhhhihhhhhhhh..",
    "Hhhhhhhhhhhhhhh.",
    "FFfffffffffffffh",
    "Fffhhhhhhhhssffh",
    "HHhhhhhhhHsssssh",
    "HHhhhSssssssewss",
    "HHhhhsssssssesss",
    "HHHhhsssssssuuss",
    ".HHhhsssssssssrs",
    "..HHhSssssssRss.",
    "...HHdSsssssSd..",
]
TUNICA_FRENTE = [
    "...ffffYYffff...",
    ".mMffcvssvcffMm.",
    ".bBckbccccvckBb.",
    ".vckcvbccccCkCC.",
    ".vckcccbyycckCC.",
    ".bbkbbbbyybbkBB.",
    ".sskccccyccCkSS.",
    "..vvcccCycccCC..",
    "..CCCCCYCCCCCC..",
]
TUNICA_COSTAS = [
    "...ffffffffff...",
    ".mMffffffffFfMm.",
    ".bBckffffffFkBb.",
    ".vckcffffffFkCC.",
    ".vckccffffFFkCC.",
    ".bbkbbbbbbbbkBB.",
    ".sskcccccccckSS.",
    "..vvcccCccccCC..",
    "..CCCCCCCCCCCC..",
]
TUNICA_LADO = [
    "...ffffffff.....",
    "..mMffccccvss...",
    "..bBffcckbgcC...",
    "...vvcckbbccC...",
    "...bbbbkyybbB...",
    "...cccckssCcC...",
    "...vvcckSSccC...",
    "..vvccCcccCcC...",
    "..CCCCCCCCCCC...",
]


# ================================================================ 2. ALDEÃO / MERCADOR (Boina, bigode simpático, colete bordado)
ALDEAO_FRENTE = [
    "...cccccccccc...",
    "..ccvvccccccCC..",
    ".ccvvccccccccCC.",
    ".CCCCCCCCCCCCCC.",
    ".yyyyyyyyyyyyYY.",
    "hhHssssssssssHhh",
    "hhsewssssssewshh",
    "hhseesssssseeshh",
    "hhsrssssssssrshh",
    ".shhhhhhhhhhhhs.",
    ".sHhhhRRRRhhhHs.",
    "..dSssssssssSd..",
]
ALDEAO_COSTAS = [
    "...cccccccccc...",
    "..ccvvccccccCC..",
    ".ccvvccccccccCC.",
    ".CCCCCCCCCCCCCC.",
    ".yyyyyyyyyyyyYY.",
    "hhhhhhhhhhhhhhHH",
    "hHhhhhhhhhhhhHHH",
    "hHhhHhhhhHhhhHHH",
    ".hHhHHhhhHHhhHH.",
    ".sHHhHhhHhHHHHs.",
    "..dSssssssssSd..",
    "................",
]
ALDEAO_LADO = [
    "..cccccccccc....",
    ".ccvvcccccccc...",
    "ccvvcccccccccc..",
    "CCCCCCCCCCCCCC..",
    ".Yyyyyyyyyyyyy..",
    "HHhhhhhSsssssss.",
    "HHhhhhhsssssewss",
    "HHhhhhhsssssesss",
    "HHHhhhhssssssrss",
    ".HHhhhhsssshhhhh",
    "..HHhSsssssRhhh.",
    "...HHdSsssssSd..",
]
COLETE_FRENTE = [
    "....aaAssAaa....",
    ".aaAbbbyybbbAaA.",
    ".aakbBaaaaBbkAA.",
    ".aakbBaaaaBbkAA.",
    ".aakbbbyybbbkAA.",
    ".sskBbaaaabBkSS.",
    ".SS.bBaaaaBb.SS.",
    "...bbBaaaaBbb...",
    "...BBBAAAABBB...",
]
COLETE_COSTAS = [
    "....aaaaaaaa....",
    ".aaAbbbbbbbbAaA.",
    ".aakbbbbbbbbkAA.",
    ".aakbbbbbbBBkAA.",
    ".aakbbbbbbbbkAA.",
    ".sskbbbbbbBBkSS.",
    ".SS.bbbbbbbb.SS.",
    "...bbBbbbbBbb...",
    "...BBBBBBBBBB...",
]
COLETE_LADO = [
    "....aaaAss......",
    "...bbbaaaccaa...",
    "...bbbaAAccaa...",
    "...bbbkssccaa...",
    "...bbbbSScaaa...",
    "...bbBbaacaaa...",
    "..bbbbBaaaaaa...",
    "..bbbBbbbbBaa...",
    "..BBBBBBBBAAA...",
]


# ================================================================ 3. ALDEÃ / SACERDOTISA (Tiara floral, tranças e vestido detalhado)
RABO = [
    ".ff.",
    "fggf",
    "hhih",
    "hihH",
    "hhhH",
    ".hhH",
    ".hHH",
    ".hHH",
    "..hH",
    "..hH",
    "...H",
]
ALDEA_FRENTE_BASE = [
    "...hhhhiihhhh...",
    "..hhhhhiihhhhh..",
    ".hffffgyygffffh.",
    ".hhhhhhhhhhhhhH.",
    "hhhhhhhHhhhhhhHH",
    "hhHsssHhhsssHhHH",
    "hHsssssssssssshH",
    "hHsewssssssewsHH",
    "hHseesssssseesHH",
    "hHsuussssssuusHH",
    "hHsrssssssssrsHH",
    "hHsssssRRssssSHH",
    ".hHdSssssssSdHH.",
]
ALDEA_COSTAS_BASE = [
    "...hhhhiihhhh...",
    "..hhhhhiihhhhh..",
    ".hffffffffffffh.",
    ".hhhhhhhhhhhhhH.",
    "hhhhhhhhhhhhhhHH",
    "hhhhhhhhhhhhhhHH",
    "hhhhhhhhhhhhhHHH",
    "hHhhhhhhhhhhhHHH",
    "hHhhhhHhhhhhHHHH",
    "hHhhhHHhhhhHHHHH",
    "hHhHhHhhHhHhHHHH",
    "hHhHhHhhHhHhHHHH",
    ".HHSdssssssdHHH.",
]
ALDEA_LADO_BASE = [
    "..hhhhhiihhh....",
    ".hhhhhhiihhhhh..",
    "hffffffgyyffffh.",
    "hhhhhhhhhhhhhhh.",
    "Hhhhhhhhhhhhhhhh",
    "HHhhhhhhhHssHssh",
    "HHhhhhSsssssssss",
    "HHhhhhsssssssews",
    "HHhhhhsssssssess",
    "HHhhhhsssssssuus",
    "HHhhhhssssssssrs",
    "HHHhhhSssssssRs.",
    ".HHHhhdSssssSd..",
]


def _com_rabo(base, lado_esquerdo=False):
    """Junta a cabeça (16 col.) com o laço/rabo de cavalo."""
    rabo = [r[::-1] for r in RABO] if lado_esquerdo else RABO
    linhas = []
    for i in range(len(base) + 2):
        cab = base[i - 2] if i >= 2 else "." * 16
        r = rabo[i] if i < len(rabo) else "...."
        if i in (3, 4):
            cab = ("g" + cab[1:]) if lado_esquerdo else (cab[:-1] + "g")
        linhas.append((r + cab + "....") if lado_esquerdo else ("...." + cab + r))
    return linhas


VESTIDO_FRENTE = [
    "....aaAssAaa....",
    ".aaAccyssyccAaA.",
    ".aakccyaaycckAA.",
    ".sskccyaaycckSS.",
    ".SScyyyyyyyycSS.",
    "..vcccaaaaaaccC.",
    ".vvcccaaaaaaccCC",
    ".vccCayyyyyyaCCC",
    ".CCCCAAAAAAACCCC",
]
VESTIDO_COSTAS = [
    "....aaaaaaaa....",
    ".aaAccccccccAaA.",
    ".aakcccaaccckAA.",
    ".sskcccaaccckSS.",
    ".SScyyyyyyyycSS.",
    "..vccccccccccC..",
    ".vvcccccccccccCC",
    ".vccCcyyyyyyccCC",
    ".CCCCCCCCCCCCCCC",
]
VESTIDO_LADO = [
    "....aaaAss......",
    "...cccaaaccaa...",
    "...cccaAAccaa...",
    "...ccckssccaa...",
    "...yyyySSyyyy...",
    "..vcccccccaaa...",
    ".vvcccccccaaaa..",
    ".vccCcyyyyccaAa.",
    ".CCCCCCCCCCAAAA.",
]


# ================================================================ 4. MAGO / SÁBIO (Chapéu arcano estrelado, barba longa prateada, cajado)
CHAPEU_FRENTE = [
    "...................yY",
    ".................ccyC",
    "............cvccccC",
    "..........cvcyccccC",
    ".........cvccccccC",
    "........cvccyccccCC",
    "......yyyyyyyyyyyyY",
    "..cvcccccccccccccccccCCC",
    "..CCCCCCCCCCCCCCCCCCCCCC",
]
CHAPEU_LADO = [
    "...Yy",
    "...Cycc",
    "......Ccccvc",
    "......CCccycvc",
    "......CCcccccvc",
    ".....CCccccyccvc",
    "....Yyyyyyyyyyyyy",
    ".CCCcccccccccccccccccvcc",
    ".CCCCCCCCCCCCCCCCCCCCCCC",
]
MAGO_ROSTO_FRENTE = [
    "aaASSSSSSSSSSAaa",
    "aassssssssssssaa",
    "aasewssssssewsaa",
    "aaseesssssseesaa",
    "Aasrssssssssrsaa",
    ".aawwwwwwwwwwaa.",
    "..aaaaaaaaaaaa..",
]
MAGO_NUCA = [
    "hhihhhhhihhhhhHH",
    "hihhHhhhihhHhhHH",
    "hhhhHhhhhhhHhHHH",
    "hHhhHhhhHhhHhHHH",
    ".hHhHHhhHhHHhHH.",
    ".sHHhHhhHhHHHHs.",
    "..SHhHhhHhHhHS..",
]
MAGO_ROSTO_LADO = [
    "AAaaaaaaaASSSSSS",
    "AAaaaaaSssssssss",
    "AAaaaaassssssews",
    "AAaaaaassssssess",
    "AAAaaaasssssssrs",
    ".AAAaaSsssswwww.",
    "..AAAaaaaaaaww..",
]
MANTO_FRENTE = [
    "....cCyaayCc....",
    ".vccccyaayccccC.",
    ".vccckyaaycckcCC",
    "vcccckyaaykcccCC",
    "ssCcckyyyykcccSS",
    "..vcccyggyccCC..",
    "..vcccyggyccCC..",
    ".vvcccyyyycceCC.",
    ".CCCCCyyyyCCCCC.",
]
MANTO_COSTAS = [
    "....cccccccc....",
    ".vcccccyyccccCC.",
    ".vccckcyyccckCC.",
    "vccccckyyckcCCCC",
    "ssCccccyyccccCSS",
    "..vccccyycccCC..",
    "..vcccccccccCC..",
    ".vvccccyyyyccCC.",
    ".CCCCCCCCCCCCCC.",
]
MANTO_LADO = [
    "....cccyss......",
    "...vvccccccaa...",
    "...vvccccccaa...",
    "...vvccvcccaass.",
    "...vvcCCCCCCCaa.",
    "...vvccccccccyC.",
    "..vvcccccccccyC.",
    "..vvccccccyyyyCC",
    "..CCCCCCCCYYYYCC",
]
CAJADO = [
    ".yyy.",
    "ygwgy",
    "yggGy",
    ".yyy.",
    "..tT.",
    ".tTtT",
] + ["..tT."] * 17


# ================================================================ 5. CAVALEIRO REAL (Elmo alado com viseira dourada, capa e armadura)
PLUMA_FRENTE = [
    "............ffff",
    "...........ffffFf",
    "..........fffFFfF",
]
PLUMA_LADO = [
    ".......ffff",
    ".....Ffffff",
    "....FFfffff",
]
ELMO_FRENTE = [
    "...ymmmmmmmmy...",
    "..ymnnmmmmmmMy..",
    ".mnnmmmyymmmmMM.",
    ".mnmmmmyymmmmMM.",
    "mmmmmmmyymmmmMMM",
    "mmmyyyyyyyyyymMM",
    "mmkkkkkkkkkkkkMM",
    "mmkSewSSSSewSkMM",
    "mmmkkkkkkkkkkmMM",
    "mmmmmmmyymmmmMMM",
    "mmmmkmkyykmkmmMM",
    ".mmmmmmYYmmmMMM.",
    "..MMMMMMMMMMMM..",
]
ELMO_COSTAS = [
    "...ymmmmmmmmy...",
    "..ymnnmmmmmmMy..",
    ".mnnmmmmmmmmmMM.",
    ".mnmmmmmmmmmmMM.",
    "mmmmmmmmmmmmmMMM",
    "mmmyyyyyyyyyymMM",
    "mmmmmmmmmmmmmMMM",
    "mmmmffffffffmMMM",
    "mMmmffffffffmMMM",
    "mMmmffffffffMMMM",
    "mMMmffffffffMMMM",
    ".MMmFFFFFFFFMMM.",
    "..MMMMMMMMMMMM..",
]
ELMO_LADO = [
    "..ymmmmmmmm.....",
    ".ymmmmmmnnmmm...",
    "mmmmmmmnnmmmmm..",
    "mmmmmmmmmmmmmmm.",
    "Mmmmmmmmmmmmmmmm",
    "MMmyyyyyyyyyyyyy",
    "MMmmmmmmmkkkkkkm",
    "MMmmmmmmmkSSSewk",
    "MMmmmmmmmmkkkkkm",
    "MMmmmmmmmmmmmmmm",
    "MMmmmmmmmmmkmkmm",
    ".MMmmmmmmmmmmmm.",
    "..MMMMMMMMMMMM..",
]
ARMADURA_FRENTE = [
    "...ffffYYffff...",
    ".nmmaaaaaaaammM.",
    ".nmkmmnyynmmmkmM",
    ".nmkmnnyynmmMkmM",
    ".mMkbbbyybbbkmM.",
    ".MMkmmmmmmMMkBB.",
    "..fcmmMmmMMMcf..",
    "..fccCccccCCcf..",
    "..FFCCCCCCCCFF..",
]
ARMADURA_COSTAS = [
    "...ffffffffff...",
    ".nmffffffffFfMM.",
    ".nmffffffffFkmM.",
    ".nmffffffffFkmM.",
    ".mMffffffffFkmM.",
    ".BBffffffffFkBB.",
    "..fffffffffffF..",
    "..fffffffffffF..",
    "..FFFFFFFFFFFF..",
]
ARMADURA_LADO = [
    "...fffffff......",
    "..fnnmmmmmmM....",
    "..fnnmkmmmMM....",
    "..fnnmkmmmMM....",
    "..FbbbkbbbbB....",
    "..FmmmkBBmMM....",
    "..FccmmBBmMc....",
    ".FFcccCccccCc...",
    ".FFCCCCCCCCCC...",
]
ESPADA_NPC = [
    ".n.....",
    ".nM....",
] + [".nM...."] * 10 + [
    "yyyYY..",
    ".BBBmmm",
    ".BBBMMm",
    "..yY...",
]
ESCUDO = [
    "yyyyyyyY",
    "yvcyYcCY",
    "ycyyycCY",
    "yyyyyyYY",
    "ycyyycCY",
    "yvcyYcCY",
    ".ycyYCY.",
    "..yyYY..",
    "...YY...",
]
ESCUDO_LADO = ["yy", "cY", "yY", "yY", "cY", "cY", "yY", ".Y"]
ESPADA_LADO = ["....n.", "....nM"] + ["....nM"] * 9 + [
    "...yyY",
    "mmmBBB",
    "MMMBBB",
    "....yY",
]




# ================================================================ 6. CAPUZ (Druida / Caçador / Eremita): capuz com rosto
CAPUZ_FRENTE_TOPO = [
    ".....cccccc.....",
    "...ccvvccccCC...",
    "..cvvccccccccC..",
    ".cvccCCCCCCCCcC.",
    ".cvcCSssssssSCcC",
    ".cvcSssssssssCcC",
]
ROSTO_CAPUZ_JOVEM = [
    ".cvcsewsssewsCcC",
    ".cvcseessseesCcC",
    ".cvcrsssssssrCcC",
    ".ccCSssRRsssSCC.",
    "..cCdSssssSdCC..",
]
ROSTO_CAPUZ_BARBA = [
    ".cvcsewsssewsCcC",
    ".cvcseessseesCcC",
    ".cvcsaaaaaaasCcC",
    ".ccaaaaaaaaaaaCC",
    "..caaaaaaaaaaC..",
]
CAPUZ_COSTAS = [
    ".....cccccc.....",
    "...ccvvccccCC...",
    "..cvvccccccccC..",
    ".cvcccccccccccC.",
    ".cvcccccccccccC.",
    ".cvccccccccccCC.",
    ".cvccccccccccCC.",
    "..cvcccccccccC..",
    "..cvccccccccCC..",
    "...cvcccccccC...",
    "....CCCCCCCC....",
]
CAPUZ_LADO_TOPO = [
    ".....cccccc.....",
    "...ccvvcccccC...",
    "..cvvcccccccccC.",
    ".cvccccccCCCCcC.",
    ".cvcccccCSsssss.",
    ".cvccccCSssssews",
    ".cvccccCsssssess",
]
ROSTO_CAPUZ_LADO_JOVEM = [
    ".cvccccCssssssrs",
    ".ccccccCSssssRs.",
    "..cCCCCCdSssSd..",
    "....CCCCC.......",
]
ROSTO_CAPUZ_LADO_BARBA = [
    ".cvccccCsaaaaaas",
    ".ccccccCaaaaaaa.",
    "..cCCCCCaaaaAa..",
    "....CCCCaAaa....",
]
BARBA_MANTO_FRENTE = [
    "...aaaaAaaaaa...",
    "....aAaaaaAa....",
    ".....aAaaAa.....",
    "......aAAa......",
]
BARBA_MANTO_LADO = [
    "........aaAa....",
    ".........aA.....",
]
CAJADO_DRUIDA = [
    ".g.g.",
    "gGtgG",
    ".gtG.",
    "..tg.",
    "..tT.",
] + ["..tT."] * 16
ARCO = [
    "..tTa",
    ".t..a",
    "t...a",
    "t...a",
    "T...a",
    "t...a",
    "t...a",
    ".t..a",
    "..tTa",
]
ALJAVA = [
    ".f.f",
    ".a.a",
    "bbbB",
    "bbbB",
    "bBbB",
    "bbbB",
    "BBBB",
]


# ================================================================ 7. FERREIRO (Careca, bandana, barba cheia, avental de couro e martelo)
FERREIRO_FRENTE = [
    "....SSssssSS....",
    "...SsswwssssS...",
    "..SsssssssssSS..",
    ".fffffffffffffF.",
    ".FFFFFFFFFFFFFF.",
    ".SsHHHssssHHHsS.",
    ".Sssewsssssewss.",
    ".Ssseessssseess.",
    ".hsrsssssssssrh.",
    ".hhhhhRRRRhhhhh.",
    ".hhhhhhhhhhhhhH.",
    "..hhhHhhhhHhhH..",
    "...HhhhhhhhhH...",
]
FERREIRO_COSTAS = [
    "....SSssssSS....",
    "...SssssssssS...",
    "..SsssssssssSS..",
    ".fffffffffffffF.",
    ".FFFFFFFFFFFFFF.",
    ".SsssssssssssSS.",
    ".SssssssssssssS.",
    ".SsssssssssssSS.",
    ".SSsssssssssSSS.",
    "..SSSssssssSSS..",
    "..dSSSSSSSSSSd..",
    "...dSSSSSSSSd...",
    "....dddddddd....",
]
FERREIRO_LADO = [
    "....SSsssss.....",
    "...SsssssswsS...",
    "..SsssssssssSs..",
    ".fffffffffffffff",
    ".FFFFFFFFFFFFFFf",
    ".SSssssssssHHsss",
    ".SSsssssssssewss",
    ".SSsssssssssesss",
    ".SShhssssssssrs.",
    ".ShhhhhhhhhhRhh.",
    "..hhhhhhhhhhhhh.",
    "...HhhhhhhhhhH..",
    "....HhhhhhhhH...",
]
AVENTAL_FRENTE = [
    "....aabBBbaa....",
    ".ssSabbbbbbaSss.",
    ".sskbbbyybbbkSS.",
    ".sskbbbbbbbbkSS.",
    ".SSkbbbBbbbbkSS.",
    ".ssBbbbbbbbbBss.",
    ".SS.bbbbbbbb.SS.",
    "...bbbbBbbbbb...",
    "...BBBBBBBBBB...",
]
AVENTAL_COSTAS = [
    "....aaaaaaaa....",
    ".ssSaabaabaaSss.",
    ".sskaabaabaakSS.",
    ".sskaaabbaaakSS.",
    ".SSkaaabbaaakSS.",
    ".ssbbbbbbbbbbss.",
    ".SS.aaaaaaaa.SS.",
    "...ppppPPpppp...",
    "...PPPPPPPPPP...",
]
AVENTAL_LADO = [
    "....aaaaSs......",
    "...aaaabbbbb....",
    "...aaaabbbbbb...",
    "...aasssbbbbb...",
    "...aaSSSbbbbb...",
    "...aasssbbbbb...",
    "...aaaaabbbbb...",
    "..aaaaabbbbbb...",
    "..PPPPPBBBBBB...",
]
MARTELO = [
    "mmmmM",
    "mnnmM",
    "MMMMM",
    "..t..",
    "..t..",
    "..T..",
    "..t..",
    "..T..",
]


def _sobrepor(base, camada):
    """Desenha `camada` por cima das primeiras linhas de `base` ('.' mantém o pixel original)."""
    resultado = list(base)
    for i, linha in enumerate(camada):
        resultado[i] = "".join(c if c != "." else b for b, c in zip(base[i], linha))
    return resultado


# ================================================================ catálogo de personagens
def _direcoes(frente, costas, lado, pernas_frente=PERNAS_FRENTE, extras=None):
    extras = extras or {}
    return {
        "baixo": {"partes": frente, "pernas": pernas_frente, "extras": extras.get("baixo", [])},
        "cima": {"partes": costas, "pernas": PERNAS_COSTAS, "extras": extras.get("cima", [])},
        "direita": {"partes": lado, "pernas": PERNAS_LADO, "extras": extras.get("direita", [])},
    }


PERSONAGENS = {
    "heroi": {
        "paleta": {},
        **_direcoes(
            [corpo(TUNICA_FRENTE), cabeca(HEROI_FRENTE)],
            [corpo(TUNICA_COSTAS), cabeca(HEROI_COSTAS)],
            [corpo(TUNICA_LADO), cabeca(HEROI_LADO)],
        ),
    },
    "aldeao": {
        "paleta": {
            "h": (92, 58, 36), "H": (58, 34, 20), "i": (138, 92, 56),
            "c": (68, 146, 68), "C": (42, 98, 46), "v": (112, 188, 92),
            "b": (146, 86, 42), "B": (98, 54, 26),
            "p": (98, 76, 54), "P": (66, 48, 34),
        },
        **_direcoes(
            [corpo(COLETE_FRENTE), cabeca(ALDEAO_FRENTE)],
            [corpo(COLETE_COSTAS), cabeca(ALDEAO_COSTAS)],
            [corpo(COLETE_LADO), cabeca(ALDEAO_LADO)],
        ),
    },
    "aldea": {
        "paleta": {
            "h": (244, 196, 68), "H": (196, 140, 36), "i": (255, 236, 148),
            "c": (72, 118, 212), "C": (44, 76, 154), "v": (118, 164, 242),
            "p": (240, 236, 228), "P": (196, 192, 204),
        },
        **_direcoes(
            [corpo(VESTIDO_FRENTE), cabeca(_com_rabo(ALDEA_FRENTE_BASE), pad=4)],
            [corpo(VESTIDO_COSTAS), cabeca(_com_rabo(ALDEA_COSTAS_BASE), pad=4)],
            [corpo(VESTIDO_LADO), cabeca(_com_rabo(ALDEA_LADO_BASE, lado_esquerdo=True), pad=4)],
        ),
    },
    "mago": {
        "paleta": {
            "h": (220, 226, 238), "H": (164, 172, 192), "i": (250, 252, 255),
            "c": (68, 78, 192), "C": (42, 46, 132), "v": (110, 124, 232),
            "p": (58, 66, 168), "P": (36, 40, 112),
        },
        **_direcoes(
            [corpo(MANTO_FRENTE), cabeca(CHAPEU_FRENTE + MAGO_ROSTO_FRENTE, pad=4)],
            [corpo(MANTO_COSTAS), cabeca(CHAPEU_FRENTE + MAGO_NUCA, pad=4)],
            [corpo(MANTO_LADO), cabeca(CHAPEU_LADO + MAGO_ROSTO_LADO, pad=4)],
            extras={
                "baixo": [extra(CAJADO, 5, 6)],
                "cima": [extra(CAJADO, 21, 6, atras=True)],
                "direita": [extra(CAJADO, 20, 6, atras=True)],
            },
        ),
    },
    "cavaleiro": {
        "paleta": {
            "a": (216, 56, 56), "A": (152, 32, 38),
            "c": (58, 96, 184), "C": (38, 64, 132), "v": (102, 140, 222),
            "p": (154, 162, 182), "P": (108, 116, 138),
            "o": (96, 104, 124), "O": (62, 68, 86),
        },
        **_direcoes(
            [corpo(ARMADURA_FRENTE), cabeca(PLUMA_FRENTE + ELMO_FRENTE)],
            [corpo(ARMADURA_COSTAS), cabeca(PLUMA_FRENTE + ELMO_COSTAS)],
            [corpo(ARMADURA_LADO), cabeca(PLUMA_LADO + ELMO_LADO)],
            extras={
                "baixo": [extra(ESPADA_NPC, 3, 8), extra(ESCUDO, 21, 18)],
                "cima": [extra(ESPADA_NPC[:-3] + ["..yY..."], 22, 8, atras=True), extra(ESCUDO, 3, 18, atras=True)],
                "direita": [extra(ESPADA_LADO, 19, 9), extra(ESCUDO_LADO, 17, 18)],
            },
        ),
    },
    "ferreiro": {
        "paleta": {
            "h": (70, 42, 30), "H": (44, 26, 18), "i": (110, 70, 46),
            "s": (240, 196, 158), "S": (204, 150, 110), "d": (168, 112, 80),
            "b": (126, 76, 42), "B": (82, 48, 26),
            "p": (70, 62, 78), "P": (46, 40, 54),
        },
        **_direcoes(
            [corpo(AVENTAL_FRENTE), cabeca(FERREIRO_FRENTE)],
            [corpo(AVENTAL_COSTAS), cabeca(FERREIRO_COSTAS)],
            [corpo(AVENTAL_LADO), cabeca(FERREIRO_LADO)],
            extras={
                "baixo": [extra(MARTELO, 3, 18)],
                "cima": [extra(MARTELO, 24, 18, atras=True)],
                "direita": [extra(MARTELO, 18, 19)],
            },
        ),
    },
    "druida": {
        "paleta": {
            "c": (70, 128, 66), "C": (40, 82, 44), "v": (118, 178, 96),
            "a": (236, 238, 230), "A": (184, 188, 196),
            "g": (126, 214, 92), "G": (60, 146, 52),
            "y": (214, 176, 86), "Y": (152, 116, 48),
            "p": (92, 70, 46), "P": (62, 46, 30),
        },
        **_direcoes(
            [corpo(_sobrepor(MANTO_FRENTE, BARBA_MANTO_FRENTE)), cabeca(CAPUZ_FRENTE_TOPO + ROSTO_CAPUZ_BARBA)],
            [corpo(MANTO_COSTAS), cabeca(CAPUZ_COSTAS)],
            [corpo(_sobrepor(MANTO_LADO, BARBA_MANTO_LADO)), cabeca(CAPUZ_LADO_TOPO + ROSTO_CAPUZ_LADO_BARBA)],
            extras={
                "baixo": [extra(CAJADO_DRUIDA, 4, 7)],
                "cima": [extra(CAJADO_DRUIDA, 22, 7, atras=True)],
                "direita": [extra(CAJADO_DRUIDA, 20, 7, atras=True)],
            },
        ),
    },
    "cacador": {
        "paleta": {
            "c": (78, 120, 58), "C": (46, 78, 38), "v": (122, 168, 84),
            "f": (214, 66, 52), "F": (146, 38, 34),
            "m": (150, 104, 62), "M": (104, 68, 38), "n": (190, 146, 96),
            "p": (96, 74, 52), "P": (64, 48, 34),
            "y": (196, 160, 82), "Y": (140, 108, 52),
        },
        **_direcoes(
            [corpo(TUNICA_FRENTE), cabeca(CAPUZ_FRENTE_TOPO + ROSTO_CAPUZ_JOVEM)],
            [corpo(TUNICA_COSTAS), cabeca(CAPUZ_COSTAS)],
            [corpo(TUNICA_LADO), cabeca(CAPUZ_LADO_TOPO + ROSTO_CAPUZ_LADO_JOVEM)],
            extras={
                "baixo": [extra(ARCO, 22, 13, atras=True)],
                "cima": [extra(ARCO, 6, 13), extra(ALJAVA, 18, 14)],
                "direita": [extra(ALJAVA, 9, 15, atras=True)],
            },
        ),
    },
}

# Variações de paleta: reaproveitam os desenhos com outras cores (roupas, cabelo, pele).
_VARIACOES = {
    "herbalista": ("aldea", {
        "h": (118, 74, 42), "H": (78, 46, 24), "i": (164, 112, 66),
        "c": (88, 152, 76), "C": (52, 104, 50), "v": (136, 198, 108),
        "f": (236, 120, 168), "F": (176, 72, 118), "g": (255, 214, 96),
    }),
    "lenhador": ("aldeao", {
        "c": (190, 54, 48), "C": (128, 30, 30), "v": (232, 98, 82),
        "y": (36, 30, 40), "Y": (20, 16, 24),
        "a": (204, 64, 56), "A": (140, 38, 36),
        "h": (128, 66, 30), "H": (84, 40, 18), "i": (176, 104, 54),
    }),
    "taverneiro": ("aldeao", {
        "c": (140, 92, 54), "C": (94, 58, 32), "v": (184, 130, 80),
        "y": (226, 214, 190), "Y": (176, 164, 144),
        "h": (40, 32, 36), "H": (22, 18, 22), "i": (74, 62, 66),
        "b": (172, 58, 52), "B": (118, 34, 32),
    }),
    "nomade": ("aldeao", {
        "c": (236, 214, 166), "C": (190, 160, 110), "v": (252, 240, 206),
        "y": (204, 70, 54), "Y": (146, 44, 36),
        "s": (222, 170, 122), "S": (186, 128, 88), "d": (150, 98, 64),
        "a": (90, 150, 196), "A": (58, 104, 148),
        "b": (196, 150, 86), "B": (140, 100, 52),
        "h": (34, 28, 30), "H": (18, 14, 18), "i": (64, 54, 58),
    }),
    "sacerdote": ("mago", {
        "c": (242, 236, 218), "C": (196, 182, 150), "v": (255, 252, 240),
        "y": (248, 196, 62), "Y": (196, 132, 30),
        "g": (255, 150, 60), "G": (214, 92, 30),
        "h": (232, 196, 120), "H": (188, 148, 80), "i": (255, 232, 170),
        "p": (226, 178, 72), "P": (170, 124, 44),
    }),
    "eremita": ("druida", {
        "c": (128, 116, 102), "C": (86, 76, 66), "v": (170, 160, 146),
        "g": (152, 214, 255), "G": (86, 150, 214),
        "p": (100, 92, 84), "P": (68, 62, 56),
    }),
    "guarda": ("cavaleiro", {
        "m": (214, 172, 96), "M": (150, 110, 56), "n": (252, 230, 164),
        "f": (58, 120, 96), "F": (34, 80, 62),
        "a": (58, 120, 96), "A": (34, 80, 62),
        "c": (96, 82, 62), "C": (64, 54, 40), "v": (132, 116, 92),
    }),
    "sentinela": ("cavaleiro", {
        "m": (206, 230, 248), "M": (132, 164, 204), "n": (255, 255, 255),
        "f": (70, 136, 220), "F": (40, 86, 166),
        "a": (70, 136, 220), "A": (40, 86, 166),
        "y": (180, 236, 255), "Y": (110, 176, 220),
    }),
    "espirito": ("cavaleiro", {
        "m": (170, 214, 236), "M": (104, 150, 196), "n": (236, 252, 255),
        "f": (120, 150, 230), "F": (78, 96, 176),
        "a": (120, 150, 230), "A": (78, 96, 176),
        "c": (96, 130, 200), "C": (62, 84, 150), "v": (150, 180, 240),
        "y": (200, 236, 255), "Y": (130, 180, 230),
        "o": (90, 120, 170), "O": (60, 82, 128), "p": (120, 156, 206), "P": (84, 110, 160),
        "b": (86, 110, 170), "B": (60, 76, 130), "S": (150, 230, 255), "e": (210, 250, 255), "w": (255, 255, 255),
    }),
}
for _nome, (_base, _cores) in _VARIACOES.items():
    PERSONAGENS[_nome] = {**PERSONAGENS[_base], "paleta": {**PERSONAGENS[_base]["paleta"], **_cores}}
PERSONAGENS["espirito"]["alfa"] = 175


# ================================================================ montagem
def _desenhar(surf, parte, paleta, dy=0, direcao="baixo", quadro=0):
    tipo = parte.get("tipo", "outro")
    piscar = tipo == "cabeca" and quadro == 7
    for y, linha in enumerate(parte["linhas"]):
        for x, c in enumerate(linha):
            if c not in paleta:
                raise ValueError(f"letra desconhecida {c!r} na linha {linha!r}")
            if piscar and c in ("e", "w", "u"):
                cor = paleta["S"]
            else:
                cor = paleta[c]
            if not cor:
                continue

            ox, oy = 0, dy
            # Nos quadros de ataque (8..10), omite o braço em repouso que será desenhado empunhando a espada
            if tipo == "corpo" and quadro in (8, 9, 10):
                if direcao == "baixo" and x <= 2 and y >= 2:
                    continue
                if direcao == "cima" and x >= 13 and y >= 2:
                    continue
                if direcao == "direita" and 7 <= x <= 9 and 5 <= y <= 6 and c in ("s", "S"):
                    continue

            # Balanço natural dos braços durante a caminhada (quadros 0..5)
            if tipo == "corpo" and 1 <= y <= 6:
                if direcao in ("baixo", "cima"):
                    eh_braco_esq = x <= 2
                    eh_braco_dir = x >= 13
                    if quadro in (0, 1):
                        oy += 1 if eh_braco_esq else (-1 if eh_braco_dir else 0)
                    elif quadro in (3, 4):
                        oy += -1 if eh_braco_esq else (1 if eh_braco_dir else 0)
                elif direcao == "direita" and 6 <= x <= 10 and 3 <= y <= 6:
                    if quadro in (0, 1):
                        ox += 1
                    elif quadro in (3, 4):
                        ox -= 1

            # Torção de tronco/cabeça nos quadros de ataque (8=preparação, 9=impacto, 10=finalização)
            if quadro == 8 and tipo in ("corpo", "cabeca"):
                if direcao == "direita":
                    ox -= 1
                elif direcao == "baixo":
                    oy -= 1
            elif quadro == 9 and tipo in ("corpo", "cabeca"):
                if direcao == "direita":
                    ox += 1
                elif direcao == "baixo":
                    oy += 1

            px, py = parte["x"] + x + ox, parte["y"] + y + oy
            if 0 <= px < QUADRO and 0 <= py < QUADRO:
                surf.set_at((px, py), cor)


def _contornar(surf):
    """Contorno seletivo 16-bits ("sel-out").

    Cada pixel vazio encostado no desenho vira contorno. Em vez de um preto
    chapado, o contorno herda um tom bem escuro da cor vizinha, o que deixa
    roupas e cabelos com bordas mais ricas. A base (pés) e o lado direito,
    longe da luz, ficam com o contorno mais escuro para dar volume.
    """
    largura, altura = surf.get_size()
    mascara = pygame.mask.from_surface(surf)
    pintar = []
    for y in range(altura):
        for x in range(largura):
            if mascara.get_at((x, y)):
                continue
            vizinho = None
            for dx, dy in ((0, 1), (-1, 0), (1, 0), (0, -1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < largura and 0 <= ny < altura and mascara.get_at((nx, ny)):
                    vizinho = (nx, ny, dx, dy)
                    break
            if vizinho is None:
                continue
            nx, ny, dx, dy = vizinho
            r, g, b, _ = surf.get_at((nx, ny))
            # Lado iluminado (topo/esquerda) recebe um pouco mais da cor; sombra fica quase preta.
            peso = 0.30 if dy > 0 or dx > 0 else 0.18
            if y >= altura - 3:
                peso = 0.12
            cor = (
                round(CONTORNO[0] * (1 - peso) + r * peso * 0.55),
                round(CONTORNO[1] * (1 - peso) + g * peso * 0.55),
                round(CONTORNO[2] * (1 - peso) + b * peso * 0.55),
            )
            pintar.append((x, y, cor))
    for x, y, cor in pintar:
        surf.set_at((x, y), cor)


def _luz_de_borda(surf):
    """Realça de leve os pixels do topo de cada forma (luz vinda de cima)."""
    largura, altura = surf.get_size()
    for x in range(largura):
        for y in range(1, altura):
            cor = surf.get_at((x, y))
            if cor.a == 0:
                continue
            acima = surf.get_at((x, y - 1))
            if acima.a == 0 or sum(acima[:3]) < 120:
                if sum(cor[:3]) > 150:
                    surf.set_at((x, y), (min(255, cor.r + 18), min(255, cor.g + 18), min(255, cor.b + 14), cor.a))
                break


def montar_quadro(definicao, direcao, quadro, paleta):
    """Monta um quadro 32x32: extras de trás, pernas, corpo, cabeça e extras da frente."""
    surf = pygame.Surface((QUADRO, QUADRO), pygame.SRCALPHA)
    d = definicao[direcao]
    dy_corpo = (0, 1, 0, 0, 1, 0, -1, 0, 0, 1, 1)[quadro]
    dy_cabeca = (0, 1, 1, 0, 1, 1, -1, 0, 0, 1, 1)[quadro]
    dy_extra = (0, 1, 2, 0, 1, 2, -1, 0, 0, 1, 2)[quadro]

    for e in d["extras"]:
        if e["atras"]:
            _desenhar(surf, e, paleta, dy_extra, direcao, quadro)
    _desenhar(surf, pernas(d["pernas"][quadro]), paleta, 0, direcao, quadro)
    for p in d["partes"]:
        dy = dy_cabeca if p.get("tipo") == "cabeca" else dy_corpo
        _desenhar(surf, p, paleta, dy, direcao, quadro)
    for e in d["extras"]:
        if not e["atras"]:
            _desenhar(surf, e, paleta, dy_extra, direcao, quadro)
    _luz_de_borda(surf)
    _contornar(surf)
    alfa = definicao.get("alfa")
    if alfa:
        surf.fill((255, 255, 255, alfa), special_flags=pygame.BLEND_RGBA_MULT)
    return surf


def folha_personagem(nome):
    definicao = PERSONAGENS[nome]
    paleta = {**PALETA_BASE, **definicao["paleta"]}
    folha = pygame.Surface((QUADRO * QUADROS_POR_LINHA, QUADRO * 3), pygame.SRCALPHA)
    for linha, direcao in enumerate(("baixo", "cima", "direita")):
        for q in range(QUADROS_POR_LINHA):
            folha.blit(montar_quadro(definicao, direcao, q, paleta), (q * QUADRO, linha * QUADRO))
    return folha
