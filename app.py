from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import smtplib
from email.mime.text import MIMEText
import logging

app = Flask(__name__)
app.secret_key = 'your_secret_key'
logging.basicConfig(level=logging.DEBUG)

DATABASE = 'database.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    return conn

def send_email(to_email, subject, message):
     # Setup your email server and credentials here
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    smtp_username = "solobirdacademy@gmail.com"
    smtp_password = "eace gdpq qjnp uqez"

    msg = MIMEText(message)
    msg['Subject'] = subject
    msg['From'] = smtp_username
    msg['To'] = to_email

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.sendmail(smtp_username, to_email, msg.as_string())
        logging.debug(f"Email sent to {to_email}")
    except Exception as e:
        logging.error(f"Failed to send email: {e}")


@app.route('/')
def form():
    return render_template('form.html')

@app.route('/submit', methods=['POST'])
def submit():
    try:
        name = request.form['name']
        email = request.form['email']
        date = request.form['date']
        time = request.form['time']
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO requests (name, email, date, time) VALUES (?, ?, ?, ?)", (name, email, date, time))
        conn.commit()
        conn.close()
        flash('Request submitted successfully.')
        send_email(email, 'Request Received', f'Hi {name},\n\nYour request for {date} at {time} has been received.')
    except Exception as e:
        logging.error(f"Error in submit route: {e}")
        flash('An error occurred. Please try again.')
    return redirect(url_for('form'))

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        if request.form['username'] == 'admin1' and request.form['password'] == 'admin1ac':
            session['admin'] = True
            return redirect(url_for('view_requests'))
        else:
            flash('Invalid credentials.')
    return render_template('admin.html')

@app.route('/view_requests')
def view_requests():
    if not session.get('admin'):
        return redirect(url_for('admin'))
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM requests")
    requests = cursor.fetchall()
    conn.close()
    return render_template('view_requests.html', requests=requests)

@app.route('/respond/<int:req_id>', methods=['POST'])
def respond(req_id):
    if not session.get('admin'):
        return redirect(url_for('admin'))
    try:
        note = request.form['note']
        status = request.form['status']
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("UPDATE requests SET status = ?, note = ? WHERE id = ?", (status, note, req_id))
        cursor.execute("SELECT email FROM requests WHERE id = ?", (req_id,))
        email = cursor.fetchone()[0]
        conn.commit()
        conn.close()
        send_email(email, f"Your request has been {status}", note)
        flash(f'Request {status} successfully.')
    except Exception as e:
        logging.error(f"Error in respond route: {e}")
        flash('An error occurred. Please try again.')
    return redirect(url_for('view_requests'))

@app.route('/test_email')
def test_email():
    try:
        send_email('recipient_email@example.com', 'Test Subject', 'This is a test email.')
        return 'Email sent!'
    except Exception as e:
        logging.error(f"Error in test_email route: {e}")
        return 'Failed to send email.'

if __name__ == '__main__':
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            status TEXT DEFAULT 'Pending',
            note TEXT
        )
    ''')
    conn.close()
    app.run(debug=True)
