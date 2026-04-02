'''
This system is a Smart ID Check-In System designed to log user attendance using a magnetic stripe card scanner.

When a user swipes their ID:
- The system parses the card data to extract name and card ID
- It checks if the user exists in the database
- If recognized, the user is checked in and logged into a daily CSV file
- If not recognized, the system prompts the user to register and then logs the check-in

The system runs on a Raspberry Pi with a USB card scanner and optional webcam. Data is stored locally using CSV files.
'''



import os
import sys
import subprocess
import tkinter as tk
from PIL import Image, ImageTk
import cv2

from cam import CameraManager

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

        self.camera = CameraManager()
        self.camera_preview_job = None
        self.camera_started = False

        self.show_frame("Screen1")

    def enable_kiosk_mode(self):
        if sys.platform.startswith("win"):
            self.root.state("zoomed")
            self.root.overrideredirect(True)
        else:
            self.root.attributes("-fullscreen", True)
            self.root.after(100, lambda: self.root.overrideredirect(True))

        self.root.protocol("WM_DELETE_WINDOW", lambda: None)
        self.root.bind("<Alt-F4>", lambda event: "break")
        self.root.bind("<Escape>", lambda event: "break")
        self.root.bind("<Control-w>", lambda event: "break")

    def safe_quit_program(self):
        self.stop_camera_preview()
        self.root.destroy()

    def show_frame(self, frame_name):
        current_frame = self.frames[frame_name]
        current_frame.tkraise()

        if frame_name == "Screen1":
            current_frame.reset_screen()
            self.start_camera_preview()
        else:
            self.stop_camera_preview()

            if frame_name == "Screen2":
                current_frame.reset_screen()
            elif frame_name == "Screen3":
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

    def start_camera_preview(self):
        screen1 = self.frames["Screen1"]

        if self.camera_preview_job is not None:
            return

        try:
            if not self.camera_started:
                self.camera.start()
                self.camera_started = True

            self.update_camera_preview()
        except Exception:
            self.camera_started = False
            self.camera_preview_job = None
            screen1.show_camera_unavailable()

    def stop_camera_preview(self):
        if self.camera_preview_job is not None:
            try:
                self.root.after_cancel(self.camera_preview_job)
            except Exception:
                pass
            self.camera_preview_job = None

        if self.camera_started:
            try:
                self.camera.stop()
            except Exception:
                pass
            self.camera_started = False

    def update_camera_preview(self):
        if not self.camera_started:
            self.camera_preview_job = None
            return

        screen1 = self.frames["Screen1"]

        try:
            preview_frame, faces = self.camera.get_preview_frame()

            if preview_frame is not None:
                rgb = cv2.cvtColor(preview_frame, cv2.COLOR_BGR2RGB)
                image = Image.fromarray(rgb)
                image = image.resize((640, 360))
                tk_image = ImageTk.PhotoImage(image)
                screen1.update_camera_image(tk_image)
        except Exception:
            screen1.show_camera_unavailable()
            self.stop_camera_preview()
            return

        self.camera_preview_job = self.root.after(30, self.update_camera_preview)

    def process_swipe_from_screen1(self):
        swipe = self.swipe_var.get().strip()
        screen1 = self.frames["Screen1"]
        screen2 = self.frames["Screen2"]

        if swipe == "":
            screen1.set_message("No swipe detected.", "red")
            return

        try:
            name, card_id = parse_swipe(swipe)
        except Exception:
            screen1.set_message("Invalid swipe format.", "red")
            return

        checkin_file = get_today_checkin_file()
        create_checkin_file_if_needed(checkin_file)

        if already_checked_in_today(checkin_file, card_id):
            screen1.set_message("User, {0} already checked in.".format(name), "orange")
            self.swipe_var.set("")
            screen1.focus_swipe()
            return

        if not self.camera_started:
            screen1.set_message("Camera is not available.", "red")
            return

        screen1.set_message("Processing...", "blue")
        self.root.update_idletasks()

        student = find_student_in_database(card_id)

        if student:
            success, image_path = self.camera.capture_image_with_face_check(student["Name"])

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

            screen1.set_message(
                "User, {0} checked in.".format(student["Name"]),
                "green",
                success=True
            )
            self.swipe_var.set("")
            screen1.focus_swipe()
            return

        self.pending_name = name
        self.pending_card_id = card_id
        self.show_frame("Screen2")
        screen2.set_message("User not recognized. Add new user?", "black")

    def add_user_and_check_in(self):
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

        if not self.camera_started:
            try:
                self.camera.start()
                self.camera_started = True
            except Exception:
                screen2.set_message("Camera is not available.", "red")
                return

        success, image_path = self.camera.capture_image_with_face_check(self.pending_name)

        if not success:
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
        screen1.set_message(
            "User {0} added and checked in.".format(saved_name),
            "green",
            success=True
        )

        self.root.after(1800, lambda: self.show_frame("Screen1"))

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
