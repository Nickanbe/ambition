"""Merge contact records that share an email address.

Linear time: an email -> contact index replaces the scan over merged
contacts, a per-contact tag set replaces list membership tests, notes are
collected in a list and joined once, and counts are tallied while merging
instead of rescanning every record per contact.
"""

from .normalize import normalize_email, normalize_phone


def merge_contacts(records):
    """Return one merged contact per normalized email, in first-seen order.

    Records with no email are never merged; each becomes its own contact.
    Each contact gets "count": how many input records it was built from.
    The input records are not modified.
    """
    merged = []
    by_email = {}
    tag_sets = []
    note_lists = []

    for rec in records:
        email = normalize_email(rec.get("email"))
        slot = by_email.get(email) if email else None
        if slot is None:
            slot = len(merged)
            merged.append({"email": email, "name": "", "phone": "", "tags": [], "notes": "", "count": 0})
            tag_sets.append(set())
            note_lists.append([])
            if email:
                by_email[email] = slot
        target = merged[slot]
        target["count"] += 1

        if not target["name"]:
            name = (rec.get("name") or "").strip()
            if name:
                target["name"] = name
        if not target["phone"]:
            phone = normalize_phone(rec.get("phone"))
            if phone:
                target["phone"] = phone
        seen = tag_sets[slot]
        for tag in rec.get("tags") or []:
            tag = tag.strip().lower()
            if tag and tag not in seen:
                seen.add(tag)
                target["tags"].append(tag)
        note = (rec.get("note") or "").strip()
        if note:
            note_lists[slot].append(note)

    for contact, notes in zip(merged, note_lists):
        contact["notes"] = "\n".join(notes)
    return merged
