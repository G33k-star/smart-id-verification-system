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

        # Title
        self.title_label = tk.Label(
            self,
            text="ID Check-In System",
            font=("Arial", 24),
            fg="white",
            bg="black"
        )
        self.title_label.pack(pady=10)

        # Camera display
        self.camera_label = tk.Label(self, bg="black")
        self.camera_label.pack(pady=10)

        # Status label
        self.status_label = tk.Label(
            self,
            text="Initializing...",
            font=("Arial", 14),
            fg="white",
            bg="black"
        )
        self.status_label.pack(pady=10)

        # Swipe input (hidden characters)
        self.swipe_entry = tk.Entry(
            self,
            font=("Arial", 16),
            show="*",
            justify="center"
        )
        self.swipe_entry.pack(pady=20)
        self.swipe_entry.focus_set()

        self.swipe_entry.bind("<Return>", self.process_swipe)

        # Admin button
        self.admin_button = tk.Button(
            self,
            text="Admin",
            command=lambda: controller.show_frame("Screen3")
        )
        self.admin_button.place(relx=0.95, rely=0.02, anchor="ne")

        # Disclaimer
        self.disclaimer = tk.Label(
            self,
            text="By scanning your ID, you agree to the terms and conditions.",
            font=("Arial", 10),
            fg="gray",
            bg="black"
        )
        self.disclaimer.pack(side="bottom", pady=10)

        # =========================
        # Start Camera
        # =========================
        self.init_camera()

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
            # Convert OpenCV → Tkinter
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image = Image.fromarray(frame)
            image = image.resize((500, 350))

            photo = ImageTk.PhotoImage(image=image)

            self.camera_label.config(image=photo)
            self.camera_label.image = photo  # prevent garbage collection

        # Continue loop (DO NOT STOP on frame failure)
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

        # Clear input immediately
        self.swipe_entry.delete(0, tk.END)

        # TODO: connect to your validator + database logic
        self.status_label.config(text="Processing...")

        # Simulated success (replace with real logic)
        self.after(500, lambda: self.status_label.config(text="Check-in successful"))

    # =========================
    # Cleanup
    # =========================
    def on_hide(self):
        """
        Call this when switching away from Screen1
        """
        self.camera_active = False
        self.camera.release()
