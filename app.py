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
        for frame_class in (Screen1, Screen2, Screen3, Screen4):
            frame = frame_class(self.container, self)
            self.frames[frame_class.__name__] = frame
            frame.place(relx=0, rely=0, relwidth=1, relheight=1)

        self.show_frame("Screen1")

    def show_frame(self, frame_name):
        screen1 = self.frames["Screen1"]

        if frame_name != "Screen1":
            screen1.stop_camera()

        frame = self.frames[frame_name]
        frame.tkraise()

        if hasattr(frame, "reset_screen"):
            frame.reset_screen()

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
        except Exception as exc:
            print("[App] Failed to open path:", exc)

    def safe_quit_program(self):
        print("[App] Safe shutdown initiated")
        try:
            screen1 = self.frames.get("Screen1")
            if screen1:
                screen1.stop_camera()
        except Exception as exc:
            print("[App] Camera shutdown error:", exc)

        self.root.destroy()

    def process_swipe_from_screen1(self):
        screen1 = self.frames["Screen1"]

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
            screen1.set_message("{0} already checked in.".format(name), "orange")
            self.swipe_var.set("")
            screen1.focus_swipe()
            return

        if not screen1.camera_active:
            screen1.set_message("Camera unavailable.", "red")
            screen1.focus_swipe()
            return

        screen1.set_message("Processing...", "blue")

        student = find_student_in_database(card_id)

        if student:
            success, image_path = screen1.camera.capture_image_with_face_check(student["Name"])

            if not success:
                screen1.set_message("Camera error.", "red")
                screen1.focus_swipe()
                return

            save_checkin(
                checkin_file,
                student["Name"],
                student["Card ID"],
                student["Student ID"],
                student["Phone Number"]
            )

            print("Saved:", image_path)
            screen1.set_message("Photo captured.", "blue")
            self.root.after(
                800,
                lambda: screen1.set_message("{0} checked in.".format(student["Name"]), "green")
            )

            self.swipe_var.set("")
            screen1.focus_swipe()
            return

        self.pending_name = name
        self.pending_card_id = card_id
        self.show_frame("Screen2")

    def add_user_and_check_in(self):
        screen2 = self.frames["Screen2"]

        if not self.pending_name or not self.pending_card_id:
            screen2.set_message("No pending user found.", "red")
            return

        sid = self.student_var.get().strip()
        phone = self.phone_var.get().strip()
        username = self.mymdc_username_var.get().strip()

        if not valid_student_id(sid):
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
        self.email_var.set(email)

        self.show_frame("Screen1")
        screen1 = self.frames["Screen1"]

        if not screen1.camera_active:
            self.show_frame("Screen2")
            screen2.set_message("Camera unavailable.", "red")
            return

        success, image_path = screen1.camera.capture_image_with_face_check(self.pending_name)

        if not success:
            self.show_frame("Screen2")
            screen2.set_message("Camera error.", "red")
            return

        add_student_to_database(
            self.pending_name,
            self.pending_card_id,
            sid,
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
            sid,
            phone
        )

        print("Saved:", image_path)

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
        screen1.set_message("Photo captured.", "blue")
        self.root.after(
            800,
            lambda: screen1.set_message("{0} added and checked in.".format(saved_name), "green")
        )

    def check_admin_credentials(self):
        screen3 = self.frames["Screen3"]

        username = self.admin_user_var.get().strip()
        password = self.admin_pass_var.get().strip()

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            self.admin_user_var.set("")
            self.admin_pass_var.set("")
            self.show_frame("Screen4")
        else:
            self.admin_user_var.set("")
            self.admin_pass_var.set("")
            screen3.set_message("Incorrect credentials.")
