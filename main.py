"""
system concept simulation

procedure: Simulation on laptop > Program tested > Run from terminal > enable auto-start

TODO: 
- Have the program generate datasheet .csv file (Name, Card ID, Student ID, Phone Number, Timestamp, Total Time) and save it to a folder autonomously
    - After the user swipes their card, output "Hello, [name extracted from card], please enter your student ID and phone number."
- The program will have no check out. Only tracking who checked in for the day. Every 3am, a new .csv is created and restarts and creates a datechange
- There will be multiple .csv files. Only create a new .csv file if the date changed acccording to the internet (most recent time EST timezone)
- Include a disclaimer constanly running so the user knows what to expect before swiping ("By scanning your ID, you agree to the terms and conditions")
- If user already checked in for the day, the program will ignore
- Since the Card Scanner can read the student ID name, the program will not ask for the user's name. However, it will modify the data read from the scanner to only show specific data
- Hide "exit"
- Hide card data (line 51)
"""


import csv
import os
from datetime import datetime
from getpass import getpass

# settings
DATABASE_FILE = "database.csv"
CHECKIN_FOLDER = "checkin_logs"
DISCLAIMER = "By scanning your ID, you agree to the terms and conditions."

os.makedirs(CHECKIN_FOLDER, exist_ok=True)


# file setup
def create_database_if_needed():
    if not os.path.exists(DATABASE_FILE):
        with open(DATABASE_FILE, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(["Name", "Card ID", "Student ID", "Phone Number"])


def get_today_checkin_file():
    today = datetime.now().strftime("%Y-%m-%d")
    return os.path.join(CHECKIN_FOLDER, "checkin_{}.csv".format(today))


def create_checkin_file_if_needed(filename):
    if not os.path.exists(filename):
        with open(filename, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(["Name", "Card ID", "Student ID", "Phone Number", "Timestamp"])


# swipe parsing
def parse_swipe(swipe):
  
    parts = swipe.split("^")

    card_id = parts[0].replace("%B", "").strip()
    name_raw = parts[1].strip()

    last, first = name_raw.split("/")
    formatted_name = first.strip() + " " + last.strip()

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


# check-in function
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
create_database_if_needed()

while True: #sentinel loop
    print("\n" + DISCLAIMER)
    print("Please swipe your card.\n")

    swipe = getpass("Swipe Card: ").strip()

    if swipe.lower() == "exit":
        print("Program ended.")
        break

    try:
        name, card_id = parse_swipe(swipe)
    except Exception:
        print("Invalid swipe format. Please try again.")
        continue

    checkin_file = get_today_checkin_file()
    create_checkin_file_if_needed(checkin_file)

    if already_checked_in_today(checkin_file, card_id):
        print("{} has already checked in today. Entry ignored.".format(name))
        continue

    student = find_student_in_database(card_id)

    if student:
        print("Name: {}".format(student["Name"]))
        print("Card ID: {}".format(student["Card ID"]))
        print("Student ID: {}".format(student["Student ID"]))
        print("Phone Number: {}".format(student["Phone Number"]))

        save_checkin(
            checkin_file,
            student["Name"],
            student["Card ID"],
            student["Student ID"],
            student["Phone Number"]
        )

        print("Check-in saved successfully.")

    else:
        print("\nHello, {}. You are not in the database yet.".format(name))
        print("Please enter your Student ID and Phone Number.")

        student_id = input("Student ID (10 digits): ").strip()
        while not valid_student_id(student_id):
            print("Invalid Student ID. It must be exactly 10 digits.")
            student_id = input("Student ID (10 digits): ").strip()

        phone_number = input("Phone Number (10 digits): ").strip()
        while not valid_phone_number(phone_number):
            print("Invalid phone number. It must contain exactly 10 digits.")
            phone_number = input("Phone Number (10 digits): ").strip()

        phone_number = normalize_phone_number(phone_number)

        add_student_to_database(name, card_id, student_id, phone_number)
        save_checkin(checkin_file, name, card_id, student_id, phone_number)

        print("New student added to database.")
        print("Check-in saved successfully.")

