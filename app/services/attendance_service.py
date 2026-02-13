from datetime import date
from app.utils.db import get_db_connection

def mark_attendance(roll_nos, subject="DSA"):
    today = date.today()

    conn = get_db_connection()
    cursor = conn.cursor()

    for roll_no in roll_nos:
        student = cursor.execute(
            "SELECT id FROM students WHERE roll_no = ?",
            (roll_no,)
        ).fetchone()

        if student:
            cursor.execute("""
                INSERT INTO attendance (student_id, subject, date, status)
                VALUES (?, ?, ?, ?)
            """, (student["id"], subject, today, "Present"))

    conn.commit()
    conn.close()
