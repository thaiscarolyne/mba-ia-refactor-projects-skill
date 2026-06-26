import logging
from datetime import datetime, timedelta

from flask import Blueprint, jsonify, request
from sqlalchemy import case, func

from database import db
from middlewares.auth import admin_required, auth_required
from models.category import Category
from models.task import Task
from models.user import User
from utils.helpers import calculate_percentage, is_valid_color, log_action

logger = logging.getLogger(__name__)

report_bp = Blueprint("reports", __name__)


def _build_overdue_list(tasks):
    overdue_list = []
    for task in tasks:
        if task.is_overdue():
            overdue_list.append(
                {
                    "id": task.id,
                    "title": task.title,
                    "due_date": str(task.due_date),
                    "days_overdue": (datetime.utcnow() - task.due_date).days,
                }
            )
    return overdue_list


@report_bp.route("/reports/summary", methods=["GET"])
@auth_required
def summary_report():
    total_tasks = Task.query.count()
    total_users = User.query.count()
    total_categories = Category.query.count()

    pending = Task.query.filter_by(status="pending").count()
    in_progress = Task.query.filter_by(status="in_progress").count()
    done = Task.query.filter_by(status="done").count()
    cancelled = Task.query.filter_by(status="cancelled").count()

    priority_counts = dict(
        db.session.query(Task.priority, func.count(Task.id)).group_by(Task.priority).all()
    )

    all_tasks = Task.query.all()
    overdue_list = _build_overdue_list(all_tasks)

    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    recent_tasks = Task.query.filter(Task.created_at >= seven_days_ago).count()
    recent_done = Task.query.filter(
        Task.status == "done", Task.updated_at >= seven_days_ago
    ).count()

    productivity_rows = (
        db.session.query(
            User.id,
            User.name,
            func.count(Task.id).label("total_tasks"),
            func.sum(case((Task.status == "done", 1), else_=0)).label("completed_tasks"),
        )
        .outerjoin(Task, Task.user_id == User.id)
        .group_by(User.id, User.name)
        .all()
    )

    user_stats = [
        {
            "user_id": row.id,
            "user_name": row.name,
            "total_tasks": row.total_tasks or 0,
            "completed_tasks": int(row.completed_tasks or 0),
            "completion_rate": calculate_percentage(int(row.completed_tasks or 0), row.total_tasks or 0),
        }
        for row in productivity_rows
    ]

    report = {
        "generated_at": str(datetime.utcnow()),
        "overview": {
            "total_tasks": total_tasks,
            "total_users": total_users,
            "total_categories": total_categories,
        },
        "tasks_by_status": {
            "pending": pending,
            "in_progress": in_progress,
            "done": done,
            "cancelled": cancelled,
        },
        "tasks_by_priority": {
            "critical": priority_counts.get(1, 0),
            "high": priority_counts.get(2, 0),
            "medium": priority_counts.get(3, 0),
            "low": priority_counts.get(4, 0),
            "minimal": priority_counts.get(5, 0),
        },
        "overdue": {
            "count": len(overdue_list),
            "tasks": overdue_list,
        },
        "recent_activity": {
            "tasks_created_last_7_days": recent_tasks,
            "tasks_completed_last_7_days": recent_done,
        },
        "user_productivity": user_stats,
    }

    return jsonify(report), 200


@report_bp.route("/reports/user/<int:user_id>", methods=["GET"])
@auth_required
def user_report(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "Usuário não encontrado"}), 404

    tasks = Task.query.filter_by(user_id=user_id).all()
    total = len(tasks)
    done = sum(1 for t in tasks if t.status == "done")
    pending = sum(1 for t in tasks if t.status == "pending")
    in_progress = sum(1 for t in tasks if t.status == "in_progress")
    cancelled = sum(1 for t in tasks if t.status == "cancelled")
    overdue = sum(1 for t in tasks if t.is_overdue())
    high_priority = sum(1 for t in tasks if t.priority <= 2)

    report = {
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
        },
        "statistics": {
            "total_tasks": total,
            "done": done,
            "pending": pending,
            "in_progress": in_progress,
            "cancelled": cancelled,
            "overdue": overdue,
            "high_priority": high_priority,
            "completion_rate": calculate_percentage(done, total),
        },
    }

    return jsonify(report), 200


@report_bp.route("/categories", methods=["GET"])
def get_categories():
    categories = Category.query.all()
    counts = dict(
        db.session.query(Task.category_id, func.count(Task.id)).group_by(Task.category_id).all()
    )
    result = []
    for category in categories:
        cat_data = category.to_dict()
        cat_data["task_count"] = counts.get(category.id, 0)
        result.append(cat_data)
    return jsonify(result), 200


@report_bp.route("/categories", methods=["POST"])
@auth_required
def create_category():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Dados inválidos"}), 400

    name = data.get("name")
    if not name:
        return jsonify({"error": "Nome é obrigatório"}), 400

    color = data.get("color", "#000000")
    if not is_valid_color(color):
        return jsonify({"error": "Cor inválida. Use formato #RRGGBB"}), 400

    category = Category()
    category.name = name
    category.description = data.get("description", "")
    category.color = color

    try:
        db.session.add(category)
        db.session.commit()
        log_action("category_created", {"category_id": category.id})
        return jsonify(category.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        logger.error("Erro ao criar categoria: %s", e)
        return jsonify({"error": "Erro ao criar categoria"}), 500


@report_bp.route("/categories/<int:cat_id>", methods=["PUT"])
@auth_required
def update_category(cat_id):
    category = Category.query.get(cat_id)
    if not category:
        return jsonify({"error": "Categoria não encontrada"}), 404

    data = request.get_json()
    if "name" in data:
        category.name = data["name"]
    if "description" in data:
        category.description = data["description"]
    if "color" in data:
        if not is_valid_color(data["color"]):
            return jsonify({"error": "Cor inválida. Use formato #RRGGBB"}), 400
        category.color = data["color"]

    try:
        db.session.commit()
        log_action("category_updated", {"category_id": cat_id})
        return jsonify(category.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        logger.error("Erro ao atualizar categoria %s: %s", cat_id, e)
        return jsonify({"error": "Erro ao atualizar"}), 500


@report_bp.route("/categories/<int:cat_id>", methods=["DELETE"])
@admin_required
def delete_category(cat_id):
    category = Category.query.get(cat_id)
    if not category:
        return jsonify({"error": "Categoria não encontrada"}), 404

    try:
        db.session.delete(category)
        db.session.commit()
        log_action("category_deleted", {"category_id": cat_id})
        return jsonify({"message": "Categoria deletada"}), 200
    except Exception as e:
        db.session.rollback()
        logger.error("Erro ao deletar categoria %s: %s", cat_id, e)
        return jsonify({"error": "Erro ao deletar"}), 500
