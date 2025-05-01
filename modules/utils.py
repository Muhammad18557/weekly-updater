"""Utilitly functions for the project."""

from datetime import datetime, timedelta


def get_last_monday() -> datetime:
    today = datetime.today()
    last_monday = today - timedelta(days=today.weekday())
    return last_monday
