import logging
import secrets
from functools import wraps

from flask import g, jsonify, request

from config.settings import Settings
from models.user import User

logger = logging.getLogger(__name__)

_active_tokens = {}


def generate_token(user_id):
    token = secrets.token_urlsafe(32)
    _active_tokens[token] = user_id
    return token


def revoke_token(token):
    _active_tokens.pop(token, None)


def auth_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        token = auth_header.replace("Bearer ", "").strip()

        if not token:
            return jsonify({"error": "Token de autenticação ausente"}), 401

        user_id = _active_tokens.get(token)
        if not user_id:
            return jsonify({"error": "Token inválido ou expirado"}), 401

        user = User.query.get(user_id)
        if not user or not user.active:
            return jsonify({"error": "Usuário inválido ou inativo"}), 401

        g.current_user = user
        g.current_user_id = user_id
        return f(*args, **kwargs)

    return decorated


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        token = auth_header.replace("Bearer ", "").strip()

        if token and token == Settings.ADMIN_TOKEN:
            g.current_user = None
            g.current_user_id = None
            return f(*args, **kwargs)

        user_id = _active_tokens.get(token)
        if user_id:
            user = User.query.get(user_id)
            if user and user.active and user.role == "admin":
                g.current_user = user
                g.current_user_id = user_id
                return f(*args, **kwargs)

        return jsonify({"error": "Acesso negado. Permissão de administrador necessária."}), 403

    return decorated
