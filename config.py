import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Configuración principal de BiblioTEC."""

    SECRET_KEY = os.getenv("SECRET_KEY", "clave-local-bibliotec")
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://postgres:postgres@localhost:5432/bibliotec_db"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
