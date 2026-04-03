import tkinter as tk
from PIL import Image, ImageTk
import cv2

from cam import CameraManager


class Screen1(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)

        self.controller = controller

        # =========================
        # Camera Setup
        # =========================
        self.camera = CameraManager()
        self.camera_active = False

        # =========================
        # UI Layout
        # =========================
        self.configure(bg="black")

        self.title_label = tk.Label(
            self,
            text="ID Check-In System",
            font=("Arial", 24),
            fg="white",
            bg="black"
        )
        self.title_label.pack(pady=10)

        self.camera_label = tk.Label(self, bg="black")
        self.camera_label.pack(pady=10)

        self.status_label = tk.Label(
            self,
            text="Initializing...",
            font=("Arial", 14),
            fg="white",
            bg="black"
        )
        self.status_label.pack(pady=10)

        self.swipe_entry = tk.Entry(
            self,
            font=("Arial", 16),
            show="*",
            justify="center"
        )
        self.swipe_entry.pack(pady=20)
        self.swipe_entry.focus_set()

        self.swipe_entry.bind("<Return>", self.process_swipe)

        self.admin_button = tk.Button(
            self,
            text="Admin",
            command=lambda: controller.show_frame("Screen3")
        )
        self.admin_button.place(relx=0.95, rely=0.02, anchor="ne")

        self.disclaimer = tk.Label(
            self,
            text="By scanning your ID, you agree to the terms and conditions.",
            font=("Arial", 10),
            fg="gray",
            bg="black"
        )
        self.disclaimer.pack(side="bottom", pady=10)

        # Start camera
        self.init_camera()

    # =========================
    # REQUIRED METHOD (FIX)
    # =========================
    def reset_screen(self):
        print("[Screen1] Resetting screen")
    
        # Reset UI only
        self.status_label.config(text="Ready - Swipe ID", fg="white")
        self.swipe_entry.delete(0, tk.END)
    
        # DO NOT restart camera here
        # The camera is already running

    # =========================
    # Camera Initialization
    # =========================
    def init_camera(self):
        success = self.camera.start_camera()

        if not success:
            self.show_camera_unavailable()
        else:
            self.camera_active = True
            self.status_label.config(text="Ready - Swipe ID")
            self.update_camera()

    # =========================
    # Camera Loop
    # =========================
    def update_camera(self):
        if not self.camera_active:
            return
    
        frame = self.camera.get_frame()
    
        if frame is not None:
            # render frame
            ...
    
        # ALWAYS continue loop
        self.after(30, self.update_camera)

    # =========================
    # Camera Failure UI
    # =========================
    def show_camera_unavailable(self):
        self.camera_active = False

        self.status_label.config(
            text="Camera unavailable",
            fg="red"
        )

        print("[Screen1] Camera unavailable")

    # =========================
    # Swipe Handling
    # =========================
    def process_swipe(self, event=None):
        data = self.swipe_entry.get().strip()

        if not data:
            return

        print(f"[Screen1] Swipe received: {data}")

        self.swipe_entry.delete(0, tk.END)
        self.status_label.config(text="Processing...")

        # Placeholder logic
        self.after(500, lambda: self.status_label.config(text="Check-in successful"))

    # =========================
    # Cleanup (optional)
    # =========================
    def on_hide(self):
        self.camera_active = False
        self.camera.release()
