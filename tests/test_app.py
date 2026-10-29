
import os
import tempfile
import unittest
import sqlite3

import app as patient_app


class PatientRecordsTests(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.original_database = patient_app.DATABASE
        patient_app.DATABASE = os.path.join(
            self.temp_dir.name, "test_patients.db"
        )

        patient_app.init_db()
        patient_app.app.config["TESTING"] = True
        self.client = patient_app.app.test_client()

    def tearDown(self):
        # Close any SQLite connections before deleting the test database.
        db = getattr(self, "db", None)
        if db is not None:
            db.close()

        patient_app.DATABASE = self.original_database
        self.temp_dir.cleanup()

    def test_home_page_loads(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            b"Patient Records Management System", response.data
        )

    def test_add_patient(self):
        response = self.client.post(
            "/add",
            data={
                "patient_id": "P001",
                "name": "Test Patient",
                "age": "25",
                "gender": "Other",
                "contact": "9000000000",
                "address": "Test Address",
            },
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            b"Patient record added successfully", response.data
        )
        self.assertIn(b"P001", response.data)

    def test_duplicate_patient_id(self):
        data = {
            "patient_id": "P001",
            "name": "Test Patient",
            "age": "25",
            "gender": "Other",
            "contact": "9000000000",
            "address": "Test Address",
        }
        self.client.post("/add", data=data)
        response = self.client.post(
            "/add", data=data, follow_redirects=True
        )
        self.assertIn(b"already exists", response.data)

    def test_missing_fields(self):
        response = self.client.post(
            "/add",
            data={"patient_id": "P002"},
            follow_redirects=True,
        )
        self.assertIn(b"All fields are required", response.data)

    def test_invalid_age(self):
        response = self.client.post(
            "/add",
            data={
                "patient_id": "P003",
                "name": "Test Patient",
                "age": "999",
                "gender": "Other",
                "contact": "9000000000",
                "address": "Test Address",
            },
            follow_redirects=True,
        )
        self.assertIn(b"valid age", response.data)


if __name__ == "__main__":
    unittest.main()
