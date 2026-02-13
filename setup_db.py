from app.utils.db import get_db_connection

conn = get_db_connection()
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS marking_periods (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    start_date TEXT NOT NULL,
    end_date TEXT NOT NULL,
    max_marks INTEGER NOT NULL
)
""")

cursor.execute("""
INSERT INTO marking_periods (start_date, end_date, max_marks)
VALUES ('2026-01-01', '2026-01-15', 40)
""")

conn.commit()
conn.close()

print("marking_periods table created successfully ✅")
