import tkinter as tk
from cam import CameraManager


class Screen1(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="white")

        self.controller = controller
        self.camera = CameraManager(index=0)
        self.camera_active = False

        self.title_label = tk.Label(
            self,
            text="ID Check-In System",
            font=("Arial", 24),
            fg="black",
            bg="white"
        )
        self.title_label.pack(pady=20)

        self.message_label = tk.Label(
            self,
            text="Initializing...",
            font=("Arial", 14),
            fg="black",
            bg="white"
        )
        self.message_label.pack(pady=20)

        self.swipe_entry = tk.Entry(
            self,
            textvariable=self.controller.swipe_var,
            font=("Arial", 16),
            show="*",
            justify="center",
            width=40
        )
        self.swipe_entry.pack(pady=20)
        self.swipe_entry.bind("<Return>", lambda event: self.controller.process_swipe_from_screen1())

        self.terms_button = tk.Button(
            self,
            text="Terms and Conditions",
            width=20,
            command=self.controller.open_terms_window
        )
        self.terms_button.pack(pady=10)

        self.admin_button = tk.Button(
            self,
            text="Admin",
            width=12,
            command=lambda: self.controller.show_frame("Screen3")
        )
        self.admin_button.place(relx=0.95, rely=0.03, anchor="ne")

        self.disclaimer_label = tk.Label(
            self,
            text="By scanning your ID, you agree to the terms and conditions.",
            font=("Arial", 10),
            fg="gray",
            bg="white"
        )
        self.disclaimer_label.pack(side="bottom", pady=10)

    def reset_screen(self):
        self.set_message("Ready - Swipe ID", "black")
        self.controller.swipe_var.set("")
        self.focus_swipe()
        self.start_camera()

    def set_message(self, text, color="black"):
        self.message_label.config(text=text, fg=color)

    def focus_swipe(self):
        self.swipe_entry.focus_set()

    def start_camera(self):
        if self.camera_active:
            return

        success = self.camera.start_camera()
        if not success:
            self.set_message("Camera unavailable.", "red")
            return

        self.camera_active = True
        print("[Screen1] Camera ready")

    def stop_camera(self):
        self.camera_active = False
        self.camera.release()
