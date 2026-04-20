# Smart ID Verification System

Tkinter-based ID check-in app for Raspberry Pi. The system reads swipe data from a USB ID scanner, looks up students in the local CSV database, captures a camera image for the check-in, and creates a signed behavioral-contract PDF for new students.

## Features

- Stable Tkinter root window sized to the display
- Swipe-based student lookup
- Canonical `assets/` and `data/` storage layout
- Daily check-in CSV logs under `data/checkins/`
- App-level camera ownership so capture continues across screen changes
- Event-driven photo capture with rolling frame buffer
- Face-prioritized frame selection using lightweight OpenCV scoring
- New-student registration flow with event-triggered enrollment capture
- Behavioral-contract PDF generation from the bundled template
- Focus restoration so the swipe field is ready after startup, screen changes, and popup close

## Requirements

- Raspberry Pi OS on Raspberry Pi 3B or similar Linux system
- Python 3.9+
- USB ID card scanner that acts like a keyboard
- USB camera supported by OpenCV / V4L2

## Install

```bash
python3 -m pip install -r requirements.txt
```

## Run

App startup:

```bash
python3 main.py
```

Pi launcher script:

```bash
./start_app.sh
```

## Project Layout

Tracked app assets:

```text
assets/contracts/Robotics Lab Behavioral Contract 2026.pdf
assets/text/terms_and_conditions.txt
care_package/
screens/
app.py
cam.py
capture_session.py
config.py
contract_service.py
data_service.py
file_setup.py
main.py
validators.py
```

Runtime data created on startup and during use:

```text
data/students/database.csv
data/checkins/checkin_YYYY-MM-DD.csv
data/photos/checkins/YYYY-MM-DD/<name>_<time>.jpg
data/contracts/signed/<name>-<student_id>-signed_contract.pdf
```

The `data/` tree is runtime-only and is ignored by git. On first app start, the app creates the required directories and an empty `data/students/database.csv` if it does not exist yet.

## Runtime Flow

Known student:

1. Swipe ID.
2. Look up the card in `data/students/database.csv`.
3. Treat the swipe as a capture event.
4. Score buffered frames from a short window around the swipe, with stronger preference for frames slightly after the swipe.
5. Prefer a single clear face that is large enough, near center, and not edge-clipped, then choose the best candidate from that event window.
6. Save only the best final image to `data/photos/checkins/...`.
7. Append the check-in row to the daily CSV.

New student:

1. Swipe ID.
2. Treat the swipe as the enrollment capture event before showing the registration form.
3. Keep the best event-window candidate in memory while the form is open.
4. If registration is canceled, discard the pending capture.
5. If registration completes, save the best event-window candidate using the normal photo naming convention.
6. Create or append the student database record.
7. Generate the signed behavioral-contract PDF.
8. Append the daily check-in row.

## Capture Scoring

The capture pipeline uses only lightweight OpenCV operations:

- continuous camera stream with sampled rolling buffer
- downscaled grayscale scoring frames
- Haar-cascade face detection on sampled frames only
- strong preference for one clear centered face in the event window
- centered face preference
- minimum face-size and edge-clipping checks
- sharpness via Laplacian variance
- brightness range scoring
- post-scan timing bias so early pre-swipe frames rank lower
- general-image fallback using sharpness, brightness, and centered detail

## Capture Tuning

Capture tuning lives in `config.py`:

- `BUFFER_DURATION_SEC`
- `PRE_EVENT_WINDOW_SEC`
- `POST_EVENT_WINDOW_SEC`
- `FRAME_SAMPLE_INTERVAL_MS`
- `FACE_DETECT_SCALE`
- `MIN_FACE_SIZE_RATIO`
- `CENTER_TOLERANCE_RATIO`
- `BLUR_THRESHOLD`
- `BRIGHTNESS_MIN`
- `BRIGHTNESS_MAX`
- `MAX_BUFFER_FRAMES`
- `DEBUG_SAVE_FRAMES`

If the event window does not produce a candidate, the app falls back to the original immediate single-frame save.

## Main Files

- `main.py` - Tkinter startup
- `app.py` - main controller, screen navigation, focus restoration, check-in flow
- `cam.py` - low-level camera access and image saving
- `capture_session.py` - rolling buffer, event-window selection, and best-frame scoring
- `data_service.py` - database lookup and CSV writes
- `config.py` - canonical paths and capture tuning constants
- `file_setup.py` - canonical path setup and file creation helpers
- `contract_service.py` - behavioral-contract PDF generation
- `screens/` - Tkinter screens

## Notes

- The app keeps the cursor visible.
- Startup uses a plain Tk root window on X11/Linux and avoids `withdraw()` / `deiconify()` / `overrideredirect()` remap tricks.
- The app does not hard-lock keyboard shortcuts.
- The camera is released on quit.
