"""Liga o nome de quem fala nos diálogos à aparência (sprite) usada no retrato."""
import unicodedata

# Ordem importa: termos mais específicos primeiro.
PALAVRAS_CHAVE = [
    ("voz misteriosa", None),
    ("placa", None),
    ("ferreiro", "ferreiro"),
    ("taverneiro", "taverneiro"),
    ("herbalista", "herbalista"),
    ("druida", "druida"),
    ("lenhador", "lenhador"),
    ("cacador", "cacador"),
    ("guardiao da cabana", "cacador"),
    ("nomade", "nomade"),
    ("especiarias", "nomade"),
    ("sacerdote", "sacerdote"),
    ("eremita", "eremita"),
    ("sentinela", "sentinela"),
    ("espirito", "espirito"),
    ("guarda", "guarda"),
    ("campeao", "cavaleiro"),
    ("cavaleiro", "cavaleiro"),
    ("florista", "aldea"),
    ("hospedeira", "aldea"),
    ("guardia", "aldea"),
    ("aldea", "aldea"),
    ("sabio", "mago"),
    ("anciao", "mago"),
    ("mago", "mago"),
    ("guardiao", "mago"),
    ("mercador", "aldeao"),
    ("aldeao", "aldeao"),
    ("heroi", "heroi"),
    ("voce", "heroi"),
]
SEM_RETRATO = {"Voz Misteriosa", "Placa", "Erro na história"}


def _normalizar(texto):
    sem_acento = unicodedata.normalize("NFD", texto.lower())
    return "".join(c for c in sem_acento if unicodedata.category(c) != "Mn")


def aparencia_por_nome(nome):
    """Devolve a aparência do retrato para o nome do falante, ou None se não reconhecer."""
    if not nome:
        return None
    alvo = _normalizar(nome)
    for chave, aparencia in PALAVRAS_CHAVE:
        if chave in alvo:
            return aparencia
    return None
