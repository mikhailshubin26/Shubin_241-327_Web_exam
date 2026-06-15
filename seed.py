"""Создание таблиц и наполнение БД справочными данными (роли, жанры, пользователи)."""

from werkzeug.security import generate_password_hash

from app import create_app
from app.extensions import db
from app.models import Genre, Role, User, ROLE_ADMIN, ROLE_MODERATOR, ROLE_USER

app = create_app()

with app.app_context():
    db.create_all()

    roles = {
        ROLE_ADMIN: "Администратор (суперпользователь, имеет полный доступ к системе, в том числе к созданию и удалению книг)",
        ROLE_MODERATOR: "Модератор (может редактировать данные книг и производить модерацию рецензий)",
        ROLE_USER: "Пользователь (может оставлять рецензии)",
    }
    role_objs = {}
    for name, description in roles.items():
        role = Role.query.filter_by(name=name).first()
        if role is None:
            role = Role(name=name, description=description)
            db.session.add(role)
        role_objs[name] = role
    db.session.flush()

    genres = ["Роман", "Фантастика", "Детектив", "Поэзия", "Научная литература", "Приключения"]
    for genre_name in genres:
        if Genre.query.filter_by(name=genre_name).first() is None:
            db.session.add(Genre(name=genre_name))

    users = [
        ("admin", "admin", "Администраторов", "Админ", "Админович", ROLE_ADMIN),
        ("moderator", "moderator", "Модераторов", "Модератор", "Модераторович", ROLE_MODERATOR),
        ("user", "user", "Пользователей", "Пользователь", "Пользователевич", ROLE_USER),
    ]
    for login, password, last_name, first_name, middle_name, role_name in users:
        if User.query.filter_by(login=login).first() is None:
            db.session.add(
                User(
                    login=login,
                    password_hash=generate_password_hash(password),
                    last_name=last_name,
                    first_name=first_name,
                    middle_name=middle_name,
                    role_id=role_objs[role_name].id,
                )
            )

    db.session.commit()
    print("База данных успешно инициализирована.")
