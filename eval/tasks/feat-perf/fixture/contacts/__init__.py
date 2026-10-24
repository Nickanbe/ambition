"""Contact list cleanup: merge duplicate CRM exports into one record per person."""

from .dedupe import merge_contacts
from .normalize import normalize_email, normalize_phone

__all__ = ["merge_contacts", "normalize_email", "normalize_phone"]
