from problems.search_problem import PollutionMappingProblem


def test_actions_within_bounds():
    problem = PollutionMappingProblem(
        initial=(0, 0, 10, frozenset()),
        goal=(0, 0),
        grid_size=(3, 3),
    )

    # No canto superior-esquerdo (0,0) não deve ter CIMA/ESQUERDA
    state = (0, 0, 10, frozenset())
    acoes = problem.actions(state)
    assert "ESQUERDA" not in acoes
    assert "CIMA" not in acoes

    # No canto inferior-direito (max,max) não deve ter BAIXO/DIREITA
    max_x, max_y = problem.max_x, problem.max_y
    state2 = (max_x, max_y, 10, frozenset())
    acoes2 = problem.actions(state2)
    assert "BAIXO" not in acoes2
    assert "DIREITA" not in acoes2
