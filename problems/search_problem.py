"""
problems/search_problem.py — Problema de Mapeamento de Poluição

Implementa o Open/Closed Principle (OCP):
    O sistema é aberto para extensão (novos algoritmos de busca
    podem ser injetados) mas fechado para modificação.

Classe PollutionMappingProblem herda de search.Problem (AIMA) e modela
o problema de navegação do drone no estuário do Rio Poxim como um
problema de busca em espaço de estados.

Estado: (pos_x, pos_y, battery, frozenset(targets_pending))
Ações: CIMA, BAIXO, ESQUERDA, DIREITA
Heurística: Manhattan com ajuste de Vento Atlântico
Custo: Base 1 + Urban Penalty (3× em zonas urbanas)
"""

from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'aima-python'))

from search import Problem


class PollutionMappingProblem(Problem):
    """
    Problema de busca para mapeamento de poluição no estuário.

    Modela a missão do drone como um problema clássico de busca,
    onde o agente deve visitar pontos de interesse (chamados),
    coletar amostras e retornar à base com bateria suficiente.

    O espaço de estados é definido por:
        - Posição (x, y) no grid discretizado
        - Nível de bateria restante
        - Conjunto de alvos (pontos de coleta) pendentes
    """

    def __init__(
        self,
        initial: tuple[int, int, int, frozenset[tuple[int, int]]],
        goal: tuple[int, int],
        grid_size: tuple[int, int] = (10, 10),
        obstaculos: set[tuple[int, int]] | None = None,
        zonas_urbanas: set[tuple[int, int]] | None = None,
        vento_atlantico: str = "leste",
        fator_vento: float = 1.5,
    ) -> None:
        super().__init__(initial, goal)
        self.max_x: int = grid_size[0] - 1
        self.max_y: int = grid_size[1] - 1
        self.obstaculos: set[tuple[int, int]] = obstaculos or set()
        self.zonas_urbanas: set[tuple[int, int]] = zonas_urbanas or set()
        self.base: tuple[int, int] = goal
        self.vento_atlantico: str = vento_atlantico
        self.fator_vento: float = fator_vento

    def actions(self, state: tuple) -> list[str]:
        """
        Retorna ações possíveis dado o estado atual.
        Verifica limites do grid, obstáculos e bateria disponível.
        O agente não pode se mover se a bateria estiver zerada.
        """
        x, y, bateria, alvos = state
        acoes: list[str] = []

        if bateria <= 0:
            return acoes

        if y > 0 and (x, y - 1) not in self.obstaculos:
            acoes.append("CIMA")
        if y < self.max_y and (x, y + 1) not in self.obstaculos:
            acoes.append("BAIXO")
        if x > 0 and (x - 1, y) not in self.obstaculos:
            acoes.append("ESQUERDA")
        if x < self.max_x and (x + 1, y) not in self.obstaculos:
            acoes.append("DIREITA")

        return acoes

    def result(self, state: tuple, action: str) -> tuple:
        """
        Retorna o estado resultante de executar a ação.
        Atualiza posição, consome bateria (com Urban Penalty se aplicável),
        e remove alvos visitados do conjunto pendente.
        """
        x, y, bateria, alvos = state
        novo_x, novo_y = x, y

        if action == "CIMA":
            novo_y -= 1
        elif action == "BAIXO":
            novo_y += 1
        elif action == "ESQUERDA":
            novo_x -= 1
        elif action == "DIREITA":
            novo_x += 1

        custo = 3 if (novo_x, novo_y) in self.zonas_urbanas else 1

        novos_alvos = alvos - frozenset({(novo_x, novo_y)})

        return (novo_x, novo_y, bateria - custo, novos_alvos)

    def goal_test(self, state: tuple) -> bool:
        """
        Verifica se o estado é um objetivo.
        O objetivo é atingido quando:
        1. Todos os alvos foram coletados (frozenset vazio)
        2. O drone retornou à posição da base
        3. A bateria é suficiente (>= 0) para confirmar pouso seguro
        """
        x, y, bateria, alvos = state
        return (
            len(alvos) == 0
            and (x, y) == self.base
            and bateria >= 0
        )

    def path_cost(
        self,
        c: float,
        state1: tuple,
        action: str,
        state2: tuple
    ) -> float:
        """
        Calcula o custo acumulado do caminho até state2.
        Integra o Urban Penalty: movimentos em zonas urbanas
        custam 3× mais que em áreas naturais.
        """
        x2, y2, _, _ = state2
        custo_passo = 3 if (x2, y2) in self.zonas_urbanas else 1
        return c + custo_passo

    def h(self, node) -> float:
        """
        Função heurística admissível com ajuste de Vento Atlântico.
        Calcula a distância de Manhattan estimada considerando a distância até o alvo e base, 
        e penaliza movimentos contra o vento (LESTE/OESTE).
        """
        x, y, bateria, alvos = node.state
        x_base, y_base = self.base

        def _manhattan_com_vento(
            x1: int, y1: int, x2: int, y2: int
        ) -> float:
            dx = abs(x1 - x2)
            dy = abs(y1 - y2)

            penalidade_x = dx
            if self.vento_atlantico == "leste" and x2 > x1:
                penalidade_x = dx * self.fator_vento
            elif self.vento_atlantico == "oeste" and x2 < x1:
                penalidade_x = dx * self.fator_vento

            return penalidade_x + dy

        if not alvos:
            return _manhattan_com_vento(x, y, x_base, y_base)

        estimativas: list[float] = []
        for alvo_x, alvo_y in alvos:
            dist_ate_alvo = _manhattan_com_vento(x, y, alvo_x, alvo_y)
            dist_alvo_base = _manhattan_com_vento(
                alvo_x, alvo_y, x_base, y_base
            )
            estimativas.append(dist_ate_alvo + dist_alvo_base)

        return min(estimativas)
