import tkinter as tk


class Screen5(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="white")

        self.controller = controller

        tk.Label(
            self,
            text="Confirm Card Link",
            font=("Arial", 22),
            fg="black",
            bg="white"
        ).pack(pady=20)

        self.message_label = tk.Label(
            self,
            text="",
            font=("Arial", 14),
            fg="black",
            bg="white",
            wraplength=760,
            justify="center"
        )
        self.message_label.pack(pady=10)

        self.details_label = tk.Label(
            self,
            text="",
            font=("Arial", 12),
            fg="black",
            bg="white",
            wraplength=760,
            justify="left"
        )
        self.details_label.pack(pady=10)

        btn_frame = tk.Frame(self, bg="white")
        btn_frame.pack(pady=20)

        tk.Button(
            btn_frame,
            text="Link Card",
            width=16,
            command=controller.confirm_card_link
        ).grid(row=0, column=0, padx=10)

        tk.Button(
            btn_frame,
            text="Back to Edit",
            width=16,
            command=controller.back_to_registration_from_link
        ).grid(row=0, column=1, padx=10)

        tk.Button(
            btn_frame,
            text="Cancel",
            width=16,
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
            text="We found an existing pre-registered record that matches the entered Student ID and myMDC username. Link this card to that record and use the confirmed card name as the stored canonical name?",
            fg="black"
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
        return None
