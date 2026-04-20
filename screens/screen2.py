import tkinter as tk

from config import (
    ACCENT_TEXT_COLOR,
    APP_BACKGROUND_COLOR,
    BODY_FONT,
    BUTTON_FONT,
    DETAIL_FONT,
    INPUT_BACKGROUND_COLOR,
    INPUT_FONT,
    PANEL_BACKGROUND_COLOR,
    PANEL_BORDER_COLOR,
    PRIMARY_TEXT_COLOR,
    SCREEN_TITLE_FONT,
    SECONDARY_TEXT_COLOR,
)


class Screen2(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=APP_BACKGROUND_COLOR)

        self.controller = controller

        content = tk.Frame(self, bg=APP_BACKGROUND_COLOR)
        content.pack(expand=True)

        panel = tk.Frame(
            content,
            bg=PANEL_BACKGROUND_COLOR,
            bd=1,
            relief="solid",
            highlightbackground=PANEL_BORDER_COLOR,
            highlightcolor=PANEL_BORDER_COLOR,
            highlightthickness=1,
            padx=42,
            pady=34
        )
        panel.pack()

        self.title_label = tk.Label(
            panel,
            text="Registration",
            font=SCREEN_TITLE_FONT,
            fg=PRIMARY_TEXT_COLOR,
            bg=PANEL_BACKGROUND_COLOR
        )
        self.title_label.pack(pady=(0, 12))

        self.message_label = tk.Label(
            panel,
            text="",
            font=DETAIL_FONT,
            fg=ACCENT_TEXT_COLOR,
            bg=PANEL_BACKGROUND_COLOR,
            wraplength=760,
            justify="center"
        )
        self.message_label.pack(pady=(0, 18))

        form = tk.Frame(panel, bg=PANEL_BACKGROUND_COLOR)
        form.pack(pady=(0, 24))

        self.name_entry = self._build_labeled_entry(
            form,
            row=0,
            label_text="Full Name",
            textvariable=controller.name_var
        )
        self.student_entry = self._build_labeled_entry(
            form,
            row=1,
            label_text="Student ID",
            textvariable=controller.student_var
        )
        self.phone_entry = self._build_labeled_entry(
            form,
            row=2,
            label_text="Phone Number",
            textvariable=controller.phone_var
        )
        self.username_entry = self._build_labeled_entry(
            form,
            row=3,
            label_text="myMDC Username",
            textvariable=controller.mymdc_username_var
        )

        tk.Label(
            form,
            text="Example: john.smith001",
            font=DETAIL_FONT,
            fg=SECONDARY_TEXT_COLOR,
            bg=PANEL_BACKGROUND_COLOR
        ).grid(row=4, column=1, sticky="w", pady=(2, 0))

        btn_frame = tk.Frame(panel, bg=PANEL_BACKGROUND_COLOR)
        btn_frame.pack()

        self.primary_button = tk.Button(
            btn_frame,
            text="Continue",
            font=BUTTON_FONT,
            width=16,
            height=2,
            command=controller.submit_registration_form
        )
        self.primary_button.grid(row=0, column=0, padx=10)

        tk.Button(
            btn_frame,
            text="Cancel",
            font=BUTTON_FONT,
            width=16,
            height=2,
            command=controller.cancel_new_user_flow
        ).grid(row=0, column=1, padx=10)

    def _build_labeled_entry(self, parent, row, label_text, textvariable):
        tk.Label(
            parent,
            text=label_text,
            font=BODY_FONT,
            fg=PRIMARY_TEXT_COLOR,
            bg=PANEL_BACKGROUND_COLOR
        ).grid(row=row, column=0, sticky="e", padx=(0, 16), pady=10)

        entry = tk.Entry(
            parent,
            textvariable=textvariable,
            font=INPUT_FONT,
            width=26,
            bg=INPUT_BACKGROUND_COLOR,
            fg=PRIMARY_TEXT_COLOR,
            relief="solid",
            bd=1,
            insertwidth=3
        )
        entry.grid(row=row, column=1, sticky="w", ipady=8, pady=10)
        return entry

    def reset_screen(self):
        context = self.controller.registration_context
        mode = context.get("mode")

        if mode == "manual":
            self.title_label.config(text="Register / Check In Without Card")
            self.primary_button.config(text="Continue")
            self.set_message(
                "Enter your information to register or check in without using a card."
            )
        else:
            self.title_label.config(text="Complete Registration")
            self.primary_button.config(text="Continue")
            self.set_message(
                "Review your information below to register or link a pre-registered record."
            )

    def set_message(self, text, color=ACCENT_TEXT_COLOR):
        self.message_label.config(text=text, fg=color)

    def get_primary_focus_widget(self):
        return self.name_entry

    def clear_fields(self):
        self.controller.name_var.set("")
        self.controller.student_var.set("")
        self.controller.phone_var.set("")
        self.controller.mymdc_username_var.set("")
