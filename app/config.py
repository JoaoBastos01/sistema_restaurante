import os

class Config:
    DB_DSN = os.getenv("DATABASE_URL", "postgresql://user:pw@localhost/restaurante")
    SECRET_KEY = os.getenv("SECRET_KEY", "BrewStack")