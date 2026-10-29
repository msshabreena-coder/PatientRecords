
import os
import sqlite3
import tempfile
import unittest
from contextlib import closing

import app as patient_app


class PatientAppTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.original_database = patient_app.DATABASE
        patient_app.DATABASE = os.path.join(
            self.temp_dir.name, "test_patients.db"
        )
        patient_app.app.config["TESTING"] = True
        patient_app.init_db()
        self.client = patient_app.app.test_client()

    def tearDown(self):
        patient_app.DATABASE = self.original_database
        self.temp_dir.cleanup()

    def add_patient(self, patient_id="P001", name="Asha"):
        return self.client.post("/add", data={
            "patient_id": patient_id,
            "name": name,
            "age": "25",
            "gender": "Female",
            "contact": "9876543210",
            "address": "Chennai"
        }, follow_redirects=True)

    def test_home_page_loads(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Patient Records Management System", response.data)

    def test_add_patient(self):
        response = self.add_patient()
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Asha", response.data)

    def test_duplicate_patient_id(self):
        self.add_patient()
        response = self.add_patient(name="Another Patient")
        self.assertEqual(response.status_code, 409)

    def test_missing_fields(self):
        response = self.client.post("/add", data={"patient_id": "P002"})
        self.assertEqual(response.status_code, 400)

    def test_invalid_age(self):
        data = {
            "patient_id": "P003", "name": "Ravi", "age": "abc",
            "gender": "Male", "contact": "9999999999",
            "address": "Vellore"
        }
        response = self.client.post("/add", data=data)
        self.assertEqual(response.status_code, 400)

    def test_stored_in_database(self):
        self.add_patient()
        with closing(sqlite3.connect(patient_app.DATABASE)) as db:
            result = db.execute(
                "SELECT name FROM patients WHERE patient_id = ?",
                ("P001",)
            ).fetchone()
        self.assertEqual(result[0], "Asha")

    def test_search_by_name(self):
        self.add_patient(name="Asha")
        self.add_patient(patient_id="P002", name="Ravi")
        response = self.client.get("/?q=Asha")
        self.assertIn(b"Asha", response.data)
        self.assertNotIn(b"Ravi", response.data)

    def test_search_by_patient_id(self):
        self.add_patient()
        self.add_patient(patient_id="P002", name="Ravi")
        response = self.client.get("/?q=P002")
        self.assertIn(b"Ravi", response.data)
        self.assertNotIn(b"Asha", response.data)


if __name__ == "__main__":
    unittest.main()
