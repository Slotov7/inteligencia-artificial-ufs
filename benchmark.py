import random
import statistics
from problems.search_problem import PollutionMappingProblem


def run_mission(grid_size=(10, 10), n_targets=3, zonas_urbanas=None, battery_capacity=50):
    width, height = grid_size
    zonas_urbanas = zonas_urbanas or set()
    # gerar alvos aleatórios distintos
    targets = set()
    while len(targets) < n_targets:
        targets.add((random.randrange(width), random.randrange(height)))

    # inicializa problema: começa na base (0,0)
    initial = (0, 0, battery_capacity, frozenset(targets))
    problem = PollutionMappingProblem(initial=initial, goal=(0, 0), grid_size=grid_size, zonas_urbanas=zonas_urbanas)

    # Simulação simples: mover guloso até cada alvo e depois voltar
    cur_x, cur_y, bateria, alvos = initial
    pending = set(alvos)

    def move_step(tx, ty):
        nonlocal cur_x, cur_y, bateria
        if cur_x < tx:
            cur_x += 1
        elif cur_x > tx:
            cur_x -= 1
        elif cur_y < ty:
            cur_y += 1
        elif cur_y > ty:
            cur_y -= 1

        custo = 3 if (cur_x, cur_y) in zonas_urbanas else 1
        bateria -= custo

    # Visit targets
    while pending and bateria > 0:
        # escolher alvo mais próximo
        alvo = min(pending, key=lambda t: abs(t[0] - cur_x) + abs(t[1] - cur_y))
        while (cur_x, cur_y) != alvo and bateria > 0:
            move_step(*alvo)
        if (cur_x, cur_y) == alvo:
            pending.remove(alvo)

    # Voltar para base
    while (cur_x, cur_y) != (0, 0) and bateria > 0:
        move_step(0, 0)

    success = (len(pending) == 0) and (cur_x, cur_y) == (0, 0) and bateria >= 0
    return success, bateria


def main(runs: int = 100):
    results = []
    for _ in range(runs):
        success, remaining = run_mission()
        results.append((success, remaining))

    successes = [1 for s, _ in results if s]
    battery_left = [r for _, r in results]

    taxa_sucesso = sum(successes) / runs * 100
    media_bateria = statistics.mean(battery_left)
    dp_bateria = statistics.pstdev(battery_left)
    pior = min(battery_left)
    melhor = max(battery_left)

    print(f"Runs: {runs}")
    print(f"Taxa de sucesso: {taxa_sucesso:.2f}%")
    print(f"Bateria média restante: {media_bateria:.2f}")
    print(f"Desvio padrão (pop): {dp_bateria:.2f}")
    print(f"Melhor caso (maior bateria restante): {melhor}")
    print(f"Pior caso (menor bateria restante): {pior}")


if __name__ == "__main__":
    main(100)
