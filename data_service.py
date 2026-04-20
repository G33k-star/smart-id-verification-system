import csv
import os
from datetime import datetime

from config import DATABASE_FILE
from file_setup import DATABASE_HEADERS


def _normalize_text(value):
    return str(value or "").strip()


def _normalize_card_id(card_id):
    return _normalize_text(card_id)


def _normalize_student_id(student_id):
    return _normalize_text(student_id)


def _normalize_username(username):
    value = _normalize_text(username).lower()
    if value.endswith("@mymdc.net"):
        value = value[:-10]
    return value


def _iter_rows(filename):
    if not os.path.exists(filename):
        return

    with open(filename, mode="r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            yield {key: _normalize_text(value) for key, value in row.items()}


def _read_database_rows():
    return list(_iter_rows(DATABASE_FILE) or [])


def _write_database_rows(rows):
    os.makedirs(os.path.dirname(DATABASE_FILE), exist_ok=True)

    with open(DATABASE_FILE, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=DATABASE_HEADERS)
        writer.writeheader()

        for row in rows:
            writer.writerow({
                header: _normalize_text(row.get(header, ""))
                for header in DATABASE_HEADERS
            })


def student_has_card(row):
    return bool(_normalize_card_id(row.get("Card ID", "")))


def find_student_in_database(card_id):
    return find_student_by_card_id(card_id)


def find_student_by_card_id(card_id):
    normalized_card_id = _normalize_card_id(card_id)
    if not normalized_card_id:
        return None

    for row in _iter_rows(DATABASE_FILE):
        if _normalize_card_id(row.get("Card ID", "")) == normalized_card_id:
            return row

    return None


def find_student_by_student_id(student_id):
    normalized_student_id = _normalize_student_id(student_id)
    if not normalized_student_id:
        return None

    for row in _iter_rows(DATABASE_FILE):
        if _normalize_student_id(row.get("Student ID", "")) == normalized_student_id:
            return row

    return None


def find_student_by_mymdc_username(mymdc_username):
    normalized_username = _normalize_username(mymdc_username)
    if not normalized_username:
        return None

    for row in _iter_rows(DATABASE_FILE):
        if _normalize_username(row.get("myMDC Username", "")) == normalized_username:
            return row

    return None


def find_student_by_credentials(student_id, mymdc_username):
    normalized_student_id = _normalize_student_id(student_id)
    normalized_username = _normalize_username(mymdc_username)
    if not normalized_student_id or not normalized_username:
        return None

    for row in _iter_rows(DATABASE_FILE):
        if (
            _normalize_student_id(row.get("Student ID", "")) == normalized_student_id and
            _normalize_username(row.get("myMDC Username", "")) == normalized_username
        ):
            return row

    return None


def find_pre_registered_student(student_id, mymdc_username):
    student = find_student_by_credentials(student_id, mymdc_username)
    if student and not student_has_card(student):
        return student

    return None


def get_registration_conflict(student_id, mymdc_username):
    student_by_id = find_student_by_student_id(student_id)
    student_by_username = find_student_by_mymdc_username(mymdc_username)

    if student_by_id and student_by_username and student_by_id != student_by_username:
        return "Student ID and myMDC username already belong to different records."

    if student_by_id and (
        _normalize_username(student_by_id.get("myMDC Username", "")) !=
        _normalize_username(mymdc_username)
    ):
        return "That student ID is already linked to a different myMDC username."

    if student_by_username and (
        _normalize_student_id(student_by_username.get("Student ID", "")) !=
        _normalize_student_id(student_id)
    ):
        return "That myMDC username is already linked to a different student ID."

    return None


def add_student_to_database(
    name,
    card_id,
    student_id,
    phone_number,
    mymdc_username,
    email
):
    rows = _read_database_rows()
    rows.append({
        "Name": name,
        "Card ID": card_id,
        "Student ID": student_id,
        "Phone Number": phone_number,
        "myMDC Username": mymdc_username,
        "Email": email,
    })
    _write_database_rows(rows)


def update_student_for_first_card_link(student_id, card_id, canonical_name):
    normalized_student_id = _normalize_student_id(student_id)
    normalized_card_id = _normalize_card_id(card_id)
    normalized_name = _normalize_text(canonical_name)
    if not normalized_student_id or not normalized_card_id or not normalized_name:
        return None, None

    rows = _read_database_rows()
    old_row = None
    updated_row = None

    for row in rows:
        if (
            _normalize_card_id(row.get("Card ID", "")) == normalized_card_id and
            _normalize_student_id(row.get("Student ID", "")) != normalized_student_id
        ):
            return None, None

    for row in rows:
        if _normalize_student_id(row.get("Student ID", "")) == normalized_student_id:
            old_row = dict(row)
            row["Card ID"] = normalized_card_id
            row["Name"] = normalized_name
            updated_row = dict(row)
            break

    if updated_row is None:
        return None, None

    _write_database_rows(rows)
    return old_row, updated_row


def update_student_card_id(student_id, card_id):
    normalized_student_id = _normalize_student_id(student_id)
    normalized_card_id = _normalize_card_id(card_id)
    if not normalized_student_id or not normalized_card_id:
        return None

    rows = _read_database_rows()
    updated_row = None

    for row in rows:
        if (
            _normalize_card_id(row.get("Card ID", "")) == normalized_card_id and
            _normalize_student_id(row.get("Student ID", "")) != normalized_student_id
        ):
            return None

    for row in rows:
        if _normalize_student_id(row.get("Student ID", "")) == normalized_student_id:
            row["Card ID"] = normalized_card_id
            updated_row = dict(row)
            break

    if updated_row is None:
        return None

    _write_database_rows(rows)
    return updated_row


def already_checked_in_today(filename, card_id=None, student_id=None):
    if not os.path.exists(filename):
        return False

    normalized_card_id = _normalize_card_id(card_id)
    normalized_student_id = _normalize_student_id(student_id)

    for row in _iter_rows(filename):
        if normalized_card_id and _normalize_card_id(row.get("Card ID", "")) == normalized_card_id:
            return True

        if normalized_student_id and _normalize_student_id(row.get("Student ID", "")) == normalized_student_id:
            return True

    return False


def save_checkin(filename, name, card_id, student_id, phone_number):
    timestamp = datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
    os.makedirs(os.path.dirname(filename), exist_ok=True)

    with open(filename, mode="a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow([name, card_id, student_id, phone_number, timestamp])
