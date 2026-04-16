import os

DATABASE_FOLDER = "database_folder"
DATABASE_FILE = os.path.join(DATABASE_FOLDER, "database.csv")
BEHAVIORAL_CONTRACT_TEMPLATE = os.path.join(
    DATABASE_FOLDER,
    "behavioral contract",
    "Robotics Lab Behavioral Contract 2026.pdf"
)
BEHAVIORAL_CONTRACT_SIGNED_FOLDER = os.path.join(
    "database",
    "behavioral contract",
    "signed contracts"
)

CHECKIN_FOLDER = "checkin_logs"
TERMS_FILE = "terms_and_conditions.txt"
PHOTO_FOLDER = "checkin_photos"

ADMIN_USERNAME = "admin" # PLEASE CHANGE (Look in "System Info" file)
ADMIN_PASSWORD = "admin1234" # PLEASE CHANGE (Look in "System Info" file)

WINDOW_WIDTH = 900
WINDOW_HEIGHT = 550
