import tkinter as tk


class Screen2(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="white")

        self.controller = controller

        tk.Label(self, text="Add New User",
                 font=("Arial", 22), fg="black", bg="white").pack(pady=20)
