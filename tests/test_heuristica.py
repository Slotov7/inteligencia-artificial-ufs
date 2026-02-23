from problems.search_problem import PollutionMappingProblem


class SimpleNode:
    def __init__(self, state):
        self.state = state


def simulate_cost_to_goal(problem, state):
    # Simula um caminho guloso em direção ao objetivo e soma custos reais
    x, y, bateria, alvos = state
    total_cost = 0
    # Se houver alvos, visita o mais próximo repetidamente
    pending = set(alvos)
    cur_x, cur_y = x, y

    def step_towards(tx, ty):
        nonlocal cur_x, cur_y, total_cost
        if cur_x < tx:
            cur_x += 1
        elif cur_x > tx:
            cur_x -= 1
        elif cur_y < ty:
            cur_y += 1
        elif cur_y > ty:
            cur_y -= 1
        cost = 3 if (cur_x, cur_y) in problem.zonas_urbanas else 1
        total_cost += cost

    # Visita todos os alvos (guloso por distância Manhattan)
    while pending:
        # escolher alvo mais próximo
        alvo = min(pending, key=lambda t: abs(t[0] - cur_x) + abs(t[1] - cur_y))
        while (cur_x, cur_y) != alvo:
            step_towards(*alvo)
        pending.remove(alvo)

    # voltar para base
    base = problem.base
    while (cur_x, cur_y) != base:
        step_towards(*base)

    return total_cost


def test_h_nao_superestima():
    # Grid simples sem vento e sem zonas urbanas -> custo real == Manhattan
    problem = PollutionMappingProblem(
        initial=(0, 0, 10, frozenset({(2, 0)})),
        goal=(0, 0),
        grid_size=(5, 5),
        obstaculos=set(),
        zonas_urbanas=set(),
        vento_atlantico="nenhum",
        fator_vento=1.0,
    )

    state = (0, 0, 10, frozenset({(2, 0)}))
    node = SimpleNode(state)

    h_value = problem.h(node)
    real_cost = simulate_cost_to_goal(problem, state)

    assert h_value <= real_cost
