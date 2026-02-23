from drone_agents.api_gateway import APIGateway


def test_api_gateway_fallback_simulation_mode():
    gateway = APIGateway(usar_simulacao=True)

    chamados = gateway.get_all_chamados()
    assert isinstance(chamados, list)
    assert len(chamados) >= 1

    # Atualiza um chamado simulado e verifica retorno
    primeiro_id = chamados[0]["id"]
    ok = gateway.update_chamado_status(primeiro_id, "fechado")
    assert ok is True

    # Confirma que o status foi alterado localmente
    novos = gateway.get_all_chamados()
    for c in novos:
        if c["id"] == primeiro_id:
            assert c["status"] == "fechado"
