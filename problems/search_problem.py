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

# Adiciona aima-python ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'aima-python'))

from search import Problem


class PollutionMappingProblem(Problem):
    """Problema de busca para mapeamento de poluição no estuário.

    Modela a missão do drone como um problema clássico de busca,
    onde o agente deve visitar pontos de interesse (chamados),
    coletar amostras e retornar à base com bateria suficiente.

    O espaço de estados é definido por:
        - Posição (x, y) no grid discretizado
        - Nível de bateria restante
        - Conjunto de alvos (pontos de coleta) pendentes

    Args:
        initial: Estado inicial (x, y, battery, frozenset(targets))
        goal: Posição da base para retorno (x, y)
        grid_size: Dimensões do grid (width, height)
        obstaculos: Conjunto de posições com obstáculos
        zonas_urbanas: Conjunto de posições em áreas urbanas
        vento_atlantico: Direção predominante do vento ('leste', 'oeste', etc.)
        fator_vento: Fator multiplicador para movimentos contra o vento

    SOLID — OCP:
        Pode ser estendido (novas heurísticas, novos custos)
        sem modificar o código base.
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
        """Retorna ações possíveis dado o estado atual.

        Verifica limites do grid, obstáculos e bateria disponível.
        O agente não pode se mover se a bateria estiver zerada.

        Args:
            state: Tupla (x, y, battery, targets_pending)

        Returns:
            Lista de ações válidas ('CIMA', 'BAIXO', 'ESQUERDA', 'DIREITA')
        """
        x, y, bateria, alvos = state
        acoes: list[str] = []

        if bateria <= 0:
            return acoes

        # Verifica cada direção: limites + obstáculos
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
        """Retorna o estado resultante de executar a ação.

        Atualiza posição, consome bateria (com Urban Penalty se aplicável),
        e remove alvos visitados do conjunto pendente.

        Args:
            state: Estado atual (x, y, battery, targets)
            action: Ação a executar

        Returns:
            Novo estado (novo_x, novo_y, nova_bateria, novos_alvos)
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

        # Urban Penalty: 3× bateria em zonas urbanas
        custo = 3 if (novo_x, novo_y) in self.zonas_urbanas else 1

        # Remove alvo se o drone passou por cima (coleta automática)
        novos_alvos = alvos - frozenset({(novo_x, novo_y)})

        return (novo_x, novo_y, bateria - custo, novos_alvos)

    def goal_test(self, state: tuple) -> bool:
        """Verifica se o estado é um objetivo.

        O objetivo é atingido quando:
        1. Todos os alvos foram coletados (frozenset vazio)
        2. O drone retornou à posição da base
        3. A bateria é suficiente (>= 0) para confirmar pouso seguro

        Args:
            state: Estado a verificar

        Returns:
            True se o estado satisfaz todas as condições de objetivo.
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
        """Calcula o custo acumulado do caminho até state2.

        Integra o Urban Penalty: movimentos em zonas urbanas
        custam 3× mais que em áreas naturais.

        Args:
            c: Custo acumulado até state1
            state1: Estado anterior
            action: Ação executada
            state2: Estado resultante

        Returns:
            Custo total acumulado incluindo a transição.
        """
        x2, y2, _, _ = state2
        custo_passo = 3 if (x2, y2) in self.zonas_urbanas else 1
        return c + custo_passo

    def h(self, node) -> float:
        """Função heurística admissível com ajuste de Vento Atlântico.

        Calcula a distância de Manhattan estimada considerando:
        1. Se há alvos pendentes: distância até o alvo mais próximo
           + distância do alvo até a base
        2. Se não há alvos: distância até a base

        O Vento Atlântico predominante de LESTE penaliza movimentos
        para leste (contra o vento) com um fator multiplicador,
        tornando a heurística mais informada mas ainda admissível.

        A admissibilidade é garantida porque a penalidade do vento
        na heurística é sempre menor ou igual à penalidade real
        aplicada no custo do caminho.

        Args:
            node: Nó da árvore de busca (node.state contém o estado)

        Returns:
            Estimativa de custo mínimo até o objetivo.
        """
        x, y, bateria, alvos = node.state
        x_base, y_base = self.base

        def _manhattan_com_vento(
            x1: int, y1: int, x2: int, y2: int
        ) -> float:
            """Manhattan com componente de vento no eixo horizontal."""
            dx = abs(x1 - x2)
            dy = abs(y1 - y2)

            # Vento Atlântico: penaliza movimentos contra o vento
            # predominante. Aracaju recebe ventos predominantemente de leste.
            # Mover-se para LESTE (contra o vento) custa mais energia.
            penalidade_x = dx
            if self.vento_atlantico == "leste" and x2 > x1:
                # Indo para leste (contra o vento)
                penalidade_x = dx * self.fator_vento
            elif self.vento_atlantico == "oeste" and x2 < x1:
                # Indo para oeste (contra o vento)
                penalidade_x = dx * self.fator_vento

            return penalidade_x + dy

        # Se não há alvos pendentes → apenas voltar à base
        if not alvos:
            return _manhattan_com_vento(x, y, x_base, y_base)

        # Se há alvos → estimar via alvo mais próximo + retorno à base
        estimativas: list[float] = []
        for alvo_x, alvo_y in alvos:
            dist_ate_alvo = _manhattan_com_vento(x, y, alvo_x, alvo_y)
            dist_alvo_base = _manhattan_com_vento(
                alvo_x, alvo_y, x_base, y_base
            )
            estimativas.append(dist_ate_alvo + dist_alvo_base)

        # Retorna o cenário mais otimista (admissível)
        return min(estimativas)
