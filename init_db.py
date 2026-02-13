import sqlite3

conn = sqlite3.connect("database/attendance.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    roll_no TEXT UNIQUE,
    name TEXT,
    section TEXT,
    face_id TEXT,
    created_at DATE DEFAULT CURRENT_DATE
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS attendance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER,
    subject TEXT,
    date DATE,
    status TEXT,
    FOREIGN KEY (student_id) REFERENCES students(id)
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS marks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER,
    subject TEXT,
    attendance_percentage REAL,
    internal_marks INTEGER,
    FOREIGN KEY (student_id) REFERENCES students(id)
)
""")

conn.commit()
conn.close()

print("✅ Database & tables created successfully")
