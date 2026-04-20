import tkinter as tk

from config import (
    APP_BACKGROUND_COLOR,
    BUTTON_FONT,
    DETAIL_FONT,
    PANEL_BACKGROUND_COLOR,
    PANEL_BORDER_COLOR,
    PRIMARY_TEXT_COLOR,
    SCREEN_TITLE_FONT,
)


class Screen4(tk.Frame):
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
            padx=40,
            pady=34
        )
        panel.pack()

        tk.Label(
            panel,
            text="Admin Dashboard",
            font=SCREEN_TITLE_FONT,
            fg=PRIMARY_TEXT_COLOR,
            bg=PANEL_BACKGROUND_COLOR
        ).pack(pady=(0, 10))

        tk.Label(
            panel,
            text="Open folders or close the program using the controls below.",
            font=DETAIL_FONT,
            fg=PRIMARY_TEXT_COLOR,
            bg=PANEL_BACKGROUND_COLOR
        ).pack(pady=(0, 18))

        self.primary_button = None
        for text, command in (
            ("Open Check-In Folder", controller.open_checkins_folder),
            ("Open Student Data Folder", controller.open_student_data_folder),
            ("Back", lambda: controller.show_frame("Screen1")),
            ("Quit Program", controller.safe_quit_program),
        ):
            button = tk.Button(
                panel,
                text=text,
                width=26,
                height=2,
                font=BUTTON_FONT,
                command=command
            )
            button.pack(pady=8)
            if self.primary_button is None:
                self.primary_button = button

    def reset_screen(self):
        pass

    def get_primary_focus_widget(self):
        return self.primary_button
