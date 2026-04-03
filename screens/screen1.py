import tkinter as tk
from cam import CameraManager


class Screen1(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="white")

        self.controller = controller
        self.camera = CameraManager()
        self.camera_active = False

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
        self.set_message("Ready - Swipe ID")
        self.controller.swipe_var.set("")
        self.focus_swipe()
        self.start_camera()

    def set_message(self, text, color="black"):
        self.message_label.config(text=text, fg=color)

    def focus_swipe(self):
        self.swipe_entry.focus_set()

    def start_camera(self):
        if not self.camera_active:
            if self.camera.start_camera():
                self.camera_active = True
            else:
                self.set_message("Camera unavailable", "red")

    def stop_camera(self):
        self.camera_active = False
        self.camera.release()
