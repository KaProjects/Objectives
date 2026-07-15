from datetime import date, datetime


def normalize_date(value: str, allow_empty: bool = True) -> str:
    """Return an ISO date, accepting the project's legacy DD/MM/YYYY format."""
    if value == '' and allow_empty:
        return value
    if not isinstance(value, str):
        raise ValueError('date must be a string')

    try:
        return date.fromisoformat(value).isoformat()
    except ValueError:
        try:
            return datetime.strptime(value, '%d/%m/%Y').date().isoformat()
        except ValueError as error:
            raise ValueError("date must use ISO format YYYY-MM-DD") from error


def validate_iso_date(value: str, allow_empty: bool = False) -> str:
    if value == '' and allow_empty:
        return value
    if not isinstance(value, str):
        raise ValueError('date must be a string')
    try:
        return date.fromisoformat(value).isoformat()
    except ValueError as error:
        raise ValueError('date must use ISO format YYYY-MM-DD') from error
