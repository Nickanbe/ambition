"""Merge contact records that share an email address."""

from .normalize import normalize_email, normalize_phone


def _merge_into(target, rec):
    """Fold one raw record into a merged contact.

    The first non-empty name and phone win. Tags are lowercased and unioned in
    first-seen order. Notes are appended, one per line.
    """
    name = (rec.get("name") or "").strip()
    if not target["name"] and name:
        target["name"] = name
    phone = normalize_phone(rec.get("phone"))
    if not target["phone"] and phone:
        target["phone"] = phone
    for tag in rec.get("tags") or []:
        tag = tag.strip().lower()
        if tag and tag not in target["tags"]:
            target["tags"].append(tag)
    note = (rec.get("note") or "").strip()
    if note:
        if target["notes"]:
            target["notes"] = target["notes"] + "\n" + note
        else:
            target["notes"] = note


def merge_contacts(records):
    """Return one merged contact per normalized email, in first-seen order.

    Records with no email are never merged; each becomes its own contact.
    Each contact gets "count": how many input records it was built from.
    The input records are not modified.
    """
    merged = []
    index = {}
    for rec in records:
        email = normalize_email(rec.get("email"))
        target = None
        if email:
            target = index.get(email)
        if target is None:
            target = {"email": email, "name": "", "phone": "", "tags": [], "notes": "", "count": 0}
            merged.append(target)
            if email:
                index[email] = target
        target["count"] += 1
        _merge_into(target, rec)

    return merged
