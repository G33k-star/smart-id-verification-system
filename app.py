import os
import logging
import subprocess
import sys
import threading
import tkinter as tk

from cam import CameraManager
from capture_session import CaptureService
from config import (
    ADMIN_PASSWORD,
    ADMIN_USERNAME,
    APP_BACKGROUND_COLOR,
    BUTTON_FONT,
    DATA_CHECKINS_FOLDER,
    DATA_STUDENTS_FOLDER,
    DETAIL_FONT,
    INPUT_BACKGROUND_COLOR,
    KIOSK_ALLOW_ESC_EXIT,
    KIOSK_FULLSCREEN,
    KIOSK_LOCK_KEYS,
    PANEL_BACKGROUND_COLOR,
    PANEL_BORDER_COLOR,
    PRIMARY_TEXT_COLOR,
    SCREEN_TITLE_FONT,
    WINDOW_HEIGHT,
    WINDOW_WIDTH,
)
from contract_service import (
    generate_behavioral_contract,
    get_signed_contract_path,
    has_signed_contract,
    rename_signed_contract,
)
from data_service import (
    add_student_to_database,
    already_checked_in_today,
    find_student_by_credentials,
    find_student_in_database,
    get_registration_conflict,
    save_checkin,
    update_student_for_first_card_link,
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


LOGGER = logging.getLogger(__name__)


def configure_root_window(window):
    width = window.winfo_screenwidth()
    height = window.winfo_screenheight()

    window.overrideredirect(False)
    window.configure(cursor="")

    try:
        window.attributes("-topmost", False)
    except tk.TclError:
        pass

    if KIOSK_FULLSCREEN:
        window.geometry(f"{width}x{height}+0+0")
        window.resizable(False, False)
        try:
            window.attributes("-fullscreen", True)
        except tk.TclError:
            window.geometry(f"{width}x{height}+0+0")
    else:
        try:
            window.attributes("-fullscreen", False)
        except tk.TclError:
            pass
        x_pos = max((width - WINDOW_WIDTH) // 2, 0)
        y_pos = max((height - WINDOW_HEIGHT) // 2, 0)
        window.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}+{x_pos}+{y_pos}")
        window.resizable(True, True)


class CheckInApp:
    FOCUS_RETRY_MS = 150

    def __init__(self, root):
        self.root = root
        self.root.title("Robotics Lab Check-In")
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.root.configure(bg=APP_BACKGROUND_COLOR)
        self.active_screen_name = None

        initialize_storage()

        self.camera_manager = CameraManager()
        self.capture_service = CaptureService(self.camera_manager)
        self.camera_manager.set_state_callback(self._handle_camera_state_change)

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

        self.root.bind("<Escape>", self._handle_escape_key, add="+")
        if KIOSK_LOCK_KEYS:
            self._install_kiosk_key_lock()
        self.container = tk.Frame(self.root, bg=APP_BACKGROUND_COLOR)
        self.container.pack(fill="both", expand=True)

        self.frames = {}
        for frame_class in (Screen1, Screen2, Screen3, Screen4, Screen5):
            frame = frame_class(self.container, self)
            self.frames[frame_class.__name__] = frame
            frame.place(relwidth=1, relheight=1)

        self.root.bind("<FocusIn>", self._handle_root_focus_in, add="+")
        self.show_frame("Screen1")

    def show_frame(self, name):
        frame = self.frames[name]
        self.active_screen_name = name

        if hasattr(frame, "reset_screen"):
            frame.reset_screen()

        frame.tkraise()
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

    def _install_kiosk_key_lock(self):
        blocked_sequences = (
            "<KeyPress-Alt_L>",
            "<KeyRelease-Alt_L>",
            "<KeyPress-Alt_R>",
            "<KeyRelease-Alt_R>",
            "<KeyPress-Control_L>",
            "<KeyRelease-Control_L>",
            "<KeyPress-Control_R>",
            "<KeyRelease-Control_R>",
            "<KeyPress-Super_L>",
            "<KeyRelease-Super_L>",
            "<KeyPress-Super_R>",
            "<KeyRelease-Super_R>",
            "<KeyPress-Meta_L>",
            "<KeyRelease-Meta_L>",
            "<KeyPress-Meta_R>",
            "<KeyRelease-Meta_R>",
            "<KeyPress-Escape>",
            "<KeyRelease-Escape>",
        )

        for sequence in blocked_sequences:
            self.root.bind_all(sequence, self._suppress_key_event, add="+")

    def _suppress_key_event(self, _event):
        return "break"

    def _handle_escape_key(self, _event):
        if KIOSK_ALLOW_ESC_EXIT:
            self.safe_quit_program()
            return "break"

        return "break"

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
        except Exception:
            LOGGER.exception("Failed to open path %s", path)

    def open_terms_window(self):
        win = tk.Toplevel(self.root)
        win.title("Terms and Conditions")
        width = 760
        height = 520
        x_pos = (self.root.winfo_screenwidth() - width) // 2
        y_pos = (self.root.winfo_screenheight() - height) // 2
        win.geometry(f"{width}x{height}+{x_pos}+{y_pos}")
        win.transient(self.root)
        win.attributes("-topmost", True)
        win.resizable(False, False)
        win.lift()
        win.focus_set()
        win.configure(bg=APP_BACKGROUND_COLOR)

        def close_terms_window():
            if win.winfo_exists():
                win.destroy()
            self.restore_active_focus()

        win.protocol("WM_DELETE_WINDOW", close_terms_window)

        panel = tk.Frame(
            win,
            bg=PANEL_BACKGROUND_COLOR,
            bd=1,
            relief="solid",
            highlightbackground=PANEL_BORDER_COLOR,
            highlightcolor=PANEL_BORDER_COLOR,
            highlightthickness=1
        )
        panel.pack(fill="both", expand=True, padx=20, pady=20)

        tk.Label(
            panel,
            text="Terms and Conditions",
            font=SCREEN_TITLE_FONT,
            fg=PRIMARY_TEXT_COLOR,
            bg=PANEL_BACKGROUND_COLOR
        ).pack(pady=(18, 10))

        text = tk.Text(
            panel,
            wrap="word",
            font=DETAIL_FONT,
            bg=INPUT_BACKGROUND_COLOR,
            fg=PRIMARY_TEXT_COLOR,
            relief="solid",
            bd=1
        )
        text.pack(fill="both", expand=True, padx=20, pady=(0, 16))
        text.insert("1.0", get_terms_text())
        text.config(state="disabled")

        tk.Button(
            panel,
            text="Close",
            font=BUTTON_FONT,
            width=14,
            command=close_terms_window
        ).pack(pady=(0, 18))

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

        canonical_card_name = form.get("swipe_name") or candidate["Name"]
        old_student, updated_student = update_student_for_first_card_link(
            candidate["Student ID"],
            self.pending_card_id,
            canonical_card_name
        )
        if not old_student or not updated_student:
            self._end_processing()
            self._handle_background_failure()
            return

        photo_rename_result = self.camera_manager.rename_saved_photos(
            old_student["Name"],
            updated_student["Name"],
            identity_value=updated_student["Student ID"]
        )
        contract_rename_result = rename_signed_contract(
            updated_student["Student ID"],
            old_student["Name"],
            updated_student["Name"]
        )

        if photo_rename_result["collisions"]:
            LOGGER.warning(
                "Skipped photo rename for student %s because one or more destination files already exist.",
                updated_student["Student ID"]
            )

        if contract_rename_result["collision"]:
            LOGGER.warning(
                "Skipped contract rename for student %s because the destination file already exists.",
                updated_student["Student ID"]
            )

        if not get_signed_contract_path(updated_student["Name"], updated_student["Student ID"]).exists():
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
            success, _, _ = self.capture_service.capture_known_user(
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

                self._set_main_status(f"{student['Name']} checked in.", "green", auto_clear=True)
                self.swipe_var.set("")
                self._end_processing()

            self.root.after(0, finish)
        except Exception:
            LOGGER.exception("Known-user processing failed")
            self.root.after(0, self._handle_background_failure)

    def _complete_existing_user_manual_flow(self, student, checkin_file):
        try:
            success, _, _ = self.capture_service.capture_known_user(
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

                self.swipe_var.set("")
                self.show_frame("Screen1")
                self._set_main_status(f"{student['Name']} checked in.", "green", auto_clear=True)
                self._clear_registration_state()
                self._end_processing()

            self.root.after(0, finish)
        except Exception:
            LOGGER.exception("Manual existing-user processing failed")
            self.root.after(0, self._handle_background_failure)

    def _complete_new_user_flow(self, name, card_id, sid, phone, username, email):
        try:
            success, _, _ = self.capture_service.finalize_enrollment_capture(
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

            if not has_signed_contract(name, sid):
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
                self.swipe_var.set("")
                self.show_frame("Screen1")
                self._set_main_status(f"{name} added and checked in.", "green", auto_clear=True)
                self._clear_registration_state()
                self._end_processing()

            self.root.after(0, finish)
        except Exception:
            LOGGER.exception("Enrollment processing failed")
            self.root.after(0, self._handle_background_failure)

    def _complete_card_link_flow(self, student, checkin_file, phone_number):
        try:
            success, _, _ = self.capture_service.finalize_enrollment_capture(
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

                self.show_frame("Screen1")
                self._set_main_status(
                    "Card linked for {0}. Check-in complete.".format(student["Name"]),
                    "green",
                    auto_clear=True
                )
                self._clear_registration_state()
                self._end_processing()

            self.root.after(0, finish)
        except Exception:
            LOGGER.exception("Card link processing failed")
            self.root.after(0, self._handle_background_failure)

    def _handle_background_failure(self):
        self.show_frame("Screen1")
        self._set_main_status("Unexpected error.", "red", auto_clear=True)
        self.capture_service.cancel_enrollment_session()
        self._clear_registration_state()
        self._end_processing()
