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
from contract_service import generate_behavioral_contract, has_signed_contract
from data_service import (
    add_student_to_database,
    already_checked_in_today,
    find_student_by_credentials,
    find_student_in_database,
    get_registration_conflict,
    save_checkin,
    update_student_card_id,
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
from screens.screen5 import Screen5
from validators import (
    build_mymdc_email,
    normalize_person_name,
    normalize_phone_number,
    parse_swipe,
    valid_mymdc_username,
    valid_phone_number,
    valid_student_id,
)


def describe_root_window(window):
    try:
        state = window.state()
    except tk.TclError:
        state = "unavailable"

    return "state={0} mapped={1} viewable={2} geometry={3}".format(
        state,
        window.winfo_ismapped(),
        window.winfo_viewable(),
        window.winfo_geometry()
    )


def configure_root_window(window):
    width = window.winfo_screenwidth()
    height = window.winfo_screenheight()
    print("[Startup] Configuring stable root window: {0}x{1}".format(width, height))

    window.overrideredirect(False)

    try:
        window.attributes("-topmost", False)
    except tk.TclError as exc:
        print("[Startup] Could not disable -topmost:", exc)

    try:
        window.attributes("-fullscreen", False)
    except tk.TclError as exc:
        print("[Startup] Could not disable -fullscreen:", exc)

    window.geometry(f"{width}x{height}+0+0")
    print("[Startup] Root configured:", describe_root_window(window))


class CheckInApp:
    FOCUS_RETRY_MS = 150

    def __init__(self, root):
        print("[Startup] CheckInApp init start")
        self.root = root
        self.root.title("ID Check-In System")
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.root.configure(bg="white")
        self.active_screen_name = None

        initialize_storage()
        print("[Startup] Storage initialized")

        self.camera_manager = CameraManager()
        self.capture_service = CaptureService(self.camera_manager)
        self.camera_manager.set_state_callback(self._handle_camera_state_change)
        print("[Startup] Camera services created")

        self.swipe_var = tk.StringVar()
        self.name_var = tk.StringVar()
        self.student_var = tk.StringVar()
        self.phone_var = tk.StringVar()
        self.mymdc_username_var = tk.StringVar()
        self.admin_user_var = tk.StringVar()
        self.admin_pass_var = tk.StringVar()

        self.pending_name = None
        self.pending_card_id = None
        self.pending_link_candidate = None
        self.pending_link_form = None
        self.registration_context = {}
        self.processing = False
        self.processing_lock = threading.Lock()

        self.container = tk.Frame(self.root, bg="white")
        self.container.pack(fill="both", expand=True)
        print("[Startup] Root container created")

        self.frames = {}
        for frame_class in (Screen1, Screen2, Screen3, Screen4, Screen5):
            print("[Startup] Creating frame:", frame_class.__name__)
            frame = frame_class(self.container, self)
            self.frames[frame_class.__name__] = frame
            frame.place(relwidth=1, relheight=1)
            print("[Startup] Frame ready:", frame_class.__name__)

        self.root.bind("<FocusIn>", self._handle_root_focus_in, add="+")
        self.show_frame("Screen1")
        print("[Startup] CheckInApp init complete")

    def show_frame(self, name):
        print("[Startup] show_frame ->", name)
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
            print("[Startup] No primary focus widget for", self.active_screen_name)
            return

        print("[Startup] Scheduling focus restore for", self.active_screen_name)
        self.root.after_idle(lambda: self._focus_widget(widget))
        self.root.after(
            self.FOCUS_RETRY_MS,
            lambda: self._focus_widget(widget)
        )

    def _set_main_status(self, text, color="black", auto_clear=False):
        screen1 = self.frames.get("Screen1")
        if screen1:
            screen1.set_message(text, color, auto_clear=auto_clear)

    def _handle_camera_state_change(self, available):
        try:
            self.root.after(0, lambda: self._apply_camera_state_change(available))
        except tk.TclError:
            pass

    def _apply_camera_state_change(self, available):
        try:
            if not self.root.winfo_exists():
                return
        except tk.TclError:
            return

        if available:
            self.capture_service.start_camera()

        if self.active_screen_name != "Screen1" or self._is_processing():
            return

        screen1 = self.frames.get("Screen1")
        if not screen1:
            return

        if available:
            if screen1.message_label.cget("text") == "Camera unavailable":
                screen1.reset_status_message()
            return

        self._set_main_status("Camera unavailable", "red")

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
        print("[Startup] ensure_camera_running called")
        return self.capture_service.start_camera()

    def is_camera_running(self):
        return self.capture_service.is_camera_running()

    def safe_quit_program(self):
        print("[Startup] safe_quit_program called")
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
        if not self._begin_processing():
            self._set_main_status("Already processing...", "orange", auto_clear=True)
            return

        swipe = self.swipe_var.get().strip()
        if not swipe:
            self._set_main_status("No swipe detected.", "red", auto_clear=True)
            self._end_processing()
            return

        try:
            name, card_id = parse_swipe(swipe)
        except Exception:
            self._set_main_status("Invalid swipe format.", "red", auto_clear=True)
            self.swipe_var.set("")
            self._end_processing()
            return

        student = find_student_in_database(card_id)
        canonical_name = student["Name"] if student else name

        checkin_file = get_today_checkin_file()
        create_checkin_file_if_needed(checkin_file)

        if already_checked_in_today(
            checkin_file,
            card_id=card_id,
            student_id=student["Student ID"] if student else None
        ):
            self._set_main_status(
                f"{canonical_name} already checked in.",
                "orange",
                auto_clear=True
            )
            self.swipe_var.set("")
            self._end_processing()
            return

        if not self.is_camera_running():
            self._set_main_status("Camera unavailable.", "red", auto_clear=True)
            self._end_processing()
            return

        self._set_main_status("Processing...", "blue")
        self.root.update_idletasks()

        event_capture = self.capture_service.trigger_capture_event()
        if event_capture is None:
            self._set_main_status("Camera unavailable.", "red", auto_clear=True)
            self._end_processing()
            return

        if student:
            self.swipe_var.set("")
            threading.Thread(
                target=self._process_known_user_capture,
                args=(student, checkin_file, event_capture),
                daemon=True
            ).start()
            return

        self.pending_name = canonical_name
        self.pending_card_id = card_id
        self.pending_link_candidate = None
        self.pending_link_form = None

        if not self.capture_service.start_enrollment_session(event_capture):
            self._clear_registration_state()
            self._set_main_status("Camera unavailable.", "red", auto_clear=True)
            self._end_processing()
            return

        self._prepare_registration_form(
            mode="swipe",
            initial_name=canonical_name
        )
        self._end_processing()
        self.show_frame("Screen2")

    def start_manual_registration_flow(self):
        if self._is_processing():
            return

        self._clear_registration_state()
        self.capture_service.cancel_enrollment_session()
        self._prepare_registration_form(mode="manual")
        self.show_frame("Screen2")

    def submit_registration_form(self):
        screen2 = self.frames["Screen2"]

        if not self._begin_processing():
            screen2.set_message("Already processing...", "orange")
            return

        try:
            normalized_name = normalize_person_name(self.name_var.get().strip())
        except ValueError:
            screen2.set_message("Enter a valid full name.", "red")
            self._end_processing()
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

        if validation_failed:
            self._end_processing()
            return

        normalized_phone = normalize_phone_number(phone)
        normalized_username, email = build_mymdc_email(username)
        existing_student = find_student_by_credentials(sid, normalized_username)
        conflict_message = get_registration_conflict(sid, normalized_username)

        if existing_student:
            if self.registration_context.get("mode") == "swipe":
                if not existing_student.get("Card ID"):
                    self.pending_link_candidate = existing_student
                    self.pending_link_form = {
                        "name": normalized_name,
                        "student_id": sid,
                        "phone_number": normalized_phone,
                        "mymdc_username": normalized_username,
                        "email": email,
                        "swipe_name": self.pending_name,
                    }
                    self._end_processing()
                    self.show_frame("Screen5")
                    return

                screen2.set_message(
                    "This student record already has a different card linked. Please see staff.",
                    "red"
                )
                self._end_processing()
                return

            checkin_file = get_today_checkin_file()
            create_checkin_file_if_needed(checkin_file)
            if already_checked_in_today(
                checkin_file,
                card_id=existing_student.get("Card ID"),
                student_id=existing_student.get("Student ID")
            ):
                screen2.set_message(
                    "{0} already checked in today.".format(existing_student["Name"]),
                    "orange"
                )
                self._end_processing()
                return

            if not self.is_camera_running():
                screen2.set_message("Camera unavailable.", "red")
                self._end_processing()
                return

            screen2.set_message("Processing...", "blue")
            threading.Thread(
                target=self._complete_existing_user_manual_flow,
                args=(existing_student, checkin_file),
                daemon=True
            ).start()
            return

        if conflict_message:
            screen2.set_message(conflict_message, "red")
            self._end_processing()
            return

        if not self.is_camera_running():
            screen2.set_message("Camera unavailable.", "red")
            self._end_processing()
            return

        if self.registration_context.get("mode") == "manual":
            if not self.capture_service.start_enrollment_session():
                screen2.set_message("Camera unavailable.", "red")
                self._end_processing()
                return

        screen2.set_message("Finalizing...", "blue")
        threading.Thread(
            target=self._complete_new_user_flow,
            args=(
                normalized_name,
                self.pending_card_id or "",
                sid,
                normalized_phone,
                normalized_username,
                email,
            ),
            daemon=True
        ).start()

    def confirm_card_link(self):
        if not self._begin_processing():
            return

        candidate = self.pending_link_candidate
        form = self.pending_link_form or {}
        if not candidate or not self.pending_card_id:
            self._end_processing()
            self._handle_background_failure()
            return

        updated_student = update_student_card_id(candidate["Student ID"], self.pending_card_id)
        if not updated_student:
            self._end_processing()
            self._handle_background_failure()
            return

        if not has_signed_contract(updated_student["Name"], updated_student["Student ID"]):
            generate_behavioral_contract(
                student_name=updated_student["Name"],
                student_id=updated_student["Student ID"],
                signed_name=updated_student["Name"]
            )

        checkin_file = get_today_checkin_file()
        create_checkin_file_if_needed(checkin_file)
        if already_checked_in_today(
            checkin_file,
            card_id=updated_student.get("Card ID"),
            student_id=updated_student.get("Student ID")
        ):
            self.capture_service.cancel_enrollment_session()

            def finish_already_checked_in():
                self.show_frame("Screen1")
                self._set_main_status(
                    "Card linked for {0}. Already checked in today.".format(updated_student["Name"]),
                    "orange",
                    auto_clear=True
                )
                self._clear_registration_state()
                self._end_processing()

            self.root.after(0, finish_already_checked_in)
            return

        threading.Thread(
            target=self._complete_card_link_flow,
            args=(updated_student, checkin_file, form.get("phone_number", updated_student.get("Phone Number", ""))),
            daemon=True
        ).start()

    def back_to_registration_from_link(self):
        self.show_frame("Screen2")

    def cancel_new_user_flow(self):
        if self._is_processing():
            return

        self.capture_service.cancel_enrollment_session()
        self._clear_registration_state()
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

    def _prepare_registration_form(self, mode, initial_name=""):
        self.registration_context = {"mode": mode}
        self.name_var.set(initial_name)
        self.student_var.set("")
        self.phone_var.set("")
        self.mymdc_username_var.set("")

    def _clear_registration_state(self):
        self.pending_name = None
        self.pending_card_id = None
        self.pending_link_candidate = None
        self.pending_link_form = None
        self.registration_context = {}
        self.name_var.set("")
        self.student_var.set("")
        self.phone_var.set("")
        self.mymdc_username_var.set("")

    def _process_known_user_capture(self, student, checkin_file, event_capture):
        try:
            success, path, metrics = self.capture_service.capture_known_user(
                student["Name"],
                identity_value=student["Student ID"],
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
                if not success:
                    self._set_main_status("Camera error.", "red", auto_clear=True)
                    self._end_processing()
                    return

                print("[Capture] Final photo path:", path)
                if metrics:
                    print("[Capture] Known-user best score:", round(metrics.total_score, 3))

                self._set_main_status(f"{student['Name']} checked in.", "green", auto_clear=True)
                self.swipe_var.set("")
                self._end_processing()

            self.root.after(0, finish)
        except Exception as exc:
            print("[App] Known-user processing failed:", exc)
            self.root.after(0, self._handle_background_failure)

    def _complete_existing_user_manual_flow(self, student, checkin_file):
        try:
            success, path, metrics = self.capture_service.capture_known_user(
                student["Name"],
                identity_value=student["Student ID"]
            )

            if success:
                save_checkin(
                    checkin_file,
                    student["Name"],
                    student.get("Card ID", ""),
                    student["Student ID"],
                    student["Phone Number"]
                )

            def finish():
                if not success:
                    self.frames["Screen2"].set_message("Camera error.", "red")
                    self._end_processing()
                    return

                if metrics:
                    print("[Capture] Manual known-user best score:", round(metrics.total_score, 3))
                print("[Capture] Final photo path:", path)

                self.swipe_var.set("")
                self.show_frame("Screen1")
                self._set_main_status(f"{student['Name']} checked in.", "green", auto_clear=True)
                self._clear_registration_state()
                self._end_processing()

            self.root.after(0, finish)
        except Exception as exc:
            print("[App] Manual existing-user processing failed:", exc)
            self.root.after(0, self._handle_background_failure)

    def _complete_new_user_flow(self, name, card_id, sid, phone, username, email):
        try:
            success, path, metrics = self.capture_service.finalize_enrollment_capture(
                name,
                identity_value=sid
            )

            if not success:
                def fail():
                    self.show_frame("Screen1")
                    self._set_main_status("Camera error.", "red", auto_clear=True)
                    self._clear_registration_state()
                    self._end_processing()

                self.root.after(0, fail)
                return

            add_student_to_database(
                name,
                card_id,
                sid,
                phone,
                username,
                email
            )

            if has_signed_contract(name, sid):
                print("[Contract] Signed contract already exists for:", name, sid)
            else:
                generate_behavioral_contract(
                    student_name=name,
                    student_id=sid,
                    signed_name=name
                )

            checkin_file = get_today_checkin_file()
            create_checkin_file_if_needed(checkin_file)
            save_checkin(
                checkin_file,
                name,
                card_id,
                sid,
                phone
            )

            def finish():
                if metrics:
                    print("[Capture] Enrollment best score:", round(metrics.total_score, 3))
                print("[Capture] Final photo path:", path)

                self.swipe_var.set("")
                self.show_frame("Screen1")
                self._set_main_status(f"{name} added and checked in.", "green", auto_clear=True)
                self._clear_registration_state()
                self._end_processing()

            self.root.after(0, finish)
        except Exception as exc:
            print("[App] Enrollment processing failed:", exc)
            self.root.after(0, self._handle_background_failure)

    def _complete_card_link_flow(self, student, checkin_file, phone_number):
        try:
            success, path, metrics = self.capture_service.finalize_enrollment_capture(
                student["Name"],
                identity_value=student["Student ID"]
            )

            if success:
                save_checkin(
                    checkin_file,
                    student["Name"],
                    student["Card ID"],
                    student["Student ID"],
                    phone_number or student.get("Phone Number", "")
                )

            def finish():
                if not success:
                    self._set_main_status("Camera error.", "red", auto_clear=True)
                    self.show_frame("Screen1")
                    self._clear_registration_state()
                    self._end_processing()
                    return

                if metrics:
                    print("[Capture] Linked-user best score:", round(metrics.total_score, 3))
                print("[Capture] Final photo path:", path)

                self.show_frame("Screen1")
                self._set_main_status(
                    "Card linked for {0}. Check-in complete.".format(student["Name"]),
                    "green",
                    auto_clear=True
                )
                self._clear_registration_state()
                self._end_processing()

            self.root.after(0, finish)
        except Exception as exc:
            print("[App] Card link processing failed:", exc)
            self.root.after(0, self._handle_background_failure)

    def _handle_background_failure(self):
        self.show_frame("Screen1")
        self._set_main_status("Unexpected error.", "red", auto_clear=True)
        self.capture_service.cancel_enrollment_session()
        self._clear_registration_state()
        self._end_processing()
