from flask import Blueprint
import src.controllers.user_controller as controller

user_bp = Blueprint("usuarios", __name__)

user_bp.add_url_rule("/usuarios", "listar_usuarios", controller.listar_usuarios, methods=["GET"])
user_bp.add_url_rule("/usuarios/<int:id>", "buscar_usuario", controller.buscar_usuario, methods=["GET"])
user_bp.add_url_rule("/usuarios", "criar_usuario", controller.criar_usuario, methods=["POST"])
user_bp.add_url_rule("/login", "login", controller.login, methods=["POST"])
