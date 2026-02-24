"""
main_autonomous.py — Loop de Coordenação do Sistema Autônomo

Script principal que integra todos os módulos seguindo a arquitetura SOLID:
    - PoximEnvironment (SRP): gerencia o estado do mundo
    - PollutionMappingProblem (OCP): define o problema de busca
    - AutonomousDroneAgent (LSP): toma decisões inteligentes
    - APIGateway (SRP/DIP): comunica com a API de chamados

Uso:
    python main_autonomous.py
    python main_autonomous.py --simulacao
"""

from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'aima-python'))

from agents import Agent

from env.estuario import PoximEnvironment, PollutionSample, MangroveObstacle
from drone_agents.api_gateway import APIGateway
from drone_agents.drone_agent import AutonomousDroneAgent


def configurar_ambiente() -> tuple[
    PoximEnvironment,
    set[tuple[int, int]],
    set[tuple[int, int]],
]:
    """
    Configura o ambiente estuarino do Rio Poxim.

    Cria o grid 10×10 representando a região do estuário com:
    - Obstáculos (mangues densos, pontes)
    - Zonas urbanas (áreas residenciais de Aracaju)
    - Base de operações (ponto de decolagem/pouso)
    """
    zonas_urbanas: set[tuple[int, int]] = {
        (1, 1), (2, 1), (3, 1),
        (1, 2), (2, 2),
        (5, 5), (6, 5),
        (4, 3), (5, 3),
    }

    obstaculos: set[tuple[int, int]] = {
        (4, 4),
        (5, 4),
        (6, 3),
        (7, 4),
        (2, 6),
    }

    env = PoximEnvironment(
        width=10,
        height=10,
        zonas_urbanas=zonas_urbanas,
        base_position=(0, 0),
        battery_capacity=60,
    )

    for pos in obstaculos:
        env.add_thing(MangroveObstacle(), pos)

    return env, obstaculos, zonas_urbanas


def executar_missao(usar_simulacao: bool = False) -> None:
    """Executa a missão completa de monitoramento autônomo."""

    print("=" * 64)
    print("  🛰️  SISTEMA ADEMA-DRONE — Monitoramento do Rio Poxim")
    print("  📍 Estuário do Rio Poxim, Aracaju-SE")
    print("=" * 64)

    print("\n🌊 Configurando ambiente estuarino...")
    env, obstaculos, zonas_urbanas = configurar_ambiente()

    print("📡 Inicializando comunicação com API de chamados...")
    gateway = APIGateway(usar_simulacao=usar_simulacao)

    print("🤖 Inicializando Drone Sentinela Autônomo...")
    drone_program = AutonomousDroneAgent(
        api_gateway=gateway,
        grid_size=(10, 10),
        obstaculos=obstaculos,
        zonas_urbanas=zonas_urbanas,
        base_position=(0, 0),
        battery_capacity=60,
    )

    drone = Agent(drone_program)

    chamados = gateway.get_open_chamados()
    for chamado in chamados:
        coord = gateway.get_chamado_coordinates(chamado)
        sample = PollutionSample(
            chamado_id=chamado["id"],
            titulo=chamado["titulo"],
        )
        env.add_thing(sample, coord)

    env.add_agent_at(drone, location=(0, 0))

    env.print_grid()

    print("\n" + "=" * 64)
    print("  ▶️  INICIANDO SIMULAÇÃO DE MISSÃO")
    print("=" * 64)

    max_steps = 200
    step = 0

    while not env.is_done() and step < max_steps:
        step += 1
        print(f"\n{'─'*40}")
        print(f"  Passo {step} | Posição: {drone.location} "
              f"| Bateria: {env.get_battery(drone)}")
        print(f"{'─'*40}")

        env.step()

        if env.get_battery(drone) <= 0:
            print("\n⚠️  BATERIA ESGOTADA! Missão interrompida.")
            break

    print("\n" + "=" * 64)
    print("  📊 RELATÓRIO FINAL DA MISSÃO")
    print("=" * 64)

    report = drone_program.get_mission_report()
    samples_collected = env.get_collected_samples(drone)

    posicao_final = drone.location
    na_base = posicao_final == (0, 0)
    all_samples = [t for t in env.things if isinstance(t, PollutionSample)]
    missao_ok = all(s.coletado for s in all_samples) and na_base

    print(f"\n  Passos executados:      {env.get_step_count()}")
    print(f"  Chamados processados:   {report['chamados_processados']}")
    print(f"  Chamados pendentes:     {report['chamados_pendentes']}")
    print(f"  Bateria restante:       {env.get_battery(drone)}")
    print(f"  Posição final:          {posicao_final}")
    print(f"  Na base:                {'✅ Sim' if na_base else '❌ Não'}")
    print(f"  Missão completa:        {'✅ Sim' if missao_ok else '❌ Não'}")

    if samples_collected:
        print(f"\n  🧪 Amostras coletadas ({len(samples_collected)}):")
        for sample in samples_collected:
            print(f"     - {sample}")

    env.print_grid()

    print("\n" + "=" * 64)
    print("  🏁 FIM DA SIMULAÇÃO")
    print("=" * 64)

if __name__ == "__main__":
    modo_simulacao = "--simulacao" in sys.argv or "--sim" in sys.argv

    if modo_simulacao:
        print("ℹ️  Modo simulação ativado (sem conexão com API Flask)")
    else:
        print("ℹ️  Tentando conectar com API Flask em http://localhost:5000")
        print("   (Use --simulacao para executar sem a API)")

    executar_missao(usar_simulacao=modo_simulacao)
