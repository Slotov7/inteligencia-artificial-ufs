"""
agents/api_gateway.py — Gateway de Comunicação com a API Flask

Implementa o Single Responsibility Principle (SRP):
    Esta classe é responsável EXCLUSIVAMENTE pela comunicação HTTP
    com a API de chamados.

Implementa o Dependency Inversion Principle (DIP):
    O agente depende desta abstração para obter dados de missão,
    não da implementação concreta da API Flask.
"""

from __future__ import annotations

from typing import Any


class APIGateway:
    """
    Gateway para comunicação com a API REST de chamados.
    Isola toda a lógica de comunicação HTTP, autenticação e
    tratamento de erros da API Flask.
    """

    def __init__(
        self,
        base_url: str = "http://localhost:5000",
        username: str = "admin",
        password: str = "123456",
        usar_simulacao: bool = False,
    ) -> None:
        self.base_url: str = base_url
        self.username: str = username
        self.password: str = password
        self.usar_simulacao: bool = usar_simulacao

        self._chamados_simulados: list[dict[str, Any]] = [
            {
                "id": 1,
                "titulo": "Amostragem Ponto Norte - Mangue Degradado",
                "descricao": "Coletar amostras no trecho norte.",
                "status": "aberto",
                "coordenadas": {"x": 7, "y": 2},
                "dados_ecotoxicologicos": None,
            },
            {
                "id": 2,
                "titulo": "Verificação de Metais Pesados - Zona Industrial",
                "descricao": "Medição de metais pesados.",
                "status": "aberto",
                "coordenadas": {"x": 3, "y": 8},
                "dados_ecotoxicologicos": None,
            },
            {
                "id": 3,
                "titulo": "Monitoramento Biodiversidade - Caranguejos",
                "descricao": "Avaliar habitat do caranguejo-uçá.",
                "status": "aberto",
                "coordenadas": {"x": 8, "y": 6},
                "dados_ecotoxicologicos": None,
            },
        ]

    def get_all_chamados(self) -> list[dict[str, Any]]:
        """Retorna todos os chamados do sistema."""
        if self.usar_simulacao:
            return list(self._chamados_simulados)

        try:
            import requests
            response = requests.get(
                f"{self.base_url}/chamados",
                auth=(self.username, self.password),
                timeout=5,
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"  ⚠️  API indisponível ({e}). Usando dados simulados.")
            self.usar_simulacao = True
            return list(self._chamados_simulados)

    def get_open_chamados(self) -> list[dict[str, Any]]:
        """Retorna apenas os chamados com status 'aberto'."""
        todos = self.get_all_chamados()
        return [c for c in todos if c.get("status") == "aberto"]

    def update_chamado_status(
        self,
        chamado_id: int,
        novo_status: str,
        dados_extras: dict[str, Any] | None = None,
    ) -> bool:
        """
        Atualiza o status de um chamado na API.
        Transições válidas: aberto → em_andamento → fechado
        """
        payload: dict[str, Any] = {"status": novo_status}
        if dados_extras:
            payload["dados_ecotoxicologicos"] = dados_extras

        if self.usar_simulacao:
            for chamado in self._chamados_simulados:
                if chamado["id"] == chamado_id:
                    chamado["status"] = novo_status
                    if dados_extras:
                        chamado["dados_ecotoxicologicos"] = dados_extras
                    print(
                        f"  📡 [SIM] Chamado #{chamado_id} → {novo_status}"
                    )
                    return True
            return False

        try:
            import requests
            response = requests.put(
                f"{self.base_url}/chamados/{chamado_id}",
                json=payload,
                auth=(self.username, self.password),
                timeout=5,
            )
            response.raise_for_status()
            print(f"  📡 [API] Chamado #{chamado_id} → {novo_status}")
            return True
        except Exception as e:
            print(f"  ⚠️  Falha ao atualizar chamado #{chamado_id}: {e}")
            for chamado in self._chamados_simulados:
                if chamado["id"] == chamado_id:
                    chamado["status"] = novo_status
            return False

    def get_chamado_coordinates(
        self, chamado: dict[str, Any]
    ) -> tuple[int, int]:
        """Extrai as coordenadas (x, y) de um chamado."""
        coords = chamado.get("coordenadas", {"x": 0, "y": 0})
        return (coords["x"], coords["y"])
