import tkinter as tk


class Screen2(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="white")

        self.controller = controller

        # Title
        tk.Label(
            self,
            text="Add New User",
            font=("Arial", 22),
            fg="black",
            bg="white"
        ).pack(pady=15)

        # Message
        self.message_label = tk.Label(
            self,
            text="",
            font=("Arial", 14),
            fg="black",
            bg="white"
        )
        self.message_label.pack(pady=5)

        # Form
        form = tk.Frame(self, bg="white")
        form.pack(pady=15)

        tk.Label(form, text="Student ID:", bg="white", fg="black").grid(row=0, column=0, pady=5, sticky="e")
        self.student_entry = tk.Entry(form, textvariable=controller.student_var, width=30)
        self.student_entry.grid(row=0, column=1, pady=5)

        tk.Label(form, text="Phone Number:", bg="white", fg="black").grid(row=1, column=0, pady=5, sticky="e")
        tk.Entry(form, textvariable=controller.phone_var, width=30).grid(row=1, column=1, pady=5)

        tk.Label(form, text="myMDC Username:", bg="white", fg="black").grid(row=2, column=0, pady=5, sticky="e")
        tk.Entry(form, textvariable=controller.mymdc_username_var, width=30).grid(row=2, column=1, pady=5)
        tk.Label(
            form,
            text="Example: john.smith001",
            bg="white",
            fg="gray"
        ).grid(row=3, column=1, sticky="w")

        # Buttons
        btn_frame = tk.Frame(self, bg="white")
        btn_frame.pack(pady=20)

        tk.Button(btn_frame, text="Add User", width=15,
                  command=controller.add_user_and_check_in).grid(row=0, column=0, padx=10)

        tk.Button(btn_frame, text="Cancel", width=15,
                  command=controller.cancel_new_user_flow).grid(row=0, column=1, padx=10)

    def reset_screen(self):
        self.clear_fields()
        self.set_message("User not recognized. Add new user?")

    def set_message(self, text, color="black"):
        self.message_label.config(text=text, fg=color)

    def get_primary_focus_widget(self):
        return self.student_entry

    def clear_fields(self):
        self.controller.student_var.set("")
        self.controller.phone_var.set("")
        self.controller.mymdc_username_var.set("")
