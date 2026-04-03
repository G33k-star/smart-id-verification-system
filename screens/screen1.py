import tkinter as tk
from PIL import Image, ImageTk
import cv2

from cam import CameraManager


class Screen1(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="black")

        self.controller = controller
        self.camera = CameraManager(index=0)
        self.camera_active = False
        self.camera_loop_job = None

        self.title_label = tk.Label(
            self,
            text="ID Check-In System",
            font=("Arial", 24),
            fg="white",
            bg="black"
        )
        self.title_label.pack(pady=10)

        self.camera_label = tk.Label(
            self,
            bg="black",
            width=640,
            height=360
        )
        self.camera_label.pack(pady=10)

        self.message_label = tk.Label(
            self,
            text="Initializing...",
            font=("Arial", 14),
            fg="white",
            bg="black"
        )
        self.message_label.pack(pady=10)

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

        self.admin_button = tk.Button(
            self,
            text="Admin",
            width=12,
            command=lambda: self.controller.show_frame("Screen3")
        )
        self.admin_button.place(relx=0.95, rely=0.03, anchor="ne")

        self.terms_button = tk.Button(
            self,
            text="Terms and Conditions",
            width=20,
            command=self.controller.open_terms_window
        )
        self.terms_button.pack(pady=(0, 10))

        self.disclaimer_label = tk.Label(
            self,
            text="By scanning your ID, you agree to the terms and conditions.",
            font=("Arial", 10),
            fg="gray",
            bg="black"
        )
        self.disclaimer_label.pack(side="bottom", pady=10)

    def reset_screen(self):
        self.set_message("Ready - Swipe ID", "white")
        self.controller.swipe_var.set("")
        self.focus_swipe()
        self.start_camera()

    def set_message(self, text, color="white", success=False):
        self.message_label.config(text=text, fg=color)

    def focus_swipe(self):
        self.swipe_entry.focus_set()

    def show_camera_unavailable(self):
        self.camera_active = False
        self.set_message("Camera unavailable", "red")
        self.camera_label.config(image="", text="", bg="black")

        if self.camera_loop_job is not None:
            try:
                self.after_cancel(self.camera_loop_job)
            except Exception:
                pass
            self.camera_loop_job = None

    def start_camera(self):
        if self.camera_active:
            return

        success = self.camera.start_camera()
        if not success:
            self.show_camera_unavailable()
            return

        self.camera_active = True
        self._schedule_next_frame()

    def stop_camera(self):
        self.camera_active = False

        if self.camera_loop_job is not None:
            try:
                self.after_cancel(self.camera_loop_job)
            except Exception:
                pass
            self.camera_loop_job = None

        self.camera.release()

    def _schedule_next_frame(self):
        if not self.camera_active:
            self.camera_loop_job = None
            return

        self.update_camera()
        self.camera_loop_job = self.after(30, self._schedule_next_frame)

    def update_camera(self):
        frame = self.camera.get_frame()

        if frame is None:
            return

        try:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image = Image.fromarray(rgb)
            image = image.resize((640, 360))
            photo = ImageTk.PhotoImage(image=image)

            self.camera_label.config(image=photo)
            self.camera_label.image = photo
        except Exception:
            self.show_camera_unavailable()
