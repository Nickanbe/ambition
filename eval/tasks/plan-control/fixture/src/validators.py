import re

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class ValidationError(ValueError):
    pass


def validate_email(value: str) -> str:
    value = value.strip()
    if not EMAIL_RE.match(value):
        raise ValidationError(f"Invalid emial address: {value!r}")
    return value.lower()
