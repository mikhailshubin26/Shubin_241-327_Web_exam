import hashlib
import uuid
from functools import wraps

import bleach
import markdown as md
from flask import abort, flash, redirect, request, session, url_for
from flask_login import current_user

from app.models import ROLE_ADMIN, ROLE_MODERATOR, ROLE_USER

ALLOWED_TAGS = [
    "p", "br", "strong", "em", "b", "i", "u", "s", "del",
    "ul", "ol", "li", "blockquote", "code", "pre",
    "h1", "h2", "h3", "h4", "h5", "h6",
    "a", "img", "hr", "table", "thead", "tbody", "tr", "th", "td",
]
ALLOWED_ATTRS = {
    "a": ["href", "title", "rel"],
    "img": ["src", "alt", "title"],
}


def sanitize_markdown_input(text):
    """Очищает исходный markdown-текст от потенциально опасных тегов."""
    return bleach.clean(text or "", tags=[], strip=True)


def render_markdown(text):
    """Преобразует markdown в безопасный HTML."""
    html = md.markdown(text or "", extensions=["fenced_code", "tables"])
    return bleach.clean(html, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRS, strip=True)


def role_required(*role_names):
    """Доступ только пользователям с указанными ролями."""

    def decorator(view_func):
        @wraps(view_func)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                flash("Для выполнения данного действия необходимо пройти процедуру аутентификации", "warning")
                return redirect(url_for("auth.login", next=request.path))
            if not current_user.has_role(*role_names):
                flash("У вас недостаточно прав для выполнения данного действия", "danger")
                return redirect(url_for("main.index"))
            return view_func(*args, **kwargs)

        return wrapped

    return decorator


def get_session_key():
    """Возвращает уникальный идентификатор анонимной сессии для учёта просмотров."""
    key = session.get("session_key")
    if not key:
        key = uuid.uuid4().hex
        session["session_key"] = key
    return key


def compute_md5(file_bytes):
    return hashlib.md5(file_bytes).hexdigest()


__all__ = [
    "ROLE_ADMIN",
    "ROLE_MODERATOR",
    "ROLE_USER",
    "sanitize_markdown_input",
    "render_markdown",
    "role_required",
    "get_session_key",
    "compute_md5",
    "bleach",
]
