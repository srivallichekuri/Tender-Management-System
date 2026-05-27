from flask import Flask, render_template, request, redirect
import sqlite3
import re

from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)


# ---------------- DATABASE SETUP ---------------- #

def init_db():

    conn = sqlite3.connect('tender.db')
    cursor = conn.cursor()

    # TENDERS TABLE

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tenders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            budget TEXT,
            deadline TEXT
        )
    ''')

    # USERS TABLE

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            password TEXT,
            role TEXT
        )
    ''')

    # BIDS TABLE

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bids (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            contractor TEXT,
            tender_id INTEGER,
            amount TEXT,
            proposal TEXT
        )
    ''')

    # DEFAULT ADMIN

    cursor.execute(
        "SELECT * FROM users WHERE username = ?",
        ("admin",)
    )

    admin = cursor.fetchone()

    if admin is None:

        admin_password = generate_password_hash("Admin@123")

        cursor.execute(
            "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
            ("admin", admin_password, "admin")
        )

    conn.commit()
    conn.close()


# ---------------- HOME PAGE ---------------- #

@app.route('/')
def home():
    return render_template('index.html')


# ---------------- REGISTER PAGE ---------------- #

@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']

        # PASSWORD VALIDATION

        if len(password) < 8:
            return "Password must contain at least 8 characters"

        if not re.search(r'[A-Z]', password):
            return "Password must contain at least one capital letter"

        if not re.search(r'[0-9]', password):
            return "Password must contain at least one number"

        if not re.search(r'[@$!%*?&]', password):
            return "Password must contain at least one special character"

        hashed_password = generate_password_hash(password)

        conn = sqlite3.connect('tender.db')
        cursor = conn.cursor()

        # CHECK EXISTING USER

        cursor.execute(
            "SELECT * FROM users WHERE username = ?",
            (username,)
        )

        existing_user = cursor.fetchone()

        if existing_user:

            conn.close()
            return "Username already exists"

        # INSERT CONTRACTOR

        cursor.execute(
            "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
            (username, hashed_password, "contractor")
        )

        conn.commit()
        conn.close()

        return redirect('/login')

    return render_template('register.html')


# ---------------- LOGIN PAGE ---------------- #

@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect('tender.db')
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM users WHERE username = ?",
            (username,)
        )

        user = cursor.fetchone()

        conn.close()

        if user and check_password_hash(user[2], password):

            role = user[3]

            # ADMIN LOGIN

            if role == "admin":
                return redirect('/dashboard')

            # CONTRACTOR LOGIN

            elif role == "contractor":
                return redirect('/view_tenders/contractor')

        else:
            return "Invalid Username or Password"

    return render_template('login.html')


# ---------------- ADMIN DASHBOARD ---------------- #

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')


# ---------------- CREATE TENDER ---------------- #

@app.route('/create_tender', methods=['GET', 'POST'])
def create_tender():

    if request.method == 'POST':

        title = request.form['title']
        budget = request.form['budget']
        deadline = request.form['deadline']

        conn = sqlite3.connect('tender.db')
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO tenders (title, budget, deadline) VALUES (?, ?, ?)",
            (title, budget, deadline)
        )

        conn.commit()
        conn.close()

        return redirect('/view_tenders/admin')

    return render_template('create_tender.html')


# ---------------- VIEW TENDERS ---------------- #

@app.route('/view_tenders/<role>')
def view_tenders(role):

    conn = sqlite3.connect('tender.db')
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM tenders")

    tenders = cursor.fetchall()

    conn.close()

    return render_template(
        'view_tenders.html',
        tenders=tenders,
        role=role
    )


# ---------------- SUBMIT BID ---------------- #

@app.route('/bid/<int:tender_id>', methods=['GET', 'POST'])
def bid(tender_id):

    if request.method == 'POST':

        contractor = request.form['contractor']
        amount = request.form['amount']
        proposal = request.form['proposal']

        conn = sqlite3.connect('tender.db')
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO bids (contractor, tender_id, amount, proposal) VALUES (?, ?, ?, ?)",
            (contractor, tender_id, amount, proposal)
        )

        conn.commit()
        conn.close()

        return '''
         <script>
           alert("Bid Submitted Successfully!");
           window.location.href = "/view_tenders/contractor";
         </script>
         '''

    return render_template('bid.html')


# ---------------- VIEW BIDS ---------------- #

@app.route('/view_bids/<int:tender_id>')
def view_bids(tender_id):

    conn = sqlite3.connect('tender.db')
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM bids WHERE tender_id = ?",
        (tender_id,)
    )

    bids = cursor.fetchall()

    conn.close()

    return render_template(
        'view_bids.html',
        bids=bids
    )


# ---------------- DELETE TENDER ---------------- #

@app.route('/delete_tender/<int:id>')
def delete_tender(id):

    conn = sqlite3.connect('tender.db')
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM tenders WHERE id = ?",
        (id,)
    )

    conn.commit()
    conn.close()

    return redirect('/view_tenders/admin')


# ---------------- RUN APPLICATION ---------------- #

init_db()

if __name__ == '__main__':
    app.run(debug=True)