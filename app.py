"""
app.py — API Flask para Gestão de Chamados (Missões de Monitoramento)

Backend para gerenciar chamados/tickets de missão no estuário do Rio Poxim.
Fornece autenticação HTTP Basic, CRUD completo e documentação Swagger em /apidocs.

Endpoints:
    GET    /chamados       — Lista todos os chamados
    GET    /chamados/<id>  — Detalhe de um chamado
    POST   /chamados       — Criar novo chamado
    PUT    /chamados/<id>  — Atualizar chamado (status, dados ecotoxicológicos)
    DELETE /chamados/<id>  — Remover chamado
    GET    /apidocs        — Interface Swagger UI
"""

from functools import wraps
from typing import Any

from flask import Flask, jsonify, request, Response
from flasgger import Swagger

app = Flask(__name__)

swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": "apispec",
            "route": "/apispec.json",
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/apidocs",
}

swagger_template = {
    "swagger": "2.0",
    "info": {
        "title": "ADEMA-Drone — API de Chamados Rio Poxim",
        "description": (
            "API REST para gestão de chamados de monitoramento ambiental "
            "no estuário do Rio Poxim, Aracaju-SE. "
            "Use **admin / 123456** para autenticação HTTP Basic."
        ),
        "version": "1.0.0",
    },
    "host": "localhost:5000",
    "basePath": "/",
    "schemes": ["http"],
    "securityDefinitions": {
        "basicAuth": {
            "type": "basic",
            "description": "Usuário: admin | Senha: 123456",
        }
    },
    "security": [{"basicAuth": []}],
}

Swagger(app, config=swagger_config, template=swagger_template)

# ---------------------------------------------------------------------------
# Dados em memória
# ---------------------------------------------------------------------------

USUARIOS: dict[str, str] = {"admin": "123456"}

chamados: list[dict[str, Any]] = []

proximo_id: int = 1


# ---------------------------------------------------------------------------
# Autenticação
# ---------------------------------------------------------------------------

def autenticar(f):
    """Decorator que exige autenticação HTTP Basic."""
    @wraps(f)
    def decorador(*args, **kwargs):
        auth = request.authorization
        if not auth or USUARIOS.get(auth.username) != auth.password:
            return Response(
                "Acesso não autorizado. Credenciais inválidas.",
                401,
                {"WWW-Authenticate": 'Basic realm="Login Necessário"'},
            )
        return f(*args, **kwargs)
    return decorador


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.route("/chamados", methods=["GET"])
@autenticar
def listar_chamados():
    """
    Lista todos os chamados cadastrados.
    ---
    tags:
      - Chamados
    security:
      - basicAuth: []
    responses:
      200:
        description: Lista de chamados
        schema:
          type: array
          items:
            $ref: '#/definitions/Chamado'
    definitions:
      Chamado:
        type: object
        properties:
          id:
            type: integer
            example: 1
          titulo:
            type: string
            example: "Amostragem Ponto Norte"
          descricao:
            type: string
          status:
            type: string
            enum: [aberto, em_andamento, fechado]
            example: aberto
          coordenadas:
            type: object
            properties:
              x:
                type: integer
                example: 7
              y:
                type: integer
                example: 2
          dados_ecotoxicologicos:
            type: object
    """
    return jsonify(chamados), 200


@app.route("/chamados/<int:chamado_id>", methods=["GET"])
@autenticar
def obter_chamado(chamado_id: int):
    """
    Retorna os detalhes de um chamado específico.
    ---
    tags:
      - Chamados
    security:
      - basicAuth: []
    parameters:
      - in: path
        name: chamado_id
        type: integer
        required: true
        description: ID do chamado
    responses:
      200:
        description: Chamado encontrado
        schema:
          $ref: '#/definitions/Chamado'
      404:
        description: Chamado não encontrado
    """
    for chamado in chamados:
        if chamado["id"] == chamado_id:
            return jsonify(chamado), 200
    return jsonify({"erro": "Chamado não encontrado"}), 404


@app.route("/chamados", methods=["POST"])
@autenticar
def criar_chamado():
    """
    Cria um novo chamado de missão.
    ---
    tags:
      - Chamados
    security:
      - basicAuth: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - titulo
            - coordenadas
          properties:
            titulo:
              type: string
              example: "Novo Ponto de Coleta"
            descricao:
              type: string
              example: "Descrição da missão"
            status:
              type: string
              enum: [aberto, em_andamento, fechado]
              example: aberto
            coordenadas:
              type: object
              required: [x, y]
              properties:
                x:
                  type: integer
                  example: 5
                y:
                  type: integer
                  example: 5
    responses:
      201:
        description: Chamado criado com sucesso
        schema:
          $ref: '#/definitions/Chamado'
      400:
        description: Dados inválidos
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
        "dados_ecotoxicologicos": None,
    }

    chamados.append(novo_chamado)
    proximo_id += 1

    return jsonify(novo_chamado), 201


@app.route("/chamados/<int:chamado_id>", methods=["PUT"])
@autenticar
def atualizar_chamado(chamado_id: int):
    """
    Atualiza um chamado existente.
    ---
    tags:
      - Chamados
    security:
      - basicAuth: []
    parameters:
      - in: path
        name: chamado_id
        type: integer
        required: true
        description: ID do chamado
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            status:
              type: string
              enum: [aberto, em_andamento, fechado]
              example: em_andamento
            titulo:
              type: string
            descricao:
              type: string
            coordenadas:
              type: object
              properties:
                x:
                  type: integer
                y:
                  type: integer
            dados_ecotoxicologicos:
              type: object
    responses:
      200:
        description: Chamado atualizado
        schema:
          $ref: '#/definitions/Chamado'
      400:
        description: Corpo da requisição vazio
      404:
        description: Chamado não encontrado
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
    """
    Remove um chamado do sistema.
    ---
    tags:
      - Chamados
    security:
      - basicAuth: []
    parameters:
      - in: path
        name: chamado_id
        type: integer
        required: true
        description: ID do chamado a remover
    responses:
      200:
        description: Chamado removido com sucesso
      404:
        description: Chamado não encontrado
    """
    for i, chamado in enumerate(chamados):
        if chamado["id"] == chamado_id:
            chamados.pop(i)
            return jsonify({"mensagem": "Chamado removido com sucesso"}), 200

    return jsonify({"erro": "Chamado não encontrado"}), 404


if __name__ == "__main__":
    print("=" * 60)
    print("  API de Gestão de Chamados — Rio Poxim")
    print("  Servidor:    http://localhost:5000")
    print("  Swagger UI:  http://localhost:5000/apidocs")
    print("  Credenciais: admin / 123456")
    print("=" * 60)
    app.run(debug=True, port=5000)
