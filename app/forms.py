from datetime import date

from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField, FileRequired
from wtforms import (
    BooleanField,
    IntegerField,
    PasswordField,
    SelectField,
    SelectMultipleField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.validators import DataRequired, NumberRange, ValidationError

from app.models import Genre


class LoginForm(FlaskForm):
    login = StringField("Логин", validators=[DataRequired()])
    password = PasswordField("Пароль", validators=[DataRequired()])
    remember_me = BooleanField("Запомнить меня")
    submit = SubmitField("Войти")


class BookForm(FlaskForm):
    title = StringField("Название", validators=[DataRequired()])
    description = TextAreaField("Краткое описание", validators=[DataRequired()])
    year = IntegerField(
        "Год",
        validators=[DataRequired(), NumberRange(min=1000, max=date.today().year + 1)],
    )
    publisher = StringField("Издательство", validators=[DataRequired()])
    author = StringField("Автор", validators=[DataRequired()])
    pages = IntegerField("Объём (страниц)", validators=[DataRequired(), NumberRange(min=1)])
    genres = SelectMultipleField("Жанры", coerce=int, validators=[DataRequired()])
    cover = FileField("Обложка", validators=[FileAllowed(["jpg", "jpeg", "png", "gif", "webp"])])
    submit = SubmitField("Сохранить")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.genres.choices = [(g.id, g.name) for g in Genre.query.order_by(Genre.name).all()]


class BookAddForm(BookForm):
    cover = FileField(
        "Обложка",
        validators=[FileRequired("Необходимо загрузить обложку"), FileAllowed(["jpg", "jpeg", "png", "gif", "webp"])],
    )


class ReviewForm(FlaskForm):
    rating = SelectField(
        "Оценка",
        choices=[
            ("5", "5 – отлично"),
            ("4", "4 – хорошо"),
            ("3", "3 – удовлетворительно"),
            ("2", "2 – неудовлетворительно"),
            ("1", "1 – плохо"),
            ("0", "0 – ужасно"),
        ],
        default="5",
        validators=[DataRequired()],
    )
    text = TextAreaField("Текст рецензии", validators=[DataRequired()])
    submit = SubmitField("Сохранить")


class StatsFilterForm(FlaskForm):
    date_from = StringField("Дата от")
    date_to = StringField("Дата до")
    submit = SubmitField("Применить")
