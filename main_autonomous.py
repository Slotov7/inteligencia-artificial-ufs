"""
main_autonomous.py — Loop de Coordenação do Sistema Autônomo

Script principal que integra todos os módulos seguindo a arquitetura SOLID:
    - PoximEnvironment (SRP): gerencia o estado do mundo
    - PollutionMappingProblem (OCP): define o problema de busca
    - AutonomousDroneAgent (LSP): toma decisões inteligentes
    - APIGateway (SRP/DIP): comunica com a API de chamados

Fluxo de execução:
    1. Configura o ambiente estuarino com obstáculos e zonas urbanas
    2. Sincroniza chamados abertos da API Flask
    3. Adiciona amostras de poluição nas coordenadas dos chamados
    4. Executa o loop de simulação até missão completa
    5. Imprime relatório final da missão

Uso:
    # Com API Flask rodando:
    python main_autonomous.py

    # Sem API (modo simulação):
    python main_autonomous.py --simulacao
"""

from __future__ import annotations

import sys
import os

# Adiciona aima-python ao path
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
    """Configura o ambiente estuarino do Rio Poxim.

    Cria o grid 10×10 representando a região do estuário com:
    - Obstáculos (mangues densos, pontes)
    - Zonas urbanas (áreas residenciais de Aracaju)
    - Base de operações (ponto de decolagem/pouso)

    Returns:
        Tupla (ambiente, obstáculos, zonas_urbanas)
    """
    # Zonas urbanas de Aracaju adjacentes ao estuário
    # Representam áreas com Urban Penalty (3× custo de bateria)
    zonas_urbanas: set[tuple[int, int]] = {
        (1, 1), (2, 1), (3, 1),  # Bairro norte
        (1, 2), (2, 2),          # Centro urbano
        (5, 5), (6, 5),          # Zona comercial
        (4, 3), (5, 3),          # Área residencial
    }

    # Obstáculos: mangues densos e estruturas
    obstaculos: set[tuple[int, int]] = {
        (4, 4),  # Mangue denso central
        (5, 4),  # Mangue denso central
        (6, 3),  # Ponte sobre o rio
        (7, 4),  # Vegetação densa
        (2, 6),  # Mangue ribeirinho
    }

    # Cria ambiente
    env = PoximEnvironment(
        width=10,
        height=10,
        zonas_urbanas=zonas_urbanas,
        base_position=(0, 0),
        battery_capacity=60,
    )

    # Adiciona obstáculos ao ambiente
    for pos in obstaculos:
        env.add_thing(MangroveObstacle(), pos)

    return env, obstaculos, zonas_urbanas


def executar_missao(usar_simulacao: bool = False) -> None:
    """Executa a missão completa de monitoramento autônomo.

    Args:
        usar_simulacao: Se True, usa dados simulados em vez da API Flask.
    """

    print("=" * 64)
    print("  🛰️  SISTEMA ADEMA-DRONE — Monitoramento do Rio Poxim")
    print("  📍 Estuário do Rio Poxim, Aracaju-SE")
    print("=" * 64)

    # 1. Configura ambiente
    print("\n🌊 Configurando ambiente estuarino...")
    env, obstaculos, zonas_urbanas = configurar_ambiente()

    # 2. Inicializa gateway de comunicação com a API
    print("📡 Inicializando comunicação com API de chamados...")
    gateway = APIGateway(usar_simulacao=usar_simulacao)

    # 3. Cria o agente autônomo
    print("🤖 Inicializando Drone Sentinela Autônomo...")
    drone_program = AutonomousDroneAgent(
        api_gateway=gateway,
        grid_size=(10, 10),
        obstaculos=obstaculos,
        zonas_urbanas=zonas_urbanas,
        base_position=(0, 0),
        battery_capacity=60,
    )

    # Transforma o programa em um agente AIMA
    drone = Agent(drone_program)

    # 4. Adiciona amostras de poluição nos pontos dos chamados
    chamados = gateway.get_open_chamados()
    for chamado in chamados:
        coord = gateway.get_chamado_coordinates(chamado)
        sample = PollutionSample(
            chamado_id=chamado["id"],
            titulo=chamado["titulo"],
        )
        env.add_thing(sample, coord)

    # 5. Adiciona o drone ao ambiente na base
    env.add_agent_at(drone, location=(0, 0))

    # Imprime estado inicial do grid
    env.print_grid()

    # 6. Loop principal de simulação
    print("\n" + "=" * 64)
    print("  ▶️  INICIANDO SIMULAÇÃO DE MISSÃO")
    print("=" * 64)

    max_steps = 200  # Proteção contra loops infinitos
    step = 0

    while not env.is_done() and step < max_steps:
        step += 1
        print(f"\n{'─'*40}")
        print(f"  Passo {step} | Posição: {drone.location} "
              f"| Bateria: {env.get_battery(drone)}")
        print(f"{'─'*40}")

        env.step()

        # Verifica se o drone ficou sem bateria
        if env.get_battery(drone) <= 0:
            print("\n⚠️  BATERIA ESGOTADA! Missão interrompida.")
            break

    # 7. Relatório final
    print("\n" + "=" * 64)
    print("  📊 RELATÓRIO FINAL DA MISSÃO")
    print("=" * 64)

    report = drone_program.get_mission_report()
    samples_collected = env.get_collected_samples(drone)

    # Usa posição real do drone no ambiente (pode diferir do estado
    # interno do agente se is_done() interrompeu antes do próximo percept)
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

    # Grid final
    env.print_grid()

    print("\n" + "=" * 64)
    print("  🏁 FIM DA SIMULAÇÃO")
    print("=" * 64)


# ============================================================================
# Ponto de Entrada
# ============================================================================

if __name__ == "__main__":
    # Verifica se o modo simulação foi solicitado
    modo_simulacao = "--simulacao" in sys.argv or "--sim" in sys.argv

    if modo_simulacao:
        print("ℹ️  Modo simulação ativado (sem conexão com API Flask)")
    else:
        print("ℹ️  Tentando conectar com API Flask em http://localhost:5000")
        print("   (Use --simulacao para executar sem a API)")

    executar_missao(usar_simulacao=modo_simulacao)
