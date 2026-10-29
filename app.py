
import os
import sqlite3
from contextlib import closing
from flask import Flask, request, redirect, url_for, render_template_string

app = Flask(__name__)

DATABASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "patients.db")


def get_db():
    return sqlite3.connect(DATABASE)


def init_db():
    with closing(get_db()) as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS patients (
                patient_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                age INTEGER NOT NULL,
                gender TEXT NOT NULL,
                contact TEXT NOT NULL,
                address TEXT NOT NULL
            )
        """)
        db.commit()


PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Patient Records Management System</title>
    <style>
        body { font-family: Arial; max-width: 1000px; margin: 35px auto; }
        input, button { padding: 9px; margin: 5px; }
        input { box-sizing: border-box; max-width: 100%; }
        form { margin-bottom: 18px; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th, td { border: 1px solid #ccc; padding: 10px; text-align: left; }
        th { background: #e8eef8; }
        .panel { background: #f6f8fb; padding: 18px; margin: 18px 0; }
    </style>
</head>
<body>
    <h1>Patient Records Management System</h1>
    <p>Registration Number: 24MIS0124</p>
    <h3>Version 2 — Add and Search Patient Records</h3>

    <div class="panel">
        <h2>Add Patient</h2>
        <form method="POST" action="/add">
            <input name="patient_id" placeholder="Patient ID" required>
            <input name="name" placeholder="Full name" required>
            <input name="age" type="number" min="0" max="120"
                   placeholder="Age" required>
            <input name="gender" placeholder="Gender" required>
            <input name="contact" placeholder="Contact" required>
            <input name="address" placeholder="Address" required>
            <button type="submit">Add Patient</button>
        </form>
    </div>

    <div class="panel">
        <h2>Search Patients</h2>
        <form method="GET" action="/">
            <input name="q" value="{{ query }}"
                   placeholder="Search by patient ID or name">
            <button type="submit">Search</button>
            <a href="/">Show All</a>
        </form>
    </div>

    {% if message %}
        <p>{{ message }}</p>
    {% endif %}

    <h2>Patient Records ({{ patients|length }})</h2>
    <table>
        <tr>
            <th>Patient ID</th><th>Name</th><th>Age</th>
            <th>Gender</th><th>Contact</th><th>Address</th>
        </tr>
        {% for p in patients %}
        <tr>
            <td>{{ p[0] }}</td><td>{{ p[1] }}</td><td>{{ p[2] }}</td>
            <td>{{ p[3] }}</td><td>{{ p[4] }}</td><td>{{ p[5] }}</td>
        </tr>
        {% else %}
        <tr><td colspan="6">No matching patient records found.</td></tr>
        {% endfor %}
    </table>
</body>
</html>
"""


@app.route("/")
def home():
    query = request.args.get("q", "").strip()

    with closing(get_db()) as db:
        if query:
            patients = db.execute("""
                SELECT * FROM patients
                WHERE patient_id LIKE ? OR name LIKE ?
                ORDER BY patient_id
            """, (f"%{query}%", f"%{query}%")).fetchall()
        else:
            patients = db.execute(
                "SELECT * FROM patients ORDER BY patient_id"
            ).fetchall()

    return render_template_string(
        PAGE, patients=patients, query=query, message=""
    )


@app.route("/add", methods=["POST"])
def add_patient():
    data = {
        key: request.form.get(key, "").strip()
        for key in [
            "patient_id", "name", "age",
            "gender", "contact", "address"
        ]
    }

    if not all(data.values()):
        return "All fields are required.", 400

    try:
        age = int(data["age"])
        if not 0 <= age <= 120:
            raise ValueError
    except ValueError:
        return "Age must be an integer from 0 to 120.", 400

    db = get_db()
    try:
        db.execute("""
            INSERT INTO patients
            (patient_id, name, age, gender, contact, address)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            data["patient_id"], data["name"], age,
            data["gender"], data["contact"], data["address"]
        ))
        db.commit()
    except sqlite3.IntegrityError:
        return "A patient with this ID already exists.", 409
    finally:
        db.close()

    return redirect(url_for("home"))


init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
