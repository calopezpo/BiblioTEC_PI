import os

from dotenv import load_dotenv
from sqlalchemy import URL

load_dotenv()


class Config:

    SECRET_KEY = os.getenv(
        "SECRET_KEY",
        "clave-local-bibliotec"
    )

    SQLALCHEMY_DATABASE_URI = URL.create(
        drivername="postgresql+psycopg2",
        username=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT", 5432)),
        database=os.getenv("DB_NAME")
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False