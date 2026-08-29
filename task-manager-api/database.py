from contextlib import contextmanager

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


@contextmanager
def transaction():
    """Commit on success; rollback on any exception (domain AppError or DB error)."""
    try:
        yield db.session
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
