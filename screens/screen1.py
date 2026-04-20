import tkinter as tk

from config import (
    ACCENT_TEXT_COLOR,
    APP_BACKGROUND_COLOR,
    BUTTON_FONT,
    DETAIL_FONT,
    INPUT_BACKGROUND_COLOR,
    INPUT_FONT,
    INSTRUCTION_FONT,
    MESSAGE_FONT,
    PANEL_BACKGROUND_COLOR,
    PANEL_BORDER_COLOR,
    PRIMARY_TEXT_COLOR,
    SMALL_FONT,
    STATUS_BACKGROUND_COLOR,
    STATUS_MESSAGE_TIMEOUT_MS,
    TITLE_FONT,
)


class Screen1(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=APP_BACKGROUND_COLOR)

        self.controller = controller
        self.message_timeout_job = None

        content = tk.Frame(self, bg=APP_BACKGROUND_COLOR)
        content.pack(expand=True)

        self.panel = tk.Frame(
            content,
            bg=PANEL_BACKGROUND_COLOR,
            bd=1,
            relief="solid",
            highlightbackground=PANEL_BORDER_COLOR,
            highlightcolor=PANEL_BORDER_COLOR,
            highlightthickness=1,
            padx=46,
            pady=36
        )
        self.panel.pack()

        tk.Label(
            self.panel,
            text="Robotics Lab Check-In",
            font=TITLE_FONT,
            fg=PRIMARY_TEXT_COLOR,
            bg=PANEL_BACKGROUND_COLOR
        ).pack(pady=(0, 10))

        tk.Label(
            self.panel,
            text="Swipe ID or Register",
            font=INSTRUCTION_FONT,
            fg=ACCENT_TEXT_COLOR,
            bg=PANEL_BACKGROUND_COLOR
        ).pack(pady=(0, 24))

        self.status_frame = tk.Frame(
            self.panel,
            bg=STATUS_BACKGROUND_COLOR,
            bd=1,
            relief="solid",
            highlightbackground=PANEL_BORDER_COLOR,
            highlightcolor=PANEL_BORDER_COLOR,
            highlightthickness=1,
            padx=18,
            pady=16
        )
        self.status_frame.pack(fill="x", pady=(0, 22))

        tk.Label(
            self.status_frame,
            text="Status",
            font=DETAIL_FONT,
            fg=ACCENT_TEXT_COLOR,
            bg=STATUS_BACKGROUND_COLOR
        ).pack(anchor="w")

        self.message_label = tk.Label(
            self.status_frame,
            text="Initializing...",
            font=MESSAGE_FONT,
            fg=PRIMARY_TEXT_COLOR,
            bg=STATUS_BACKGROUND_COLOR,
            justify="center"
        )
        self.message_label.pack(fill="x", pady=(8, 0))

        tk.Label(
            self.panel,
            text="Swipe your card into the reader or use the registration option below.",
            font=DETAIL_FONT,
            fg=PRIMARY_TEXT_COLOR,
            bg=PANEL_BACKGROUND_COLOR
        ).pack(pady=(0, 12))

        self.swipe_entry = tk.Entry(
            self.panel,
            textvariable=controller.swipe_var,
            font=INPUT_FONT,
            show="*",
            justify="center",
            width=28,
            bg=INPUT_BACKGROUND_COLOR,
            fg=PRIMARY_TEXT_COLOR,
            relief="solid",
            bd=1,
            insertwidth=3
        )
        self.swipe_entry.pack(ipady=12, pady=(0, 18))
        self.swipe_entry.bind("<Return>", lambda e: controller.process_swipe_from_screen1())

        tk.Button(
            self.panel,
            text="Register / Check In Without Card",
            font=BUTTON_FONT,
            width=28,
            height=2,
            command=controller.start_manual_registration_flow
        ).pack(pady=(0, 12))

        action_row = tk.Frame(self.panel, bg=PANEL_BACKGROUND_COLOR)
        action_row.pack(pady=(0, 18))

        tk.Button(
            action_row,
            text="Terms and Conditions",
            font=BUTTON_FONT,
            width=18,
            command=controller.open_terms_window
        ).grid(row=0, column=0, padx=8)

        tk.Button(
            action_row,
            text="Admin",
            font=BUTTON_FONT,
            width=10,
            command=lambda: controller.show_frame("Screen3")
        ).grid(row=0, column=1, padx=8)

        tk.Label(
            self.panel,
            text="By using this kiosk, you acknowledge the terms and conditions.",
            font=SMALL_FONT,
            fg=ACCENT_TEXT_COLOR,
            bg=PANEL_BACKGROUND_COLOR,
            wraplength=720,
            justify="center"
        ).pack()

    def reset_screen(self):
        self.controller.swipe_var.set("")
        if self.controller.ensure_camera_running():
            self.set_message("Ready - Swipe ID")
        else:
            self.set_message("Camera unavailable", "red")

    def set_message(self, text, color="black", auto_clear=False):
        self._cancel_message_timeout()
        self.message_label.config(text=text, fg=color)
        if auto_clear:
            self.message_timeout_job = self.after(
                STATUS_MESSAGE_TIMEOUT_MS,
                self.reset_status_message
            )

    def reset_status_message(self):
        self._cancel_message_timeout()
        if self.controller.is_camera_running():
            self.message_label.config(text="Ready - Swipe ID", fg=PRIMARY_TEXT_COLOR)
        else:
            self.message_label.config(text="Camera unavailable", fg="red")

    def _cancel_message_timeout(self):
        if self.message_timeout_job is not None:
            self.after_cancel(self.message_timeout_job)
            self.message_timeout_job = None

    def get_primary_focus_widget(self):
        return self.swipe_entry
