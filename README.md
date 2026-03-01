# 🗳 VoteSecure India — Online Voting System

**B.Sc Data Science Final Year Project**
**Siddhesh Vaity** 

---

## ⚠️ Disclaimer — Sample Data Only

> **This project is entirely based on a synthetically generated mock dataset.**
> No real personal data, real Aadhaar numbers, or real voter information has been used anywhere in this project.
> All 1,00,000 records in the database (names, Aadhaar numbers, phone numbers, addresses, emails) are randomly generated for demonstration purposes only.
> This project is **NOT affiliated** with UIDAI, the Election Commission of India, or any Government body.
> Built purely as a college academic project to simulate a real-world voting system.

---

## 📖 About

VoteSecure India is a secure, full-stack digital voting platform that simulates a real-world online election system. It replaces paper-based voting with a web application where voters can register using Aadhaar verification, confirm identity via OTP, and cast their vote securely from any device.

---

## ✅ Features

### 🧑 Voter
- Real-time Aadhaar number validation (AJAX)
- Phone number verification against Aadhaar records
- 3-step registration: Aadhaar + Phone → OTP → Account
- OTP delivered to email via Gmail SMTP
- Unique auto-generated Voter ID
- One-vote-per-person enforcement
- Live results with charts

### 🛡 Admin
- Secure admin dashboard
- Add / delete candidates
- View all registered voters
- Real-time vote distribution charts (Matplotlib)
- Full audit log with IP address & timestamps
- Vote reset for testing

### 📊 Data Science
- Pandas-powered Aadhaar database queries (1,00,000 records)
- Live vote distribution bar charts
- Voter turnout percentage tracking
- Audit-based anomaly detection

### 🔒 Security
- SHA-256 password hashing
- OTP-based 2FA (5-minute expiry)
- Duplicate vote prevention (DB + session)
- Duplicate Aadhaar & phone registration blocked
- Full audit trail for all system events

---

## 🛠 Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Python · Flask |
| Database | SQLite |
| Data Processing | Pandas |
| Visualization | Matplotlib |
| Frontend | Jinja2 · HTML5 · CSS3 · JavaScript |
| Email | Gmail SMTP (smtplib) |
| Security | SHA-256 · Session OTP |

---

## 🚀 How to Download & Run Locally

### Step 1 — Download the project

Click the green **"Code"** button on this page → **"Download ZIP"** → Extract the ZIP on your computer.

Or if you have Git installed, open CMD/Terminal and run:
```bash
git clone https://github.com/YOURUSERNAME/voting_system.git
```

---

### Step 2 — Open the project folder in CMD

Open the extracted folder, click the **address bar**, type `cmd` and press **Enter**.

Or in an already open terminal:
```bash
cd path/to/voting_system
```

---

### Step 3 — Install Python

Make sure Python 3.10 or above is installed.
Check by running:
```bash
python --version
```
If not installed, download from 👉 [python.org/downloads](https://www.python.org/downloads)

---

### Step 4 — Install dependencies

```bash
pip install flask pandas matplotlib
```

---

### Step 5 — Run the app

```bash
python app.py
```

You should see:
```
* Running on http://127.0.0.1:5000
```

---

### Step 6 — Open in browser

Go to 👉 [http://localhost:5000](http://localhost:5000)

---

## 🔐 Default Login Credentials

| Role | Username / ID | Password |
|------|--------------|----------|
| Admin | `admin` | `admin123` |
| Voter | Register first at `/register` | Your chosen password |

---

## 🪪 Sample Aadhaar Numbers for Testing

Use these to test the registration flow (these are all fake/generated records):

| Aadhaar | Name | DOB | Phone |
|---------|------|-----|-------|
| `123456789101` | Nawaz Kotwalkar | 30/04/2005 | 8433534194 |
| `234567891234` | Siddhesh Vaity | 14/05/2003 | 9876543210 |
| `123456789012` | Priya Sharma | 22/03/1998 | 9123456780 |
| `345678901234` | Rahul Mehta | 10/07/1995 | 9234567801 |
| `456789012345` | Anjali Desai | 05/11/2001 | 9345678012 |

> Enter the Aadhaar number, matching name, DOB, and phone exactly as shown above.

---

## 📁 Project Structure

```
voting_system/
├── app.py                    # Main Flask application
├── wsgi.py                   # WSGI entry point (for deployment)
├── requirements.txt          # Python dependencies
├── README.md
├── data/
│   ├── aadhaar_db.csv        # Synthetically generated mock Aadhaar database (1,00,000 records)
│   └── voting.db             # SQLite database (auto-created on first run)
└── templates/
    ├── base.html             # Base layout & navigation
    ├── index.html            # Home page
    ├── register.html         # 3-step Aadhaar registration
    ├── login.html            # Voter login
    ├── dashboard.html        # Voter dashboard + voting
    ├── results.html          # Live results with charts
    ├── admin_login.html      # Admin login
    └── admin_dashboard.html  # Admin panel
```

---

## 🌐 Live Demo

Hosted on PythonAnywhere 👉 `YOURUSERNAME.pythonanywhere.com`

---

## 👤 Author

**Siddhesh Vaity**
B.Sc Data Science — Seat No. 46
N.G. Acharya & D.K. Marathe College of Arts, Science & Commerce
Affiliated to University of Mumbai · 2025–26
