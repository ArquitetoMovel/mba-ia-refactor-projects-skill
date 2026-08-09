from datetime import date, datetime, timezone
import logging
import re

logger = logging.getLogger(__name__)


def format_date(date_obj):
    if date_obj is None:
        return None
    if isinstance(date_obj, datetime):
        return date_obj.isoformat()
    return str(date_obj)


def calculate_percentage(part, total):
    if total == 0:
        return 0
    return round((part / total) * 100, 2)


def serialize_tags(tags):
    if tags is None:
        return None
    if isinstance(tags, list):
        return ','.join(tags)
    return tags


def to_datetime(value):
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value
    if isinstance(value, date):
        return datetime(value.year, value.month, value.day, tzinfo=timezone.utc)
    return None


def is_valid_color(color):
    return bool(color and re.match(r'^#[0-9A-Fa-f]{6}$', color))
