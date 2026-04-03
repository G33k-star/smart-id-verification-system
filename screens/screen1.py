import tkinter as tk
from cam import CameraManager


class Screen1(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="white")

        self.controller = controller
        self.camera = CameraManager()
        self.camera_active = False

        tk.Label(self, text="ID Check-In System",
                 font=("Arial", 24), fg="black", bg="white").pack(pady=20)

        self.message_label = tk.Label(self, text="Initializing...",
                                      font=("Arial", 14), fg="black", bg="white")
        self.message_label.pack(pady=20)

        self.swipe_entry = tk.Entry(self, textvariable=controller.swipe_var,
                                   font=("Arial", 16), show="*", justify="center")
        self.swipe_entry.pack(pady=20)
        self.swipe_entry.bind("<Return>", lambda e: controller.process_swipe_from_screen1())

    def reset_screen(self):
        self.set_message("Ready - Swipe ID")
        self.start_camera()

    def set_message(self, text, color="black"):
        self.message_label.config(text=text, fg=color)

    def start_camera(self):
        if not self.camera_active:
            if self.camera.start_camera():
                self.camera_active = True

    def stop_camera(self):
        self.camera.release()
