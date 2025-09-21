from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import validates

db = SQLAlchemy()

CLICKBAIT_PHRASES = ["Won't Believe", "Secret", "Top", "Guess"]


class Author(db.Model):
    __tablename__ = 'authors'

    id = db.Column(db.Integer, primary_key=True)
    # Keep DB constraints, but also validate at the model layer (eager failure)
    name = db.Column(db.String, unique=True, nullable=False)
    phone_number = db.Column(db.String)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, onupdate=db.func.now())

    # --------- Validators ---------
    @validates('name')
    def validate_name(self, key, value):
        """Require a non-empty, unique name."""
        if not value or not str(value).strip():
            raise ValueError("Author must have a name.")

        normalized = str(value).strip()

        # Enforce uniqueness early (before hitting the unique index)
        existing = Author.query.filter(Author.name == normalized).first()
        if existing and existing.id != self.id:
            # Mirror tests: raise ValueError on duplicate attempt
            raise ValueError("Author name must be unique.")

        return normalized

    @validates('phone_number')
    def validate_phone_number(self, key, value):
        """
        Require exactly 10 digits, all numeric.
        (Tests expect ValueError for too short, too long, or non-digit chars.)
        """
        if value is None:
            # If business rules require 'always present', make it non-nullable and validate here.
            return value

        if not isinstance(value, str) or len(value) != 10 or not value.isdigit():
            raise ValueError("Phone number must be exactly 10 digits.")
        return value

    def __repr__(self):
        return f'Author(id={self.id}, name={self.name})'


class Post(db.Model):
    __tablename__ = 'posts'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, nullable=False)
    content = db.Column(db.String)
    category = db.Column(db.String)
    summary = db.Column(db.String)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, onupdate=db.func.now())

    # --------- Validators ---------
    @validates('title')
    def validate_title(self, key, value):
        """
        Non-empty AND must contain at least one clickbait phrase:
        "Won't Believe", "Secret", "Top", or "Guess".
        """
        if not value or not str(value).strip():
            raise ValueError("Post must have a title.")
        if not any(phrase in value for phrase in CLICKBAIT_PHRASES):
            raise ValueError(
                "Title must be clickbait-y and contain one of: "
                + ", ".join(CLICKBAIT_PHRASES)
            )
        return value.strip()

    @validates('content')
    def validate_content(self, key, value):
        """Content must be at least 250 characters."""
        if value is None or len(value) < 250:
            raise ValueError("Content must be at least 250 characters long.")
        return value

    @validates('summary')
    def validate_summary(self, key, value):
        """Summary must be at most 250 characters (if provided)."""
        if value is not None and len(value) > 250:
            raise ValueError("Summary must be at most 250 characters.")
        return value

    @validates('category')
    def validate_category(self, key, value):
        """Category must be either 'Fiction' or 'Non-Fiction'."""
        allowed = {"Fiction", "Non-Fiction"}
        if value not in allowed:
            raise ValueError("Category must be 'Fiction' or 'Non-Fiction'.")
        return value

    def __repr__(self):
        return (
            f'Post(id={self.id}, title={self.title} '
            f'content={self.content}, summary={self.summary})'
        )