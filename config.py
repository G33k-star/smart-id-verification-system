import os

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

ASSETS_FOLDER = os.path.join(PROJECT_ROOT, "assets")
ASSETS_CONTRACTS_FOLDER = os.path.join(ASSETS_FOLDER, "contracts")
ASSETS_TEXT_FOLDER = os.path.join(ASSETS_FOLDER, "text")

DATA_FOLDER = os.path.join(PROJECT_ROOT, "data")
DATA_STUDENTS_FOLDER = os.path.join(DATA_FOLDER, "students")
DATA_CHECKINS_FOLDER = os.path.join(DATA_FOLDER, "checkins")
DATA_PHOTOS_FOLDER = os.path.join(DATA_FOLDER, "photos")
DATA_PHOTOS_CHECKINS_FOLDER = os.path.join(DATA_PHOTOS_FOLDER, "checkins")
DATA_CONTRACTS_FOLDER = os.path.join(DATA_FOLDER, "contracts")
DATA_CONTRACTS_SIGNED_FOLDER = os.path.join(DATA_CONTRACTS_FOLDER, "signed")

DATABASE_FILE = os.path.join(DATA_STUDENTS_FOLDER, "database.csv")
BEHAVIORAL_CONTRACT_TEMPLATE = os.path.join(
    ASSETS_CONTRACTS_FOLDER,
    "Robotics Lab Behavioral Contract 2026.pdf"
)
BEHAVIORAL_CONTRACT_SIGNED_FOLDER = DATA_CONTRACTS_SIGNED_FOLDER
TERMS_FILE = os.path.join(ASSETS_TEXT_FOLDER, "terms_and_conditions.txt")
RUNTIME_DIRECTORIES = (
    DATA_STUDENTS_FOLDER,
    DATA_CHECKINS_FOLDER,
    DATA_PHOTOS_CHECKINS_FOLDER,
    DATA_CONTRACTS_SIGNED_FOLDER,
)

ADMIN_USERNAME = "admin" # PLEASE CHANGE (Look in "System Info" file)
ADMIN_PASSWORD = "admin1234" # PLEASE CHANGE (Look in "System Info" file)

WINDOW_WIDTH = 900
WINDOW_HEIGHT = 550
