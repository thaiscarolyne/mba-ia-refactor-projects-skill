import logging
from flask import request, jsonify
import src.models.user as user_model

logger = logging.getLogger(__name__)

def listar_usuarios():
    try:
        usuarios = user_model.get_todos_usuarios()
        return jsonify({"dados": usuarios, "sucesso": True}), 200
    except Exception as e:
        logger.error(f"Erro ao listar usuários: {str(e)}")
        return jsonify({"erro": str(e)}), 500

def buscar_usuario(id):
    try:
        usuario = user_model.get_usuario_por_id(id)
        if usuario:
            return jsonify({"dados": usuario, "sucesso": True}), 200
        else:
            return jsonify({"erro": "Usuário não encontrado"}), 404
    except Exception as e:
        logger.error(f"Erro ao buscar usuário {id}: {str(e)}")
        return jsonify({"erro": str(e)}), 500

def criar_usuario():
    try:
        dados = request.get_json()
        if not dados:
            return jsonify({"erro": "Dados inválidos"}), 400

        nome = dados.get("nome", "")
        email = dados.get("email", "")
        senha = dados.get("senha", "")
        tipo = dados.get("tipo", "cliente")

        if not nome or not email or not senha:
            return jsonify({"erro": "Nome, email e senha são obrigatórios"}), 400

        user_id = user_model.criar_usuario(nome, email, senha, tipo)
        logger.info(f"Usuário criado com sucesso: {email}")
        return jsonify({"dados": {"id": user_id}, "sucesso": True}), 201
    except Exception as e:
        logger.error(f"Erro ao criar usuário: {str(e)}")
        return jsonify({"erro": str(e)}), 500

def login():
    try:
        dados = request.get_json()
        if not dados:
            return jsonify({"erro": "Dados inválidos"}), 400
        email = dados.get("email", "")
        senha = dados.get("senha", "")

        if not email or not senha:
            return jsonify({"erro": "Email e senha são obrigatórios"}), 400

        usuario = user_model.login_usuario(email, senha)
        if usuario:
            logger.info(f"Login bem-sucedido: {email}")
            return jsonify({"dados": usuario, "sucesso": True, "mensagem": "Login OK"}), 200
        else:
            logger.warning(f"Tentativa de login malsucedida para o e-mail: {email}")
            return jsonify({"erro": "Email ou senha inválidos", "sucesso": False}), 401
    except Exception as e:
        logger.error(f"Erro no processamento de login: {str(e)}")
        return jsonify({"erro": str(e)}), 500
