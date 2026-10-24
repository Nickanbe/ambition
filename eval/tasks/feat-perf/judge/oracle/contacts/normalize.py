import re


def normalize_email(value):
    """Lowercase and drop all whitespace. None/blank -> ""."""
    if not value:
        return ""
    return re.sub(r"\s+", "", value).lower()


def normalize_phone(value):
    """Keep digits only; drop a leading US country code on 11-digit numbers."""
    if not value:
        return ""
    digits = re.sub(r"\D", "", str(value))
    if len(digits) == 11 and digits.startswith("1"):
        digits = digits[1:]
    return digits
