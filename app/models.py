from datetime import datetime

from flask_login import UserMixin

from app.extensions import db

# Role name constants
ROLE_ADMIN = "admin"
ROLE_MODERATOR = "moderator"
ROLE_USER = "user"


book_genres = db.Table(
    "book_genres",
    db.Column("book_id", db.Integer, db.ForeignKey("books.id", ondelete="CASCADE"), primary_key=True),
    db.Column("genre_id", db.Integer, db.ForeignKey("genres.id", ondelete="CASCADE"), primary_key=True),
)


class Role(db.Model):
    __tablename__ = "roles"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=False)

    users = db.relationship("User", back_populates="role")

    def __repr__(self):
        return f"<Role {self.name}>"


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    last_name = db.Column(db.String(64), nullable=False)
    first_name = db.Column(db.String(64), nullable=False)
    middle_name = db.Column(db.String(64), nullable=True)
    role_id = db.Column(db.Integer, db.ForeignKey("roles.id"), nullable=False)

    role = db.relationship("Role", back_populates="users")
    reviews = db.relationship("Review", back_populates="user")

    @property
    def full_name(self):
        parts = [self.last_name, self.first_name, self.middle_name]
        return " ".join(p for p in parts if p)

    def has_role(self, *role_names):
        return self.role is not None and self.role.name in role_names

    def __repr__(self):
        return f"<User {self.login}>"


class Genre(db.Model):
    __tablename__ = "genres"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)

    books = db.relationship("Book", secondary=book_genres, back_populates="genres")

    def __repr__(self):
        return f"<Genre {self.name}>"


class Book(db.Model):
    __tablename__ = "books"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    publisher = db.Column(db.String(255), nullable=False)
    author = db.Column(db.String(255), nullable=False)
    pages = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    genres = db.relationship("Genre", secondary=book_genres, back_populates="books")
    cover = db.relationship(
        "Cover", back_populates="book", uselist=False, cascade="all, delete-orphan", passive_deletes=True
    )
    reviews = db.relationship("Review", back_populates="book", cascade="all, delete-orphan", passive_deletes=True)
    views = db.relationship("BookView", back_populates="book", cascade="all, delete-orphan", passive_deletes=True)

    @property
    def average_rating(self):
        if not self.reviews:
            return None
        return sum(r.rating for r in self.reviews) / len(self.reviews)

    @property
    def review_count(self):
        return len(self.reviews)

    def __repr__(self):
        return f"<Book {self.title}>"


class Cover(db.Model):
    __tablename__ = "covers"

    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    mime_type = db.Column(db.String(128), nullable=False)
    md5_hash = db.Column(db.String(32), nullable=False, index=True)
    book_id = db.Column(db.Integer, db.ForeignKey("books.id", ondelete="CASCADE"), nullable=False)

    book = db.relationship("Book", back_populates="cover")

    def __repr__(self):
        return f"<Cover {self.filename}>"


class Review(db.Model):
    __tablename__ = "reviews"

    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey("books.id", ondelete="CASCADE"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    book = db.relationship("Book", back_populates="reviews")
    user = db.relationship("User", back_populates="reviews")

    def __repr__(self):
        return f"<Review book={self.book_id} user={self.user_id}>"


class BookView(db.Model):
    """История просмотров страниц книг (Вариант 4)."""

    __tablename__ = "book_views"

    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey("books.id", ondelete="CASCADE"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    session_key = db.Column(db.String(64), nullable=True)
    viewed_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    book = db.relationship("Book", back_populates="views")
    user = db.relationship("User")

    def __repr__(self):
        return f"<BookView book={self.book_id} user={self.user_id} at={self.viewed_at}>"
