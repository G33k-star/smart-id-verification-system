# Smart ID Verification System

Tkinter-based ID check-in app for Raspberry Pi. The system reads swipe data from a USB ID scanner, supports a no-card registration/check-in path, looks up students in the local CSV database, captures a camera image for the check-in, and creates a signed behavioral-contract PDF for student onboarding.

## Features

- Stable Tkinter root window sized to the display
- Swipe-based student lookup
- Manual registration / check-in path using Student ID and myMDC username
- First-card linking confirmation for pre-registered students
- Canonical `assets/` and `data/` storage layout
- Daily check-in CSV logs under `data/checkins/`
- App-level camera ownership so capture continues across screen changes
- Automatic camera discovery across configurable indices
- Background camera reconnect if no camera is present at startup or a camera is unplugged later
- Event-driven photo capture with rolling frame buffer
- Face-prioritized frame selection using lightweight OpenCV scoring
- New-student registration flow with event-triggered enrollment capture
- Behavioral-contract PDF generation from the read-only master contract template
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
backup_data.sh
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
data/photos/checkins/YYYY-MM-DD/<name>-<student_id>_<time>.jpg
data/contracts/signed/<name>-<student_id>-signed_contract.pdf
```

The `data/` tree is runtime-only and is ignored by git. On first app start, the app creates the required directories and an empty `data/students/database.csv` if it does not exist yet.
The master behavioral-contract template lives at `assets/contracts/Robotics Lab Behavioral Contract 2026.pdf` and is treated as read-only input. The app only writes per-student signed copies under `data/contracts/signed/`.

## Data Backup

The repo includes `backup_data.sh` for simple Git-based cloud backups of the `data/` folder only. The script:

- runs from the repo root
- force-stages only `data/`
- does nothing if `data/` has no changes
- commits backup changes with a UTC timestamp
- pushes to `origin/main`
- refuses to run if unrelated staged changes already exist outside `data/`

Make it executable on the Pi:

```bash
chmod +x backup_data.sh
```

Example cron setup for an hourly backup:

```bash
crontab -e
```

Add:

```cron
0 * * * * cd /home/pi/smart-id-verification-system && ./backup_data.sh >> /home/pi/smart-id-backup.log 2>&1
```

## Runtime Flow

Known student:

1. Swipe ID.
2. Look up the card in `data/students/database.csv`.
3. Treat the swipe as a capture event.
4. Score buffered frames from a short window around the swipe, with stronger preference for frames slightly after the swipe.
5. Prefer a single clear face that is large enough, near center, and not edge-clipped, then choose the best candidate from that event window.
6. Save only the best final image to `data/photos/checkins/...`, and skip duplicate photo saves if the same student already has one for that day.
7. Append the check-in row to the daily CSV.

Swipe-based new student:

1. Swipe ID.
2. Treat the swipe as the enrollment capture event before showing the registration form.
3. If the user later enters a Student ID + myMDC username that matches a pre-registered record with no card linked yet, the app shows a confirmation step before linking the swiped card.
4. When that first-card link is confirmed, the cleaned Track 1 card name becomes the canonical stored name for the student, and existing canonical student files are renamed where safe.
5. Keep the best event-window candidate in memory while the form is open.
6. If registration is canceled, discard the pending capture.
7. If registration completes, save the best event-window candidate using the normal photo naming convention.
8. Create or append the student database record.
9. Generate the signed behavioral-contract PDF only if one does not already exist for that student.
10. Append the daily check-in row.

No-card registration / check-in:

1. Use the main-screen no-card option.
2. Enter full name, Student ID, phone number, and myMDC username.
3. If Student ID + myMDC username already match an existing student record, the app uses that canonical record for check-in.
4. If no record exists, the app creates a pre-registered student record with no card linked yet.
5. The app captures the check-in photo, generates the signed behavioral-contract PDF if needed, and writes the daily check-in row.

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
- `CAMERA_INDEX_MIN`
- `CAMERA_INDEX_MAX`
- `CAMERA_DISCOVERY_RETRY_SEC`
- `CAMERA_PROBE_WARMUP_SEC`
- `CAMERA_PROBE_ATTEMPTS`
- `CAMERA_PROBE_READ_INTERVAL_SEC`
- `CAMERA_READ_FAILURE_LIMIT`

If the event window does not produce a candidate, the app falls back to the original immediate single-frame save.

## Main Files

- `main.py` - Tkinter startup
- `app.py` - main controller, screen navigation, focus restoration, check-in flow
- `screens/screen5.py` - first-card link confirmation screen
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
- Cardholder names are parsed from Track 1 only and normalized to canonical `First Middle Last` form for saved outputs.
- On confirmed first-card link, the cleaned Track 1 card name replaces the pre-registered name as the canonical stored student name.
- The blank master contract template is never rewritten by the app.
- Main-screen success/error messages auto-reset after a short timeout.
- The main screen stays silent when the camera is healthy and only shows camera messages when the camera is unavailable or capture fails.
- The camera is released on quit.
- If no USB camera is available at startup, the app stays open and keeps retrying in the background until a working camera appears.
- If the active camera is unplugged or stops producing frames, the app releases it and returns to discovery mode automatically.
