import os
import subprocess
import sys
import threading
import tkinter as tk

from cam import CameraManager
from capture_session import CaptureService
from config import (
    ADMIN_PASSWORD,
    ADMIN_USERNAME,
    DATA_CHECKINS_FOLDER,
    DATA_STUDENTS_FOLDER,
    WINDOW_HEIGHT,
    WINDOW_WIDTH,
)
from contract_service import generate_behavioral_contract
from data_service import (
    add_student_to_database,
    already_checked_in_today,
    find_student_in_database,
    save_checkin,
)
from file_setup import (
    create_checkin_file_if_needed,
    get_terms_text,
    get_today_checkin_file,
    initialize_storage,
)
from screens.screen1 import Screen1
from screens.screen2 import Screen2
from screens.screen3 import Screen3
from screens.screen4 import Screen4
from validators import (
    build_mymdc_email,
    normalize_phone_number,
    parse_swipe,
    valid_mymdc_username,
    valid_phone_number,
    valid_student_id,
)


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

        self.swipe_var = tk.StringVar()
        self.student_var = tk.StringVar()
        self.phone_var = tk.StringVar()
        self.mymdc_username_var = tk.StringVar()
        self.admin_user_var = tk.StringVar()
        self.admin_pass_var = tk.StringVar()

        self.pending_name = None
        self.pending_card_id = None
        self.processing = False
        self.processing_lock = threading.Lock()

        self.container = tk.Frame(self.root, bg="white")
        self.container.pack(fill="both", expand=True)

        self.frames = {}
        for frame_class in (Screen1, Screen2, Screen3, Screen4):
            frame = frame_class(self.container, self)
            self.frames[frame_class.__name__] = frame
            frame.place(relwidth=1, relheight=1)

        self.root.bind("<FocusIn>", self._handle_root_focus_in, add="+")
        self.show_frame("Screen1")

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
        except Exception as exc:
            print("[App] Failed to open path:", exc)

    def open_terms_window(self):
        win = tk.Toplevel(self.root)
        win.title("Terms and Conditions")
        width = 600
        height = 400
        x_pos = (self.root.winfo_screenwidth() - width) // 2
        y_pos = (self.root.winfo_screenheight() - height) // 2
        win.geometry(f"{width}x{height}+{x_pos}+{y_pos}")
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

    def process_swipe_from_screen1(self):
        screen1 = self.frames["Screen1"]

        if not self._begin_processing():
            screen1.set_message("Already processing...", "orange")
            return

        swipe = self.swipe_var.get().strip()
        if not swipe:
            screen1.set_message("No swipe detected.", "red")
            self._end_processing()
            return

        try:
            name, card_id = parse_swipe(swipe)
        except Exception:
            screen1.set_message("Invalid swipe format.", "red")
            self.swipe_var.set("")
            self._end_processing()
            return

        checkin_file = get_today_checkin_file()
        create_checkin_file_if_needed(checkin_file)

        if already_checked_in_today(checkin_file, card_id):
            screen1.set_message(f"{name} already checked in.", "orange")
            self.swipe_var.set("")
            self._end_processing()
            return

        if not self.is_camera_running():
            screen1.set_message("Camera unavailable.", "red")
            self._end_processing()
            return

        screen1.set_message("Processing...", "blue")
        self.root.update_idletasks()

        event_capture = self.capture_service.trigger_capture_event()
        if event_capture is None:
            screen1.set_message("Camera unavailable.", "red")
            self._end_processing()
            return

        student = find_student_in_database(card_id)
        if student:
            self.swipe_var.set("")
            threading.Thread(
                target=self._process_known_user_capture,
                args=(student, checkin_file, event_capture),
                daemon=True
            ).start()
            return

        self.pending_name = name
        self.pending_card_id = card_id

        if not self.capture_service.start_enrollment_session(event_capture):
            self.pending_name = None
            self.pending_card_id = None
            screen1.set_message("Camera unavailable.", "red")
            self._end_processing()
            return

        self._end_processing()
        self.show_frame("Screen2")

    def add_user_and_check_in(self):
        screen2 = self.frames["Screen2"]

        if not self._begin_processing():
            screen2.set_message("Already processing...", "orange")
            return

        sid = self.student_var.get().strip()
        phone = self.phone_var.get().strip()
        username = self.mymdc_username_var.get().strip()

        validation_failed = False
        if not valid_student_id(sid):
            screen2.set_message("Invalid Student ID", "red")
            validation_failed = True

        if not valid_phone_number(phone):
            screen2.set_message("Invalid phone number", "red")
            validation_failed = True

        if not valid_mymdc_username(username):
            screen2.set_message("Invalid username", "red")
            validation_failed = True

        if not validation_failed:
            screen2.set_message("Finalizing...", "blue")

        pending_name = self.pending_name
        pending_card_id = self.pending_card_id
        threading.Thread(
            target=self._complete_new_user_flow,
            args=(pending_name, pending_card_id, sid, phone, username),
            daemon=True
        ).start()

    def cancel_new_user_flow(self):
        if self._is_processing():
            return

        self.capture_service.cancel_enrollment_session()
        self.pending_name = None
        self.pending_card_id = None
        self.student_var.set("")
        self.phone_var.set("")
        self.mymdc_username_var.set("")
        self.show_frame("Screen1")

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

    def _begin_processing(self):
        with self.processing_lock:
            if self.processing:
                return False

            self.processing = True
            return True

    def _end_processing(self):
        with self.processing_lock:
            self.processing = False

    def _is_processing(self):
        with self.processing_lock:
            return self.processing

    def _process_known_user_capture(self, student, checkin_file, event_capture):
        try:
            success, path, metrics = self.capture_service.capture_known_user(
                student["Name"],
                event_capture=event_capture
            )

            if success:
                save_checkin(
                    checkin_file,
                    student["Name"],
                    student["Card ID"],
                    student["Student ID"],
                    student["Phone Number"]
                )

            def finish():
                screen1 = self.frames["Screen1"]

                if not success:
                    screen1.set_message("Camera error.", "red")
                    self._end_processing()
                    return

                print("Saved:", path)
                if metrics:
                    print("[Capture] Known-user best score:", round(metrics.total_score, 3))

                screen1.set_message(f"{student['Name']} checked in.", "green")
                self.swipe_var.set("")
                self._end_processing()

            self.root.after(0, finish)
        except Exception as exc:
            print("[App] Known-user processing failed:", exc)
            self.root.after(0, self._handle_background_failure)

    def _complete_new_user_flow(self, pending_name, pending_card_id, sid, phone, username):
        try:
            normalized_phone = normalize_phone_number(phone)
            normalized_username, email = build_mymdc_email(username)
            success, path, metrics = self.capture_service.finalize_enrollment_capture(pending_name)

            if not success:
                def fail():
                    screen1 = self.frames["Screen1"]
                    self.pending_name = None
                    self.pending_card_id = None
                    self.show_frame("Screen1")
                    screen1.set_message("Camera error.", "red")
                    self._end_processing()

                self.root.after(0, fail)
                return

            add_student_to_database(
                pending_name,
                pending_card_id,
                sid,
                normalized_phone,
                normalized_username,
                email
            )
            generate_behavioral_contract(
                student_name=pending_name,
                student_id=sid,
                signed_name=pending_name
            )

            checkin_file = get_today_checkin_file()
            create_checkin_file_if_needed(checkin_file)
            save_checkin(
                checkin_file,
                pending_name,
                pending_card_id,
                sid,
                normalized_phone
            )

            def finish():
                screen1 = self.frames["Screen1"]

                if metrics:
                    print("[Capture] Enrollment best score:", round(metrics.total_score, 3))
                print("Saved:", path)

                self.pending_name = None
                self.pending_card_id = None
                self.student_var.set("")
                self.phone_var.set("")
                self.mymdc_username_var.set("")
                self.swipe_var.set("")

                self.show_frame("Screen1")
                screen1.set_message(f"{pending_name} added and checked in.", "green")
                self._end_processing()

            self.root.after(0, finish)
        except Exception as exc:
            print("[App] Enrollment processing failed:", exc)
            self.root.after(0, self._handle_background_failure)

    def _handle_background_failure(self):
        screen1 = self.frames["Screen1"]
        self.pending_name = None
        self.pending_card_id = None
        self.show_frame("Screen1")
        screen1.set_message("Unexpected error.", "red")
        self._end_processing()
