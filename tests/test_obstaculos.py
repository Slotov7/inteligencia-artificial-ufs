from problems.search_problem import PollutionMappingProblem


def test_obstacles_block_actions():
    obst = {(1, 0)}
    problem = PollutionMappingProblem(
        initial=(0, 0, 10, frozenset()),
        goal=(0, 0),
        grid_size=(3, 3),
        obstaculos=obst,
    )

    # A partir de (0,0) não deve permitir mover para (1,0)
    state = (0, 0, 10, frozenset())
    acoes = problem.actions(state)
    assert "DIREITA" not in acoes
