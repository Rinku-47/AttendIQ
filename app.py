from flask import Flask, jsonify, render_template, request, redirect, session, flash, send_file
from datetime import date
import sqlite3
import io
from openpyxl import Workbook
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import pagesizes

from app.services.face_services import capture_faces
from app.services.recognition_service import recognize_face
from app.services.attendance_service import mark_attendance
from app.utils.db import get_db_connection

app = Flask(__name__,
            template_folder="app/templates",
            static_folder="app/static")

app.secret_key = "smart-attendance-secret"

# ================= HOME =================

@app.route("/")
def home():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM students")
    total_students = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM attendance")
    total_records = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM attendance WHERE status='Present'")
    total_present = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(DISTINCT date) FROM attendance")
    total_days = cursor.fetchone()[0] or 1

    avg_attendance = round((total_present / (total_students * total_days)) * 100, 2) \
        if total_students and total_days else 0

    today = date.today().isoformat()
    cursor.execute("SELECT COUNT(*) FROM attendance WHERE date=? AND status='Present'", (today,))
    present_today = cursor.fetchone()[0]

    cursor.execute("SELECT section, COUNT(*) as count FROM students GROUP BY section")
    sections = cursor.fetchall()

    conn.close()

    return render_template("dashboard.html",
                           total_students=total_students,
                           total_records=total_records,
                           present_today=present_today,
                           avg_attendance=avg_attendance,
                           sections=sections)


@app.route("/dashboard")
def dashboard():
    return redirect("/")


# ================= ADMIN =================

@app.route("/admin")
def admin_dashboard():
    if not session.get("admin_logged_in"):
        return redirect("/login")

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, roll_no, name, section FROM students ORDER BY roll_no")
    students = cursor.fetchall()
    conn.close()

    return render_template("admin_dashboard.html", students=students)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form["username"] == "admin" and request.form["password"] == "admin123":
            session["admin_logged_in"] = True
            return redirect("/admin")
        return render_template("login.html", error="Invalid credentials")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# ================= STUDENTS =================

@app.route("/register-student", methods=["POST"])
def register_student():
    if not session.get("admin_logged_in"):
        return redirect("/login")

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO students (roll_no, name, section, face_id)
            VALUES (?, ?, ?, ?)
        """, (request.form["roll_no"],
              request.form["name"],
              request.form["section"],
              request.form["roll_no"]))
        conn.commit()
        conn.close()

        flash("Student registered successfully!", "success")
    except sqlite3.IntegrityError:
        flash("Roll number already exists!", "error")

    return redirect("/admin")


@app.route("/delete-student/<int:student_id>")
def delete_student(student_id):
    if not session.get("admin_logged_in"):
        return redirect("/login")

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM attendance WHERE student_id=?", (student_id,))
    cursor.execute("DELETE FROM students WHERE id=?", (student_id,))
    conn.commit()
    conn.close()

    flash("Student deleted successfully!", "success")
    return redirect("/admin")


@app.route("/register-face/<roll_no>")
def register_face(roll_no):
    capture_faces(roll_no)
    return redirect("/admin")


# ================= ATTENDANCE =================

@app.route("/take-attendance")
def take_attendance():
    if not session.get("admin_logged_in"):
        return redirect("/login")

    try:
        recognized = recognize_face()
        mark_attendance(recognized)
        flash("Attendance marked successfully!", "success")
    except Exception:
        flash("Camera error or recognition failed!", "error")

    return redirect("/admin")


@app.route("/attendance-page")
def attendance_page():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT s.roll_no, s.name, a.date, a.status
        FROM attendance a
        JOIN students s ON a.student_id = s.id
        ORDER BY a.date DESC
    """)
    data = cursor.fetchall()
    conn.close()

    return render_template("attendance.html", attendance_data=data)


# ================= MARKS =================

@app.route("/marks")
def marks_page():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, roll_no, name FROM students")
    students = cursor.fetchall()

    BASE_DAYS = 15
    MAX_MARKS = 80
    results = []

    for student in students:
        cursor.execute("""
            SELECT COUNT(*) FROM attendance
            WHERE student_id=? AND status='Present'
        """, (student["id"],))
        present = cursor.fetchone()[0]

        marks = min(round((present / BASE_DAYS) * MAX_MARKS, 2), MAX_MARKS)

        results.append({
            "roll_no": student["roll_no"],
            "name": student["name"],
            "periods": [{
                "range": "Overall Attendance",
                "present_days": present,
                "marks": marks,
                "max_marks": MAX_MARKS
            }],
            "total_marks": marks
        })

    conn.close()
    return render_template("marks.html", students=results)


# ================= REPORTS =================

@app.route("/reports")
def reports():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM students")
    total_students = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(DISTINCT date) FROM attendance")
    total_days = cursor.fetchone()[0] or 1

    cursor.execute("SELECT COUNT(*) FROM attendance WHERE status='Present'")
    total_present = cursor.fetchone()[0]

    overall_attendance = round(
        (total_present / (total_students * total_days)) * 100, 2
    ) if total_students and total_days else 0

    cursor.execute("SELECT id, roll_no, name, section FROM students")
    students = cursor.fetchall()

    BASE_DAYS = 15
    MAX_MARKS = 80

    student_reports = []

    for student in students:
        cursor.execute("""
            SELECT COUNT(*) FROM attendance
            WHERE student_id = ? AND status='Present'
        """, (student["id"],))

        present_days = cursor.fetchone()[0]

        attendance_percent = round(
            (present_days / total_days) * 100, 2
        ) if total_days else 0

        marks = min(round((present_days / BASE_DAYS) * MAX_MARKS, 2), MAX_MARKS)

        status = "Good"
        if attendance_percent < 75:
            status = "Warning"
        if attendance_percent < 50:
            status = "Critical"

        student_reports.append({
            "roll_no": student["roll_no"],
            "name": student["name"],
            "section": student["section"],
            "present_days": present_days,
            "attendance_percent": attendance_percent,
            "marks": marks,
            "status": status
        })

    cursor.execute("""
        SELECT section, COUNT(*) as total
        FROM students
        GROUP BY section
    """)
    sections = cursor.fetchall()

    section_reports = []

    for sec in sections:
        cursor.execute("""
            SELECT COUNT(*) FROM attendance a
            JOIN students s ON a.student_id = s.id
            WHERE s.section = ? AND a.status='Present'
        """, (sec["section"],))

        section_present = cursor.fetchone()[0]

        section_total_possible = sec["total"] * total_days

        section_attendance = round(
            (section_present / section_total_possible) * 100, 2
        ) if section_total_possible else 0

        section_reports.append({
            "section": sec["section"],
            "total_students": sec["total"],
            "attendance_percent": section_attendance
        })

    conn.close()

    return render_template(
        "reports.html",
        total_students=total_students,
        total_days=total_days,
        overall_attendance=overall_attendance,
        student_reports=student_reports,
        section_reports=section_reports
    )


@app.route("/students-page")
def students_page():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT roll_no, name, section
        FROM students
        ORDER BY roll_no
    """)
    students = cursor.fetchall()

    conn.close()

    return render_template("students.html", students=students)

if __name__ == "__main__":
    app.run()
