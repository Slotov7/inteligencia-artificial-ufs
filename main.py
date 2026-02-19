import sys
import os

# Adiciona o diretório 'aima-python' ao path do sistema para permitir a importação
sys.path.append(os.path.join(os.path.dirname(__file__), 'aima-python'))

from search import Problem

class SentinelaEstuarino(Problem):
    def __init__(self, initial, goal, grid_limites, obstaculos):
        # initial format: (x, y, bateria_atual, frozenset(alvos_pendentes))
        # goal format: (x_base, y_base)
        super().__init__(initial, goal)
        self.max_x, self.max_y = grid_limites # Para o grid 10x10 -> (9, 9)
        self.obstaculos = obstaculos # set de tuplas, ex: {(1,1), (2,2)}
        self.base = goal

    def actions(self, state):
        x, y, bateria, alvos = state
        acoes_possiveis = []
        
        # Se não tem bateria para o próximo passo, o drone não pode agir
        if bateria <= 0:
            return acoes_possiveis
            
        # Lógica para verificar limites do grid e obstáculos
        if x > 0 and (x - 1, y) not in self.obstaculos: acoes_possiveis.append('ESQUERDA')
        if x < self.max_x and (x + 1, y) not in self.obstaculos: acoes_possiveis.append('DIREITA')
        if y > 0 and (x, y - 1) not in self.obstaculos: acoes_possiveis.append('CIMA')
        if y < self.max_y and (x, y + 1) not in self.obstaculos: acoes_possiveis.append('BAIXO')
        
        return acoes_possiveis

    def h(self, node):
        # Função heurística h(n).
        # Calcula a Distância de Manhattan estimada até o objetivo.
        # Sua admissibilidade se dá pelo fato de estimar o custo ÓTIMO para chegar ao objetivo
        x, y, bateria, alvos = node.state
        x_base, y_base = self.base

        # Se não há mais alvos pendentes, a estimativa é apenas voltar para a base
        if not alvos:
            return abs(x - x_base) + abs(y - y_base)

        # Se ainda há alvos, estimamos o custo de ir até o alvo
        # mais próximo e depois voltar para a base.
        estimativas = []
        for (alvo_x, alvo_y) in alvos:
            # Distância de Manhattan do drone até este alvo específico
            dist_ate_alvo = abs(x - alvo_x) + abs(y - alvo_y)
            
            # Distância de Manhattan do alvo até a base
            dist_alvo_ate_base = abs(alvo_x - x_base) + abs(alvo_y - y_base)
            
            estimativas.append(dist_ate_alvo + dist_alvo_ate_base)

        # Retornamos o cenário mais otimista (o menor caminho estimado)
        return min(estimativas)

    def result(self, state, action):
        x, y, bateria, alvos = state
        novo_x, novo_y = x, y
        
        if action == 'ESQUERDA': novo_x -= 1
        elif action == 'DIREITA': novo_x += 1
        elif action == 'CIMA': novo_y -= 1
        elif action == 'BAIXO': novo_y += 1
        
        # Remove o alvo se o drone passar por cima
        novos_alvos = alvos - frozenset({(novo_x, novo_y)})
        
        return (novo_x, novo_y, bateria - 1, novos_alvos)

    def goal_test(self, state):
        x, y, bateria, alvos = state
        # Objetivo: todos os alvos coletados E voltou para a base
        return len(alvos) == 0 and (x, y) == self.base