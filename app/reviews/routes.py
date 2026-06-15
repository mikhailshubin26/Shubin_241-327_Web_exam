from flask import Blueprint, flash, redirect, render_template, url_for
from flask_login import current_user

from app.extensions import db
from app.forms import ReviewForm
from app.models import ROLE_ADMIN, ROLE_MODERATOR, ROLE_USER, Book, Review
from app.utils import role_required, sanitize_markdown_input

reviews_bp = Blueprint("reviews", __name__, url_prefix="/books")


@reviews_bp.route("/<int:book_id>/review/add", methods=["GET", "POST"])
@role_required(ROLE_USER, ROLE_MODERATOR, ROLE_ADMIN)
def add(book_id):
    book = Book.query.get_or_404(book_id)

    existing = Review.query.filter_by(book_id=book.id, user_id=current_user.id).first()
    if existing:
        return redirect(url_for("books.view", book_id=book.id))

    form = ReviewForm()
    if form.validate_on_submit():
        try:
            review = Review(
                book_id=book.id,
                user_id=current_user.id,
                rating=int(form.rating.data),
                text=sanitize_markdown_input(form.text.data),
            )
            db.session.add(review)
            db.session.commit()
            return redirect(url_for("books.view", book_id=book.id))
        except Exception:
            db.session.rollback()
            flash("При сохранении данных возникла ошибка. Проверьте корректность введённых данных.", "danger")

    return render_template("review_form.html", form=form, book=book)
