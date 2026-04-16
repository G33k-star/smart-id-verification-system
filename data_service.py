# database module 

import csv
import os
from datetime import datetime
from config import (
    DATABASE_FILE,
    LEGACY_DATABASE_FILE,
    LEGACY_CHECKIN_FOLDER
)


def _existing_read_paths(*paths):
    existing = []
    for path in paths:
        if path and path not in existing and os.path.exists(path):
            existing.append(path)
    return existing


def _iter_student_rows():
    for path in _existing_read_paths(DATABASE_FILE, LEGACY_DATABASE_FILE):
        with open(path, mode="r", newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            for row in reader:
                yield row


def _checkin_read_paths(filename):
    legacy_path = os.path.join(LEGACY_CHECKIN_FOLDER, os.path.basename(filename))
    return _existing_read_paths(filename, legacy_path)

def find_student_in_database(card_id):
    if not _existing_read_paths(DATABASE_FILE, LEGACY_DATABASE_FILE):
        return None

    for row in _iter_student_rows():
        if row["Card ID"] == card_id:
            return row

    return None

def add_student_to_database(
    name,
    card_id,
    student_id,
    phone_number,
    mymdc_username,
    email
):
    os.makedirs(os.path.dirname(DATABASE_FILE), exist_ok=True)
    with open(DATABASE_FILE, mode="a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow([
            name,
            card_id,
            student_id,
            phone_number,
            mymdc_username,
            email
        ])

def already_checked_in_today(filename, card_id):
    paths = _checkin_read_paths(filename)

    if not paths:
        return False

    for path in paths:
        with open(path, mode="r", newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            for row in reader:
                if row["Card ID"] == card_id:
                    return True

    return False

def save_checkin(filename, name, card_id, student_id, phone_number):
    timestamp = datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
    os.makedirs(os.path.dirname(filename), exist_ok=True)

    with open(filename, mode="a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow([name, card_id, student_id, phone_number, timestamp])
