from flask import Blueprint
import src.controllers.order_controller as controller

order_bp = Blueprint("pedidos", __name__)

order_bp.add_url_rule("/pedidos", "criar_pedido", controller.criar_pedido, methods=["POST"])
order_bp.add_url_rule("/pedidos", "listar_todos_pedidos", controller.listar_todos_pedidos, methods=["GET"])
order_bp.add_url_rule("/pedidos/usuario/<int:usuario_id>", "listar_pedidos_usuario", controller.listar_pedidos_usuario, methods=["GET"])
order_bp.add_url_rule("/pedidos/<int:pedido_id>/status", "atualizar_status_pedido", controller.atualizar_status_pedido, methods=["PUT"])
order_bp.add_url_rule("/relatorios/vendas", "relatorio_vendas", controller.relatorio_vendas, methods=["GET"])
