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
)


class Screen3(tk.Frame):
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
            padx=38,
            pady=32
        )
        panel.pack()

        tk.Label(
            panel,
            text="Admin Login",
            font=SCREEN_TITLE_FONT,
            fg=PRIMARY_TEXT_COLOR,
            bg=PANEL_BACKGROUND_COLOR
        ).pack(pady=(0, 10))

        self.message_label = tk.Label(
            panel,
            text="",
            font=DETAIL_FONT,
            fg="red",
            bg=PANEL_BACKGROUND_COLOR,
            wraplength=520,
            justify="center"
        )
        self.message_label.pack(pady=(0, 16))

        form = tk.Frame(panel, bg=PANEL_BACKGROUND_COLOR)
        form.pack(pady=(0, 22))

        tk.Label(
            form,
            text="Username",
            font=BODY_FONT,
            fg=PRIMARY_TEXT_COLOR,
            bg=PANEL_BACKGROUND_COLOR
        ).grid(row=0, column=0, sticky="e", padx=(0, 16), pady=10)
        self.username_entry = tk.Entry(
            form,
            textvariable=controller.admin_user_var,
            width=24,
            font=INPUT_FONT,
            bg=INPUT_BACKGROUND_COLOR,
            fg=PRIMARY_TEXT_COLOR,
            relief="solid",
            bd=1,
            insertwidth=3
        )
        self.username_entry.grid(row=0, column=1, ipady=8, pady=10)

        tk.Label(
            form,
            text="Password",
            font=BODY_FONT,
            fg=PRIMARY_TEXT_COLOR,
            bg=PANEL_BACKGROUND_COLOR
        ).grid(row=1, column=0, sticky="e", padx=(0, 16), pady=10)
        tk.Entry(
            form,
            textvariable=controller.admin_pass_var,
            show="*",
            width=24,
            font=INPUT_FONT,
            bg=INPUT_BACKGROUND_COLOR,
            fg=PRIMARY_TEXT_COLOR,
            relief="solid",
            bd=1,
            insertwidth=3
        ).grid(row=1, column=1, ipady=8, pady=10)

        btn_frame = tk.Frame(panel, bg=PANEL_BACKGROUND_COLOR)
        btn_frame.pack()

        tk.Button(
            btn_frame,
            text="Login",
            font=BUTTON_FONT,
            width=14,
            height=2,
            command=controller.check_admin_credentials
        ).grid(row=0, column=0, padx=10)

        tk.Button(
            btn_frame,
            text="Back",
            font=BUTTON_FONT,
            width=14,
            height=2,
            command=lambda: controller.show_frame("Screen1")
        ).grid(row=0, column=1, padx=10)

    def reset_screen(self):
        self.controller.admin_user_var.set("")
        self.controller.admin_pass_var.set("")
        self.set_message("")

    def set_message(self, text):
        self.message_label.config(text=text)

    def get_primary_focus_widget(self):
        return self.username_entry
