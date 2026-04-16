import tkinter as tk
from app import CheckInApp

root = tk.Tk()
root.attributes("-fullscreen", True)
root.attributes("-topmost", True)
root.configure(cursor="none")
root.bind("<Escape>", lambda e: "break")
root.bind("<Alt-Key>", lambda e: "break")
root.bind("<Control-Key>", lambda e: "break")
root.resizable(False, False)

app = CheckInApp(root)
root.mainloop()
