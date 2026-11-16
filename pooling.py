"""Sistema de Object Pooling para Partículas e Projéteis (Fase 1 - Otimização de Performance).

Inspirado nas diretrizes de arquitetura de jogos de skills/game-development/SKILL.md:
- Reduz drasticamente alocações de memória e pausas de Garbage Collector (GC).
- Reutiliza instâncias em vetores de alta frequência (partículas de corte, passos, explosões, magias e projéteis de chefões).
- Compatível 100% com a API de listas do Pygame e convenções do projeto.
"""
import random
import pygame


class PoolParticulas:
    """Pool estático de partículas pré-alocadas e recicladas."""

    _disponiveis = []
    _max_capacidade = 1500
    _stats = {
        "criadas": 0,
        "reaproveitadas": 0,
        "liberadas": 0,
    }

    @classmethod
    def obter(cls, pos, cor, vel=None, vida=None):
        from efeitos import Particula

        if cls._disponiveis:
            p = cls._disponiveis.pop()
            p.reset(pos, cor, vel, vida)
            cls._stats["reaproveitadas"] += 1
            return p

        cls._stats["criadas"] += 1
        return Particula(pos, cor, vel, vida)

    @classmethod
    def obter_explosao(cls, centro, cores, quantidade=8):
        return [cls.obter(centro, random.choice(cores)) for _ in range(quantidade)]

    @classmethod
    def liberar(cls, particula):
        if len(cls._disponiveis) < cls._max_capacidade:
            cls._disponiveis.append(particula)
            cls._stats["liberadas"] += 1

    @classmethod
    def limpar(cls):
        cls._disponiveis.clear()

    @classmethod
    def stats(cls):
        total_usos = cls._stats["criadas"] + cls._stats["reaproveitadas"]
        taxa = (cls._stats["reaproveitadas"] / total_usos * 100.0) if total_usos > 0 else 0.0
        return {
            **cls._stats,
            "em_espera": len(cls._disponiveis),
            "taxa_reaproveitamento_pct": round(taxa, 1),
        }


class PoolProjeteis:
    """Pool estático para projéteis do herói, chefões e inimigos."""

    _disponiveis_magicos = []
    _disponiveis_chefes = []
    _disponiveis_flechas = []
    _max_capacidade = 500
    _stats = {
        "magicos_criados": 0,
        "magicos_reaproveitados": 0,
        "chefes_criados": 0,
        "chefes_reaproveitados": 0,
        "flechas_criadas": 0,
        "flechas_reaproveitadas": 0,
        "total_liberados": 0,
    }

    @classmethod
    def obter_magico(cls, pos, direcao_vetor, dano=2, cor=(255, 115, 45)):
        from rpg import ProjetilMagico

        if cls._disponiveis_magicos:
            p = cls._disponiveis_magicos.pop()
            p.reset(pos, direcao_vetor, dano, cor)
            cls._stats["magicos_reaproveitados"] += 1
            return p

        cls._stats["magicos_criados"] += 1
        return ProjetilMagico(pos, direcao_vetor, dano, cor)

    @classmethod
    def obter_chefe(
        cls,
        pos,
        vel,
        dano=1,
        raio=4,
        cor=(255, 90, 60),
        cor_borda=(160, 20, 30),
        duracao=4.5,
        elemento=None,
        estilo=None,
    ):
        from chefe import ProjetilChefe

        if cls._disponiveis_chefes:
            p = cls._disponiveis_chefes.pop()
            p.reset(pos, vel, dano, raio, cor, cor_borda, duracao, elemento, estilo)
            cls._stats["chefes_reaproveitados"] += 1
            return p

        cls._stats["chefes_criados"] += 1
        return ProjetilChefe(pos, vel, dano, raio, cor, cor_borda, duracao, elemento, estilo)

    @classmethod
    def obter_flecha(cls, pos, vel, dano=1):
        from enemy import FlechaInimigo

        if cls._disponiveis_flechas:
            p = cls._disponiveis_flechas.pop()
            p.reset(pos, vel, dano)
            cls._stats["flechas_reaproveitadas"] += 1
            return p

        cls._stats["flechas_criadas"] += 1
        return FlechaInimigo(pos, vel, dano)

    @classmethod
    def liberar(cls, proj):
        if proj is None:
            return
        from rpg import ProjetilMagico
        from chefe import ProjetilChefe
        from enemy import FlechaInimigo

        if isinstance(proj, ProjetilMagico):
            if len(cls._disponiveis_magicos) < cls._max_capacidade:
                cls._disponiveis_magicos.append(proj)
                cls._stats["total_liberados"] += 1
        elif isinstance(proj, ProjetilChefe):
            if len(cls._disponiveis_chefes) < cls._max_capacidade:
                cls._disponiveis_chefes.append(proj)
                cls._stats["total_liberados"] += 1
        elif isinstance(proj, FlechaInimigo):
            if len(cls._disponiveis_flechas) < cls._max_capacidade:
                cls._disponiveis_flechas.append(proj)
                cls._stats["total_liberados"] += 1

    @classmethod
    def limpar(cls):
        cls._disponiveis_magicos.clear()
        cls._disponiveis_chefes.clear()
        cls._disponiveis_flechas.clear()

    @classmethod
    def stats(cls):
        return {
            **cls._stats,
            "magicos_em_espera": len(cls._disponiveis_magicos),
            "chefes_em_espera": len(cls._disponiveis_chefes),
            "flechas_em_espera": len(cls._disponiveis_flechas),
        }


class ListaParticulas(list):
    """Lista especializada de partículas com atualização in-place e reciclagem automática para a Pool."""

    def atualizar(self, dt):
        """Atualiza todas as partículas in-place, devolvendo à pool as que expirarem."""
        i = 0
        n = len(self)
        while i < n:
            p = self[i]
            if p.atualizar(dt):
                i += 1
            else:
                PoolParticulas.liberar(p)
                # Troca rápida O(1) pelo último elemento
                n -= 1
                self[i] = self[n]
        del self[n:]

    def clear(self):
        for p in self:
            PoolParticulas.liberar(p)
        super().clear()
