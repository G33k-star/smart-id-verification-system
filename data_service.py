import csv
import os
from datetime import datetime
from config import DATABASE_FILE


def _iter_rows(filename):
    if not os.path.exists(filename):
        return

    with open(filename, mode="r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            yield row


def find_student_in_database(card_id):
    for row in _iter_rows(DATABASE_FILE):
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
    if not os.path.exists(filename):
        return False

    for row in _iter_rows(filename):
        if row["Card ID"] == card_id:
            return True

    return False

def save_checkin(filename, name, card_id, student_id, phone_number):
    timestamp = datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
    os.makedirs(os.path.dirname(filename), exist_ok=True)

    with open(filename, mode="a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow([name, card_id, student_id, phone_number, timestamp])
