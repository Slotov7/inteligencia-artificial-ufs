import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), 'aima-python'))

from search import Problem

class SentinelaEstuarino(Problem):
    def __init__(self, initial, goal, grid_limites, obstaculos):
        super().__init__(initial, goal)
        self.max_x, self.max_y = grid_limites 
        self.obstaculos = obstaculos 
        self.base = goal

    def actions(self, state):
        x, y, bateria, alvos = state
        acoes_possiveis = []
        
        if bateria <= 0:
            return acoes_possiveis
            
        if x > 0 and (x - 1, y) not in self.obstaculos: acoes_possiveis.append('ESQUERDA')
        if x < self.max_x and (x + 1, y) not in self.obstaculos: acoes_possiveis.append('DIREITA')
        if y > 0 and (x, y - 1) not in self.obstaculos: acoes_possiveis.append('CIMA')
        if y < self.max_y and (x, y + 1) not in self.obstaculos: acoes_possiveis.append('BAIXO')
        
        return acoes_possiveis

    def h(self, node):
        """
        Função heurística h(n).
        Calcula a Distância de Manhattan estimada até o objetivo.
        """
        x, y, bateria, alvos = node.state
        x_base, y_base = self.base

        if not alvos:
            return abs(x - x_base) + abs(y - y_base)

        estimativas = []
        for (alvo_x, alvo_y) in alvos:
            dist_ate_alvo = abs(x - alvo_x) + abs(y - alvo_y)
            dist_alvo_ate_base = abs(alvo_x - x_base) + abs(alvo_y - y_base)
            estimativas.append(dist_ate_alvo + dist_alvo_ate_base)

        return min(estimativas)

    def result(self, state, action):
        x, y, bateria, alvos = state
        novo_x, novo_y = x, y
        
        if action == 'ESQUERDA': novo_x -= 1
        elif action == 'DIREITA': novo_x += 1
        elif action == 'CIMA': novo_y -= 1
        elif action == 'BAIXO': novo_y += 1
        
        novos_alvos = alvos - frozenset({(novo_x, novo_y)})
        
        return (novo_x, novo_y, bateria - 1, novos_alvos)

    def goal_test(self, state):
        x, y, bateria, alvos = state
        return len(alvos) == 0 and (x, y) == self.base