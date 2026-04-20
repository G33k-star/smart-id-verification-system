import tkinter as tk

from config import STATUS_MESSAGE_TIMEOUT_MS


class Screen1(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="white")

        self.controller = controller
        self.message_timeout_job = None

        # Title
        tk.Label(
            self,
            text="ID Check-In System",
            font=("Arial", 24),
            fg="black",
            bg="white"
        ).pack(pady=20)

        # Message
        self.message_label = tk.Label(
            self,
            text="Initializing...",
            font=("Arial", 14),
            fg="black",
            bg="white"
        )
        self.message_label.pack(pady=20)

        # Swipe Entry
        self.swipe_entry = tk.Entry(
            self,
            textvariable=controller.swipe_var,
            font=("Arial", 16),
            show="*",
            justify="center",
            width=40
        )
        self.swipe_entry.pack(pady=20)
        self.swipe_entry.bind("<Return>", lambda e: controller.process_swipe_from_screen1())

        # Terms Button
        tk.Button(
            self,
            text="Terms and Conditions",
            command=controller.open_terms_window
        ).pack(pady=10)

        # Admin Button
        tk.Button(
            self,
            text="Admin",
            command=lambda: controller.show_frame("Screen3")
        ).place(relx=0.95, rely=0.03, anchor="ne")

        # Disclaimer
        tk.Label(
            self,
            text="By scanning your ID, you agree to the terms and conditions.",
            font=("Arial", 10),
            fg="gray",
            bg="white"
        ).pack(side="bottom", pady=10)

    def reset_screen(self):
        print("[Startup] Screen1.reset_screen")
        self.controller.swipe_var.set("")
        if self.controller.ensure_camera_running():
            self.set_message("Ready - Swipe ID")
        else:
            self.set_message("Camera unavailable", "red")

    def set_message(self, text, color="black", auto_clear=False):
        self._cancel_message_timeout()
        self.message_label.config(text=text, fg=color)
        if auto_clear:
            self.message_timeout_job = self.after(
                STATUS_MESSAGE_TIMEOUT_MS,
                self.reset_status_message
            )

    def reset_status_message(self):
        self._cancel_message_timeout()
        if self.controller.is_camera_running():
            self.message_label.config(text="Ready - Swipe ID", fg="black")
        else:
            self.message_label.config(text="Camera unavailable", fg="red")

    def _cancel_message_timeout(self):
        if self.message_timeout_job is not None:
            self.after_cancel(self.message_timeout_job)
            self.message_timeout_job = None

    def get_primary_focus_widget(self):
        return self.swipe_entry
