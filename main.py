import logging
import tkinter as tk

from app import CheckInApp, configure_root_window


LOGGER = logging.getLogger(__name__)


def install_tk_error_logging(root):
    def report_callback_exception(exc_type, exc_value, exc_traceback):
        LOGGER.error(
            "Tk callback exception",
            exc_info=(exc_type, exc_value, exc_traceback)
        )

    root.report_callback_exception = report_callback_exception


def main():
    logging.basicConfig(
        level=logging.WARNING,
        format="%(levelname)s %(name)s: %(message)s"
    )

    root = tk.Tk()
    install_tk_error_logging(root)

    app = CheckInApp(root)
    root.protocol("WM_DELETE_WINDOW", app.safe_quit_program)

    configure_root_window(root)
    root.after_idle(app.restore_active_focus)
    root.mainloop()


if __name__ == "__main__":
    main()
