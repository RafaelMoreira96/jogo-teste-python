"""Sistema de Equipamentos (Armas, Escudos e Túnicas) para A Lenda Perdida."""

CATALOGO_ARMAS = {
    "espada_ferro": {
        "id": "espada_ferro",
        "nome": "Espada de Ferro",
        "dano": 1,
        "efeito": "normal",
        "cor": (195, 205, 220),
        "desc": "Espada de ferro forjada na vila. Dano equilibrado.",
        "preco": 0,
    },
    "lamina_vulcanica": {
        "id": "lamina_vulcanica",
        "nome": "Lâmina Vulcânica",
        "dano": 2,
        "efeito": "fogo",
        "cor": (255, 90, 40),
        "desc": "Imbuída com fogo das profundezas. Dano 2 + queimadura.",
        "preco": 60,
    },
    "sabre_tempestade": {
        "id": "sabre_tempestade",
        "nome": "Sabre da Tempestade",
        "dano": 2,
        "efeito": "raio",
        "cor": (110, 235, 255),
        "desc": "Leve e reluzente como um relâmpago. Ataques 40% mais rápidos.",
        "preco": 90,
    },
    "lamina_lendaria": {
        "id": "lamina_lendaria",
        "nome": "Lâmina dos Guardiões",
        "dano": 3,
        "efeito": "luz",
        "cor": (255, 235, 120),
        "desc": "Forjada pelo mestre ferreiro com minérios ancestrais. Dano máximo.",
        "preco": 150,
    },
}

CATALOGO_ESCUDOS = {
    "nenhum": {
        "id": "nenhum",
        "nome": "Sem Escudo",
        "bloqueio": False,
        "desc": "Você não possui um escudo equipado.",
        "preco": 0,
    },
    "escudo_madeira": {
        "id": "escudo_madeira",
        "nome": "Escudo de Carvalho",
        "bloqueio": True,
        "desc": "Segure [E / LCtrl] para erguer o escudo e anular flechas e projéteis.",
        "preco": 30,
    },
    "escudo_guardiao": {
        "id": "escudo_guardiao",
        "nome": "Escudo do Guardião",
        "bloqueio": True,
        "desc": "Escudo reforçado com brasão dourado. Bloqueia e empurra inimigos.",
        "preco": 80,
    },
}

CATALOGO_TUNICAS = {
    "tunica_verde": {
        "id": "tunica_verde",
        "nome": "Túnica do Bosque",
        "red_dano": 1.0,
        "regen_mana": 1.0,
        "paleta_corpo": (88, 179, 63),
        "desc": "Túnica confortável tradicional do jovem herói.",
        "preco": 0,
    },
    "armadura_carmesim": {
        "id": "armadura_carmesim",
        "nome": "Armadura Carmesim",
        "red_dano": 0.5,
        "regen_mana": 1.0,
        "paleta_corpo": (185, 45, 55),
        "desc": "Peitoral de aço real escarlate. Reduz todo dano recebido em 50%.",
        "preco": 75,
    },
    "manto_astral": {
        "id": "manto_astral",
        "nome": "Manto Astral",
        "red_dano": 0.85,
        "regen_mana": 1.8,
        "paleta_corpo": (70, 140, 230),
        "desc": "Tecido com fios de luz celestial. Regenera mana 80% mais rápido.",
        "preco": 95,
    },
}
