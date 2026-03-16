import csv
import os
from datetime import datetime
from getpass import getpass
import sys
import time

# settings
DATABASE_FOLDER = "database_folder"
DATABASE_FILE = os.path.join(DATABASE_FOLDER, "database.csv")
CHECKIN_FOLDER = "checkin_logs"
DISCLAIMER = "By scanning your ID, you agree to the terms and conditions."
EXIT_CODE = "adminexit"


def check_exit(value):
    if value.strip().lower() == EXIT_CODE:
        print("Exit code entered. Program ending", end="", flush=True)
        for _ in range(3):
            time.sleep(1)
            print(".", end="", flush=True)
        sys.exit()


# create check-in folder if it does not exist
if not os.path.exists(CHECKIN_FOLDER):
    os.makedirs(CHECKIN_FOLDER)

# create database folder if it does not exist
if not os.path.exists(DATABASE_FOLDER):
    os.makedirs(DATABASE_FOLDER)

# creates database
def create_database_if_needed():
    if not os.path.exists(DATABASE_FILE):
        with open(DATABASE_FILE, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(["Name", "Card ID", "Student ID", "Phone Number"])


# current time function
def get_today_checkin_file():
    today = datetime.now().strftime("%Y-%m-%d")
    filename = "checkin_{0}.csv".format(today)
    return os.path.join(CHECKIN_FOLDER, filename)

# creates checkin file
def create_checkin_file_if_needed(filename):
    if not os.path.exists(filename):
        with open(filename, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(["Name", "Card ID", "Student ID", "Phone Number", "Timestamp"])


# swipe parsing
def parse_swipe(swipe):
    swipe = swipe.strip()

    # must contain track 1 separators
    if "^" not in swipe:
        raise ValueError("Swipe data missing '^' separators")

    parts = swipe.split("^")

    if len(parts) < 2:
        raise ValueError("Swipe data incomplete")

    # first part contains %B + card id
    card_part = parts[0].strip()

    if not card_part.startswith("%B"):
        raise ValueError("Swipe data missing Track 1 start")

    card_id = card_part.replace("%B", "").strip()

    # name section
    name_raw = parts[1].strip()

    if "/" not in name_raw:
        raise ValueError("Name format invalid")

    name_parts = name_raw.split("/")

    if len(name_parts) < 2:
        raise ValueError("Name format incomplete")

    last = name_parts[0].strip()
    first = name_parts[1].strip()

    # clean extra spaces inside first name
    first = " ".join(first.split())
    last = " ".join(last.split())

    formatted_name = "{0} {1}".format(first, last)

    return formatted_name, card_id


# validating student ID and phone number is 10 digits
def valid_student_id(student_id):
    return student_id.isdigit() and len(student_id) == 10


def valid_phone_number(phone):
    digits_only = "".join(ch for ch in phone if ch.isdigit())
    return len(digits_only) == 10


def normalize_phone_number(phone):
    return "".join(ch for ch in phone if ch.isdigit())


# database function
def find_student_in_database(card_id):
    if not os.path.exists(DATABASE_FILE):
        return None

    with open(DATABASE_FILE, mode="r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row["Card ID"] == card_id:
                return row

    return None


def add_student_to_database(name, card_id, student_id, phone_number):
    with open(DATABASE_FILE, mode="a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow([name, card_id, student_id, phone_number])


# check-in functions
def already_checked_in_today(filename, card_id):
    if not os.path.exists(filename):
        return False

    with open(filename, mode="r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row["Card ID"] == card_id:
                return True

    return False


def save_checkin(filename, name, card_id, student_id, phone_number):
    timestamp = datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")

    with open(filename, mode="a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow([name, card_id, student_id, phone_number, timestamp])


# main
def main():
    create_database_if_needed()

    while True: # sentinel loop
        print("")
        print(DISCLAIMER)
        print("Please swipe your card.")
        print("")

        # used getpass() instead of input()
        swipe = getpass("Swipe Card: ").strip() # used getpass instead of input() to hide info
        check_exit(swipe)

        if swipe == "":
            print("No swipe detected. Please try again.")
            continue

        try:
            name, card_id = parse_swipe(swipe)
        except Exception as error:
            print("Invalid swipe format. Please try again.")
            print("Debug info:", error)
            continue

        checkin_file = get_today_checkin_file()
        create_checkin_file_if_needed(checkin_file)

        if already_checked_in_today(checkin_file, card_id):
            print("{0} has already checked in today. Entry ignored.".format(name))
            continue

        student = find_student_in_database(card_id)

        if student:
            print("")
            print("Student found in database:")
            print("Name: {0}".format(student["Name"]))
            print("Card ID: {0}".format(student["Card ID"]))
            print("Student ID: {0}".format(student["Student ID"]))
            print("Phone Number: {0}".format(student["Phone Number"]))

            save_checkin(
                checkin_file,
                student["Name"],
                student["Card ID"],
                student["Student ID"],
                student["Phone Number"]
            )

            print("Check-in saved successfully.")

        else:
            print("")
            print("Hello, {0}. You are not in the database yet.".format(name))
            print("Please enter your Student ID and Phone Number.")

            student_id = getpass("Student ID (10 digits): ").strip() # used getpass instead of input() to hide info
            check_exit(student_id)
            
            while not valid_student_id(student_id):
                print("Invalid Student ID. It must be exactly 10 digits.")
                student_id = getpass("Student ID (10 digits): ").strip() # used getpass instead of input() to hide info
                check_exit(student_id)

            phone_number = getpass("Phone Number (10 digits): ").strip() # used getpass instead of input() to hide info
            check_exit(phone_number)
            
            while not valid_phone_number(phone_number):
                print("Invalid phone number. It must contain exactly 10 digits.")
                phone_number = getpass("Phone Number (10 digits): ").strip() # used getpass instead of input() to hide info
                check_exit(phone_number)

            phone_number = normalize_phone_number(phone_number)

            add_student_to_database(name, card_id, student_id, phone_number)
            save_checkin(checkin_file, name, card_id, student_id, phone_number)

            print("New student added to database.")
            print("Check-in saved successfully.")


if __name__ == "__main__":
    main()
