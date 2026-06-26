import logging
from flask import request, jsonify
import src.models.order as order_model

logger = logging.getLogger(__name__)

def criar_pedido():
    try:
        dados = request.get_json()
        if not dados:
            return jsonify({"erro": "Dados inválidos"}), 400

        usuario_id = dados.get("usuario_id")
        itens = dados.get("itens", [])

        if not usuario_id:
            return jsonify({"erro": "Usuario ID é obrigatório"}), 400
        if not itens or len(itens) == 0:
            return jsonify({"erro": "Pedido deve ter pelo menos 1 item"}), 400

        resultado = order_model.criar_pedido(usuario_id, itens)

        if "erro" in resultado:
            return jsonify({"erro": resultado["erro"], "sucesso": False}), 400

        logger.info(f"Pedido {resultado['pedido_id']} criado para usuario {usuario_id}")
        logger.info(f"NOTIFICAÇÃO EMAIL: Pedido {resultado['pedido_id']} criado para usuario {usuario_id}")
        logger.info("NOTIFICAÇÃO SMS: Seu pedido foi recebido!")
        logger.info("NOTIFICAÇÃO PUSH: Novo pedido recebido pelo sistema")

        return jsonify({
            "dados": resultado,
            "sucesso": True,
            "mensagem": "Pedido criado com sucesso"
        }), 201
    except Exception as e:
        logger.error(f"Erro ao criar pedido: {str(e)}")
        return jsonify({"erro": str(e)}), 500

def listar_pedidos_usuario(usuario_id):
    try:
        pedidos = order_model.get_pedidos_usuario(usuario_id)
        return jsonify({"dados": pedidos, "sucesso": True}), 200
    except Exception as e:
        logger.error(f"Erro ao listar pedidos do usuário {usuario_id}: {str(e)}")
        return jsonify({"erro": str(e)}), 500

def listar_todos_pedidos():
    try:
        pedidos = order_model.get_todos_pedidos()
        return jsonify({"dados": pedidos, "sucesso": True}), 200
    except Exception as e:
        logger.error(f"Erro ao listar todos os pedidos: {str(e)}")
        return jsonify({"erro": str(e)}), 500

def atualizar_status_pedido(pedido_id):
    try:
        dados = request.get_json()
        if not dados:
            return jsonify({"erro": "Dados inválidos"}), 400
        novo_status = dados.get("status", "")

        if novo_status not in ["pendente", "aprovado", "enviado", "entregue", "cancelado"]:
            return jsonify({"erro": "Status inválido"}), 400

        order_model.atualizar_status_pedido(pedido_id, novo_status)

        if novo_status == "aprovado":
            logger.info(f"NOTIFICAÇÃO: Pedido {pedido_id} foi aprovado! Preparar envio.")
        elif novo_status == "cancelado":
            logger.info(f"NOTIFICAÇÃO: Pedido {pedido_id} cancelado. Devolver estoque.")

        return jsonify({"sucesso": True, "mensagem": "Status atualizado"}), 200
    except Exception as e:
        logger.error(f"Erro ao atualizar status do pedido {pedido_id}: {str(e)}")
        return jsonify({"erro": str(e)}), 500

def relatorio_vendas():
    try:
        relatorio = order_model.relatorio_vendas()
        return jsonify({"dados": relatorio, "sucesso": True}), 200
    except Exception as e:
        logger.error(f"Erro ao carregar relatório de vendas: {str(e)}")
        return jsonify({"erro": str(e)}), 500
