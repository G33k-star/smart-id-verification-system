import tkinter as tk
from app import CheckInApp, apply_kiosk_window

root = tk.Tk()
root.resizable(False, False)

app = CheckInApp(root)
apply_kiosk_window(root)
root.after(100, lambda: (apply_kiosk_window(root), app.restore_active_focus()))
root.mainloop()
