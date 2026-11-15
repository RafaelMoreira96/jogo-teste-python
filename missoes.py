"""Sistema de Missões (Quests) para A Lenda Perdida."""

CATALOGO_MISSOES = {
    "remedio_ancestral": {
        "id": "remedio_ancestral",
        "titulo": "O Remédio Ancestral",
        "npc": "Herbalista da Vila",
        "desc": "O herbalista precisa de 3 Cogumelos Noturnos do Pântano para curar uma praga na vila.",
        "tipo": "coleta",
        "item_alvo": "cogumelo_noturno",
        "qtd_alvo": 3,
        "recompensa_ouro": 40,
        "recompensa_ph": 1,
    },
    "fonte_corrompida": {
        "id": "fonte_corrompida",
        "titulo": "A Fonte Corrompida",
        "npc": "Druida do Bosque",
        "desc": "Monstros corromperam a nascente sagrada no Bosque de Outono. Elimine os monstros ao redor.",
        "tipo": "combate",
        "monstros_alvo": 4,
        "recompensa_ouro": 50,
        "recompensa_ph": 1,
    },
    "lamina_guardioes": {
        "id": "lamina_guardioes",
        "titulo": "A Lâmina dos Guardiões",
        "npc": "Mestre Ferreiro",
        "desc": "Traga 2 Minérios de Cristal da Caverna de Cristal para o ferreiro forjar uma arma lendária.",
        "tipo": "coleta",
        "item_alvo": "minerio_cristal",
        "qtd_alvo": 2,
        "recompensa_ouro": 60,
        "recompensa_arma": "lamina_lendaria",
    },
}


class GerenciadorMissoes:
    """Controla o progresso de missões e itens de quest."""

    def __init__(self, ativas=None, concluidas=None, itens_quest=None):
        self.ativas = dict(ativas or {})
        self.concluidas = set(concluidas or [])
        self.itens_quest = dict(itens_quest or {})  # item_id -> quantidade

    def aceitar(self, id_missao, jogo=None):
        if id_missao not in CATALOGO_MISSOES or id_missao in self.concluidas:
            return False
        if id_missao in self.ativas:
            return False

        self.ativas[id_missao] = {
            "progresso": 0,
        }
        if jogo and hasattr(jogo, "textos_flutuantes"):
            from rpg import TextoFlutuante
            jogo.textos_flutuantes.append(
                TextoFlutuante(jogo.jogador.rect.midtop, f"NOVA MISSÃO: {CATALOGO_MISSOES[id_missao]['titulo']}", (255, 235, 90))
            )
            if hasattr(jogo.app, "audio"):
                jogo.app.audio.sfx("menu_confirmar")
        return True

    def adicionar_item_quest(self, item_id, qtd=1, jogo=None):
        self.itens_quest[item_id] = self.itens_quest.get(item_id, 0) + qtd
        # Atualiza missões de coleta
        for id_m, dados in self.ativas.items():
            info = CATALOGO_MISSOES[id_m]
            if info["tipo"] == "coleta" and info["item_alvo"] == item_id:
                dados["progresso"] = min(info["qtd_alvo"], self.itens_quest[item_id])
                if jogo and hasattr(jogo, "textos_flutuantes"):
                    from rpg import TextoFlutuante
                    jogo.textos_flutuantes.append(
                        TextoFlutuante(jogo.jogador.rect.center, f"{info['titulo']}: {dados['progresso']}/{info['qtd_alvo']}", (120, 240, 255))
                    )

    def registrar_monstro_derrotado(self, jogo=None):
        for id_m, dados in self.ativas.items():
            info = CATALOGO_MISSOES[id_m]
            if info["tipo"] == "combate":
                dados["progresso"] = min(info["monstros_alvo"], dados["progresso"] + 1)
                if jogo and hasattr(jogo, "textos_flutuantes") and dados["progresso"] <= info["monstros_alvo"]:
                    from rpg import TextoFlutuante
                    jogo.textos_flutuantes.append(
                        TextoFlutuante(jogo.jogador.rect.center, f"{info['titulo']}: {dados['progresso']}/{info['monstros_alvo']}", (120, 240, 255))
                    )

    def pronta_para_entregar(self, id_missao):
        if id_missao not in self.ativas:
            return False
        info = CATALOGO_MISSOES[id_missao]
        dados = self.ativas[id_missao]
        if info["tipo"] == "coleta":
            return self.itens_quest.get(info["item_alvo"], 0) >= info["qtd_alvo"]
        elif info["tipo"] == "combate":
            return dados["progresso"] >= info["monstros_alvo"]
        return False

    def entregar(self, id_missao, jogo):
        if not self.pronta_para_entregar(id_missao):
            if hasattr(jogo, "textos_flutuantes"):
                from rpg import TextoFlutuante
                jogo.textos_flutuantes.append(
                    TextoFlutuante(jogo.jogador.rect.midtop, "Objetivos ainda não cumpridos!", (255, 140, 120))
                )
            if hasattr(jogo.app, "audio"):
                jogo.app.audio.sfx("bloqueio")
            return False

        info = CATALOGO_MISSOES[id_missao]
        if info["tipo"] == "coleta":
            self.itens_quest[info["item_alvo"]] -= info["qtd_alvo"]

        del self.ativas[id_missao]
        self.concluidas.add(id_missao)
        if hasattr(jogo, "flags"):
            jogo.flags.add(f"{id_missao}_concluida")
            jogo.flags.discard(f"{id_missao}_ativa")

        # Recompensas
        ouro = info.get("recompensa_ouro", 0)
        ph = info.get("recompensa_ph", 0)
        arma = info.get("recompensa_arma")

        if ouro > 0:
            jogo.rpg.ouro += ouro
        if ph > 0:
            jogo.rpg.pontos_habilidade += ph
        if arma:
            jogo.rpg.arma_equipada = arma

        if hasattr(jogo, "conquistas"):
            jogo.conquistas.desbloquear("heroi_prestimoso", jogo)

        if hasattr(jogo, "textos_flutuantes"):
            from rpg import TextoFlutuante
            txt_rec = f"MISSÃO CONCLUÍDA: {info['titulo']}!"
            jogo.textos_flutuantes.append(
                TextoFlutuante(jogo.jogador.rect.midtop, txt_rec, (255, 235, 90))
            )
        if hasattr(jogo.app, "audio"):
            jogo.app.audio.sfx("fanfarra_item")
        return True
