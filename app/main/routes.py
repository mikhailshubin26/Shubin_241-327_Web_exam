from datetime import datetime, timedelta

from flask import Blueprint, render_template, request
from flask_login import current_user
from sqlalchemy import desc, func

from app.extensions import db
from app.models import Book, BookView
from app.utils import get_session_key

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    page = request.args.get("page", 1, type=int)
    pagination = Book.query.order_by(Book.year.desc(), Book.id.desc()).paginate(
        page=page, per_page=10, error_out=False
    )

    cutoff = datetime.utcnow() - timedelta(days=90)
    popular_books = (
        db.session.query(Book, func.count(BookView.id).label("views_count"))
        .join(BookView, BookView.book_id == Book.id)
        .filter(BookView.viewed_at >= cutoff)
        .group_by(Book.id)
        .order_by(desc("views_count"))
        .limit(5)
        .all()
    )

    if current_user.is_authenticated:
        recent_filter = BookView.user_id == current_user.id
    else:
        recent_filter = BookView.session_key == get_session_key()

    recent_books = (
        db.session.query(Book, func.max(BookView.viewed_at).label("last_view"))
        .join(BookView, BookView.book_id == Book.id)
        .filter(recent_filter)
        .group_by(Book.id)
        .order_by(desc("last_view"))
        .limit(5)
        .all()
    )

    return render_template(
        "index.html",
        pagination=pagination,
        books=pagination.items,
        popular_books=popular_books,
        recent_books=recent_books,
    )
