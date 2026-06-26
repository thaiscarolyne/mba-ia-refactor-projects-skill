from functools import wraps
from flask import request, jsonify
from src.config.settings import Settings

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        token = auth_header.replace("Bearer ", "").strip()
        
        if not token:
            token = request.args.get("token", "")
            
        if token != Settings.ADMIN_TOKEN:
            return jsonify({"erro": "Não autorizado. Token de administrador inválido ou ausente."}), 401
            
        return f(*args, **kwargs)
    return decorated_function
