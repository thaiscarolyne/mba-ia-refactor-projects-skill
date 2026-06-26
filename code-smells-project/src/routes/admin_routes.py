from flask import Blueprint
import src.controllers.admin_controller as controller
from src.middlewares.auth import admin_required

admin_bp = Blueprint("admin", __name__)

admin_bp.add_url_rule("/admin/reset-db", "reset_database", admin_required(controller.reset_database), methods=["POST"])
admin_bp.add_url_rule("/health", "health_check", controller.health_check, methods=["GET"])
