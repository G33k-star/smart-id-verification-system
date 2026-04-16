import tkinter as tk
import os
import subprocess
import sys

from config import (
    WINDOW_WIDTH,
    WINDOW_HEIGHT,
    ADMIN_USERNAME,
    ADMIN_PASSWORD,
    CHECKIN_FOLDER,
    DATABASE_FOLDER
)

from file_setup import (
    create_database_if_needed,
    create_terms_file_if_needed,
    get_terms_text,
    get_today_checkin_file,
    create_checkin_file_if_needed
)

from validators import (
    parse_swipe,
    valid_student_id,
    valid_phone_number,
    normalize_phone_number,
    valid_mymdc_username,
    build_mymdc_email
)

from data_service import (
    find_student_in_database,
    add_student_to_database,
    already_checked_in_today,
    save_checkin
)
from contract_service import generate_behavioral_contract

from screens.screen1 import Screen1
from screens.screen2 import Screen2
from screens.screen3 import Screen3
from screens.screen4 import Screen4


def apply_kiosk_window(window, fullscreen=True):
    window.update_idletasks()
    window.withdraw()
    window.overrideredirect(True)
    window.attributes("-topmost", True)
    window.option_add("*cursor", "none")
    window.configure(cursor="none")

    if fullscreen:
        width = window.winfo_screenwidth()
        height = window.winfo_screenheight()
        window.geometry(f"{width}x{height}+0+0")
        window.attributes("-fullscreen", True)

    window.deiconify()
    window.lift()
    window.focus_force()


class CheckInApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ID Check-In System")
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.root.configure(bg="white")

        create_database_if_needed()
        create_terms_file_if_needed()

        # Variables
        self.swipe_var = tk.StringVar()
        self.student_var = tk.StringVar()
        self.phone_var = tk.StringVar()
        self.mymdc_username_var = tk.StringVar()
        self.email_var = tk.StringVar()

        self.admin_user_var = tk.StringVar()
        self.admin_pass_var = tk.StringVar()

        self.pending_name = None
        self.pending_card_id = None

        # Container
        self.container = tk.Frame(self.root, bg="white")
        self.container.pack(fill="both", expand=True)

        # Screens
        self.frames = {}
        for FrameClass in (Screen1, Screen2, Screen3, Screen4):
            frame = FrameClass(self.container, self)
            self.frames[FrameClass.__name__] = frame
            frame.place(relwidth=1, relheight=1)

        self.show_frame("Screen1")

    # -------------------------
    # Navigation
    # -------------------------
    def show_frame(self, name):
        screen1 = self.frames["Screen1"]

        if name != "Screen1":
            screen1.stop_camera()

        frame = self.frames[name]
        frame.tkraise()

        if hasattr(frame, "reset_screen"):
            frame.reset_screen()

    # -------------------------
    # System Functions
    # -------------------------
    def safe_quit_program(self):
        screen1 = self.frames.get("Screen1")
        if screen1:
            screen1.stop_camera()
        self.root.destroy()

    def open_csv_folder(self):
        self.open_path(CHECKIN_FOLDER)

    def open_database_folder(self):
        self.open_path(DATABASE_FOLDER)

    def open_path(self, path):
        try:
            if sys.platform.startswith("linux"):
                subprocess.Popen(["xdg-open", path])
            elif sys.platform.startswith("win"):
                os.startfile(path)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", path])
        except Exception as e:
            print("[App] Failed to open path:", e)

    def open_terms_window(self):
        win = tk.Toplevel(self.root)
        win.title("Terms and Conditions")
        width = 600
        height = 400
        x = (self.root.winfo_screenwidth() - width) // 2
        y = (self.root.winfo_screenheight() - height) // 2
        win.geometry(f"{width}x{height}+{x}+{y}")
        apply_kiosk_window(win, fullscreen=False)
        win.transient(self.root)
        win.grab_set()

        text = tk.Text(win, wrap="word")
        text.pack(fill="both", expand=True, padx=10, pady=10)

        text.insert("1.0", get_terms_text())
        text.config(state="disabled")

        tk.Button(win, text="Close", command=win.destroy).pack(pady=10)

    # -------------------------
    # Swipe Logic
    # -------------------------
    def process_swipe_from_screen1(self):
        screen1 = self.frames["Screen1"]

        swipe = self.swipe_var.get().strip()

        if not swipe:
            screen1.set_message("No swipe detected.", "red")
            return

        try:
            name, card_id = parse_swipe(swipe)
        except Exception:
            screen1.set_message("Invalid swipe format.", "red")
            self.swipe_var.set("")
            return

        checkin_file = get_today_checkin_file()
        create_checkin_file_if_needed(checkin_file)

        if already_checked_in_today(checkin_file, card_id):
            screen1.set_message(f"{name} already checked in.", "orange")
            self.swipe_var.set("")
            return

        if not screen1.camera_active:
            screen1.set_message("Camera unavailable.", "red")
            return

        screen1.set_message("Processing...", "blue")

        student = find_student_in_database(card_id)

        # Existing user
        if student:
            success, path = screen1.camera.capture_image_with_face_check(student["Name"])

            if not success:
                screen1.set_message("Camera error.", "red")
                return

            save_checkin(
                checkin_file,
                student["Name"],
                student["Card ID"],
                student["Student ID"],
                student["Phone Number"]
            )

            print("Saved:", path)

            screen1.set_message(f"{student['Name']} checked in.", "green")
            self.swipe_var.set("")
            return

        # New user
        self.pending_name = name
        self.pending_card_id = card_id
        self.show_frame("Screen2")

    # -------------------------
    # Add User (FIXED)
    # -------------------------
    def add_user_and_check_in(self):
        screen1 = self.frames["Screen1"]
        screen2 = self.frames["Screen2"]

        sid = self.student_var.get().strip()
        phone = self.phone_var.get().strip()
        username = self.mymdc_username_var.get().strip()

        # Show validation messages but DO NOT stop execution
        if not valid_student_id(sid):
            screen2.set_message("Invalid Student ID", "red")

        if not valid_phone_number(phone):
            screen2.set_message("Invalid phone number", "red")

        if not valid_mymdc_username(username):
            screen2.set_message("Invalid username", "red")

        phone = normalize_phone_number(phone)
        username, email = build_mymdc_email(username)
        self.email_var.set(email)

        self.show_frame("Screen1")
        screen1 = self.frames["Screen1"]

        success, path = screen1.camera.capture_image_with_face_check(self.pending_name)

        if not success:
            screen1.set_message("Camera error.", "red")
            return

        add_student_to_database(
            self.pending_name,
            self.pending_card_id,
            sid,
            phone,
            username,
            email
        )
        generate_behavioral_contract(
            student_name=self.pending_name,
            student_id=sid,
            signed_name=self.pending_name
        )

        checkin_file = get_today_checkin_file()
        create_checkin_file_if_needed(checkin_file)

        save_checkin(
            checkin_file,
            self.pending_name,
            self.pending_card_id,
            sid,
            phone
        )

        name = self.pending_name
        self.pending_name = None
        self.pending_card_id = None

        self.student_var.set("")
        self.phone_var.set("")
        self.mymdc_username_var.set("")
        self.email_var.set("")
        self.swipe_var.set("")

        self.show_frame("Screen1")
        screen1.set_message(f"{name} added and checked in.", "green")

    # -------------------------
    # Admin Login
    # -------------------------
    def check_admin_credentials(self):
        screen3 = self.frames["Screen3"]

        user = self.admin_user_var.get().strip()
        pwd = self.admin_pass_var.get().strip()

        if user == ADMIN_USERNAME and pwd == ADMIN_PASSWORD:
            self.admin_user_var.set("")
            self.admin_pass_var.set("")
            self.show_frame("Screen4")
        else:
            self.admin_user_var.set("")
            self.admin_pass_var.set("")
            screen3.set_message("Incorrect credentials.")
