# Transport Management System (TMS)

A complete beginner-friendly Transport Management System built with **Python Flask, SQLite, HTML, CSS, Bootstrap, and Bootstrap Icons**. The interface follows the supplied references: blue/cyan gradient background, centered login/register cards, blue navigation bar, dark sidebar, four colored dashboard cards, and a recent-trips table.

## Features
- User registration with password confirmation and hashed passwords
- Login/logout using secure session cookies
- Dashboard counts calculated from the database
- Vehicle management: add, search, edit, and delete
- Driver management: add, search, edit, and delete
- Trip management: create trips, search trips, update trip status, and delete trips
- Trip statuses: Ongoing, Completed, Cancelled
- Validation for required fields, unique vehicle registration numbers, unique driver license numbers, and positive vehicle capacity
- Responsive layout for desktop, tablet, and mobile
- SQLite database created automatically on startup

## Requirements
- Python 3.10 or newer
- Internet connection for Bootstrap and Bootstrap Icons CDN assets (the app logic runs locally)
- Visual Studio Code is recommended, but optional

## Run on Windows
1. Download and extract the ZIP.
2. Open the `transport_management_system` folder in VS Code.
3. Select **Terminal → New Terminal**.
4. Create a virtual environment:
   ```powershell
   py -m venv .venv
   ```
5. Activate it in PowerShell:
   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```
   If PowerShell blocks activation, use Command Prompt and run `.venv\Scripts\activate.bat` instead.
6. Install dependencies:
   ```powershell
   py -m pip install -r requirements.txt
   ```
7. Run the app:
   ```powershell
   py app.py
   ```
8. Open **http://127.0.0.1:5000** in your browser.
9. Select **Register**, create an account, then log in.
10. Optional: to populate the dashboard with demo values like the reference image (12 vehicles, 5 drivers, 3 ongoing trips, 17 completed trips), stop the server and run `py seed_demo.py`, then start the server again with `py app.py`. Run this only on an empty database.

The database file `transport.db` is created in the project folder automatically. Add a vehicle and a driver before creating a trip. The dashboard totals update automatically based on the records in the database.

## Project structure
```text
transport_management_system/
├── app.py
├── seed_demo.py
├── requirements.txt
├── README.md
├── templates/
│   ├── base.html
│   ├── auth.html
│   ├── dashboard.html
│   ├── list.html
│   ├── edit.html
│   └── trips.html
└── static/
    └── style.css
```

## Troubleshooting
- If `py` is not recognized, install Python from python.org and select **Add Python to PATH** during setup.
- If Flask is missing, activate the virtual environment and run `py -m pip install -r requirements.txt` again.
- If port 5000 is busy, close the other application using it or change the port in the final `app.run()` line.
- To reset demo data, stop the server and delete `transport.db`; the app will create a fresh database on the next run. This permanently deletes all stored users and records.

## Before public deployment
This is an educational project. Set a unique `TMS_SECRET_KEY`, disable Flask debug mode, add CSRF protection and rate limiting, and review deployment security before exposing it to the internet.
