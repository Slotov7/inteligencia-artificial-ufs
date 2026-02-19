"""
env/estuario.py — Ambiente Estuarino do Rio Poxim

Implementa o Single Responsibility Principle (SRP):
    Esta classe gerencia APENAS o estado do mundo e a execução
    física de ações. A lógica de decisão pertence ao agente.

Classes:
    PollutionSample(Thing): Ponto de coleta de amostra no estuário
    MangroveObstacle(Obstacle): Obstáculo de mangue denso
    PoximEnvironment(XYEnvironment): Ambiente 2D do estuário

O "Urban Penalty" é aplicado em coordenadas pré-definidas como urbanas,
multiplicando o consumo de bateria por 3× conforme as diretrizes do projeto.
"""

from __future__ import annotations

import sys
import os
from typing import Any

# Adiciona aima-python ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'aima-python'))

from agents import Thing, Agent, XYEnvironment

# Importação condicional de Obstacle (pode variar entre versões do AIMA)
try:
    from agents import Obstacle
except ImportError:
    class Obstacle(Thing):
        """Fallback caso Obstacle não exista na versão do AIMA."""
        pass


# ============================================================================
# Tipos de Objetos no Ambiente
# ============================================================================

class PollutionSample(Thing):
    """Ponto de interesse para coleta de amostra ambiental.

    Representa um local no estuário onde há uma amostra de poluição
    ou contaminante a ser coletada pelo drone sentinela.

    Attributes:
        chamado_id: ID do chamado associado na API Flask.
        titulo: Nome descritivo do ponto de coleta.
        coletado: Flag indicando se a amostra já foi coletada.
    """

    def __init__(self, chamado_id: int = 0, titulo: str = "Amostra") -> None:
        super().__init__()
        self.chamado_id: int = chamado_id
        self.titulo: str = titulo
        self.coletado: bool = False

    def __repr__(self) -> str:
        status = "✓" if self.coletado else "○"
        return f"[{status}] Amostra({self.chamado_id}: {self.titulo})"


class MangroveObstacle(Obstacle):
    """Obstáculo representando vegetação densa de manguezal.

    O drone não pode atravessar estes pontos e deve replanejar
    seu caminho ao encontrá-los.
    """

    def __repr__(self) -> str:
        return "🌿 Mangue"


# ============================================================================
# Ambiente Estuarino do Rio Poxim
# ============================================================================

class PoximEnvironment(XYEnvironment):
    """Ambiente 2D representando o estuário do Rio Poxim.

    Herda de XYEnvironment (AIMA) e adiciona semântica específica:
    - Zonas urbanas com penalidade de custo (Urban Penalty 3×)
    - Rastreamento de bateria por agente
    - Lógica de coleta de amostras (Suck/Coletar)
    - Controle de missão baseado em chamados

    Args:
        width: Largura do grid (default: 10).
        height: Altura do grid (default: 10).
        zonas_urbanas: Conjunto de coordenadas que representam áreas urbanas.
        base_position: Posição (x, y) da base de decolagem/pouso.
        battery_capacity: Capacidade total de bateria do drone.

    SOLID — SRP:
        Responsabilidade única: gerenciar o estado do mundo.
        NÃO contém lógica de decisão do agente.
        NÃO contém lógica de comunicação com API.
    """

    def __init__(
        self,
        width: int = 10,
        height: int = 10,
        zonas_urbanas: set[tuple[int, int]] | None = None,
        base_position: tuple[int, int] = (0, 0),
        battery_capacity: int = 50,
    ) -> None:
        super().__init__(width, height)
        self.zonas_urbanas: set[tuple[int, int]] = zonas_urbanas or set()
        self.base_position: tuple[int, int] = base_position
        self.battery_capacity: int = battery_capacity

        # Rastreamento de bateria e amostras coletadas por agente
        self._agent_batteries: dict[int, int] = {}
        self._agent_samples: dict[int, list[PollutionSample]] = {}
        self._step_count: int = 0

    # ----------------------------------------------------------------
    # Métodos herdados de Environment que DEVEM ser implementados
    # ----------------------------------------------------------------

    def percept(self, agent: Agent) -> dict[str, Any]:
        """Retorna a percepção do agente no ambiente.

        A percepção inclui:
            - location: posição atual (x, y)
            - battery: nível atual de bateria
            - nearby_samples: amostras no raio de percepção
            - is_urban: se a posição atual é zona urbana
            - at_base: se está na posição da base

        Returns:
            Dict com todas as informações perceptíveis pelo agente.
        """
        agent_id = id(agent)
        location = agent.location
        battery = self._agent_batteries.get(agent_id, self.battery_capacity)

        # Amostras próximas (no raio de percepção padrão)
        nearby = self.things_near(agent.location, radius=1)
        nearby_samples = [
            (thing, dist) for thing, dist in nearby
            if isinstance(thing, PollutionSample) and not thing.coletado
        ]

        return {
            "location": location,
            "battery": battery,
            "nearby_samples": nearby_samples,
            "is_urban": location in self.zonas_urbanas,
            "at_base": location == self.base_position,
        }

    def execute_action(self, agent: Agent, action: str | None) -> None:
        """Executa uma ação no ambiente, atualizando o estado do mundo.

        Ações suportadas:
            - 'CIMA': Move o drone para cima (y - 1)
            - 'BAIXO': Move o drone para baixo (y + 1)
            - 'ESQUERDA': Move o drone para a esquerda (x - 1)
            - 'DIREITA': Move o drone para a direita (x + 1)
            - 'COLETAR': Coleta amostra de poluição na posição atual
            - 'NoOp' / None: Nenhuma ação (espera)

        O custo de bateria é 1 por movimento em área natural,
        e 3 por movimento em zona urbana (Urban Penalty).
        """
        if action is None or action == "NoOp":
            return

        agent_id = id(agent)
        if agent_id not in self._agent_batteries:
            self._agent_batteries[agent_id] = self.battery_capacity

        # Sem bateria → drone inoperante
        if self._agent_batteries[agent_id] <= 0:
            print(f"⚠️  Drone sem bateria em {agent.location}! Ação ignorada.")
            return

        # --- Movimentação ---
        movement_map: dict[str, tuple[int, int]] = {
            "CIMA":     (0, -1),
            "BAIXO":    (0,  1),
            "ESQUERDA": (-1, 0),
            "DIREITA":  (1,  0),
        }

        if action in movement_map:
            dx, dy = movement_map[action]
            x, y = agent.location
            new_location = (x + dx, y + dy)

            # Verifica se está dentro dos limites
            if not self.is_inbounds(new_location):
                agent.bump = True
                print(f"⚠️  Movimento bloqueado: {new_location} fora dos limites.")
                return

            # Verifica obstáculos (mangues densos)
            if self.some_things_at(new_location, Obstacle):
                agent.bump = True
                print(f"⚠️  Movimento bloqueado: obstáculo em {new_location}.")
                return

            # Calcula custo de bateria com Urban Penalty
            custo_bateria = 3 if new_location in self.zonas_urbanas else 1

            if self._agent_batteries[agent_id] < custo_bateria:
                print(f"⚠️  Bateria insuficiente para mover ({custo_bateria} necessário).")
                return

            # Executa o movimento
            old_location = agent.location
            agent.location = new_location
            self._agent_batteries[agent_id] -= custo_bateria

            zona = "🏙️  URBANA" if new_location in self.zonas_urbanas else "🌊 natural"
            print(
                f"  → {action}: {old_location} → {new_location} "
                f"| Bateria: -{custo_bateria} ({zona}) "
                f"| Restante: {self._agent_batteries[agent_id]}"
            )
            return

        # --- Coleta de Amostra ---
        if action == "COLETAR":
            samples_here = self.list_things_at(agent.location, PollutionSample)
            if samples_here:
                for sample in samples_here:
                    if not sample.coletado:
                        sample.coletado = True
                        if agent_id not in self._agent_samples:
                            self._agent_samples[agent_id] = []
                        self._agent_samples[agent_id].append(sample)
                        print(f"  🧪 Amostra coletada: {sample}")
                        # Custo de coleta = 1 unidade de bateria
                        self._agent_batteries[agent_id] -= 1
            else:
                print(f"  ℹ️  Nenhuma amostra para coletar em {agent.location}.")
            return

        print(f"  ❓ Ação desconhecida: '{action}'")

    # ----------------------------------------------------------------
    # Métodos auxiliares
    # ----------------------------------------------------------------

    def get_battery(self, agent: Agent) -> int:
        """Retorna o nível atual de bateria de um agente."""
        return self._agent_batteries.get(id(agent), self.battery_capacity)

    def get_collected_samples(self, agent: Agent) -> list[PollutionSample]:
        """Retorna a lista de amostras coletadas por um agente."""
        return self._agent_samples.get(id(agent), [])

    def is_done(self) -> bool:
        """Verifica se a simulação está concluída.

        A simulação termina quando:
        - Não há agentes vivos, OU
        - Todos os agentes estão sem bateria, OU
        - Todas as amostras foram coletadas e agentes na base
        """
        if not any(agent.is_alive() for agent in self.agents):
            return True

        # Todas as amostras coletadas?
        all_samples = [t for t in self.things if isinstance(t, PollutionSample)]
        all_collected = all(s.coletado for s in all_samples) if all_samples else True

        # Todos os agentes na base (ou sem bateria)?
        all_at_base = all(
            agent.location == self.base_position
            for agent in self.agents if agent.is_alive()
        )

        all_drained = all(
            self._agent_batteries.get(id(agent), 0) <= 0
            for agent in self.agents if agent.is_alive()
        )

        return all_collected and all_at_base or all_drained

    def step(self) -> None:
        """Executa um passo da simulação, rastreando o número de passos."""
        self._step_count += 1
        super().step()

    def get_step_count(self) -> int:
        """Retorna o número de passos executados na simulação."""
        return self._step_count

    def add_agent_at(
        self, agent: Agent, location: tuple[int, int] | None = None
    ) -> None:
        """Adiciona um agente ao ambiente em uma posição específica.

        Inicializa a bateria do agente e registra sua posição.
        """
        loc = location or self.base_position
        self.add_thing(agent, loc)
        self._agent_batteries[id(agent)] = self.battery_capacity
        self._agent_samples[id(agent)] = []

    def print_grid(self) -> None:
        """Imprime uma representação visual do grid do ambiente."""
        print(f"\n{'='*40}")
        print(f"  Grid do Estuário ({self.width}×{self.height})")
        print(f"{'='*40}")

        for y in range(self.height):
            row = ""
            for x in range(self.width):
                pos = (x, y)

                # Verifica o que há nesta posição
                has_agent = any(
                    a.location == pos for a in self.agents if a.is_alive()
                )
                has_sample = any(
                    isinstance(t, PollutionSample) and not t.coletado
                    for t in self.list_things_at(pos)
                )
                has_obstacle = self.some_things_at(pos, Obstacle)
                is_base = pos == self.base_position
                is_urban = pos in self.zonas_urbanas

                if has_agent:
                    row += " 🤖"
                elif has_sample:
                    row += " 🔴"
                elif has_obstacle:
                    row += " 🌿"
                elif is_base:
                    row += " 🏠"
                elif is_urban:
                    row += " 🏙️"
                else:
                    row += " · "

            print(f"  {y:2d} |{row}")

        # Eixo X
        x_labels = "".join(f" {x:2d}" for x in range(self.width))
        print(f"     +{'---' * self.width}")
        print(f"      {x_labels}")
        print()
