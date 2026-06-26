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
    DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///tasks.db")
    ADMIN_TOKEN = _require_env("ADMIN_TOKEN")
    SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
    SMTP_USER = os.environ.get("SMTP_USER", "")
    SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
