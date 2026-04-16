# .csv check-in sheet module

import csv
import os
from datetime import datetime, timedelta
from config import (
    DATA_STUDENTS_FOLDER,
    DATA_CHECKINS_FOLDER,
    ASSETS_TEXT_FOLDER,
    DATABASE_FILE,
    CHECKIN_FOLDER,
    TERMS_FILE,
    LEGACY_TERMS_FILE
)

os.makedirs(CHECKIN_FOLDER, exist_ok=True)
os.makedirs(DATA_STUDENTS_FOLDER, exist_ok=True)

def create_database_if_needed():
    os.makedirs(DATA_STUDENTS_FOLDER, exist_ok=True)
    if not os.path.exists(DATABASE_FILE):
        with open(DATABASE_FILE, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow([
                "Name",
                "Card ID",
                "Student ID",
                "Phone Number",
                "myMDC Username",
                "Email"
            ])

def create_terms_file_if_needed():
    os.makedirs(ASSETS_TEXT_FOLDER, exist_ok=True)
    if os.path.exists(TERMS_FILE):
        return
    if os.path.exists(LEGACY_TERMS_FILE):
        return
    if not os.path.exists(TERMS_FILE):
        with open(TERMS_FILE, mode="w", encoding="utf-8") as file:
            file.write("")

def get_terms_text():
    create_terms_file_if_needed()
    terms_path = TERMS_FILE if os.path.exists(TERMS_FILE) else LEGACY_TERMS_FILE
    with open(terms_path, mode="r", encoding="utf-8") as file:
        return file.read()

def get_today_checkin_file():
    os.makedirs(DATA_CHECKINS_FOLDER, exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")
    filename = "checkin_{0}.csv".format(today)
    return os.path.join(CHECKIN_FOLDER, filename)

def create_checkin_file_if_needed(filename):
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    if not os.path.exists(filename):
        with open(filename, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow([
                "Name",
                "Card ID",
                "Student ID",
                "Phone Number",
                "Timestamp"
            ])
            
def get_system_day():
    now = datetime.now()

    # If current time is before 3:00 AM,
    # treat it as part of the previous day
    if now.hour < 3:
        now = now - timedelta(days=1)

    return now.strftime("%Y-%m-%d")
