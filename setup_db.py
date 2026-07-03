"""Create a synthetic clinical SQLite database. Fully seeded and reproducible."""

import random
import sqlite3

DB_PATH = "clinical.db"
SEED = 42

DEPARTMENTS = ["Cardiology", "Oncology", "Nuclear Medicine", "General Medicine", "Endocrinology"]

DIAGNOSES = [
    ("I10", "Essential hypertension"),
    ("E11.9", "Type 2 diabetes mellitus"),
    ("I25.10", "Coronary artery disease"),
    ("C34.90", "Non small cell lung cancer"),
    ("E78.5", "Hyperlipidemia"),
    ("I48.91", "Atrial fibrillation"),
    ("J44.9", "Chronic obstructive pulmonary disease"),
    ("N18.3", "Chronic kidney disease stage 3"),
]

LAB_TESTS = [
    ("Glucose", "mg/dL", 70, 100, 60, 260),
    ("Total cholesterol", "mg/dL", 125, 200, 110, 320),
    ("Creatinine", "mg/dL", 0.6, 1.2, 0.4, 3.5),
    ("Hemoglobin", "g/dL", 12.0, 17.5, 8.0, 19.0),
    ("Troponin I", "ng/mL", 0.0, 0.04, 0.0, 2.0),
    ("HbA1c", "%", 4.0, 5.6, 4.0, 12.0),
]


def create_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        DROP TABLE IF EXISTS lab_results;
        DROP TABLE IF EXISTS diagnoses;
        DROP TABLE IF EXISTS visits;
        DROP TABLE IF EXISTS patients;

        CREATE TABLE patients (
            patient_id INTEGER PRIMARY KEY,
            sex TEXT NOT NULL CHECK (sex IN ('F', 'M')),
            birth_year INTEGER NOT NULL
        );

        CREATE TABLE visits (
            visit_id INTEGER PRIMARY KEY,
            patient_id INTEGER NOT NULL REFERENCES patients(patient_id),
            visit_date TEXT NOT NULL,
            department TEXT NOT NULL
        );

        CREATE TABLE diagnoses (
            diagnosis_id INTEGER PRIMARY KEY,
            visit_id INTEGER NOT NULL REFERENCES visits(visit_id),
            icd10_code TEXT NOT NULL,
            description TEXT NOT NULL
        );

        CREATE TABLE lab_results (
            lab_id INTEGER PRIMARY KEY,
            visit_id INTEGER NOT NULL REFERENCES visits(visit_id),
            test_name TEXT NOT NULL,
            value REAL NOT NULL,
            unit TEXT NOT NULL,
            ref_low REAL NOT NULL,
            ref_high REAL NOT NULL
        );
        """
    )


def random_date(rng: random.Random, start_year: int = 2024, end_year: int = 2026) -> str:
    year = rng.randint(start_year, end_year)
    month = rng.randint(1, 12)
    day = rng.randint(1, 28)
    return f"{year:04d}-{month:02d}-{day:02d}"


def populate(conn: sqlite3.Connection, n_patients: int = 200) -> None:
    rng = random.Random(SEED)

    for pid in range(1, n_patients + 1):
        sex = rng.choice(["F", "M"])
        birth_year = rng.randint(1940, 2005)
        conn.execute(
            "INSERT INTO patients (patient_id, sex, birth_year) VALUES (?, ?, ?)",
            (pid, sex, birth_year),
        )

    visit_id = 0
    lab_id = 0
    diagnosis_id = 0
    for pid in range(1, n_patients + 1):
        for _ in range(rng.randint(1, 6)):
            visit_id += 1
            conn.execute(
                "INSERT INTO visits (visit_id, patient_id, visit_date, department) "
                "VALUES (?, ?, ?, ?)",
                (visit_id, pid, random_date(rng), rng.choice(DEPARTMENTS)),
            )

            for _ in range(rng.randint(0, 2)):
                diagnosis_id += 1
                code, desc = rng.choice(DIAGNOSES)
                conn.execute(
                    "INSERT INTO diagnoses (diagnosis_id, visit_id, icd10_code, description) "
                    "VALUES (?, ?, ?, ?)",
                    (diagnosis_id, visit_id, code, desc),
                )

            for _ in range(rng.randint(1, 4)):
                lab_id += 1
                name, unit, ref_low, ref_high, lo, hi = rng.choice(LAB_TESTS)
                value = round(rng.uniform(lo, hi), 2)
                conn.execute(
                    "INSERT INTO lab_results "
                    "(lab_id, visit_id, test_name, value, unit, ref_low, ref_high) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (lab_id, visit_id, name, value, unit, ref_low, ref_high),
                )

    print(f"Created {n_patients} patients, {visit_id} visits, "
          f"{diagnosis_id} diagnoses, {lab_id} lab results")


if __name__ == "__main__":
    conn = sqlite3.connect(DB_PATH)
    create_schema(conn)
    populate(conn)
    conn.commit()
    conn.close()
    print(f"Database written to {DB_PATH}")
