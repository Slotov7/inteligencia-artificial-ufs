"""
analise_algoritmos.py — Comparação de Algoritmos de Busca

Compara BFS (Busca em Largura), Greedy Best-First Search e A* no cenário
de monitoramento do estuário do Rio Poxim.

Métricas coletadas para cada algoritmo:
    - Nós expandidos durante a busca
    - Tempo de execução (ms)
    - Custo total do caminho
    - Bateria consumida

Referência AIMA: Capítulos 3 (Busca Não-Informada) e 4 (Busca Informada)

Uso:
    python analise_algoritmos.py
"""

from __future__ import annotations

import sys
import os
import time

# Adiciona aima-python ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'aima-python'))

from search import (
    breadth_first_graph_search,
    greedy_best_first_graph_search,
    astar_search,
    Node,
)

from problems.search_problem import PollutionMappingProblem


# ============================================================================
# Wrapper para Contagem de Nós Expandidos
# ============================================================================

class InstrumentedProblem:
    """Wrapper que decora um Problem para contar nós expandidos.

    Proxy transparente: delega todos os métodos ao problema original,
    mas intercepta chamadas a `actions()` para contar quantas vezes
    um estado é expandido (explorado).

    Attributes:
        problem: Instância original de PollutionMappingProblem.
        nos_expandidos: Contador de expansões.
    """

    def __init__(self, problem: PollutionMappingProblem) -> None:
        self.problem = problem
        self.nos_expandidos: int = 0

    def actions(self, state):
        """Conta a expansão e delega ao problema original."""
        self.nos_expandidos += 1
        return self.problem.actions(state)

    def result(self, state, action):
        return self.problem.result(state, action)

    def goal_test(self, state):
        return self.problem.goal_test(state)

    def path_cost(self, c, state1, action, state2):
        return self.problem.path_cost(c, state1, action, state2)

    def h(self, node):
        return self.problem.h(node)

    # Propriedades necessárias para os algoritmos do AIMA
    @property
    def initial(self):
        return self.problem.initial

    @initial.setter
    def initial(self, value):
        self.problem.initial = value

    @property
    def goal(self):
        return self.problem.goal

    @goal.setter
    def goal(self, value):
        self.problem.goal = value


# ============================================================================
# Função de Execução de Busca com Métricas
# ============================================================================

def executar_busca(
    nome_algoritmo: str,
    funcao_busca,
    problem: PollutionMappingProblem,
) -> dict:
    """Executa um algoritmo de busca e coleta métricas de desempenho.

    Args:
        nome_algoritmo: Nome do algoritmo para exibição.
        funcao_busca: Função de busca do AIMA (ex: astar_search).
        problem: Instância do problema de busca.

    Returns:
        Dict com métricas: nome, nós expandidos, tempo (ms),
        custo do caminho, bateria consumida, solução encontrada.
    """
    # Envolve o problema com instrumentação
    instrumento = InstrumentedProblem(problem)

    # Mede o tempo de execução
    inicio = time.perf_counter()
    resultado = funcao_busca(instrumento)
    fim = time.perf_counter()

    tempo_ms = (fim - inicio) * 1000

    if resultado is None:
        return {
            "algoritmo": nome_algoritmo,
            "nos_expandidos": instrumento.nos_expandidos,
            "tempo_ms": tempo_ms,
            "custo_caminho": float("inf"),
            "bateria_consumida": 0,
            "solucao": None,
            "acoes": [],
        }

    # Extrai informações do nó solução
    custo = resultado.path_cost
    estado_final = resultado.state
    bateria_inicial = problem.initial[2]  # bateria no estado inicial
    bateria_final = estado_final[2]
    bateria_consumida = bateria_inicial - bateria_final

    return {
        "algoritmo": nome_algoritmo,
        "nos_expandidos": instrumento.nos_expandidos,
        "tempo_ms": tempo_ms,
        "custo_caminho": custo,
        "bateria_consumida": bateria_consumida,
        "solucao": resultado,
        "acoes": resultado.solution(),
    }


# ============================================================================
# Configuração do Cenário de Teste
# ============================================================================

def criar_cenario() -> dict:
    """Cria o cenário padrão do estuário do Rio Poxim.

    Retorna a configuração compartilhada por todos os algoritmos,
    incluindo grid, obstáculos, zonas urbanas e chamados.

    Returns:
        Dict com configuração completa do cenário.
    """
    return {
        "grid_size": (10, 10),
        "base_position": (0, 0),
        "battery_capacity": 60,
        "obstaculos": {(4, 4), (5, 4), (6, 3), (7, 4), (2, 6)},
        "zonas_urbanas": {
            (1, 1), (2, 1), (3, 1),
            (1, 2), (2, 2),
            (5, 5), (6, 5),
            (4, 3), (5, 3),
        },
        # Chamados simulados (mesmos do APIGateway)
        "chamados": [
            {"id": 1, "titulo": "Ponto Norte - Mangue Degradado", "coord": (7, 2)},
            {"id": 2, "titulo": "Metais Pesados - Zona Industrial", "coord": (3, 8)},
            {"id": 3, "titulo": "Biodiversidade - Caranguejos", "coord": (8, 6)},
        ],
    }


# ============================================================================
# Impressão da Tabela Comparativa
# ============================================================================

def imprimir_tabela(resultados: list[dict], titulo_chamado: str) -> None:
    """Imprime tabela comparativa formatada dos resultados.

    Args:
        resultados: Lista de dicts com métricas por algoritmo.
        titulo_chamado: Título do chamado para contexto.
    """
    print(f"\n{'═' * 78}")
    print(f"  📋 {titulo_chamado}")
    print(f"{'═' * 78}")

    # Cabeçalho
    print(
        f"  {'Algoritmo':<25} │ {'Nós Exp.':<10} │ {'Tempo (ms)':<12} │ "
        f"{'Custo':<8} │ {'Bateria':<8}"
    )
    print(f"  {'─' * 25}─┼─{'─' * 10}─┼─{'─' * 12}─┼─{'─' * 8}─┼─{'─' * 8}")

    for r in resultados:
        if r["solucao"] is None:
            print(
                f"  {r['algoritmo']:<25} │ {r['nos_expandidos']:<10} │ "
                f"{r['tempo_ms']:<12.3f} │ {'∞':<8} │ {'N/A':<8}"
            )
        else:
            print(
                f"  {r['algoritmo']:<25} │ {r['nos_expandidos']:<10} │ "
                f"{r['tempo_ms']:<12.3f} │ {r['custo_caminho']:<8.1f} │ "
                f"{r['bateria_consumida']:<8}"
            )

    print()

    # Destaque do melhor algoritmo
    validos = [r for r in resultados if r["solucao"] is not None]
    if validos:
        melhor_nos = min(validos, key=lambda r: r["nos_expandidos"])
        melhor_custo = min(validos, key=lambda r: r["custo_caminho"])
        print(f"  🏆 Menos nós expandidos: {melhor_nos['algoritmo']} ({melhor_nos['nos_expandidos']})")
        print(f"  🏆 Menor custo:          {melhor_custo['algoritmo']} ({melhor_custo['custo_caminho']:.1f})")


def imprimir_resumo_geral(todos_resultados: dict[str, list[dict]]) -> None:
    """Imprime um resumo geral de todos os cenários.

    Args:
        todos_resultados: Dict mapeando título do chamado → lista de resultados.
    """
    print(f"\n{'═' * 78}")
    print(f"  📊 RESUMO GERAL — COMPARAÇÃO DE ALGORITMOS")
    print(f"{'═' * 78}")

    # Agregar por algoritmo
    algoritmos = ["BFS (Busca em Largura)", "Greedy Best-First", "A* Search"]
    totais: dict[str, dict] = {}

    for nome in algoritmos:
        totais[nome] = {
            "total_nos": 0,
            "total_tempo": 0.0,
            "total_custo": 0.0,
            "total_bateria": 0,
            "cenarios_resolvidos": 0,
        }

    for _titulo, resultados in todos_resultados.items():
        for r in resultados:
            nome = r["algoritmo"]
            totais[nome]["total_nos"] += r["nos_expandidos"]
            totais[nome]["total_tempo"] += r["tempo_ms"]
            if r["solucao"] is not None:
                totais[nome]["total_custo"] += r["custo_caminho"]
                totais[nome]["total_bateria"] += r["bateria_consumida"]
                totais[nome]["cenarios_resolvidos"] += 1

    print(
        f"\n  {'Algoritmo':<25} │ {'Total Nós':<12} │ {'Tempo Total':<14} │ "
        f"{'Custo Total':<12} │ {'Bat. Total':<10}"
    )
    print(
        f"  {'─' * 25}─┼─{'─' * 12}─┼─{'─' * 14}─┼─{'─' * 12}─┼─{'─' * 10}"
    )

    for nome in algoritmos:
        t = totais[nome]
        print(
            f"  {nome:<25} │ {t['total_nos']:<12} │ "
            f"{t['total_tempo']:<14.3f} │ {t['total_custo']:<12.1f} │ "
            f"{t['total_bateria']:<10}"
        )

    print()

    # Determinar vencedor geral
    melhor = min(algoritmos, key=lambda n: totais[n]["total_nos"])
    print(f"  ✅ Algoritmo mais eficiente (menos nós): {melhor}")
    melhor_custo = min(algoritmos, key=lambda n: totais[n]["total_custo"])
    print(f"  ✅ Algoritmo com menor custo total:      {melhor_custo}")

    print(f"\n{'═' * 78}")
    print("  📖 Análise (AIMA Cap. 3-4):")
    print("  • BFS é completo e ótimo para custo uniforme, mas expande MUITOS nós")
    print("  • Greedy é rápido mas NÃO garante caminho ótimo (pode ser subótimo)")
    print("  • A* combina custo real g(n) + heurística h(n), sendo ótimo e eficiente")
    print("  • Com heurística admissível (Manhattan+Vento), A* encontra o caminho")
    print("    ótimo expandindo significativamente menos nós que BFS")
    print(f"{'═' * 78}\n")


# ============================================================================
# Execução Principal
# ============================================================================

def main() -> None:
    """Executa a comparação completa de algoritmos de busca."""

    print("=" * 78)
    print("  🧠 ANÁLISE COMPARATIVA DE ALGORITMOS DE BUSCA")
    print("  📍 Cenário: Estuário do Rio Poxim, Aracaju-SE")
    print("  📖 Referência: AIMA — Capítulos 3 e 4")
    print("=" * 78)

    cenario = criar_cenario()
    todos_resultados: dict[str, list[dict]] = {}

    # Para cada chamado, executa os 3 algoritmos
    for chamado in cenario["chamados"]:
        coord = chamado["coord"]
        titulo = f"Chamado #{chamado['id']}: {chamado['titulo']} → {coord}"

        print(f"\n\n🔬 Testando: {titulo}")
        print(f"   Origem: {cenario['base_position']} → Destino: {coord}")

        # Cria o problema de busca: ir da base até o alvo e voltar
        # Estado: (x, y, bateria, alvos_pendentes)
        alvo = frozenset({coord})
        estado_inicial = (
            cenario["base_position"][0],
            cenario["base_position"][1],
            cenario["battery_capacity"],
            alvo,
        )

        # Cria problema para ir ao alvo (objetivo = posição do alvo quando
        # todos alvos coletados)
        # Para comparação justa, usamos o goal_test padrão: alvos vazios + na base
        problem = PollutionMappingProblem(
            initial=estado_inicial,
            goal=cenario["base_position"],
            grid_size=cenario["grid_size"],
            obstaculos=cenario["obstaculos"],
            zonas_urbanas=cenario["zonas_urbanas"],
        )

        # Executa os 3 algoritmos com o MESMO problema
        resultados = []

        # 1. BFS — Busca em Largura (Cap. 3, Fig 3.11)
        # BFS não usa heurística, expande todos os nós nível a nível
        resultados.append(
            executar_busca("BFS (Busca em Largura)", breadth_first_graph_search, problem)
        )

        # 2. Greedy Best-First Search (Cap. 3, Fig 3.14)
        # Usa apenas h(n), ignora g(n) — rápido mas não ótimo
        # greedy_best_first_graph_search(problem, f) requer f=h(n)
        resultados.append(
            executar_busca(
                "Greedy Best-First",
                lambda p: greedy_best_first_graph_search(p, lambda n: p.h(n)),
                problem,
            )
        )

        # 3. A* Search (Cap. 3, Fig 3.14)
        # Usa f(n) = g(n) + h(n) — ótimo com heurística admissível
        resultados.append(
            executar_busca("A* Search", astar_search, problem)
        )

        # Imprime tabela comparativa para este chamado
        imprimir_tabela(resultados, titulo)

        # Mostra as soluções encontradas
        for r in resultados:
            if r["solucao"] is not None:
                print(f"  📍 {r['algoritmo']}: {r['acoes'][:10]}{'...' if len(r['acoes']) > 10 else ''}")
            else:
                print(f"  ❌ {r['algoritmo']}: Sem solução encontrada")

        todos_resultados[titulo] = resultados

    # Resumo geral
    imprimir_resumo_geral(todos_resultados)


if __name__ == "__main__":
    main()
