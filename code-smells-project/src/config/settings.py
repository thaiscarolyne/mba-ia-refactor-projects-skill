import os

from dotenv import load_dotenv

load_dotenv()


def _require_env(name):
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(
            f"Variável de ambiente obrigatória ausente: {name}. "
            f"Copie .env.example para .env e configure os valores."
        )
    return value


class Settings:
    SECRET_KEY = _require_env("SECRET_KEY")
    DEBUG = os.environ.get("DEBUG", "False").lower() in ("true", "1", "t")
    DB_PATH = os.environ.get("DB_PATH", "loja.db")
    ADMIN_TOKEN = _require_env("ADMIN_TOKEN")
