import logging

from flask import Blueprint, jsonify, request
from database import db
from middlewares.auth import auth_required
from models.category import Category
from models.task import Task
from models.user import User
from services.notification_service import NotificationService
from utils.helpers import log_action, process_task_data

logger = logging.getLogger(__name__)

task_bp = Blueprint("tasks", __name__)
notification_service = NotificationService()


@task_bp.route("/tasks", methods=["GET"])
def get_tasks():
    try:
        tasks = Task.query.all()
        return jsonify([t.to_dict() for t in tasks]), 200
    except Exception as e:
        logger.error("Erro ao listar tasks: %s", e)
        return jsonify({"error": "Erro interno"}), 500


@task_bp.route("/tasks/<int:task_id>", methods=["GET"])
def get_task(task_id):
    task = Task.query.get(task_id)
    if task:
        return jsonify(task.to_dict()), 200
    return jsonify({"error": "Task não encontrada"}), 404


@task_bp.route("/tasks", methods=["POST"])
@auth_required
def create_task():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Dados inválidos"}), 400

    processed, error = process_task_data(data)
    if error:
        return jsonify({"error": error}), 400

    if "title" not in processed:
        return jsonify({"error": "Título é obrigatório"}), 400

    user_id = data.get("user_id")
    category_id = data.get("category_id")

    if user_id and not User.query.get(user_id):
        return jsonify({"error": "Usuário não encontrado"}), 404
    if category_id and not Category.query.get(category_id):
        return jsonify({"error": "Categoria não encontrada"}), 404

    task = Task()
    task.title = processed["title"]
    task.description = processed.get("description", data.get("description", ""))
    task.status = processed.get("status", data.get("status", "pending"))
    task.priority = processed.get("priority", data.get("priority", 3))
    task.user_id = user_id
    task.category_id = category_id
    task.due_date = processed.get("due_date")
    if "tags" in processed:
        task.tags = processed["tags"]
    elif data.get("tags"):
        tags = data["tags"]
        task.tags = ",".join(tags) if isinstance(tags, list) else tags

    try:
        db.session.add(task)
        db.session.commit()
        log_action("task_created", {"task_id": task.id, "title": task.title})

        if task.user_id:
            user = User.query.get(task.user_id)
            if user:
                notification_service.notify_task_assigned(user, task)

        return jsonify(task.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        logger.error("Erro ao criar task: %s", e)
        return jsonify({"error": "Erro ao criar task"}), 500


@task_bp.route("/tasks/<int:task_id>", methods=["PUT"])
@auth_required
def update_task(task_id):
    task = Task.query.get(task_id)
    if not task:
        return jsonify({"error": "Task não encontrada"}), 404

    data = request.get_json()
    if not data:
        return jsonify({"error": "Dados inválidos"}), 400

    processed, error = process_task_data(data)
    if error:
        return jsonify({"error": error}), 400

    if "title" in processed:
        task.title = processed["title"]
    if "description" in processed:
        task.description = processed["description"]
    if "status" in processed:
        task.status = processed["status"]
    if "priority" in processed:
        task.priority = processed["priority"]
    if "due_date" in processed:
        task.due_date = processed["due_date"]
    if "tags" in processed:
        task.tags = processed["tags"]

    if "user_id" in data:
        if data["user_id"] and not User.query.get(data["user_id"]):
            return jsonify({"error": "Usuário não encontrado"}), 404
        task.user_id = data["user_id"]

    if "category_id" in data:
        if data["category_id"] and not Category.query.get(data["category_id"]):
            return jsonify({"error": "Categoria não encontrada"}), 404
        task.category_id = data["category_id"]

    from datetime import datetime

    task.updated_at = datetime.utcnow()

    try:
        db.session.commit()
        log_action("task_updated", {"task_id": task.id})
        return jsonify(task.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        logger.error("Erro ao atualizar task %s: %s", task_id, e)
        return jsonify({"error": "Erro ao atualizar"}), 500


@task_bp.route("/tasks/<int:task_id>", methods=["DELETE"])
@auth_required
def delete_task(task_id):
    task = Task.query.get(task_id)
    if not task:
        return jsonify({"error": "Task não encontrada"}), 404

    try:
        db.session.delete(task)
        db.session.commit()
        log_action("task_deleted", {"task_id": task_id})
        return jsonify({"message": "Task deletada com sucesso"}), 200
    except Exception as e:
        db.session.rollback()
        logger.error("Erro ao deletar task %s: %s", task_id, e)
        return jsonify({"error": "Erro ao deletar"}), 500


@task_bp.route("/tasks/search", methods=["GET"])
def search_tasks():
    query = request.args.get("q", "")
    status = request.args.get("status", "")
    priority = request.args.get("priority", "")
    user_id = request.args.get("user_id", "")

    tasks = Task.query

    if query:
        tasks = tasks.filter(
            db.or_(Task.title.like(f"%{query}%"), Task.description.like(f"%{query}%"))
        )
    if status:
        tasks = tasks.filter(Task.status == status)
    if priority:
        tasks = tasks.filter(Task.priority == int(priority))
    if user_id:
        tasks = tasks.filter(Task.user_id == int(user_id))

    return jsonify([t.to_dict() for t in tasks.all()]), 200


@task_bp.route("/tasks/stats", methods=["GET"])
@auth_required
def task_stats():
    total = Task.query.count()
    pending = Task.query.filter_by(status="pending").count()
    in_progress = Task.query.filter_by(status="in_progress").count()
    done = Task.query.filter_by(status="done").count()
    cancelled = Task.query.filter_by(status="cancelled").count()

    overdue_count = sum(1 for t in Task.query.all() if t.is_overdue())

    stats = {
        "total": total,
        "pending": pending,
        "in_progress": in_progress,
        "done": done,
        "cancelled": cancelled,
        "overdue": overdue_count,
        "completion_rate": round((done / total) * 100, 2) if total > 0 else 0,
    }

    return jsonify(stats), 200
