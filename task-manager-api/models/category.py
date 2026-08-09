from datetime import datetime, timezone

from database import db


def utcnow():
    return datetime.now(timezone.utc)


class Category(db.Model):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(300), nullable=True)
    color = db.Column(db.String(7), default='#000000')
    created_at = db.Column(db.DateTime, default=utcnow)

    def to_dict(self, task_count=None):
        data = {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'color': self.color,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
        if task_count is not None:
            data['task_count'] = task_count
        return data
