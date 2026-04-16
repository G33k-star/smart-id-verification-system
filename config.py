import os

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

DATABASE_FOLDER = os.path.join(PROJECT_ROOT, "database_folder")
DATABASE_FILE = os.path.join(DATABASE_FOLDER, "database.csv")
BEHAVIORAL_CONTRACT_TEMPLATE = os.path.join(
    DATABASE_FOLDER,
    "behavioral contract",
    "Robotics Lab Behavioral Contract 2026.pdf"
)
BEHAVIORAL_CONTRACT_SIGNED_FOLDER = os.path.join(
    PROJECT_ROOT,
    "database",
    "behavioral contract",
    "signed contracts"
)

CHECKIN_FOLDER = os.path.join(PROJECT_ROOT, "checkin_logs")
TERMS_FILE = os.path.join(PROJECT_ROOT, "terms_and_conditions.txt")
PHOTO_FOLDER = os.path.join(PROJECT_ROOT, "checkin_photos")

ADMIN_USERNAME = "admin" # PLEASE CHANGE (Look in "System Info" file)
ADMIN_PASSWORD = "admin1234" # PLEASE CHANGE (Look in "System Info" file)

WINDOW_WIDTH = 900
WINDOW_HEIGHT = 550
