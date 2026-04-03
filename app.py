import tkinter as tk
import os
import subprocess
import sys

from config import *
from file_setup import *
from validators import *
from data_service import *

from screens.screen1 import Screen1
from screens.screen2 import Screen2
from screens.screen3 import Screen3
from screens.screen4 import Screen4


class CheckInApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ID Check-In System")
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.root.configure(bg="white")

        create_database_if_needed()
        create_terms_file_if_needed()

        self.swipe_var = tk.StringVar()
        self.student_var = tk.StringVar()
        self.phone_var = tk.StringVar()
        self.mymdc_username_var = tk.StringVar()
        self.email_var = tk.StringVar()

        self.admin_user_var = tk.StringVar()
        self.admin_pass_var = tk.StringVar()

        self.pending_name = None
        self.pending_card_id = None

        self.container = tk.Frame(self.root, bg="white")
        self.container.pack(fill="both", expand=True)

        self.frames = {}
        for F in (Screen1, Screen2, Screen3, Screen4):
            frame = F(self.container, self)
            self.frames[F.__name__] = frame
            frame.place(relwidth=1, relheight=1)

        self.show_frame("Screen1")

    def show_frame(self, name):
        screen1 = self.frames["Screen1"]

        if name != "Screen1":
            screen1.stop_camera()

        frame = self.frames[name]
        frame.tkraise()

        if hasattr(frame, "reset_screen"):
            frame.reset_screen()

    def safe_quit_program(self):
        screen1 = self.frames.get("Screen1")
        if screen1:
            screen1.stop_camera()
        self.root.destroy()

    def open_csv_folder(self):
        subprocess.Popen(["xdg-open", CHECKIN_FOLDER])

    def open_database_folder(self):
        subprocess.Popen(["xdg-open", DATABASE_FOLDER])

    def open_terms_window(self):
        win = tk.Toplevel(self.root)
        win.title("Terms and Conditions")

        text = tk.Text(win)
        text.pack(fill="both", expand=True)
        text.insert("1.0", get_terms_text())
        text.config(state="disabled")

    def process_swipe_from_screen1(self):
        screen1 = self.frames["Screen1"]

        swipe = self.swipe_var.get().strip()

        if not swipe:
            screen1.set_message("No swipe detected.", "red")
            return

        try:
            name, card_id = parse_swipe(swipe)
        except:
            screen1.set_message("Invalid swipe format.", "red")
            return

        checkin_file = get_today_checkin_file()
        create_checkin_file_if_needed(checkin_file)

        if already_checked_in_today(checkin_file, card_id):
            screen1.set_message(f"{name} already checked in.", "orange")
            return

        student = find_student_in_database(card_id)

        if student:
            success, _ = screen1.camera.capture_image_with_face_check(student["Name"])

            if not success:
                screen1.set_message("Camera error.", "red")
                return

            save_checkin(checkin_file, student["Name"], student["Card ID"],
                         student["Student ID"], student["Phone Number"])

            screen1.set_message(f"{student['Name']} checked in.", "green")
            return

        self.pending_name = name
        self.pending_card_id = card_id
        self.show_frame("Screen2")

    def add_user_and_check_in(self):
        print("ADD USER FUNCTION TRIGGERED")
        screen1 = self.frames["Screen1"]

        success, _ = screen1.camera.capture_image_with_face_check(self.pending_name)

        if not success:
            screen1.set_message("Camera error.", "red")
            return

        screen1.set_message(f"{self.pending_name} added and checked in.", "green")

    def check_admin_credentials(self):
        if self.admin_user_var.get() == ADMIN_USERNAME and self.admin_pass_var.get() == ADMIN_PASSWORD:
            self.show_frame("Screen4")
