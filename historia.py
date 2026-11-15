"""Motor de história: lê historia/dialogos.txt e executa os diálogos.

O formato está explicado no topo do próprio historia/dialogos.txt.
"""
from pathlib import Path

ACENTOS = str.maketrans("ãâáàçéêíóôõú", "aaaaceeiooou")


class ErroHistoria(Exception):
    pass


class Historia:
    def __init__(self, dialogos):
        self.dialogos = dialogos

    @classmethod
    def carregar(cls, caminho):
        """Nunca quebra o jogo: se houver erro, ele aparece como diálogo inicial."""
        try:
            return cls(interpretar(Path(caminho).read_text(encoding="utf-8")))
        except OSError as e:
            msg = f"Não consegui abrir {caminho}: {e}"
        except ErroHistoria as e:
            msg = str(e)
        return cls({"inicio": [("fala", "Erro na história", msg)]})


def _fala(linha):
    if linha.startswith("-"):  # "- texto" força narração
        return ("fala", "", linha[1:].strip())
    nome, sep, texto = linha.partition(":")
    nome = nome.strip()
    if sep and 0 < len(nome) <= 28 and not any(c in nome for c in "\"'“”"):
        return ("fala", nome, texto.strip())
    return ("fala", "", linha)


COMANDOS_CENA_COM_ARG = (
    "mapa",
    "cenario",
    "clima",
    "camera",
    "efeito",
    "pose",
    "olhar",
    "pular",
    "mover",
    "posicionar",
    "emocao",
    "esperar",
)
COMANDOS_CENA_OPCIONAL = ("tremer", "clarao")


def interpretar(texto):
    """Transforma o texto em {nome_do_dialogo: [comandos]}."""
    dialogos = {}
    pilha = None  # blocos abertos: o diálogo e cada @se dentro dele
    destinos = []  # (nome, linha) usados em @ir/@opcao, conferidos no fim

    def erro(n, msg):
        raise ErroHistoria(f"Linha {n}: {msg}")

    def conferir_blocos_fechados():
        if pilha and len(pilha) > 1:
            erro(pilha[-1]["linha"], "este @se não tem @fim.")

    for n, bruta in enumerate(texto.splitlines(), 1):
        linha = bruta.strip()
        if not linha or linha.startswith("#"):
            continue

        if linha.startswith("==="):
            conferir_blocos_fechados()
            nome = linha.strip("= ").strip()
            if not nome:
                erro(n, "faltou o nome do diálogo depois de '==='.")
            if nome in dialogos:
                erro(n, f"já existe um diálogo chamado '{nome}'.")
            dialogos[nome] = []
            pilha = [{"lista": dialogos[nome], "linha": n}]
            continue

        if pilha is None:
            erro(n, "escreva '=== nome_do_dialogo' antes do primeiro texto.")
        lista = pilha[-1]["lista"]

        if not linha.startswith("@"):
            lista.append(_fala(linha))
            continue

        comando, _, arg = linha[1:].partition(" ")
        comando = comando.lower().translate(ACENTOS)
        arg = arg.strip()
        if comando in ("se", "marcar", "desmarcar", "ir", "opcao", *COMANDOS_CENA_COM_ARG) and not arg:
            erro(n, f"@{comando} precisa de um complemento.")

        if comando == "se":
            no = ["se", arg.lstrip("!").strip(), arg.startswith("!"), [], []]
            lista.append(no)
            pilha.append({"lista": no[3], "no": no, "linha": n, "senao": False})
        elif comando == "senao":
            if len(pilha) < 2 or pilha[-1]["senao"]:
                erro(n, "@senao sem um @se antes.")
            pilha[-1]["senao"] = True
            pilha[-1]["lista"] = pilha[-1]["no"][4]
        elif comando == "fim":
            if len(pilha) < 2:
                erro(n, "@fim sem um @se antes.")
            pilha.pop()
        elif comando in ("marcar", "desmarcar"):
            lista.append((comando, arg))
        elif comando == "ir":
            lista.append(("ir", arg))
            destinos.append((arg, n))
        elif comando == "opcao":
            texto_opcao, seta, destino = arg.partition("->")
            texto_opcao, destino = texto_opcao.strip(), destino.strip()
            if not seta or not texto_opcao or not destino:
                erro(n, "use '@opcao Texto da escolha -> nome_do_dialogo'.")
            destinos.append((destino, n))
            if lista and lista[-1][0] == "opcoes":
                lista[-1][1].append((texto_opcao, destino))  # junta opções seguidas
            else:
                lista.append(("opcoes", [(texto_opcao, destino)]))
        elif (
            comando in (
                "curar",
                "loja",
                "missao_remedio",
                "missao_fonte",
                "missao_lamina",
                "entregar_remedio",
                "entregar_fonte",
                "entregar_lamina",
                "entregar_reliquias",
            )
            or comando.startswith("missao_")
            or comando.startswith("entregar_")
        ):
            lista.append((comando,))
        elif comando in COMANDOS_CENA_COM_ARG or comando in COMANDOS_CENA_OPCIONAL:
            lista.append(("cena", comando, arg))
        else:
            erro(n, f"não conheço o comando '@{comando}'.")

    conferir_blocos_fechados()
    for nome, n in destinos:
        if nome not in dialogos:
            erro(n, f"o diálogo '{nome}' não existe.")
    return dialogos


class Conversa:
    """Executa um diálogo passo a passo.

    proximo() devolve:
        ("fala", nome, texto)
        ("opcoes", [(texto, destino), ...])  -> responda com escolher(destino)
        ("espera", condicao)                 -> aguarda tempo ou movimento terminar
        None                                 -> acabou
    """

    def __init__(self, historia, nome, flags, acoes=None, diretor=None):
        self.historia = historia
        self.flags = flags
        self.acoes = acoes or {}
        self.diretor = diretor
        self._ir(nome)

    def _ir(self, nome):
        self.pilha = [[self.historia.dialogos[nome], 0]]

    def escolher(self, destino):
        self._ir(destino)

    def proximo(self):
        for _ in range(10_000):
            if not self.pilha:
                return None
            topo = self.pilha[-1]
            lista, i = topo
            if i >= len(lista):
                self.pilha.pop()
                continue
            topo[1] += 1
            no = lista[i]
            tipo = no[0]
            if tipo in ("fala", "opcoes"):
                return no
            if tipo == "se":
                ativo = (no[1] in self.flags) != no[2]
                self.pilha.append([no[3] if ativo else no[4], 0])
            elif tipo == "marcar":
                self.flags.add(no[1])
            elif tipo == "desmarcar":
                self.flags.discard(no[1])
            elif tipo == "ir":
                self._ir(no[1])
            elif tipo == "cena":
                if self.diretor:
                    espera = self.diretor(no[1], no[2])
                    if espera is not None:
                        return ("espera", espera)
            elif tipo in self.acoes:
                self.acoes[tipo]()
        self.pilha = []
        return ("fala", "Erro na história", "Os @ir formam um loop sem nenhuma fala no meio.")
