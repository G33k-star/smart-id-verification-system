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

        form = tk.Frame(self, bg="white")
        form.pack(pady=20)

        tk.Label(form, text="Username:", bg="white", fg="black").grid(row=0, column=0, pady=5, sticky="e")
        self.username_entry = tk.Entry(form, textvariable=controller.admin_user_var, width=30)
        self.username_entry.grid(row=0, column=1, pady=5)

        tk.Label(form, text="Password:", bg="white", fg="black").grid(row=1, column=0, pady=5, sticky="e")
        tk.Entry(form, textvariable=controller.admin_pass_var, show="*", width=30).grid(row=1, column=1, pady=5)

        btn_frame = tk.Frame(self, bg="white")
        btn_frame.pack(pady=20)

        tk.Button(btn_frame, text="Login", width=15,
                  command=controller.check_admin_credentials).grid(row=0, column=0, padx=10)

        tk.Button(btn_frame, text="Back", width=15,
                  command=lambda: controller.show_frame("Screen1")).grid(row=0, column=1, padx=10)

    def reset_screen(self):
        self.controller.admin_user_var.set("")
        self.controller.admin_pass_var.set("")
        self.set_message("")

    def set_message(self, text):
        self.message_label.config(text=text)

    def get_primary_focus_widget(self):
        return self.username_entry
