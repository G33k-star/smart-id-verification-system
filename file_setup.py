import csv
import os
from datetime import datetime
from config import (
    DATA_CHECKINS_FOLDER,
    DATABASE_FILE,
    TERMS_FILE,
    RUNTIME_DIRECTORIES
)

DATABASE_HEADERS = [
    "Name",
    "Card ID",
    "Student ID",
    "Phone Number",
    "myMDC Username",
    "Email"
]

CHECKIN_HEADERS = [
    "Name",
    "Card ID",
    "Student ID",
    "Phone Number",
    "Timestamp"
]


def initialize_storage():
    for directory in RUNTIME_DIRECTORIES:
        os.makedirs(directory, exist_ok=True)

    create_database_if_needed()
    create_terms_file_if_needed()


def create_database_if_needed():
    os.makedirs(os.path.dirname(DATABASE_FILE), exist_ok=True)
    if not os.path.exists(DATABASE_FILE):
        with open(DATABASE_FILE, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(DATABASE_HEADERS)


def create_terms_file_if_needed():
    os.makedirs(os.path.dirname(TERMS_FILE), exist_ok=True)
    if not os.path.exists(TERMS_FILE):
        with open(TERMS_FILE, mode="w", encoding="utf-8") as file:
            file.write("")


def get_terms_text():
    create_terms_file_if_needed()
    with open(TERMS_FILE, mode="r", encoding="utf-8") as file:
        return file.read()


def get_today_checkin_file():
    today = datetime.now().strftime("%Y-%m-%d")
    filename = "checkin_{0}.csv".format(today)
    return os.path.join(DATA_CHECKINS_FOLDER, filename)


def create_checkin_file_if_needed(filename):
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    if not os.path.exists(filename):
        with open(filename, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(CHECKIN_HEADERS)
