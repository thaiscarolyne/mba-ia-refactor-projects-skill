from flask import Blueprint
import src.controllers.product_controller as controller

product_bp = Blueprint("produtos", __name__)

product_bp.add_url_rule("/produtos", "listar_produtos", controller.listar_produtos, methods=["GET"])
product_bp.add_url_rule("/produtos/busca", "buscar_produtos", controller.buscar_produtos, methods=["GET"])
product_bp.add_url_rule("/produtos/<int:id>", "buscar_produto", controller.buscar_produto, methods=["GET"])
product_bp.add_url_rule("/produtos", "criar_produto", controller.criar_produto, methods=["POST"])
product_bp.add_url_rule("/produtos/<int:id>", "atualizar_produto", controller.atualizar_produto, methods=["PUT"])
product_bp.add_url_rule("/produtos/<int:id>", "deletar_produto", controller.deletar_produto, methods=["DELETE"])
