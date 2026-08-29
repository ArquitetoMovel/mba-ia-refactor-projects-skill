from datetime import date, datetime, timezone


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
