import tkinter as tk


class Screen4(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="white")

        self.controller = controller

        tk.Label(
            self,
            text="Admin Dashboard",
            font=("Arial", 22),
            fg="black",
            bg="white"
        ).pack(pady=20)

        tk.Button(
            self,
            text="Open Check-In Folder",
            width=25,
            height=2,
            command=controller.open_csv_folder
        ).pack(pady=10)

        tk.Button(
            self,
            text="Open Database Folder",
            width=25,
            height=2,
            command=controller.open_database_folder
        ).pack(pady=10)

        tk.Button(
            self,
            text="Back",
            width=25,
            height=2,
            command=lambda: controller.show_frame("Screen1")
        ).pack(pady=10)

        tk.Button(
            self,
            text="Quit Program",
            width=25,
            height=2,
            command=controller.safe_quit_program
        ).pack(pady=10)

    def reset_screen(self):
        pass
