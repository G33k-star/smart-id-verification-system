import tkinter as tk
from cam import CameraManager


class Screen1(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="black")

        self.controller = controller
        self.camera = CameraManager()
        self.camera_active = False

        # =========================
        # UI
        # =========================
        tk.Label(
            self,
            text="ID Check-In System",
            font=("Arial", 24),
            fg="white",
            bg="black"
        ).pack(pady=10)

        self.message_label = tk.Label(
            self,
            text="Initializing...",
            font=("Arial", 14),
            fg="white",
            bg="black"
        )
        self.message_label.pack(pady=20)

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

        # Admin button
        tk.Button(
            self,
            text="Admin",
            command=lambda: controller.show_frame("Screen3")
        ).place(relx=0.95, rely=0.02, anchor="ne")

        # Disclaimer
        tk.Label(
            self,
            text="By scanning your ID, you agree to the terms and conditions.",
            font=("Arial", 10),
            fg="gray",
            bg="black"
        ).pack(side="bottom", pady=10)

    # =========================
    # Lifecycle
    # =========================
    def reset_screen(self):
        self.set_message("Ready - Swipe ID", "white")
        self.controller.swipe_var.set("")
        self.focus_swipe()
        self.start_camera()

    def start_camera(self):
        if self.camera_active:
            return

        success = self.camera.start_camera()

        if not success:
            self.set_message("Camera unavailable", "red")
        else:
            self.camera_active = True
            print("[Screen1] Camera ready (event mode)")

    def stop_camera(self):
        self.camera_active = False
        self.camera.release()

    # =========================
    # UI helpers
    # =========================
    def set_message(self, text, color="white"):
        self.message_label.config(text=text, fg=color)

    def focus_swipe(self):
        self.swipe_entry.focus_set()
