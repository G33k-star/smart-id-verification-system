"""
Smart ID Check-In System

Flow:
1. User swipes card on Screen1
2. Swipe data is parsed into name + card ID
3. If user exists in database:
   - capture image
   - check in user
4. If user does not exist:
   - move to Screen2 for registration
   - capture image
   - add to database
   - check in user
"""

import os
import sys
import subprocess
import tkinter as tk

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

from screens.screen1 import Screen1
from screens.screen2 import Screen2
from screens.screen3 import Screen3
from screens.screen4 import Screen4


class CheckInApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ID Check-In System")
        self.root.geometry("{0}x{1}".format(WINDOW_WIDTH, WINDOW_HEIGHT))
        self.root.configure(bg="white")

        create_database_if_needed()
        create_terms_file_if_needed()

        self.pending_name = None
        self.pending_card_id = None

        self.swipe_var = tk.StringVar()
        self.student_var = tk.StringVar()
        self.phone_var = tk.StringVar()
        self.mymdc_username_var = tk.StringVar()
        self.email_var = tk.StringVar()
        self.admin_user_var = tk.StringVar()
        self.admin_pass_var = tk.StringVar()

        self.enable_kiosk_mode()

        self.container = tk.Frame(self.root, bg="white")
        self.container.pack(fill="both", expand=True)

        self.frames = {}
        for FrameClass in (Screen1, Screen2, Screen3, Screen4):
            frame = FrameClass(parent=self.container, controller=self)
            self.frames[FrameClass.__name__] = frame
            frame.place(relx=0, rely=0, relwidth=1, relheight=1)

        self.show_frame("Screen1")

    def enable_kiosk_mode(self):
        try:
            if sys.platform.startswith("win"):
                self.root.state("zoomed")
                self.root.overrideredirect(True)
            else:
                self.root.attributes("-fullscreen", True)
                self.root.after(100, lambda: self.root.overrideredirect(True))
        except Exception:
            pass

        self.root.protocol("WM_DELETE_WINDOW", lambda: None)
        self.root.bind("<Escape>", lambda event: "break")
        self.root.bind("<Alt-F4>", lambda event: "break")

    def safe_quit_program(self):
        try:
            screen1 = self.frames.get("Screen1")
            if screen1:
                screen1.stop_camera()
        except Exception:
            pass

        self.root.destroy()

    def show_frame(self, frame_name):
        screen1 = self.frames["Screen1"]

        if frame_name != "Screen1":
            screen1.stop_camera()

        current_frame = self.frames[frame_name]
        current_frame.tkraise()

        if hasattr(current_frame, "reset_screen"):
            current_frame.reset_screen()

    def open_terms_window(self):
        win = tk.Toplevel(self.root)
        win.title("Terms and Conditions")
        win.geometry("700x450")
        win.configure(bg="white")

        text = tk.Text(win, wrap="word", font=("Arial", 11))
        text.pack(fill="both", expand=True, padx=10, pady=10)
        text.insert("1.0", get_terms_text())
        text.config(state="disabled")

        tk.Button(win, text="Close", command=win.destroy, width=12).pack(pady=(0, 10))

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
        except Exception:
            pass

    def process_swipe_from_screen1(self):
        screen1 = self.frames["Screen1"]
        screen2 = self.frames["Screen2"]

        swipe = self.swipe_var.get().strip()
        if swipe == "":
            screen1.set_message("No swipe detected.", "red")
            screen1.focus_swipe()
            return

        try:
            name, card_id = parse_swipe(swipe)
        except Exception:
            screen1.set_message("Invalid swipe format.", "red")
            self.swipe_var.set("")
            screen1.focus_swipe()
            return

        checkin_file = get_today_checkin_file()
        create_checkin_file_if_needed(checkin_file)

        if already_checked_in_today(checkin_file, card_id):
            screen1.set_message("User, {0} already checked in.".format(name), "orange")
            self.swipe_var.set("")
            screen1.focus_swipe()
            return

        if not screen1.camera_active:
            screen1.set_message("Camera is not available.", "red")
            screen1.focus_swipe()
            return

        screen1.set_message("Processing...", "blue")
        self.root.update_idletasks()

        student = find_student_in_database(card_id)

        if student:
            success, image_path = screen1.camera.capture_image_with_face_check(student["Name"])
            if not success:
                screen1.set_message("No face detected. Please try again.", "red")
                self.swipe_var.set("")
                screen1.focus_swipe()
                return

            save_checkin(
                checkin_file,
                student["Name"],
                student["Card ID"],
                student["Student ID"],
                student["Phone Number"]
            )

            print("Captured:", image_path)
            screen1.set_message("User, {0} checked in.".format(student["Name"]), "green", success=True)
            self.swipe_var.set("")
            screen1.focus_swipe()
            return

        self.pending_name = name
        self.pending_card_id = card_id
        self.show_frame("Screen2")
        screen2.set_message("User not recognized. Add new user?", "black")

    def add_user_and_check_in(self):
        screen1 = self.frames["Screen1"]
        screen2 = self.frames["Screen2"]

        if not self.pending_name or not self.pending_card_id:
            screen2.set_message("No pending user found.", "red")
            return

        student_id = self.student_var.get().strip()
        phone = self.phone_var.get().strip()
        username = self.mymdc_username_var.get().strip()

        if not valid_student_id(student_id):
            screen2.set_message("Invalid Student ID.", "red")
            return

        if not valid_phone_number(phone):
            screen2.set_message("Invalid phone number.", "red")
            return

        if not valid_mymdc_username(username):
            screen2.set_message("Invalid myMDC username.", "red")
            return

        phone = normalize_phone_number(phone)
        username, email = build_mymdc_email(username)
        self.mymdc_username_var.set(username)
        self.email_var.set(email)

        screen2.set_status("Processing...", "blue")
        self.root.update_idletasks()

        self.show_frame("Screen1")
        screen1 = self.frames["Screen1"]

        if not screen1.camera_active:
            self.show_frame("Screen2")
            screen2.clear_status()
            screen2.set_message("Camera is not available.", "red")
            return

        success, image_path = screen1.camera.capture_image_with_face_check(self.pending_name)
        if not success:
            self.show_frame("Screen2")
            screen2.clear_status()
            screen2.set_message("No face detected. Please try again.", "red")
            return

        add_student_to_database(
            self.pending_name,
            self.pending_card_id,
            student_id,
            phone,
            username,
            email
        )

        checkin_file = get_today_checkin_file()
        create_checkin_file_if_needed(checkin_file)
        save_checkin(
            checkin_file,
            self.pending_name,
            self.pending_card_id,
            student_id,
            phone
        )

        print("Captured:", image_path)

        saved_name = self.pending_name
        self.pending_name = None
        self.pending_card_id = None

        self.swipe_var.set("")
        self.student_var.set("")
        self.phone_var.set("")
        self.mymdc_username_var.set("")
        self.email_var.set("")

        self.show_frame("Screen1")
        screen1 = self.frames["Screen1"]
        screen1.set_message("User {0} added and checked in.".format(saved_name), "green", success=True)

    def check_admin_credentials(self):
        username = self.admin_user_var.get().strip()
        password = self.admin_pass_var.get().strip()

        screen3 = self.frames["Screen3"]

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            self.admin_user_var.set("")
            self.admin_pass_var.set("")
            self.show_frame("Screen4")
        else:
            self.admin_user_var.set("")
            self.admin_pass_var.set("")
            screen3.set_message("Incorrect credentials. Please try again.")
            screen3.focus_username()
