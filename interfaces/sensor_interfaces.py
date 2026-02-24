"""
interfaces/sensor_interfaces.py — Protocolos Abstratos para Sensores

Implementa o Interface Segregation Principle (ISP) e o
Dependency Inversion Principle (DIP) do SOLID.

O agente depende destas abstrações, nunca de implementações concretas.
Isso permite:
    - Testar o sistema com simuladores antes do hardware real
    - Adicionar novos sensores via composição, não herança
    - Manter interfaces segregadas por funcionalidade
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class TelemetrySensor(Protocol):
    """
    Sensor de telemetria para posição e energia.
    Responsável por fornecer dados de GPS de alta precisão
    e nível de bateria do drone em tempo real.
    """

    def get_position(self) -> tuple[float, float]:
        """Retorna coordenadas (x, y) do drone no grid de monitoramento."""
        ...

    def get_battery_level(self) -> float:
        """Retorna nível de bateria como percentual (0.0 a 100.0)."""
        ...


@runtime_checkable
class ChemicalSensor(Protocol):
    """
    Sensor de análise química em tempo real.
    Detecta concentrações de poluentes e metais pesados
    na água e sedimentos do estuário.
    """

    def get_contamination_reading(self) -> dict[str, float]:
        """
        Retorna leitura de contaminantes detectados.
        Ex: {"mercurio": 0.05, "chumbo": 0.12, "OD": 3.2}
        """
        ...


@runtime_checkable
class ProximitySensor(Protocol):
    """
    Sensor de proximidade (Lidar/Sonar).
    Detecta obstáculos estáticos e dinâmicos ao redor do drone.
    """

    def get_obstacles_nearby(self, radius: float = 1.0) -> list[tuple[float, float]]:
        """
        Retorna lista de coordenadas de obstáculos no raio especificado.
        """
        ...


@runtime_checkable
class VisionSensor(Protocol):
    """
    Sensor de visão computacional (câmeras térmicas e RGB).
    Captura imagens para análise de saúde do manguezal.
    """

    def capture_image(self) -> bytes:
        """Captura e retorna imagem no formato bytes (JPEG/PNG)."""
        ...

    def get_thermal_reading(self) -> float:
        """Retorna temperatura superficial da água em °C."""
        ...

class SimulatedTelemetry:
    """Implementação simulada do sensor de telemetria."""

    def __init__(self, initial_position: tuple[float, float] = (0.0, 0.0),
                 initial_battery: float = 100.0) -> None:
        self._position = initial_position
        self._battery = initial_battery

    def get_position(self) -> tuple[float, float]:
        return self._position

    def get_battery_level(self) -> float:
        return self._battery

    def set_position(self, position: tuple[float, float]) -> None:
        self._position = position

    def consume_battery(self, amount: float) -> None:
        self._battery = max(0.0, self._battery - amount)


class SimulatedChemical:
    """Implementação simulada do sensor químico."""

    def __init__(self, default_readings: dict[str, float] | None = None) -> None:
        self._readings = default_readings or {
            "mercurio": 0.0,
            "chumbo": 0.0,
            "OD": 6.5
        }

    def get_contamination_reading(self) -> dict[str, float]:
        return dict(self._readings)

    def set_contamination(self, readings: dict[str, float]) -> None:
        self._readings.update(readings)
