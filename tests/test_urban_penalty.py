from env.estuario import PoximEnvironment


class DummyAgent:
    def __init__(self, location=(0, 0)):
        self.location = location
        self.bump = False

    def is_alive(self):
        return True


def test_urban_penalty_consumption():
    env = PoximEnvironment(width=3, height=3, zonas_urbanas={(1, 0)}, base_position=(0, 0), battery_capacity=10)
    agent = DummyAgent(location=(0, 0))

    # Inicializa bateria manualmente (como add_agent_at faria)
    env._agent_batteries[id(agent)] = env.battery_capacity

    # Move para a direita — destino é zona urbana (1,0) com penalidade 3×
    env.execute_action(agent, "DIREITA")

    assert env.get_battery(agent) == env.battery_capacity - 3
