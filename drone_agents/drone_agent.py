"""
agents/drone_agent.py — Agente Autônomo de Drone Sentinela

Implementa o Liskov Substitution Principle (LSP):
    AutonomousDroneAgent pode ser substituído por DroneManual
    sem quebrar o simulador do ambiente.

Herda de SimpleProblemSolvingAgentProgram (AIMA, Figura 3.1):
    O agente formula objetivos, cria problemas de busca e
    executa planos gerados por A*.

A lógica de comunicação com a API é delegada ao APIGateway (SRP).
A lógica de busca é delegada ao PollutionMappingProblem (OCP).
"""

from __future__ import annotations

import sys
import os
from typing import Any

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'aima-python'))

from search import SimpleProblemSolvingAgentProgram, astar_search

from drone_agents.api_gateway import APIGateway
from problems.search_problem import PollutionMappingProblem


class AutonomousDroneAgent(SimpleProblemSolvingAgentProgram):
    """
    Agente autônomo para monitoramento do estuário do Rio Poxim.

    Herda de SimpleProblemSolvingAgentProgram (AIMA) e implementa o ciclo
    completo de resolução de problemas:
        1. update_state: Atualiza modelo interno com percepções
        2. formulate_goal: Seleciona próximo chamado aberto
        3. formulate_problem: Cria instância de PollutionMappingProblem
        4. search: Executa A* para encontrar caminho ótimo
    """

    def __init__(
        self,
        api_gateway: APIGateway,
        grid_size: tuple[int, int] = (10, 10),
        obstaculos: set[tuple[int, int]] | None = None,
        zonas_urbanas: set[tuple[int, int]] | None = None,
        base_position: tuple[int, int] = (0, 0),
        battery_capacity: int = 50,
    ) -> None:
        super().__init__(initial_state=None)

        self.api_gateway: APIGateway = api_gateway

        self.grid_size: tuple[int, int] = grid_size
        self.obstaculos: set[tuple[int, int]] = obstaculos or set()
        self.zonas_urbanas: set[tuple[int, int]] = zonas_urbanas or set()
        self.base_position: tuple[int, int] = base_position
        self.battery_capacity: int = battery_capacity

        self._position: tuple[int, int] = base_position
        self._battery: int = battery_capacity
        self._targets: frozenset[tuple[int, int]] = frozenset()
        self._current_chamado: dict[str, Any] | None = None
        self._chamados_processados: list[dict[str, Any]] = []
        self._returning_to_base: bool = False
        self._mission_complete: bool = False

        self._sync_initial_targets()

    def _sync_initial_targets(self) -> None:
        """Sincroniza alvos iniciais a partir dos chamados abertos na API."""
        chamados_abertos = self.api_gateway.get_open_chamados()
        target_coords: set[tuple[int, int]] = set()

        for chamado in chamados_abertos:
            coord = self.api_gateway.get_chamado_coordinates(chamado)
            target_coords.add(coord)

        self._targets = frozenset(target_coords)
        self._pending_chamados = list(chamados_abertos)

        print(f"\n📋 Chamados abertos sincronizados: {len(chamados_abertos)}")
        for chamado in chamados_abertos:
            coord = self.api_gateway.get_chamado_coordinates(chamado)
            print(f"   #{chamado['id']}: {chamado['titulo']} @ {coord}")

    def update_state(self, state: Any, percept: Any) -> dict[str, Any]:
        """
        Atualiza o modelo interno do agente com base nas percepções.
        Recebe o percept do ambiente e atualiza o estado interno do agente.
        """
        if isinstance(percept, dict):
            self._position = percept.get("location", self._position)
            self._battery = percept.get("battery", self._battery)
        elif isinstance(percept, list):
            pass

        if self._position in self._targets:
            self._targets = self._targets - frozenset({self._position})

            for chamado in self._pending_chamados:
                coord = self.api_gateway.get_chamado_coordinates(chamado)
                if coord == self._position:
                    self.api_gateway.update_chamado_status(
                        chamado["id"],
                        "fechado",
                        dados_extras={
                            "bateria_restante": self._battery,
                            "posicao_coleta": list(self._position),
                        },
                    )
                    self._chamados_processados.append(chamado)
                    self._pending_chamados.remove(chamado)
                    break

        return {
            "position": self._position,
            "battery": self._battery,
            "targets": self._targets,
            "at_base": self._position == self.base_position,
        }

    def _calcular_utilidade(
        self, destino: tuple[int, int], retorno_base: bool = False
    ) -> float:
        """
        Calcula a Utilidade Máxima Esperada (MEU) de ir a um destino.
        Implementa o framework de decisão do AIMA Capítulo 16:
            U(ação) = P(sucesso) × Recompensa - P(falha) × Penalidade
        """
        dist_destino = (
            abs(destino[0] - self._position[0])
            + abs(destino[1] - self._position[1])
        )

        if retorno_base:
            dist_total = dist_destino
        else:
            dist_retorno_base = (
                abs(destino[0] - self.base_position[0])
                + abs(destino[1] - self.base_position[1])
            )
            dist_total = dist_destino + dist_retorno_base

        if dist_total == 0:
            return 100.0

        custo_estimado = dist_total * 1.5
        p_sucesso = min(1.0, self._battery / max(custo_estimado, 1))

        if retorno_base:
            recompensa = 50.0
            penalidade = 100.0
        else:
            recompensa = 100.0
            penalidade = 150.0

        risco_urbano = 1.0
        if destino in self.zonas_urbanas:
            risco_urbano = 0.85

        utilidade = (
            p_sucesso * recompensa * risco_urbano
            - (1 - p_sucesso) * penalidade
        )

        return utilidade

    def formulate_goal(self, state: Any) -> tuple[int, int] | None:
        """
        Formula o próximo objetivo do agente usando Utilidade Máxima Esperada.

        Estratégia com MEU (AIMA Cap. 16):
        1. Se missão completa → None
        2. Se não há alvos → retorna à base
        3. Se bateria >= 30% → seleciona alvo mais próximo (guloso)
        4. Se bateria < 30% → calcula U(ir ao alvo) vs U(voltar à base)
           e escolhe a ação com maior utilidade esperada
        """
        if self._mission_complete:
            return None

        if not self._targets:
            if self._position == self.base_position:
                self._mission_complete = True
                print("\n✅ Missão completa! Drone na base.")
                return None
            self._returning_to_base = True
            print(f"\n🏠 Todos os alvos coletados. Retornando à base...")
            return self.base_position

        alvo_mais_proximo = min(
            self._targets,
            key=lambda t: abs(t[0] - self._position[0])
            + abs(t[1] - self._position[1]),
        )

        limiar_bateria = 0.30 * self.battery_capacity

        if self._battery < limiar_bateria:
            u_alvo = self._calcular_utilidade(alvo_mais_proximo, retorno_base=False)
            u_base = self._calcular_utilidade(self.base_position, retorno_base=True)

            print(f"\n⚡ Bateria baixa ({self._battery}/{self.battery_capacity}"
                  f" = {self._battery / self.battery_capacity * 100:.0f}%)")
            print(f"  📊 MEU — Utilidade Máxima Esperada (AIMA Cap. 16):")
            print(f"     U(ir ao alvo {alvo_mais_proximo})  = {u_alvo:.2f}")
            print(f"     U(voltar à base {self.base_position}) = {u_base:.2f}")

            if u_base > u_alvo:
                print(f"  🔋 Decisão MEU: RETORNAR À BASE (utilidade maior)")
                self._returning_to_base = True
                self._targets = frozenset()
                return self.base_position
            else:
                print(f"  🎯 Decisão MEU: IR AO ALVO (utilidade maior)")

        for chamado in self._pending_chamados:
            coord = self.api_gateway.get_chamado_coordinates(chamado)
            if coord == alvo_mais_proximo:
                self.api_gateway.update_chamado_status(
                    chamado["id"], "em_andamento"
                )
                self._current_chamado = chamado
                break

        print(
            f"\n🎯 Objetivo: {alvo_mais_proximo} "
            f"(Bateria: {self._battery})"
        )
        return alvo_mais_proximo

    def formulate_problem(
        self, state: Any, goal: tuple[int, int]
    ) -> PollutionMappingProblem:
        """
        Formula o problema de busca para o objetivo atual.
        Cria uma instância de PollutionMappingProblem com o estado
        atual do agente e o objetivo determinado por formulate_goal.
        """
        if self._returning_to_base:
            targets = frozenset()
        else:
            targets = frozenset({goal})

        initial_state = (
            self._position[0],
            self._position[1],
            self._battery,
            targets,
        )

        problem = PollutionMappingProblem(
            initial=initial_state,
            goal=self.base_position if self._returning_to_base else goal,
            grid_size=self.grid_size,
            obstaculos=self.obstaculos,
            zonas_urbanas=self.zonas_urbanas,
        )

        print(
            f"  📐 Problema formulado: {self._position} → {goal} "
            f"(grid {self.grid_size[0]}×{self.grid_size[1]})"
        )
        return problem

    def search(self, problem: PollutionMappingProblem) -> list[str]:
        """
        Executa busca A* para encontrar sequência ótima de ações.
        Utiliza astar_search do AIMA com a heurística h() definida
        no PollutionMappingProblem (Manhattan + Vento Atlântico).
        """
        print("  🔍 Executando A* Search...")

        result = astar_search(problem)

        if result is None:
            print("  ❌ Nenhuma solução encontrada!")
            if not self._returning_to_base:
                print("  🔄 Tentando retornar à base...")
                self._returning_to_base = True
                self._targets = frozenset()
                return_problem = PollutionMappingProblem(
                    initial=(
                        self._position[0],
                        self._position[1],
                        self._battery,
                        frozenset(),
                    ),
                    goal=self.base_position,
                    grid_size=self.grid_size,
                    obstaculos=self.obstaculos,
                    zonas_urbanas=self.zonas_urbanas,
                )
                fallback = astar_search(return_problem)
                if fallback:
                    actions = fallback.solution()
                    print(f"  ✈️  Rota de retorno: {actions}")
                    return actions
            return []

        actions = result.solution()

        if not self._returning_to_base:
            actions.append("COLETAR")

        print(f"  ✈️  Plano: {actions} ({len(actions)} ações)")
        return actions

    # ----------------------------------------------------------------
    # Métodos auxiliares
    # ----------------------------------------------------------------

    def get_mission_report(self) -> dict[str, Any]:
        """Gera relatório da missão executada."""
        return {
            "chamados_processados": len(self._chamados_processados),
            "chamados_pendentes": len(self._pending_chamados),
            "bateria_restante": self._battery,
            "posicao_final": self._position,
            "na_base": self._position == self.base_position,
            "missao_completa": self._mission_complete,
        }
