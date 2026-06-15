import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'app', 'library.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    UPLOAD_FOLDER = os.path.join(BASE_DIR, "app", "static", "uploads", "covers")
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB

    BOOKS_PER_PAGE = 10
    STATS_PER_PAGE = 10

    # daily per-user view limit for view-counter (Вариант 4)
    MAX_DAILY_VIEWS = 10

    REMEMBER_COOKIE_DURATION = 60 * 60 * 24 * 30  # 30 days
