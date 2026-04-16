import tkinter as tk
from app import CheckInApp, apply_kiosk_window

root = tk.Tk()
root.bind("<Escape>", lambda e: "break")
root.bind("<Alt-Key>", lambda e: "break")
root.bind("<Control-Key>", lambda e: "break")
root.resizable(False, False)

app = CheckInApp(root)
apply_kiosk_window(root)
root.after(100, lambda: apply_kiosk_window(root))
root.mainloop()
