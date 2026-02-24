"""
app.py — API Flask para Gestão de Chamados (Missões de Monitoramento)

Backend desenvolvido por Samuel para gerenciar chamados/tickets de missão
no estuário do Rio Poxim. Fornece autenticação HTTP Basic e CRUD completo
com persistência em memória.

Endpoints:
    GET    /chamados       — Lista todos os chamados
    GET    /chamados/<id>  — Detalhe de um chamado
    POST   /chamados       — Criar novo chamado
    PUT    /chamados/<id>  — Atualizar chamado (status, dados ecotoxicológicos)
    DELETE /chamados/<id>  — Remover chamado
"""

from functools import wraps
from typing import Any

from flask import Flask, jsonify, request, Response

app = Flask(__name__)


USUARIOS: dict[str, str] = {
    "admin": "123456"
}

chamados: list[dict[str, Any]] = [
    {
        "id": 1,
        "titulo": "Amostragem Ponto Norte - Mangue Degradado",
        "descricao": "Coletar amostras de água e sedimento no trecho norte "
                     "onde há despejo de esgoto doméstico identificado.",
        "status": "aberto",
        "coordenadas": {"x": 7, "y": 2},
        "dados_ecotoxicologicos": None
    },
    {
        "id": 2,
        "titulo": "Verificação de Metais Pesados - Zona Industrial",
        "descricao": "Realizar medição de metais pesados próximo à zona "
                     "industrial adjacente ao estuário.",
        "status": "aberto",
        "coordenadas": {"x": 3, "y": 8},
        "dados_ecotoxicologicos": None
    },
    {
        "id": 3,
        "titulo": "Monitoramento Biodiversidade - Berçário de Caranguejos",
        "descricao": "Avaliar condições do habitat do caranguejo-uçá "
                     "(Ucides cordatus) no manguezal sul.",
        "status": "aberto",
        "coordenadas": {"x": 8, "y": 6},
        "dados_ecotoxicologicos": None
    },
]

proximo_id: int = 4

def autenticar(f):
    """
    Decorator que exige autenticação HTTP Basic para acessar o endpoint.
    Verifica as credenciais contra o dicionário USUARIOS.
    Retorna 401 Unauthorized se as credenciais forem inválidas.
    """
    @wraps(f)
    def decorador(*args, **kwargs):
        auth = request.authorization
        if not auth or USUARIOS.get(auth.username) != auth.password:
            return Response(
                "Acesso não autorizado. Credenciais inválidas.",
                401,
                {"WWW-Authenticate": 'Basic realm="Login Necessário"'}
            )
        return f(*args, **kwargs)
    return decorador

@app.route("/chamados", methods=["GET"])
@autenticar
def listar_chamados():
    """Lista todos os chamados cadastrados no sistema."""
    return jsonify(chamados), 200


@app.route("/chamados/<int:chamado_id>", methods=["GET"])
@autenticar
def obter_chamado(chamado_id: int):
    """Retorna os detalhes de um chamado específico pelo ID."""
    for chamado in chamados:
        if chamado["id"] == chamado_id:
            return jsonify(chamado), 200
    return jsonify({"erro": "Chamado não encontrado"}), 404


@app.route("/chamados", methods=["POST"])
@autenticar
def criar_chamado():
    """
    Cria um novo chamado de missão.

    Corpo da requisição (JSON):
        titulo (str): Título descritivo do chamado
        descricao (str): Descrição detalhada da missão
        coordenadas (dict): {"x": int, "y": int} — posição no grid
        status (str, opcional): Status inicial (default: "aberto")
    """
    global proximo_id
    dados = request.get_json()

    if not dados or "titulo" not in dados:
        return jsonify({"erro": "Campo 'titulo' é obrigatório"}), 400

    coordenadas = dados.get("coordenadas", {"x": 0, "y": 0})
    if not isinstance(coordenadas, dict) or "x" not in coordenadas or "y" not in coordenadas:
        return jsonify({"erro": "Coordenadas devem ter formato {'x': int, 'y': int}"}), 400

    novo_chamado: dict[str, Any] = {
        "id": proximo_id,
        "titulo": dados["titulo"],
        "descricao": dados.get("descricao", ""),
        "status": dados.get("status", "aberto"),
        "coordenadas": coordenadas,
        "dados_ecotoxicologicos": None
    }

    chamados.append(novo_chamado)
    proximo_id += 1

    return jsonify(novo_chamado), 201


@app.route("/chamados/<int:chamado_id>", methods=["PUT"])
@autenticar
def atualizar_chamado(chamado_id: int):
    """
    Atualiza um chamado existente.
    Permite alterar status (aberto → em_andamento → fechado),
    dados ecotoxicológicos e demais campos.
    """
    dados = request.get_json()
    if not dados:
        return jsonify({"erro": "Corpo da requisição vazio"}), 400

    for chamado in chamados:
        if chamado["id"] == chamado_id:
            if "status" in dados:
                chamado["status"] = dados["status"]
            if "titulo" in dados:
                chamado["titulo"] = dados["titulo"]
            if "descricao" in dados:
                chamado["descricao"] = dados["descricao"]
            if "coordenadas" in dados:
                chamado["coordenadas"] = dados["coordenadas"]
            if "dados_ecotoxicologicos" in dados:
                chamado["dados_ecotoxicologicos"] = dados["dados_ecotoxicologicos"]

            return jsonify(chamado), 200

    return jsonify({"erro": "Chamado não encontrado"}), 404


@app.route("/chamados/<int:chamado_id>", methods=["DELETE"])
@autenticar
def deletar_chamado(chamado_id: int):
    """Remove um chamado do sistema."""
    for i, chamado in enumerate(chamados):
        if chamado["id"] == chamado_id:
            chamados.pop(i)
            return jsonify({"mensagem": "Chamado removido com sucesso"}), 200

    return jsonify({"erro": "Chamado não encontrado"}), 404


if __name__ == "__main__":
    print("=" * 60)
    print("  API de Gestão de Chamados — Rio Poxim")
    print("  Servidor: http://localhost:5000")
    print("  Credenciais: admin / 123456")
    print("=" * 60)
    app.run(debug=True, port=5000)
