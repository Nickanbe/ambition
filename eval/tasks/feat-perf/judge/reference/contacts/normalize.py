import re

_WS = re.compile(r"\s+")
_NON_DIGIT = re.compile(r"\D")


def normalize_email(value):
    """Lowercase and drop all whitespace. None/blank -> ""."""
    if not value:
        return ""
    return _WS.sub("", value).lower()


def normalize_phone(value):
    """Keep digits only; drop a leading US country code on 11-digit numbers."""
    if not value:
        return ""
    digits = _NON_DIGIT.sub("", str(value))
    if len(digits) == 11 and digits.startswith("1"):
        digits = digits[1:]
    return digits
