from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import date
import sqlite3, os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, 'transport.db')
app = Flask(__name__)
app.secret_key = os.environ.get('TMS_SECRET_KEY', 'development-only-change-this-secret-key')
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'


def db():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    con.execute('PRAGMA foreign_keys = ON')
    return con


def init_db():
    with db() as con:
        con.executescript('''
        CREATE TABLE IF NOT EXISTS users (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          username TEXT UNIQUE NOT NULL,
          password_hash TEXT NOT NULL,
          created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS vehicles (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          registration_no TEXT UNIQUE NOT NULL,
          model TEXT NOT NULL,
          capacity INTEGER NOT NULL CHECK(capacity > 0),
          status TEXT NOT NULL DEFAULT 'Available'
        );
        CREATE TABLE IF NOT EXISTS drivers (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          name TEXT NOT NULL,
          phone TEXT NOT NULL,
          license_no TEXT UNIQUE NOT NULL,
          status TEXT NOT NULL DEFAULT 'Available'
        );
        CREATE TABLE IF NOT EXISTS trips (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          vehicle_id INTEGER NOT NULL,
          driver_id INTEGER NOT NULL,
          start_location TEXT NOT NULL,
          end_location TEXT NOT NULL,
          trip_date TEXT NOT NULL,
          status TEXT NOT NULL DEFAULT 'Ongoing',
          created_at TEXT DEFAULT CURRENT_TIMESTAMP,
          FOREIGN KEY(vehicle_id) REFERENCES vehicles(id) ON DELETE RESTRICT,
          FOREIGN KEY(driver_id) REFERENCES drivers(id) ON DELETE RESTRICT
        );
        ''')


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to continue.', 'warning')
            return redirect(url_for('login'))
        return view(*args, **kwargs)
    return wrapped


@app.route('/')
def home():
    return redirect(url_for('dashboard' if 'user_id' in session else 'login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if session.get('user_id'):
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        confirm = request.form.get('confirm_password', '')
        if len(username) < 3:
            flash('Username must contain at least 3 characters.', 'danger')
        elif len(password) < 8:
            flash('Password must contain at least 8 characters.', 'danger')
        elif password != confirm:
            flash('Passwords do not match.', 'danger')
        else:
            try:
                with db() as con:
                    con.execute('INSERT INTO users(username, password_hash) VALUES (?, ?)',
                                (username, generate_password_hash(password)))
                flash('Registration successful. Please log in.', 'success')
                return redirect(url_for('login'))
            except sqlite3.IntegrityError:
                flash('That username is already registered.', 'danger')
    return render_template('auth.html', mode='Register')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('user_id'):
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        with db() as con:
            user = con.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        if user and check_password_hash(user['password_hash'], password):
            session.clear()
            session['user_id'] = user['id']
            session['username'] = user['username']
            return redirect(url_for('dashboard'))
        flash('Incorrect username or password.', 'danger')
    return render_template('auth.html', mode='Login')


@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))


@app.route('/dashboard')
@login_required
def dashboard():
    with db() as con:
        totals = {
            'vehicles': con.execute('SELECT COUNT(*) FROM vehicles').fetchone()[0],
            'drivers': con.execute('SELECT COUNT(*) FROM drivers').fetchone()[0],
            'ongoing': con.execute("SELECT COUNT(*) FROM trips WHERE status='Ongoing'").fetchone()[0],
            'completed': con.execute("SELECT COUNT(*) FROM trips WHERE status='Completed'").fetchone()[0],
        }
        trips = con.execute('''SELECT t.*, v.registration_no, d.name AS driver_name
            FROM trips t JOIN vehicles v ON v.id=t.vehicle_id JOIN drivers d ON d.id=t.driver_id
            ORDER BY t.id DESC LIMIT 8''').fetchall()
    return render_template('dashboard.html', totals=totals, trips=trips)


@app.route('/vehicles', methods=['GET', 'POST'])
@login_required
def vehicles():
    if request.method == 'POST':
        registration_no = request.form.get('registration_no', '').strip().upper()
        model = request.form.get('model', '').strip()
        try:
            capacity = int(request.form.get('capacity', '0'))
            status = request.form.get('status', 'Available')
            if not registration_no or not model or capacity < 1 or status not in ('Available', 'In Service', 'Maintenance'):
                raise ValueError
            with db() as con:
                con.execute('INSERT INTO vehicles(registration_no, model, capacity, status) VALUES (?, ?, ?, ?)',
                            (registration_no, model, capacity, status))
            flash('Vehicle added successfully.', 'success')
        except (sqlite3.IntegrityError, ValueError):
            flash('Could not add vehicle. Check all fields and use a unique registration number.', 'danger')
        return redirect(url_for('vehicles'))
    q = request.args.get('q', '').strip()
    with db() as con:
        rows = con.execute('''SELECT * FROM vehicles WHERE registration_no LIKE ? OR model LIKE ? OR status LIKE ? ORDER BY id DESC''',
                           (f'%{q}%', f'%{q}%', f'%{q}%')).fetchall()
    return render_template('list.html', page='Vehicles', kind='vehicles', rows=rows, q=q,
        columns=[('registration_no','Registration No.'),('model','Model'),('capacity','Capacity'),('status','Status')],
        fields=[('registration_no','Registration number','text'),('model','Vehicle model','text'),('capacity','Seating capacity','number')],
        statuses=['Available','In Service','Maintenance'])


@app.route('/drivers', methods=['GET', 'POST'])
@login_required
def drivers():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        phone = request.form.get('phone', '').strip()
        license_no = request.form.get('license_no', '').strip().upper()
        status = request.form.get('status', 'Available')
        try:
            if not name or not phone or not license_no or status not in ('Available', 'On Trip', 'Unavailable'):
                raise ValueError
            with db() as con:
                con.execute('INSERT INTO drivers(name, phone, license_no, status) VALUES (?, ?, ?, ?)',
                            (name, phone, license_no, status))
            flash('Driver added successfully.', 'success')
        except (sqlite3.IntegrityError, ValueError):
            flash('Could not add driver. Check all fields and ensure the license number is unique.', 'danger')
        return redirect(url_for('drivers'))
    q = request.args.get('q', '').strip()
    with db() as con:
        rows = con.execute('''SELECT * FROM drivers WHERE name LIKE ? OR phone LIKE ? OR license_no LIKE ? OR status LIKE ? ORDER BY id DESC''',
                           (f'%{q}%', f'%{q}%', f'%{q}%', f'%{q}%')).fetchall()
    return render_template('list.html', page='Drivers', kind='drivers', rows=rows, q=q,
        columns=[('name','Name'),('phone','Phone'),('license_no','License No.'),('status','Status')],
        fields=[('name','Full name','text'),('phone','Phone number','tel'),('license_no','License number','text')],
        statuses=['Available','On Trip','Unavailable'])


@app.route('/<kind>/<int:item_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_item(kind, item_id):
    configs = {
        'vehicles': {'table':'vehicles','title':'Vehicle','fields':['registration_no','model','capacity','status'], 'statuses':['Available','In Service','Maintenance']},
        'drivers': {'table':'drivers','title':'Driver','fields':['name','phone','license_no','status'], 'statuses':['Available','On Trip','Unavailable']},
    }
    if kind not in configs:
        flash('That record type cannot be edited here.', 'danger')
        return redirect(url_for('dashboard'))
    cfg = configs[kind]
    with db() as con:
        row = con.execute(f"SELECT * FROM {cfg['table']} WHERE id=?", (item_id,)).fetchone()
        if row is None:
            flash('Record not found.', 'warning')
            return redirect(url_for(kind))
        if request.method == 'POST':
            values = [request.form.get(field, '').strip() for field in cfg['fields']]
            try:
                if kind == 'vehicles':
                    values[0] = values[0].upper()
                    values[2] = int(values[2])
                    if not values[0] or not values[1] or values[2] < 1 or values[3] not in cfg['statuses']:
                        raise ValueError
                else:
                    values[2] = values[2].upper()
                    if not all(values[:3]) or values[3] not in cfg['statuses']:
                        raise ValueError
                set_clause = ', '.join(f'{field}=?' for field in cfg['fields'])
                con.execute(f"UPDATE {cfg['table']} SET {set_clause} WHERE id=?", (*values, item_id))
                flash(f"{cfg['title']} updated successfully.", 'success')
                return redirect(url_for(kind))
            except (ValueError, sqlite3.IntegrityError):
                flash('Could not update record. Check the values and unique identifiers.', 'danger')
                row = dict(row)
                row.update(dict(zip(cfg['fields'], values)))
    return render_template('edit.html', kind=kind, cfg=cfg, row=row)


@app.route('/trips', methods=['GET', 'POST'])
@login_required
def trips():
    if request.method == 'POST':
        try:
            vehicle_id = int(request.form['vehicle_id'])
            driver_id = int(request.form['driver_id'])
            start = request.form.get('start_location', '').strip()
            end = request.form.get('end_location', '').strip()
            trip_date = request.form.get('trip_date', '')
            status = request.form.get('status', 'Ongoing')
            if not start or not end or not trip_date or status not in ('Ongoing','Completed','Cancelled'):
                raise ValueError
            with db() as con:
                con.execute('''INSERT INTO trips(vehicle_id, driver_id, start_location, end_location, trip_date, status)
                    VALUES (?, ?, ?, ?, ?, ?)''', (vehicle_id, driver_id, start, end, trip_date, status))
            flash('Trip created successfully.', 'success')
        except (sqlite3.IntegrityError, ValueError, KeyError):
            flash('Could not create trip. Check the form and make sure a vehicle and driver exist.', 'danger')
        return redirect(url_for('trips'))
    q = request.args.get('q', '').strip()
    with db() as con:
        rows = con.execute('''SELECT t.*, v.registration_no, d.name AS driver_name FROM trips t
            JOIN vehicles v ON v.id=t.vehicle_id JOIN drivers d ON d.id=t.driver_id
            WHERE v.registration_no LIKE ? OR d.name LIKE ? OR t.start_location LIKE ? OR t.end_location LIKE ? OR t.status LIKE ?
            ORDER BY t.id DESC''', tuple(f'%{q}%' for _ in range(5))).fetchall()
        vehicle_options = con.execute('SELECT id, registration_no FROM vehicles ORDER BY registration_no').fetchall()
        driver_options = con.execute('SELECT id, name FROM drivers ORDER BY name').fetchall()
    return render_template('trips.html', rows=rows, vehicle_options=vehicle_options, driver_options=driver_options, q=q, today=date.today().isoformat())


@app.route('/trips/<int:trip_id>/status', methods=['POST'])
@login_required
def update_trip_status(trip_id):
    status = request.form.get('status')
    if status not in ('Ongoing', 'Completed', 'Cancelled'):
        flash('Invalid trip status.', 'danger')
    else:
        with db() as con:
            con.execute('UPDATE trips SET status=? WHERE id=?', (status, trip_id))
        flash('Trip status updated.', 'success')
    return redirect(request.referrer or url_for('trips'))


@app.route('/delete/<kind>/<int:item_id>', methods=['POST'])
@login_required
def delete_item(kind, item_id):
    tables = {'vehicles': 'vehicles', 'drivers': 'drivers', 'trips': 'trips'}
    if kind not in tables:
        flash('Invalid item.', 'danger')
        return redirect(url_for('dashboard'))
    try:
        with db() as con:
            con.execute(f'DELETE FROM {tables[kind]} WHERE id=?', (item_id,))
        flash('Record deleted successfully.', 'success')
    except sqlite3.IntegrityError:
        flash('This vehicle or driver is assigned to a trip. Delete related trips first.', 'danger')
    return redirect(url_for(kind))


# Ensure the database exists both when run directly and when served by a WSGI server.
init_db()

if __name__ == '__main__':
    app.run(debug=True)
