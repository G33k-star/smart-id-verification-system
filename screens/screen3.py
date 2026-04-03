import tkinter as tk


class Screen3(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="white")

        self.controller = controller

        tk.Label(
            self,
            text="Admin Login",
            font=("Arial", 22),
            fg="black",
            bg="white"
        ).pack(pady=20)

        self.message_label = tk.Label(
            self,
            text="",
            font=("Arial", 12),
            fg="red",
            bg="white"
        )
        self.message_label.pack(pady=5)

        form_frame = tk.Frame(self, bg="white")
        form_frame.pack(pady=20)

        tk.Label(form_frame, text="Username:", fg="black", bg="white").grid(row=0, column=0, sticky="e", pady=5, padx=5)
        self.username_entry = tk.Entry(form_frame, textvariable=controller.admin_user_var, width=30)
        self.username_entry.grid(row=0, column=1, pady=5, padx=5)

        tk.Label(form_frame, text="Password:", fg="black", bg="white").grid(row=1, column=0, sticky="e", pady=5, padx=5)
        self.password_entry = tk.Entry(form_frame, textvariable=controller.admin_pass_var, width=30, show="*")
        self.password_entry.grid(row=1, column=1, pady=5, padx=5)

        button_frame = tk.Frame(self, bg="white")
        button_frame.pack(pady=20)

        tk.Button(
            button_frame,
            text="Login",
            width=15,
            command=controller.check_admin_credentials
        ).grid(row=0, column=0, padx=10)

        tk.Button(
            button_frame,
            text="Back",
            width=15,
            command=lambda: controller.show_frame("Screen1")
        ).grid(row=0, column=1, padx=10)

    def reset_screen(self):
        self.controller.admin_user_var.set("")
        self.controller.admin_pass_var.set("")
        self.set_message("")
        self.focus_username()

    def set_message(self, text):
        self.message_label.config(text=text)

    def focus_username(self):
        self.username_entry.focus_set()
