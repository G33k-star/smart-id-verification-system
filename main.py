import traceback
import tkinter as tk

from app import CheckInApp, configure_root_window, describe_root_window


def print_root_state(root, label):
    print("[Startup] {0}: {1}".format(label, describe_root_window(root)))


def wrap_root_method(root, method_name):
    original_method = getattr(root, method_name)

    def wrapped(*args, **kwargs):
        print_root_state(root, "root.{0} called".format(method_name))
        return original_method(*args, **kwargs)

    setattr(root, method_name, wrapped)


def install_root_diagnostics(root):
    print("[Startup] Installing root diagnostics")

    for method_name in ("destroy", "withdraw", "deiconify", "iconify"):
        wrap_root_method(root, method_name)

    def on_root_event(event, sequence_name):
        print_root_state(root, "Root event {0}".format(sequence_name))

    for sequence_name in ("<Map>", "<Unmap>", "<Visibility>", "<FocusIn>", "<FocusOut>"):
        root.bind(
            sequence_name,
            lambda event, name=sequence_name: on_root_event(event, name),
            add="+"
        )

    def report_callback_exception(exc_type, exc_value, exc_traceback):
        print("[Startup] Tk callback exception caught")
        traceback.print_exception(exc_type, exc_value, exc_traceback)

    root.report_callback_exception = report_callback_exception


def startup_idle_checkpoint(root, app):
    print_root_state(root, "after_idle checkpoint")
    app.restore_active_focus()


root = tk.Tk()
print("[Startup] Tk root created")
install_root_diagnostics(root)
root.resizable(False, False)
print_root_state(root, "after root creation")

print("[Startup] App initialization starting")
app = CheckInApp(root)
print("[Startup] App initialization finished")


def on_root_close():
    print_root_state(root, "WM_DELETE_WINDOW received")
    app.safe_quit_program()


root.protocol("WM_DELETE_WINDOW", on_root_close)
configure_root_window(root)
print_root_state(root, "after configure_root_window")

root.after_idle(lambda: startup_idle_checkpoint(root, app))
root.after(250, lambda: print_root_state(root, "startup +250ms"))
root.after(1000, lambda: print_root_state(root, "startup +1000ms"))

print_root_state(root, "before root.mainloop()")
print("[Startup] Entering root.mainloop()")
root.mainloop()
print("[Startup] root.mainloop() exited")
