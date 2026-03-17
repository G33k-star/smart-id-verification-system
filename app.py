import os
import sys
import subprocess
import tkinter as tk
from cam import capture_image


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
        self.root.destroy()

    def show_frame(self, frame_name):
        frame = self.frames[frame_name]
        frame.tkraise()

        if frame_name == "Screen1":
            frame.reset_screen()
        elif frame_name == "Screen2":
            frame.reset_screen()
        elif frame_name == "Screen3":
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
        except Exception:
            pass

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

        student = find_student_in_database(card_id)

        if student:
            save_checkin(
                checkin_file,
                student["Name"],
                student["Card ID"],
                student["Student ID"],
                student["Phone Number"]
            )
            screen1.set_message("User, {0} checked in.".format(student["Name"]), "green", success=True)
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

        image_path = capture_image(self.pending_name)
        print("Captured:", image_path)

        save_checkin(
            checkin_file,
            self.pending_name,
            self.pending_card_id,
            student_id,
            phone
        )

        screen2.set_message(
            "User {0} added and checked in.".format(self.pending_name),
            "green",
            success=True
        )

        self.pending_name = None
        self.pending_card_id = None

        self.swipe_var.set("")
        self.student_var.set("")
        self.phone_var.set("")
        self.mymdc_username_var.set("")
        self.email_var.set("")

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
