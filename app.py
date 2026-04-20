import tkinter as tk
import os
import subprocess
import sys

from cam import CameraManager
from capture_session import CaptureService
from config import (
    WINDOW_WIDTH,
    WINDOW_HEIGHT,
    ADMIN_USERNAME,
    ADMIN_PASSWORD,
    DATA_CHECKINS_FOLDER,
    DATA_STUDENTS_FOLDER
)

from file_setup import (
    initialize_storage,
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

    if fullscreen:
        width = window.winfo_screenwidth()
        height = window.winfo_screenheight()
        window.geometry(f"{width}x{height}+0+0")
        window.attributes("-fullscreen", True)

    window.deiconify()
    window.lift()


class CheckInApp:
    FOCUS_RETRY_MS = 150

    def __init__(self, root):
        self.root = root
        self.root.title("ID Check-In System")
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.root.configure(bg="white")
        self.active_screen_name = None

        initialize_storage()

        self.camera_manager = CameraManager()
        self.capture_service = CaptureService(self.camera_manager)

        # Variables
        self.swipe_var = tk.StringVar()
        self.student_var = tk.StringVar()
        self.phone_var = tk.StringVar()
        self.mymdc_username_var = tk.StringVar()

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

        self.root.bind("<FocusIn>", self._handle_root_focus_in, add="+")
        self.show_frame("Screen1")

    # -------------------------
    # Navigation
    # -------------------------
    def show_frame(self, name):
        frame = self.frames[name]
        self.active_screen_name = name
        frame.tkraise()

        if hasattr(frame, "reset_screen"):
            frame.reset_screen()

        self.restore_active_focus()

    def get_active_primary_focus_widget(self):
        frame = self.frames.get(self.active_screen_name)
        if not frame:
            return None

        getter = getattr(frame, "get_primary_focus_widget", None)
        if not getter:
            return None

        return getter()

    def restore_active_focus(self):
        widget = self.get_active_primary_focus_widget()
        if not widget:
            return

        self.root.after_idle(lambda: self._focus_widget(widget))
        self.root.after(
            self.FOCUS_RETRY_MS,
            lambda: self._focus_widget(widget)
        )

    def _focus_widget(self, widget):
        try:
            if widget and widget.winfo_exists() and widget.winfo_viewable():
                widget.focus_set()
        except tk.TclError:
            pass

    def _handle_root_focus_in(self, event):
        if event.widget is self.root:
            self.restore_active_focus()

    # -------------------------
    # System Functions
    # -------------------------
    def ensure_camera_running(self):
        return self.capture_service.start_camera()

    def is_camera_running(self):
        return self.capture_service.is_camera_running()

    def safe_quit_program(self):
        self.capture_service.stop_camera()
        self.root.destroy()

    def open_checkins_folder(self):
        self.open_path(DATA_CHECKINS_FOLDER)

    def open_student_data_folder(self):
        self.open_path(DATA_STUDENTS_FOLDER)

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
        win.transient(self.root)
        win.attributes("-topmost", True)
        win.resizable(False, False)
        win.lift()
        win.focus_set()

        def close_terms_window():
            if win.winfo_exists():
                win.destroy()
            self.restore_active_focus()

        win.protocol("WM_DELETE_WINDOW", close_terms_window)

        text = tk.Text(win, wrap="word")
        text.pack(fill="both", expand=True, padx=10, pady=10)

        text.insert("1.0", get_terms_text())
        text.config(state="disabled")

        tk.Button(win, text="Close", command=close_terms_window).pack(pady=10)

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

        if not self.is_camera_running():
            screen1.set_message("Camera unavailable.", "red")
            return

        screen1.set_message("Processing...", "blue")
        self.root.update_idletasks()

        student = find_student_in_database(card_id)

        # Existing user
        if student:
            success, path, metrics = self.capture_service.capture_known_user(student["Name"])

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
            if metrics:
                print("[Capture] Known-user best score:", round(metrics.total_score, 3))

            screen1.set_message(f"{student['Name']} checked in.", "green")
            self.swipe_var.set("")
            return

        # New user
        self.pending_name = name
        self.pending_card_id = card_id
        if not self.capture_service.start_enrollment_session():
            self.pending_name = None
            self.pending_card_id = None
            screen1.set_message("Camera unavailable.", "red")
            return
        self.show_frame("Screen2")

    # -------------------------
    # Add User
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
        success, path, metrics = self.capture_service.finalize_enrollment_capture(self.pending_name)

        if not success:
            self.pending_name = None
            self.pending_card_id = None
            self.show_frame("Screen1")
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
        if metrics:
            print("[Capture] Enrollment best score:", round(metrics.total_score, 3))

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
        self.swipe_var.set("")

        self.show_frame("Screen1")
        screen1.set_message(f"{name} added and checked in.", "green")

    def cancel_new_user_flow(self):
        self.capture_service.cancel_enrollment_session()
        self.pending_name = None
        self.pending_card_id = None
        self.student_var.set("")
        self.phone_var.set("")
        self.mymdc_username_var.set("")
        self.show_frame("Screen1")

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
