from problems.search_problem import PollutionMappingProblem


def test_goal_conditions():
    problem = PollutionMappingProblem(
        initial=(0, 0, 10, frozenset()),
        goal=(0, 0),
        grid_size=(3, 3),
    )

    # Estado que satisfaz objetivo: sem alvos, na base, bateria >= 0
    state_ok = (0, 0, 5, frozenset())
    assert problem.goal_test(state_ok)

    # Estado com alvos pendentes → não é objetivo
    state_with_targets = (0, 0, 5, frozenset({(1, 1)}))
    assert not problem.goal_test(state_with_targets)

    # Estado fora da base → não é objetivo
    state_not_base = (1, 0, 5, frozenset())
    assert not problem.goal_test(state_not_base)

    # Estado com bateria negativa → não é objetivo
    state_low_battery = (0, 0, -1, frozenset())
    assert not problem.goal_test(state_low_battery)
