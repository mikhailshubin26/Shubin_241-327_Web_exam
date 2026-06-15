import csv
import io
from datetime import datetime, timedelta

from flask import Blueprint, Response, render_template, request
from sqlalchemy import func

from app.extensions import db
from app.forms import StatsFilterForm
from app.models import ROLE_ADMIN, Book, BookView, User
from app.utils import role_required

stats_bp = Blueprint("stats", __name__, url_prefix="/stats")


def _parse_date(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        return None


def _log_query():
    return (
        db.session.query(BookView, User, Book)
        .outerjoin(User, BookView.user_id == User.id)
        .join(Book, BookView.book_id == Book.id)
        .order_by(BookView.viewed_at.desc())
    )


def _views_query(date_from, date_to):
    query = (
        db.session.query(Book.title, func.count(BookView.id).label("views_count"))
        .join(BookView, BookView.book_id == Book.id)
        .filter(BookView.user_id.isnot(None))
    )
    if date_from:
        query = query.filter(BookView.viewed_at >= date_from)
    if date_to:
        query = query.filter(BookView.viewed_at < date_to + timedelta(days=1))
    return query.group_by(Book.id).order_by(func.count(BookView.id).desc())


@stats_bp.route("/")
@role_required(ROLE_ADMIN)
def index():
    tab = request.args.get("tab", "log")

    log_page = request.args.get("log_page", 1, type=int)
    log_pagination = _log_query().paginate(page=log_page, per_page=10, error_out=False)
    log_offset = (log_pagination.page - 1) * 10

    form = StatsFilterForm(formdata=request.args, meta={"csrf": False})
    date_from = _parse_date(request.args.get("date_from"))
    date_to = _parse_date(request.args.get("date_to"))

    views_page = request.args.get("views_page", 1, type=int)
    views_pagination = _views_query(date_from, date_to).paginate(page=views_page, per_page=10, error_out=False)
    views_offset = (views_pagination.page - 1) * 10

    return render_template(
        "stats.html",
        tab=tab,
        log_pagination=log_pagination,
        log_offset=log_offset,
        views_pagination=views_pagination,
        views_offset=views_offset,
        form=form,
        date_from=request.args.get("date_from", ""),
        date_to=request.args.get("date_to", ""),
    )


@stats_bp.route("/export/log.csv")
@role_required(ROLE_ADMIN)
def export_log():
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["№", "ФИО пользователя", "Книга", "Дата и время просмотра"])

    for i, (view, user, book) in enumerate(_log_query().all(), start=1):
        user_name = user.full_name if user else "Неаутентифицированный пользователь"
        writer.writerow([i, user_name, book.title, view.viewed_at.strftime("%d.%m.%Y %H:%M:%S")])

    filename = f"action_log_{datetime.utcnow().strftime('%Y-%m-%d_%H-%M-%S')}.csv"
    return Response(
        output.getvalue().encode("utf-8-sig"),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@stats_bp.route("/export/views.csv")
@role_required(ROLE_ADMIN)
def export_views():
    date_from = _parse_date(request.args.get("date_from"))
    date_to = _parse_date(request.args.get("date_to"))

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["№", "Название книги", "Количество просмотров"])

    for i, (title, views_count) in enumerate(_views_query(date_from, date_to).all(), start=1):
        writer.writerow([i, title, views_count])

    filename = f"view_stats_{datetime.utcnow().strftime('%Y-%m-%d_%H-%M-%S')}.csv"
    return Response(
        output.getvalue().encode("utf-8-sig"),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
