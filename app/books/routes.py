import os
from datetime import datetime, timedelta

from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user
from werkzeug.utils import secure_filename

from app.extensions import db
from app.forms import BookAddForm, BookForm, ReviewForm
from app.models import ROLE_ADMIN, ROLE_MODERATOR, ROLE_USER, Book, BookView, Cover, Genre, Review
from app.utils import compute_md5, get_session_key, role_required, sanitize_markdown_input

books_bp = Blueprint("books", __name__, url_prefix="/books")


@books_bp.route("/<int:book_id>")
def view(book_id):
    book = Book.query.get_or_404(book_id)
    _record_view(book)

    user_review = None
    if current_user.is_authenticated and current_user.has_role(ROLE_USER, ROLE_MODERATOR, ROLE_ADMIN):
        user_review = Review.query.filter_by(book_id=book.id, user_id=current_user.id).first()

    reviews = Review.query.filter_by(book_id=book.id).order_by(Review.created_at.desc()).all()

    return render_template("book_view.html", book=book, reviews=reviews, user_review=user_review)


def _record_view(book):
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

    if current_user.is_authenticated:
        identity_filter = BookView.user_id == current_user.id
        user_id = current_user.id
        session_key = None
    else:
        session_key = get_session_key()
        identity_filter = BookView.session_key == session_key
        user_id = None

    views_today = BookView.query.filter(
        BookView.book_id == book.id,
        identity_filter,
        BookView.viewed_at >= today_start,
    ).count()

    if views_today < current_app.config["MAX_DAILY_VIEWS"]:
        db.session.add(BookView(book_id=book.id, user_id=user_id, session_key=session_key))
        db.session.commit()


@books_bp.route("/add", methods=["GET", "POST"])
@role_required(ROLE_ADMIN)
def add():
    form = BookAddForm()
    if form.validate_on_submit():
        try:
            book = Book(
                title=form.title.data,
                description=sanitize_markdown_input(form.description.data),
                year=form.year.data,
                publisher=form.publisher.data,
                author=form.author.data,
                pages=form.pages.data,
            )
            book.genres = Genre.query.filter(Genre.id.in_(form.genres.data)).all()
            db.session.add(book)
            db.session.flush()

            cover_file = form.cover.data
            file_bytes = cover_file.read()
            md5_hash = compute_md5(file_bytes)
            ext = os.path.splitext(secure_filename(cover_file.filename))[1].lower()

            existing_cover = Cover.query.filter_by(md5_hash=md5_hash).first()
            filename = existing_cover.filename if existing_cover else None

            cover = Cover(
                filename=filename or "",
                mime_type=cover_file.mimetype,
                md5_hash=md5_hash,
                book_id=book.id,
            )
            db.session.add(cover)
            db.session.flush()

            new_file_path = None
            if filename is None:
                filename = f"{cover.id}{ext}"
                cover.filename = filename
                new_file_path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)

            db.session.commit()

            if new_file_path:
                with open(new_file_path, "wb") as f:
                    f.write(file_bytes)

            flash("Книга успешно добавлена", "success")
            return redirect(url_for("books.view", book_id=book.id))
        except Exception:
            db.session.rollback()
            flash("При сохранении данных возникла ошибка. Проверьте корректность введённых данных.", "danger")

    return render_template("book_form.html", form=form, mode="add")


@books_bp.route("/<int:book_id>/edit", methods=["GET", "POST"])
@role_required(ROLE_ADMIN, ROLE_MODERATOR)
def edit(book_id):
    book = Book.query.get_or_404(book_id)
    form = BookForm(obj=book)

    if request.method == "GET":
        form.genres.data = [g.id for g in book.genres]
        form.description.data = book.description

    if form.validate_on_submit():
        try:
            book.title = form.title.data
            book.description = sanitize_markdown_input(form.description.data)
            book.year = form.year.data
            book.publisher = form.publisher.data
            book.author = form.author.data
            book.pages = form.pages.data
            book.genres = Genre.query.filter(Genre.id.in_(form.genres.data)).all()

            db.session.commit()
            flash("Книга успешно обновлена", "success")
            return redirect(url_for("books.view", book_id=book.id))
        except Exception:
            db.session.rollback()
            flash("При сохранении данных возникла ошибка. Проверьте корректность введённых данных.", "danger")

    return render_template("book_form.html", form=form, mode="edit", book=book)


@books_bp.route("/<int:book_id>/delete", methods=["POST"])
@role_required(ROLE_ADMIN)
def delete(book_id):
    book = Book.query.get_or_404(book_id)
    title = book.title

    cover = book.cover
    file_to_remove = None
    if cover:
        other_refs = Cover.query.filter(Cover.md5_hash == cover.md5_hash, Cover.id != cover.id).count()
        if other_refs == 0:
            file_to_remove = os.path.join(current_app.config["UPLOAD_FOLDER"], cover.filename)

    try:
        db.session.delete(book)
        db.session.commit()
    except Exception:
        db.session.rollback()
        flash("При удалении книги возникла ошибка.", "danger")
        return redirect(url_for("main.index"))

    if file_to_remove and os.path.exists(file_to_remove):
        os.remove(file_to_remove)

    flash(f"Книга «{title}» успешно удалена", "success")
    return redirect(url_for("main.index"))
