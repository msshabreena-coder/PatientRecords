
import os
import sqlite3
from contextlib import closing

from flask import Flask, request, redirect, url_for, render_template_string

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "patients.db")


def get_db():
    """Create a SQLite connection."""
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    return db


def init_db():
    """Create the patient table and always close the connection."""
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
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Patient Records Management System - V1</title>
    <style>
        * { box-sizing: border-box; }

        body {
            margin: 0;
            font-family: Arial, sans-serif;
            background: #f1f5f9;
            color: #1e293b;
        }

        header {
            background: #173b82;
            color: white;
            text-align: center;
            padding: 24px 16px;
        }

        header h1 { margin-top: 0; }

        main {
            max-width: 1100px;
            margin: 28px auto;
            padding: 0 18px;
        }

        .card {
            background: white;
            padding: 24px;
            border-radius: 12px;
            margin-bottom: 24px;
            box-shadow: 0 3px 12px #0000000d;
        }

        form {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 16px;
        }

        label {
            font-weight: bold;
            font-size: 14px;
        }

        input, select {
            width: 100%;
            padding: 11px;
            margin-top: 7px;
            border: 1px solid #cbd5e1;
            border-radius: 6px;
            font-size: 15px;
        }

        button {
            background: #1769e0;
            color: white;
            border: 0;
            border-radius: 6px;
            padding: 12px 18px;
            cursor: pointer;
            font-size: 15px;
        }

        button:hover { background: #1254b8; }

        .message {
            padding: 12px;
            border-radius: 6px;
            background: #dcfce7;
            color: #166534;
        }

        .error {
            background: #fee2e2;
            color: #991b1b;
        }

        .table-wrap { overflow-x: auto; }

        table {
            width: 100%;
            border-collapse: collapse;
        }

        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #e2e8f0;
        }

        th { background: #eff6ff; }

        @media (max-width: 650px) {
            form { grid-template-columns: 1fr; }
            .card { padding: 16px; }
        }
    </style>
</head>
<body>
<header>
    <h1>Patient Records Management System</h1>
    <p>Version 1 — Add Patient Record</p>
    <p>Registration Number: 24MIS0124</p>
</header>

<main>
    <section class="card">
        <h2>Add Patient</h2>

        {% if message %}
            <p class="message">{{ message }}</p>
        {% endif %}

        {% if error %}
            <p class="message error">{{ error }}</p>
        {% endif %}

        <form method="POST" action="{{ url_for('add_patient') }}">
            <label>Patient ID
                <input name="patient_id" required maxlength="30"
                       placeholder="Example: P001">
            </label>

            <label>Patient Name
                <input name="name" required maxlength="100">
            </label>

            <label>Age
                <input name="age" type="number" min="0" max="120" required>
            </label>

            <label>Gender
                <select name="gender" required>
                    <option value="">Select gender</option>
                    <option>Female</option>
                    <option>Male</option>
                    <option>Other</option>
                    <option>Prefer not to say</option>
                </select>
            </label>

            <label>Contact Number
                <input name="contact" required maxlength="20">
            </label>

            <label>Address
                <input name="address" required maxlength="250">
            </label>

            <button type="submit">Save Patient</button>
        </form>
    </section>

    <section class="card">
        <h2>Patient Records</h2>

        <div class="table-wrap">
            <table>
                <thead>
                    <tr>
                        <th>Patient ID</th>
                        <th>Name</th>
                        <th>Age</th>
                        <th>Gender</th>
                        <th>Contact</th>
                        <th>Address</th>
                    </tr>
                </thead>

                <tbody>
                    {% for patient in patients %}
                    <tr>
                        <td>{{ patient["patient_id"] }}</td>
                        <td>{{ patient["name"] }}</td>
                        <td>{{ patient["age"] }}</td>
                        <td>{{ patient["gender"] }}</td>
                        <td>{{ patient["contact"] }}</td>
                        <td>{{ patient["address"] }}</td>
                    </tr>
                    {% else %}
                    <tr>
                        <td colspan="6">No patient records added yet.</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </section>
</main>
</body>
</html>
"""


@app.route("/")
def home():
    # Always close the database connection, including when an error occurs.
    with closing(get_db()) as db:
        patients = db.execute(
            "SELECT * FROM patients ORDER BY patient_id"
        ).fetchall()

    return render_template_string(
        PAGE,
        patients=patients,
        message=request.args.get("message", ""),
        error=request.args.get("error", "")
    )


@app.route("/add", methods=["POST"])
def add_patient():
    patient_id = request.form.get("patient_id", "").strip()
    name = request.form.get("name", "").strip()
    age_text = request.form.get("age", "").strip()
    gender = request.form.get("gender", "").strip()
    contact = request.form.get("contact", "").strip()
    address = request.form.get("address", "").strip()

    if not all([patient_id, name, age_text, gender, contact, address]):
        return redirect(url_for(
            "home", error="All fields are required."
        ))

    try:
        age = int(age_text)
        if not 0 <= age <= 120:
            raise ValueError
    except ValueError:
        return redirect(url_for(
            "home", error="Enter a valid age from 0 to 120."
        ))

    db = get_db()
    try:
        db.execute("""
            INSERT INTO patients
                (patient_id, name, age, gender, contact, address)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (patient_id, name, age, gender, contact, address))
        db.commit()

    except sqlite3.IntegrityError:
        return redirect(url_for(
            "home", error="That patient ID already exists."
        ))

    finally:
        db.close()

    return redirect(url_for(
        "home", message="Patient record added successfully."
    ))


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=False)
