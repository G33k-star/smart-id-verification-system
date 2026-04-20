import tkinter as tk


class Screen2(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="white")

        self.controller = controller

        self.title_label = tk.Label(
            self,
            text="Registration",
            font=("Arial", 22),
            fg="black",
            bg="white"
        )
        self.title_label.pack(pady=15)

        self.message_label = tk.Label(
            self,
            text="",
            font=("Arial", 14),
            fg="black",
            bg="white",
            wraplength=760,
            justify="center"
        )
        self.message_label.pack(pady=5)

        form = tk.Frame(self, bg="white")
        form.pack(pady=15)

        tk.Label(form, text="Full Name:", bg="white", fg="black").grid(row=0, column=0, pady=5, sticky="e")
        self.name_entry = tk.Entry(form, textvariable=controller.name_var, width=30)
        self.name_entry.grid(row=0, column=1, pady=5)

        tk.Label(form, text="Student ID:", bg="white", fg="black").grid(row=1, column=0, pady=5, sticky="e")
        self.student_entry = tk.Entry(form, textvariable=controller.student_var, width=30)
        self.student_entry.grid(row=1, column=1, pady=5)

        tk.Label(form, text="Phone Number:", bg="white", fg="black").grid(row=2, column=0, pady=5, sticky="e")
        tk.Entry(form, textvariable=controller.phone_var, width=30).grid(row=2, column=1, pady=5)

        tk.Label(form, text="myMDC Username:", bg="white", fg="black").grid(row=3, column=0, pady=5, sticky="e")
        tk.Entry(form, textvariable=controller.mymdc_username_var, width=30).grid(row=3, column=1, pady=5)
        tk.Label(
            form,
            text="Example: john.smith001",
            bg="white",
            fg="gray"
        ).grid(row=4, column=1, sticky="w")

        btn_frame = tk.Frame(self, bg="white")
        btn_frame.pack(pady=20)

        self.primary_button = tk.Button(
            btn_frame,
            text="Continue",
            width=18,
            command=controller.submit_registration_form
        )
        self.primary_button.grid(row=0, column=0, padx=10)

        tk.Button(
            btn_frame,
            text="Cancel",
            width=18,
            command=controller.cancel_new_user_flow
        ).grid(row=0, column=1, padx=10)

    def reset_screen(self):
        context = self.controller.registration_context
        mode = context.get("mode")

        if mode == "manual":
            self.title_label.config(text="Register / Check In Without Card")
            self.primary_button.config(text="Continue")
            self.set_message(
                "Use your Student ID and myMDC username to register or check in without a card."
            )
        else:
            self.title_label.config(text="Complete Registration")
            self.primary_button.config(text="Continue")
            self.set_message(
                "Card not recognized yet. Review your information to register or link a pre-registered record."
            )

    def set_message(self, text, color="black"):
        self.message_label.config(text=text, fg=color)

    def get_primary_focus_widget(self):
        return self.name_entry

    def clear_fields(self):
        self.controller.name_var.set("")
        self.controller.student_var.set("")
        self.controller.phone_var.set("")
        self.controller.mymdc_username_var.set("")
