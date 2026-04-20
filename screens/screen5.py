import tkinter as tk

from config import (
    ACCENT_TEXT_COLOR,
    APP_BACKGROUND_COLOR,
    BUTTON_FONT,
    DETAIL_FONT,
    PANEL_BACKGROUND_COLOR,
    PANEL_BORDER_COLOR,
    PRIMARY_TEXT_COLOR,
    SCREEN_TITLE_FONT,
)


class Screen5(tk.Frame):
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
            text="Confirm Card Link",
            font=SCREEN_TITLE_FONT,
            fg=PRIMARY_TEXT_COLOR,
            bg=PANEL_BACKGROUND_COLOR
        ).pack(pady=(0, 12))

        self.message_label = tk.Label(
            panel,
            text="",
            font=DETAIL_FONT,
            fg=ACCENT_TEXT_COLOR,
            bg=PANEL_BACKGROUND_COLOR,
            wraplength=760,
            justify="center"
        )
        self.message_label.pack(pady=(0, 16))

        self.details_label = tk.Label(
            panel,
            text="",
            font=DETAIL_FONT,
            fg=PRIMARY_TEXT_COLOR,
            bg=PANEL_BACKGROUND_COLOR,
            wraplength=760,
            justify="left"
        )
        self.details_label.pack(pady=(0, 22))

        btn_frame = tk.Frame(panel, bg=PANEL_BACKGROUND_COLOR)
        btn_frame.pack()

        self.link_button = tk.Button(
            btn_frame,
            text="Link Card",
            width=14,
            height=2,
            font=BUTTON_FONT,
            command=controller.confirm_card_link
        )
        self.link_button.grid(row=0, column=0, padx=10)

        tk.Button(
            btn_frame,
            text="Back to Edit",
            width=14,
            height=2,
            font=BUTTON_FONT,
            command=controller.back_to_registration_from_link
        ).grid(row=0, column=1, padx=10)

        tk.Button(
            btn_frame,
            text="Cancel",
            width=14,
            height=2,
            font=BUTTON_FONT,
            command=controller.cancel_new_user_flow
        ).grid(row=0, column=2, padx=10)

    def reset_screen(self):
        candidate = self.controller.pending_link_candidate
        submitted = self.controller.pending_link_form or {}

        if not candidate:
            self.message_label.config(
                text="No pre-registered record is ready to link.",
                fg="red"
            )
            self.details_label.config(text="")
            return

        self.message_label.config(
            text="We found a matching pre-registered record. Confirm the card link and stored name below.",
            fg=ACCENT_TEXT_COLOR
        )

        details = [
            "Existing record: {0}".format(candidate.get("Name", "")),
            "Student ID: {0}".format(candidate.get("Student ID", "")),
            "myMDC Username: {0}".format(candidate.get("myMDC Username", "")),
        ]

        swipe_name = submitted.get("swipe_name")
        if swipe_name:
            details.append("Card name read as: {0}".format(swipe_name))
            details.append("Stored name after link: {0}".format(swipe_name))

        self.details_label.config(text="\n".join(details))

    def get_primary_focus_widget(self):
        return self.link_button
