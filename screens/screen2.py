import tkinter as tk


class Screen2(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="white")

        self.controller = controller

        # =========================
        # Title
        # =========================
        tk.Label(
            self,
            text="Add New User",
            font=("Arial", 22),
            bg="white"
        ).pack(pady=10)

        # =========================
        # Message (top feedback)
        # =========================
        self.message_label = tk.Label(
            self,
            text="",
            font=("Arial", 14),
            fg="black",
            bg="white"
        )
        self.message_label.pack(pady=5)

        # =========================
        # Status (processing / errors)
        # =========================
        self.status_label = tk.Label(
            self,
            text="",
            font=("Arial", 12),
            fg="blue",
            bg="white"
        )
        self.status_label.pack(pady=5)

        # =========================
        # Input Fields
        # =========================
        form_frame = tk.Frame(self, bg="white")
        form_frame.pack(pady=10)

        # Student ID
        tk.Label(form_frame, text="Student ID:", bg="white").grid(row=0, column=0, sticky="e", pady=5)
        tk.Entry(form_frame, textvariable=controller.student_var, width=30).grid(row=0, column=1, pady=5)

        # Phone
        tk.Label(form_frame, text="Phone Number:", bg="white").grid(row=1, column=0, sticky="e", pady=5)
        tk.Entry(form_frame, textvariable=controller.phone_var, width=30).grid(row=1, column=1, pady=5)

        # myMDC username
        tk.Label(form_frame, text="myMDC Username:", bg="white").grid(row=2, column=0, sticky="e", pady=5)
        tk.Entry(form_frame, textvariable=controller.mymdc_username_var, width=30).grid(row=2, column=1, pady=5)

        # Email (auto-filled)
        tk.Label(form_frame, text="Email:", bg="white").grid(row=3, column=0, sticky="e", pady=5)
        tk.Entry(form_frame, textvariable=controller.email_var, width=30, state="readonly").grid(row=3, column=1, pady=5)

        # =========================
        # Buttons
        # =========================
        button_frame = tk.Frame(self, bg="white")
        button_frame.pack(pady=15)

        tk.Button(
            button_frame,
            text="Add User",
            width=15,
            command=controller.add_user_and_check_in
        ).grid(row=0, column=0, padx=10)

        tk.Button(
            button_frame,
            text="Cancel",
            width=15,
            command=lambda: controller.show_frame("Screen1")
        ).grid(row=0, column=1, padx=10)

    # =========================
    # REQUIRED METHODS (for app.py)
    # =========================
    def reset_screen(self):
        self.clear_fields()
        self.set_message("User not recognized. Add new user?", "black")
        self.clear_status()

    def set_message(self, text, color="black"):
        self.message_label.config(text=text, fg=color)

    def set_status(self, text, color="blue"):
        self.status_label.config(text=text, fg=color)

    def clear_status(self):
        self.status_label.config(text="")

    def clear_fields(self):
        self.controller.student_var.set("")
        self.controller.phone_var.set("")
        self.controller.mymdc_username_var.set("")
        self.controller.email_var.set("")
