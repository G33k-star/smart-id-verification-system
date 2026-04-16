# Smart ID Verification System

Tkinter-based ID check-in app for Raspberry Pi. The system reads swipe data from a USB ID scanner, looks up students in a CSV database, captures a camera image for the check-in, and creates a signed behavioral-contract PDF for new students.

## Features

- Full-screen kiosk-style Tkinter UI
- Swipe-based student lookup
- Daily check-in CSV logs
- App-level camera ownership so capture continues across screen changes
- Best-frame capture sessions using lightweight OpenCV scoring
- New-student registration flow with in-memory enrollment capture
- Behavioral-contract PDF generation from the bundled template
- Absolute repo-root-based paths only
- Focus restoration so the swipe field is ready after startup, screen changes, and popup close

## Requirements

- Raspberry Pi OS on Raspberry Pi 3B or similar Linux system
- Python 3.9+
- USB ID card scanner that acts like a keyboard
- USB camera supported by OpenCV / V4L2

## Python Dependencies

- `opencv-python`
- `pypdf`
- `fpdf2`

Install example:

```bash
python3 -m pip install opencv-python pypdf fpdf2
```

## Run

Manual launch:

```bash
python3 main.py
```

Pi launcher script:

```bash
./start_app.sh
```

## Canonical Project Storage

Static app assets:

```text
assets/contracts/Robotics Lab Behavioral Contract 2026.pdf
assets/text/terms_and_conditions.txt
```

Generated runtime data:

```text
data/students/database.csv
data/checkins/checkin_YYYY-MM-DD.csv
data/photos/checkins/YYYY-MM-DD/<name>_<time>.jpg
data/contracts/signed/<name>-<student_id>-signed_contract.pdf
```

Legacy compatibility:

- The app still reads the old database from `database_folder/database.csv` if the canonical file does not exist yet.
- The app still reads old daily check-in files from `checkin_logs/` for duplicate detection.
- The app still reads terms text from `terms_and_conditions.txt` if the canonical asset file has not been moved yet.
- The contract template is read from `database_folder/behavioral contract/...` as a fallback if it has not been moved into `assets/contracts/` yet.
- New writes go only to the canonical `assets/` and `data/` layout.

## Runtime Flow

Known student:

1. Swipe ID.
2. Look up the card in `data/students/database.csv`.
3. Run a short capture session for about 1.2 seconds.
4. Sample frames every 0.2 seconds.
5. Score each candidate using lightweight OpenCV heuristics.
6. Save only the best final image to `data/photos/checkins/...`.
7. Append the check-in row to the daily CSV.

New student:

1. Swipe ID.
2. Start an enrollment capture session before showing the registration form.
3. Keep the best candidate in memory while the form is open.
4. If registration is canceled, discard the session.
5. If registration completes, save the best candidate using the normal photo naming convention.
6. Create or append the student database record.
7. Generate the signed behavioral-contract PDF.
8. Append the daily check-in row.

## Capture Scoring

The capture session uses only lightweight OpenCV operations:

- downscaled grayscale scoring frames
- Haar-cascade face detection when available
- preference for one dominant face
- centered face preference
- size and edge-clipping checks
- sharpness via Laplacian variance
- brightness check
- contrast fallback when face detection is weak or unavailable

If the capture session does not find an acceptable best candidate, the app falls back to the original immediate single-frame save.

## Main Files

- `main.py` - Tkinter startup
- `app.py` - main controller, screen navigation, focus restoration, check-in flow
- `cam.py` - low-level camera access and image saving
- `capture_session.py` - best-frame scoring and capture-session management
- `data_service.py` - database lookup and CSV writes
- `file_setup.py` - canonical path setup and file creation helpers
- `contract_service.py` - behavioral-contract PDF generation
- `screens/` - Tkinter screens

## Notes

- The app keeps the cursor visible.
- The app does not hard-lock keyboard shortcuts.
- The camera is released on quit.
