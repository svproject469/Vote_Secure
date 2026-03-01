from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
import sqlite3, hashlib, random, string, os, json
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import io, base64

app = Flask(__name__)
app.secret_key = 'voting_system_secret_2025'
DB_PATH = 'data/voting.db'
AADHAAR_CSV = 'data/aadhaar_db.csv'

# ── Gmail SMTP Config ─────────────────────────────────────────────────────────
GMAIL_ADDRESS  = 'svproject469@gmail.com'
GMAIL_APP_PWD  = 'kfljqsgklpbwcbrc'

# ─────────────────────────────────────────────
#  DB INIT
# ─────────────────────────────────────────────
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.executescript('''
        CREATE TABLE IF NOT EXISTS voters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            voter_id TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            dob TEXT NOT NULL,
            gender TEXT NOT NULL,
            address TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            mobile TEXT NOT NULL,
            aadhaar_id TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            has_voted INTEGER DEFAULT 0,
            registered_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS candidates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            candidate_id TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            party TEXT NOT NULL,
            symbol TEXT NOT NULL,
            position TEXT NOT NULL,
            bio TEXT,
            vote_count INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS elections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            election_id TEXT UNIQUE NOT NULL,
            title TEXT NOT NULL,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            status TEXT DEFAULT 'upcoming'
        );
        CREATE TABLE IF NOT EXISTS votes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            voter_id TEXT NOT NULL,
            candidate_id TEXT NOT NULL,
            election_id TEXT NOT NULL,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type TEXT NOT NULL,
            user_id TEXT,
            details TEXT,
            ip_address TEXT,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        );
    ''')
    # Seed admin
    admin_pwd = hashlib.sha256('admin123'.encode()).hexdigest()
    try:
        c.execute("INSERT INTO admins (username, password_hash) VALUES (?, ?)", ('admin', admin_pwd))
    except:
        pass
    # Seed election
    try:
        c.execute("""INSERT INTO elections (election_id, title, start_date, end_date, status)
                     VALUES (?, ?, ?, ?, ?)""",
                  ('ELECT2025', 'Mumbai Municipal Election 2025',
                   '2025-01-01', '2025-12-31', 'active'))
    except:
        pass
    # Seed candidates
    candidates = [
        ('CAND001', 'Rajesh Sharma', 'Bharatiya Janata Party', '🪷', 'Mayor', 'Experienced leader with 15 years in public service.'),
        ('CAND002', 'Sunita Patil', 'Indian National Congress', '✋', 'Mayor', 'Champion of education and womens rights.'),
        ('CAND003', 'Aakash Mehta', 'Aam Aadmi Party', '🧹', 'Mayor', 'Anti-corruption crusader focused on clean governance.'),
        ('CAND004', 'Priyanka Desai', 'Shiv Sena', '🏹', 'Mayor', 'Strong advocate for Mumbai infrastructure.'),
    ]
    for c_data in candidates:
        try:
            c.execute("INSERT INTO candidates (candidate_id, name, party, symbol, position, bio) VALUES (?,?,?,?,?,?)", c_data)
        except:
            pass
    conn.commit()
    conn.close()

# ─────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────
def hash_password(pwd):
    return hashlib.sha256(pwd.encode()).hexdigest()

def generate_voter_id():
    return 'VTR' + ''.join(random.choices(string.digits, k=7))

def log_event(event_type, user_id=None, details=None):
    conn = get_db()
    conn.execute("INSERT INTO audit_logs (event_type, user_id, details, ip_address) VALUES (?,?,?,?)",
                 (event_type, user_id, details, request.remote_addr))
    conn.commit()
    conn.close()

def normalise_dob(dob_str):
    """Convert any dob format to DD/MM/YYYY for consistent comparison."""
    dob_str = str(dob_str).strip()
    # YYYY-MM-DD  (HTML date input)
    if len(dob_str) == 10 and dob_str[4] == '-':
        parts = dob_str.split('-')
        return f"{parts[2]}/{parts[1]}/{parts[0]}"
    # DD-MM-YYYY
    if len(dob_str) == 10 and dob_str[2] == '-':
        parts = dob_str.split('-')
        return f"{parts[0]}/{parts[1]}/{parts[2]}"
    # DD/MM/YYYY (already correct)
    return dob_str

def verify_aadhaar(aadhaar_id, name, dob):
    try:
        df = pd.read_csv(AADHAAR_CSV, dtype={'aadhaar_id': str})
        record = df[df['aadhaar_id'] == str(aadhaar_id)]
        if record.empty:
            return False, "Aadhaar number not found in database."
        record = record.iloc[0]
        if record['name'].lower() != name.lower():
            return False, "Name does not match Aadhaar records."
        if normalise_dob(record['dob']) != normalise_dob(dob):
            return False, f"Date of birth does not match Aadhaar records."
        return True, record.to_dict()
    except Exception as e:
        return False, str(e)

def generate_otp():
    return ''.join(random.choices(string.digits, k=6))

def send_otp_email(to_email, voter_name, otp):
    """Send OTP to voter's email via Gmail SMTP."""
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = 'VoteSecure India — Your OTP Code'
        msg['From']    = f'VoteSecure India <{GMAIL_ADDRESS}>'
        msg['To']      = to_email

        html_body = f"""
        <div style="font-family:Arial,sans-serif;max-width:480px;margin:0 auto;background:#0f0f0f;color:#e8e8e8;border-radius:12px;overflow:hidden;">
          <div style="background:#3b82f6;padding:24px;text-align:center;">
            <h2 style="margin:0;color:#fff;font-size:1.4rem;">🗳 VoteSecure India</h2>
            <p style="margin:6px 0 0;color:rgba(255,255,255,0.8);font-size:0.9rem;">Online Voting System</p>
          </div>
          <div style="padding:32px 28px;">
            <p style="margin:0 0 8px;">Hello <strong>{voter_name}</strong>,</p>
            <p style="color:#888;margin:0 0 24px;font-size:0.9rem;">Use the OTP below to complete your voter registration.</p>
            <div style="background:#1a1a1a;border:2px dashed #3b82f6;border-radius:10px;padding:24px;text-align:center;margin-bottom:24px;">
              <p style="margin:0 0 6px;color:#888;font-size:0.78rem;letter-spacing:2px;text-transform:uppercase;">Your OTP</p>
              <p style="margin:0;font-size:2.4rem;font-weight:700;font-family:monospace;letter-spacing:10px;color:#3b82f6;">{otp}</p>
            </div>
            <p style="color:#888;font-size:0.82rem;margin:0;">⏱ Valid for <strong>5 minutes</strong> only.<br>Do not share this OTP with anyone.</p>
          </div>
          <div style="background:#1a1a1a;padding:16px;text-align:center;font-size:0.75rem;color:#555;">
            VoteSecure India — B.Sc Data Science Project, N.G. Acharya & D.K. Marathe College
          </div>
        </div>
        """
        msg.attach(MIMEText(html_body, 'html'))

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(GMAIL_ADDRESS, GMAIL_APP_PWD)
            server.sendmail(GMAIL_ADDRESS, to_email, msg.as_string())
        return True, "OTP sent successfully"
    except Exception as e:
        return False, str(e)

def make_chart(labels, values, title, colors):
    fig, ax = plt.subplots(figsize=(9, 3.5), facecolor='#161616')
    ax.set_facecolor('#161616')
    bar_colors = ['#3b82f6' if i == 0 else '#2a2a2a' for i in range(len(labels))]
    if values and max(values) == 0:
        bar_colors = ['#2a2a2a'] * len(labels)
    bars = ax.bar(labels, values, color=bar_colors, width=0.5, zorder=3)
    ax.tick_params(colors='#888', labelsize=9)
    for spine in ax.spines.values():
        spine.set_color('#252525')
    ax.yaxis.grid(True, color='#222', zorder=0, linewidth=0.5)
    ax.set_axisbelow(True)
    for bar, val in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.15,
                str(val), ha='center', va='bottom', color='#888', fontsize=9)
    fig.patch.set_linewidth(0)
    plt.tight_layout(pad=1.5)
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=130, facecolor='#161616', edgecolor='none')
    buf.seek(0)
    img_b64 = base64.b64encode(buf.read()).decode('utf-8')
    plt.close()
    return img_b64

# ─────────────────────────────────────────────
#  ROUTES — PUBLIC
# ─────────────────────────────────────────────
@app.route('/')
def index():
    conn = get_db()
    election = conn.execute("SELECT * FROM elections WHERE status='active' LIMIT 1").fetchone()
    candidates = conn.execute("SELECT * FROM candidates ORDER BY vote_count DESC").fetchall()
    total_votes = conn.execute("SELECT COUNT(*) FROM votes").fetchone()[0]
    total_voters = conn.execute("SELECT COUNT(*) FROM voters").fetchone()[0]
    conn.close()
    return render_template('index.html', election=election, candidates=candidates,
                           total_votes=total_votes, total_voters=total_voters)

# ─────────────────────────────────────────────
#  ROUTES — VOTER AUTH
# ─────────────────────────────────────────────
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        step = request.form.get('step', '1')

        if step == '1':
            # Aadhaar + Phone verification step
            aadhaar = request.form.get('aadhaar_id', '').strip()
            name = request.form.get('name', '').strip()
            dob = request.form.get('dob', '').strip()
            phone = request.form.get('phone', '').strip()

            if len(aadhaar) != 12 or not aadhaar.isdigit():
                flash('Aadhaar number must be exactly 12 digits.', 'error')
                return render_template('register.html', step=1)

            if len(phone) != 10 or not phone.isdigit():
                flash('Phone number must be exactly 10 digits.', 'error')
                return render_template('register.html', step=1)

            conn = get_db()
            existing = conn.execute("SELECT id FROM voters WHERE aadhaar_id=?", (aadhaar,)).fetchone()
            phone_exists = conn.execute("SELECT id FROM voters WHERE mobile=?", (phone,)).fetchone()
            conn.close()
            if existing:
                flash('This Aadhaar is already registered.', 'error')
                return render_template('register.html', step=1)
            if phone_exists:
                flash('This phone number is already registered.', 'error')
                return render_template('register.html', step=1)

            ok, result = verify_aadhaar(aadhaar, name, dob)
            if not ok:
                log_event('AADHAAR_FAIL', details=f"Aadhaar: {aadhaar} | Reason: {result}")
                flash(f'Aadhaar Verification Failed: {result}', 'error')
                return render_template('register.html', step=1)

            # Verify phone matches Aadhaar record
            aadhaar_phone = str(int(float(str(result['mobile'])))).strip()
            if aadhaar_phone != phone:
                log_event('PHONE_MISMATCH', details=f"Aadhaar: {aadhaar}")
                flash('Phone number does not match Aadhaar records.', 'error')
                return render_template('register.html', step=1)

            otp = generate_otp()
            session['pending_registration'] = {
                'aadhaar_id': aadhaar,
                'name': result['name'],
                'dob': dob,
                'gender': result['gender'],
                'address': result['address'],
                'mobile': phone,
                'aadhaar_email': result['email'],
                'otp': otp,
                'otp_expires': (datetime.now() + timedelta(minutes=5)).isoformat()
            }
            log_event('AADHAAR_VERIFIED', details=f"Aadhaar: {aadhaar}")

            # Send OTP via Gmail
            voter_email = result.get('email', '')
            email_sent, email_msg = send_otp_email(voter_email, result['name'], otp)
            if email_sent:
                flash(f'✅ Aadhaar & Phone Verified! OTP sent to {voter_email[:4]}****{voter_email[voter_email.index("@"):]}', 'otp')
            else:
                # Fallback — show OTP on screen if email fails
                flash(f'✅ Aadhaar Verified! (Email failed: {email_msg}) OTP: {otp}', 'otp')

            return render_template('register.html', step=2, aadhaar_data=result)

        elif step == '2':
            # OTP + account creation
            pending = session.get('pending_registration')
            if not pending:
                flash('Session expired. Please start again.', 'error')
                return redirect(url_for('register'))

            otp_entered = request.form.get('otp', '').strip()
            email = request.form.get('email', '').strip()
            password = request.form.get('password', '').strip()

            if otp_entered != pending['otp']:
                flash('Invalid OTP. Please try again.', 'error')
                return render_template('register.html', step=2, aadhaar_data=pending)

            if datetime.now() > datetime.fromisoformat(pending['otp_expires']):
                flash('OTP expired. Please start again.', 'error')
                session.pop('pending_registration', None)
                return redirect(url_for('register'))

            voter_id = generate_voter_id()
            pwd_hash = hash_password(password)

            try:
                conn = get_db()
                conn.execute("""INSERT INTO voters
                    (voter_id, name, dob, gender, address, email, mobile, aadhaar_id, password_hash)
                    VALUES (?,?,?,?,?,?,?,?,?)""",
                    (voter_id, pending['name'], pending['dob'], pending['gender'],
                     pending['address'], email, pending['mobile'],
                     pending['aadhaar_id'], pwd_hash))
                conn.commit()
                conn.close()
                session.pop('pending_registration', None)
                log_event('VOTER_REGISTERED', user_id=voter_id)
                flash(f'🎉 Registration Successful! Your Voter ID: {voter_id}', 'success')
                return render_template('register.html', step=3, voter_id=voter_id)
            except Exception as e:
                flash(f'Registration error: {str(e)}', 'error')
                return render_template('register.html', step=2, aadhaar_data=pending)

    return render_template('register.html', step=1)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        voter_id = request.form.get('voter_id', '').strip()
        password = request.form.get('password', '').strip()
        conn = get_db()
        voter = conn.execute("SELECT * FROM voters WHERE voter_id=? AND password_hash=?",
                             (voter_id, hash_password(password))).fetchone()
        conn.close()
        if voter:
            session['voter'] = dict(voter)
            log_event('LOGIN_SUCCESS', user_id=voter_id)
            return redirect(url_for('dashboard'))
        else:
            log_event('LOGIN_FAIL', user_id=voter_id)
            flash('Invalid Voter ID or Password.', 'error')
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('voter', None)
    return redirect(url_for('index'))


# ─────────────────────────────────────────────
#  ROUTES — VOTER DASHBOARD
# ─────────────────────────────────────────────
@app.route('/dashboard')
def dashboard():
    if 'voter' not in session:
        return redirect(url_for('login'))
    conn = get_db()
    election = conn.execute("SELECT * FROM elections WHERE status='active' LIMIT 1").fetchone()
    candidates = conn.execute("SELECT * FROM candidates ORDER BY name").fetchall()
    conn.close()
    voter = session['voter']
    return render_template('dashboard.html', voter=voter, election=election, candidates=candidates)


@app.route('/vote', methods=['POST'])
def vote():
    if 'voter' not in session:
        return redirect(url_for('login'))
    voter = session['voter']
    if voter['has_voted']:
        flash('You have already cast your vote!', 'error')
        return redirect(url_for('dashboard'))
    candidate_id = request.form.get('candidate_id')
    election_id = request.form.get('election_id')
    conn = get_db()
    # Double check
    already = conn.execute("SELECT id FROM votes WHERE voter_id=? AND election_id=?",
                           (voter['voter_id'], election_id)).fetchone()
    if already:
        flash('Duplicate vote attempt blocked!', 'error')
        conn.close()
        return redirect(url_for('dashboard'))
    conn.execute("INSERT INTO votes (voter_id, candidate_id, election_id) VALUES (?,?,?)",
                 (voter['voter_id'], candidate_id, election_id))
    conn.execute("UPDATE voters SET has_voted=1 WHERE voter_id=?", (voter['voter_id'],))
    conn.execute("UPDATE candidates SET vote_count=vote_count+1 WHERE candidate_id=?", (candidate_id,))
    conn.commit()
    # Refresh session
    updated = conn.execute("SELECT * FROM voters WHERE voter_id=?", (voter['voter_id'],)).fetchone()
    session['voter'] = dict(updated)
    conn.close()
    log_event('VOTE_CAST', user_id=voter['voter_id'], details=f"Candidate: {candidate_id}")
    flash('✅ Your vote has been cast successfully!', 'success')
    return redirect(url_for('results'))


@app.route('/results')
def results():
    conn = get_db()
    candidates = conn.execute("SELECT * FROM candidates ORDER BY vote_count DESC").fetchall()
    election = conn.execute("SELECT * FROM elections WHERE status='active' LIMIT 1").fetchone()
    total_votes = conn.execute("SELECT COUNT(*) FROM votes").fetchone()[0]
    total_voters = conn.execute("SELECT COUNT(*) FROM voters").fetchone()[0]
    conn.close()
    labels = [c['name'] for c in candidates]
    values = [c['vote_count'] for c in candidates]
    colors = ['#e63946', '#457b9d', '#2a9d8f', '#e9c46a']
    chart = make_chart(labels, values, 'Live Vote Count', colors) if total_votes > 0 else None
    turnout = round((total_votes / total_voters * 100), 1) if total_voters > 0 else 0
    return render_template('results.html', candidates=candidates, election=election,
                           total_votes=total_votes, total_voters=total_voters,
                           chart=chart, turnout=turnout)


# ─────────────────────────────────────────────
#  ROUTES — ADMIN
# ─────────────────────────────────────────────
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        conn = get_db()
        admin = conn.execute("SELECT * FROM admins WHERE username=? AND password_hash=?",
                             (username, hash_password(password))).fetchone()
        conn.close()
        if admin:
            session['admin'] = username
            log_event('ADMIN_LOGIN', user_id=username)
            return redirect(url_for('admin_dashboard'))
        flash('Invalid credentials.', 'error')
    return render_template('admin_login.html')


@app.route('/admin/logout')
def admin_logout():
    session.pop('admin', None)
    return redirect(url_for('admin_login'))


@app.route('/admin/dashboard')
def admin_dashboard():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    conn = get_db()
    stats = {
        'total_voters': conn.execute("SELECT COUNT(*) FROM voters").fetchone()[0],
        'total_votes': conn.execute("SELECT COUNT(*) FROM votes").fetchone()[0],
        'candidates': conn.execute("SELECT COUNT(*) FROM candidates").fetchone()[0],
        'elections': conn.execute("SELECT COUNT(*) FROM elections").fetchone()[0],
    }
    candidates = conn.execute("SELECT * FROM candidates ORDER BY vote_count DESC").fetchall()
    voters = conn.execute("SELECT * FROM voters ORDER BY registered_at DESC LIMIT 20").fetchall()
    logs = conn.execute("SELECT * FROM audit_logs ORDER BY timestamp DESC LIMIT 30").fetchall()
    election = conn.execute("SELECT * FROM elections WHERE status='active' LIMIT 1").fetchone()
    total_voters = stats['total_voters']
    total_votes = stats['total_votes']
    conn.close()

    # Charts
    labels = [c['name'] for c in candidates]
    values = [c['vote_count'] for c in candidates]
    colors = ['#e63946', '#457b9d', '#2a9d8f', '#e9c46a']
    chart = make_chart(labels, values, 'Votes Per Candidate', colors) if total_votes > 0 else None
    turnout = round((total_votes / total_voters * 100), 1) if total_voters > 0 else 0

    return render_template('admin_dashboard.html', stats=stats, candidates=candidates,
                           voters=voters, logs=logs, election=election, chart=chart, turnout=turnout)


@app.route('/admin/add_candidate', methods=['POST'])
def add_candidate():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    cid = 'CAND' + ''.join(random.choices(string.digits, k=3))
    conn = get_db()
    conn.execute("INSERT INTO candidates (candidate_id, name, party, symbol, position, bio) VALUES (?,?,?,?,?,?)",
                 (cid, request.form['name'], request.form['party'],
                  request.form['symbol'], request.form['position'], request.form['bio']))
    conn.commit()
    conn.close()
    flash('Candidate added successfully!', 'success')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/reset_votes', methods=['POST'])
def reset_votes():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    conn = get_db()
    conn.execute("DELETE FROM votes")
    conn.execute("UPDATE voters SET has_voted=0")
    conn.execute("UPDATE candidates SET vote_count=0")
    conn.commit()
    conn.close()
    log_event('VOTES_RESET', user_id=session['admin'])
    flash('All votes have been reset.', 'success')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/delete_candidate/<candidate_id>', methods=['POST'])
def delete_candidate(candidate_id):
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    conn = get_db()
    conn.execute("DELETE FROM candidates WHERE candidate_id=?", (candidate_id,))
    conn.commit()
    conn.close()
    flash('Candidate deleted.', 'success')
    return redirect(url_for('admin_dashboard'))


# ─────────────────────────────────────────────
#  API — AADHAAR CHECK (AJAX)
# ─────────────────────────────────────────────
@app.route('/api/check_aadhaar', methods=['POST'])
def check_aadhaar():
    data = request.get_json()
    aadhaar = data.get('aadhaar_id', '')
    if len(aadhaar) != 12 or not aadhaar.isdigit():
        return jsonify({'valid': False, 'message': 'Must be 12 digits'})
    df = pd.read_csv(AADHAAR_CSV, dtype={'aadhaar_id': str})
    exists = not df[df['aadhaar_id'] == aadhaar].empty
    return jsonify({'valid': exists, 'message': '✅ Aadhaar found' if exists else '❌ Not found in database'})


app.jinja_env.globals['enumerate'] = enumerate

if __name__ == '__main__':
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    init_db()
    app.run(debug=True, port=5000)
