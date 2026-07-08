import pandas as pd
import os
import qrcode
from flask_mail import Mail, Message
from flask import send_from_directory
from werkzeug.utils import secure_filename
from flask import send_file
from datetime import date
from flask import Flask, render_template, request, redirect, session
from flask_mysqldb import MySQL
from reportlab.platypus import SimpleDocTemplate
from reportlab.platypus import Paragraph
from reportlab.platypus import Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch

app = Flask(__name__)
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True

app.config['MAIL_USERNAME'] = 'dhanasaravanan150603@gmail.com'
app.config['MAIL_PASSWORD'] = 'abcdefghijklmnop'
mail = Mail(app)
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
QR_FOLDER = 'static/qr_codes'
app.config['QR_FOLDER'] = QR_FOLDER
app.secret_key = 'studentmanagementsecretkey'

# MySQL Configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'DG@1847'
app.config['MYSQL_DB'] = 'student_management'

mysql = MySQL(app)


# Home Page
@app.route('/')
def home():
    if 'logged_in' in session:
        return redirect('/dashboard')
    return render_template('index.html')


# Login Page
@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']

        if username == 'admin' and password == 'admin123':

            session['logged_in'] = True
            

            return redirect('/dashboard')

        return "Invalid Credentials"

    return render_template('login.html')


@app.route('/add_student', methods=['GET', 'POST'])
def add_student():

    if 'logged_in' not in session:
        return redirect('/login')

    if request.method == 'POST':

        name = request.form['name']
        email = request.form['email']
        department = request.form['department']
        year = request.form['year']

        photo = request.files['photo']

        filename = secure_filename(photo.filename)

        photo.save(
            os.path.join(
                app.config['UPLOAD_FOLDER'],
                filename
            )
        )

        # Save QR Code
        qr = qrcode.make(f"""
Name: {name}
Email: {email}
Department: {department}
Year: {year}
""")

        qr.save(
            os.path.join(
                app.config['QR_FOLDER'],
                f"{name}.png"
            )
        )

        # Insert into database
        cur = mysql.connection.cursor()

        cur.execute(
            """
            INSERT INTO students
            (name,email,department,year,photo)
            VALUES(%s,%s,%s,%s,%s)
            """,
            (name, email, department, year, filename)
        )

        mysql.connection.commit()

        # Send Email
        msg = Message(
            "Welcome to Student Management System",
            sender=app.config['MAIL_USERNAME'],
            recipients=[email]
        )

        msg.body = f"""
Hello {name},

Your student profile has been created successfully.

Name : {name}
Department : {department}
Year : {year}

Thank you.
"""

        mail.send(msg)

        cur.close()

        return redirect('/view_students')

    return render_template('add_student.html')
# View Students
@app.route('/view_students')
def view_students():

    if 'logged_in' not in session:
        return redirect('/login')

    cur = mysql.connection.cursor()

    cur.execute("SELECT * FROM students")

    students = cur.fetchall()

    cur.close()

    return render_template(
        'view_students.html',
        students=students
    )


# Update Student
@app.route('/update_student/<int:id>', methods=['GET', 'POST'])
def update_student(id):
    if 'logged_in' not in session:
       return redirect('/login')

    cur = mysql.connection.cursor()

    if request.method == 'POST':

        name = request.form['name']
        email = request.form['email']
        department = request.form['department']
        year = request.form['year']

        cur.execute(
            """
            UPDATE students
            SET name=%s, email=%s, department=%s, year=%s
            WHERE id=%s
            """,
            (name, email, department, year, id)
        )

        mysql.connection.commit()
        cur.close()

        return redirect('/view_students')

    cur.execute("SELECT * FROM students WHERE id=%s", (id,))
    student = cur.fetchone()

    cur.close()

    return render_template(
        'update_student.html',
        student=student
    )


# Delete Student
@app.route('/delete_student/<int:id>')
def delete_student(id):

    if 'logged_in' not in session:
        return redirect('/login')

    cur = mysql.connection.cursor()

    cur.execute(
        "DELETE FROM students WHERE id=%s",
        (id,)
    )

    mysql.connection.commit()
    cur.close()

    return redirect('/view_students')
@app.route('/search_student', methods=['GET', 'POST'])
def search_student():

    students = []
    if 'logged_in' not in session:
        return redirect('/login')

    if request.method == 'POST':

        keyword = request.form['keyword']

        cur = mysql.connection.cursor()

        cur.execute(
            """
            SELECT * FROM students
            WHERE name LIKE %s
            OR department LIKE %s
            """,
            ('%' + keyword + '%', '%' + keyword + '%')
        )

        students = cur.fetchall()

        cur.close()

    return render_template(
        'search_student.html',
        students=students
    )
@app.route('/logout')
def logout():

    session.pop('logged_in', None)

    return redirect('/login')
@app.route('/attendance')
def attendance():

    if 'logged_in' not in session:
        return redirect('/login')

    cur = mysql.connection.cursor()

    cur.execute("SELECT * FROM students")

    students = cur.fetchall()

    cur.close()

    return render_template(
        'attendance.html',
        students=students
    )

@app.route('/mark_attendance/<int:student_id>/<status>')
def mark_attendance(student_id, status):

    if 'logged_in' not in session:
        return redirect('/login')

    cur = mysql.connection.cursor()

    cur.execute(
        """
        INSERT INTO attendance
        (student_id, attendance_date, status)
        VALUES (%s, %s, %s)
        """,
        (student_id, date.today(), status)
    )

    mysql.connection.commit()

    cur.close()

    return redirect('/attendance')
@app.route('/view_attendance')
def view_attendance():

    if 'logged_in' not in session:
        return redirect('/login')

    cur = mysql.connection.cursor()

    cur.execute("""
        SELECT attendance.id,
               students.name,
               attendance.attendance_date,
               attendance.status
        FROM attendance
        JOIN students
        ON attendance.student_id = students.id
        ORDER BY attendance.attendance_date DESC
    """)

    records = cur.fetchall()

    cur.close()

    return render_template(
        'view_attendance.html',
        records=records
    )
@app.route('/attendance_report')
def attendance_report():

    if 'logged_in' not in session:
        return redirect('/login')

    cur = mysql.connection.cursor()

    cur.execute("""
        SELECT
            students.name,

            SUM(
                CASE
                    WHEN attendance.status='Present'
                    THEN 1
                    ELSE 0
                END
            ) AS present_days,

            COUNT(attendance.id) AS total_days

        FROM students

        LEFT JOIN attendance
        ON students.id = attendance.student_id

        GROUP BY students.id
    """)

    data = cur.fetchall()

    cur.close()

    return render_template(
        'attendance_report.html',
        data=data
    )
@app.route('/add_marks', methods=['GET', 'POST'])
def add_marks():

    if 'logged_in' not in session:
        return redirect('/login')

    cur = mysql.connection.cursor()

    if request.method == 'POST':

        student_id = request.form['student_id']
        subject = request.form['subject']
        marks = request.form['marks']

        cur.execute(
            """
            INSERT INTO marks(student_id, subject, marks)
            VALUES(%s, %s, %s)
            """,
            (student_id, subject, marks)
        )

        mysql.connection.commit()

        return redirect('/view_marks')

    cur.execute("SELECT id, name FROM students")
    students = cur.fetchall()

    cur.close()

    return render_template(
        'add_marks.html',
        students=students
    )
@app.route('/view_marks')
def view_marks():

    if 'logged_in' not in session:
        return redirect('/login')

    cur = mysql.connection.cursor()

    cur.execute("""
        SELECT
            marks.id,
            students.name,
            marks.subject,
            marks.marks
        FROM marks
        JOIN students
        ON marks.student_id = students.id
    """)

    records = cur.fetchall()

    cur.close()

    return render_template(
        'view_marks.html',
        records=records
    )
@app.route('/generate_result', methods=['GET', 'POST'])
def generate_result():

    if 'logged_in' not in session:
        return redirect('/login')

    cur = mysql.connection.cursor()

    if request.method == 'POST':

        student_id = request.form['student_id']
        semester = request.form['semester']

        # Get Average and Total Marks
        cur.execute("""
            SELECT
                SUM(marks),
                AVG(marks)
            FROM marks
            WHERE student_id=%s
        """, (student_id,))

        result = cur.fetchone()

        total_marks = result[0] if result[0] else 0
        percentage = result[1] if result[1] else 0

        # Grade Calculation
        if percentage >= 90:
            grade = "A+"
            status = "Pass"

        elif percentage >= 80:
            grade = "A"
            status = "Pass"

        elif percentage >= 70:
            grade = "B"
            status = "Pass"

        elif percentage >= 60:
            grade = "C"
            status = "Pass"

        elif percentage >= 50:
            grade = "D"
            status = "Pass"

        else:
            grade = "F"
            status = "Fail"

        cur.execute("""
            INSERT INTO results
            (
                student_id,
                semester,
                total_marks,
                percentage,
                grade,
                result_status
            )
            VALUES(%s,%s,%s,%s,%s,%s)
        """,
        (
            student_id,
            semester,
            total_marks,
            percentage,
            grade,
            status
        ))

        mysql.connection.commit()

        return redirect('/view_results')

    # Student List
    cur.execute("SELECT id,name FROM students")
    students = cur.fetchall()

    cur.close()

    return render_template(
        "generate_result.html",
        students=students
    )
@app.route('/marks_report')
def marks_report():

    if 'logged_in' not in session:
        return redirect('/login')

    cur = mysql.connection.cursor()

    cur.execute("""
        SELECT
            students.name,
            AVG(marks.marks) AS average_marks
        FROM students
        JOIN marks
        ON students.id = marks.student_id
        GROUP BY students.id
        ORDER BY average_marks DESC
    """)

    data = cur.fetchall()

    cur.close()

    return render_template(
        'marks_report.html',
        data=data
    )
@app.route('/dashboard')
def dashboard():

    if 'logged_in' not in session:
        return redirect('/login')

    cur = mysql.connection.cursor()

    # Total Students
    cur.execute("SELECT COUNT(*) FROM students")
    total_students = cur.fetchone()[0]

    # Recent Students
    cur.execute("SELECT * FROM students ORDER BY id DESC LIMIT 5")
    recent_students = cur.fetchall()

    # Department Statistics
    cur.execute("""
        SELECT department, COUNT(*)
        FROM students
        GROUP BY department
    """)

    dept_data = cur.fetchall()

    departments = [row[0] for row in dept_data]
    dept_counts = [row[1] for row in dept_data]

    cur.close()

    return render_template(
        'dashboard.html',
        total_students=total_students,
        recent_students=recent_students,
        departments=departments,
        dept_counts=dept_counts
    )
@app.route('/export_students')
def export_students():

    if 'logged_in' not in session:
        return redirect('/login')

    cur = mysql.connection.cursor()

    cur.execute("""
        SELECT
            id,
            name,
            email,
            department,
            year
        FROM students
    """)

    data = cur.fetchall()

    cur.close()

    df = pd.DataFrame(
        data,
        columns=[
            'ID',
            'Name',
            'Email',
            'Department',
            'Year'
        ]
    )

    file_name = 'students.xlsx'

    df.to_excel(
        file_name,
        index=False
    )

    return send_file(
        file_name,
        as_attachment=True
    )
@app.route('/student_profile/<int:id>')
def student_profile(id):

    if 'logged_in' not in session:
        return redirect('/login')

    cur = mysql.connection.cursor()

    # Student Details
    cur.execute(
        "SELECT * FROM students WHERE id=%s",
        (id,)
    )

    student = cur.fetchone()

    # Attendance Count
    cur.execute("""
        SELECT COUNT(*)
        FROM attendance
        WHERE student_id=%s
        AND status='Present'
    """, (id,))

    attendance_count = cur.fetchone()[0]

    # Marks Details
    cur.execute("""
        SELECT subject, marks
        FROM marks
        WHERE student_id=%s
    """, (id,))

    marks = cur.fetchall()

    # Average Marks
    cur.execute("""
        SELECT AVG(marks)
        FROM marks
        WHERE student_id=%s
    """, (id,))

    avg_marks = cur.fetchone()[0]

    cur.close()

    return render_template(
        'student_profile.html',
        student=student,
        attendance_count=attendance_count,
        marks=marks,
        avg_marks=avg_marks
    )
@app.route('/student_id/<int:id>')
def student_id(id):

    if 'logged_in' not in session:
        return redirect('/login')

    cur = mysql.connection.cursor()

    cur.execute(
        "SELECT * FROM students WHERE id=%s",
        (id,)
    )

    student = cur.fetchone()

    cur.close()

    return render_template(
        'student_id_card.html',
        student=student
    )
@app.route('/analytics')
def analytics():

    if 'logged_in' not in session:
        return redirect('/login')

    cur = mysql.connection.cursor()

    cur.execute("""
        SELECT department, COUNT(*)
        FROM students
        GROUP BY department
    """)

    result = cur.fetchall()

    departments = []
    dept_counts = []

    for row in result:
        departments.append(row[0])
        dept_counts.append(row[1])

    cur.close()

    return render_template(
        'analytics.html',
        departments=departments,
        dept_counts=dept_counts
    )
@app.route('/add_subject', methods=['GET', 'POST'])
def add_subject():

    if 'logged_in' not in session:
        return redirect('/login')

    if request.method == 'POST':

        subject_name = request.form['subject_name']
        department = request.form['department']

        cur = mysql.connection.cursor()

        cur.execute(
            """
            INSERT INTO subjects(subject_name, department)
            VALUES(%s, %s)
            """,
            (subject_name, department)
        )

        mysql.connection.commit()

        cur.close()

        return redirect('/view_subjects')

    return render_template('add_subject.html')
@app.route('/view_subjects')
def view_subjects():

    cur = mysql.connection.cursor()

    cur.execute("SELECT * FROM subjects")

    subjects = cur.fetchall()

    cur.close()

    return render_template(
        'view_subjects.html',
        subjects=subjects
    )
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
@app.route('/add_fee', methods=['GET', 'POST'])
def add_fee():

    if 'logged_in' not in session:
        return redirect('/login')

    cur = mysql.connection.cursor()

    if request.method == 'POST':

        student_id = request.form['student_id']
        total_fee = float(request.form['total_fee'])
        paid_fee = float(request.form['paid_fee'])

        balance_fee = total_fee - paid_fee

        if balance_fee == 0:
            status = "Paid"
        elif paid_fee == 0:
            status = "Pending"
        else:
            status = "Partial"

        cur.execute("""
            INSERT INTO fees
            (student_id,total_fee,paid_fee,balance_fee,status)
            VALUES(%s,%s,%s,%s,%s)
        """,(student_id,total_fee,paid_fee,balance_fee,status))

        mysql.connection.commit()

        return redirect('/view_fees')

    cur.execute("SELECT id,name FROM students")
    students = cur.fetchall()

    cur.close()

    return render_template(
        'add_fee.html',
        students=students
    )
@app.route('/view_fees')
def view_fees():

    if 'logged_in' not in session:
        return redirect('/login')

    cur = mysql.connection.cursor()

    cur.execute("""
        SELECT
            fees.id,
            students.name,
            fees.total_fee,
            fees.paid_fee,
            fees.balance_fee,
            fees.status
        FROM fees
        JOIN students
        ON fees.student_id = students.id
    """)

    records = cur.fetchall()

    cur.close()

    return render_template(
        'view_fees.html',
        records=records
    )
@app.route('/fee_receipt/<int:id>')
def fee_receipt(id):

    if 'logged_in' not in session:
        return redirect('/login')

    cur = mysql.connection.cursor()

    cur.execute("""
        SELECT
            fees.id,
            students.name,
            students.department,
            fees.total_fee,
            fees.paid_fee,
            fees.balance_fee,
            fees.status
        FROM fees
        JOIN students
        ON fees.student_id = students.id
        WHERE fees.id=%s
    """, (id,))

    receipt = cur.fetchone()

    cur.close()

    return render_template(
        'fee_receipt.html',
        receipt=receipt
    )
@app.route('/add_company', methods=['GET', 'POST'])
def add_company():

    if 'logged_in' not in session:
        return redirect('/login')

    if request.method == 'POST':

        company_name = request.form['company_name']
        job_role = request.form['job_role']
        package = request.form['package']
        eligibility_cgpa = request.form['eligibility_cgpa']
        interview_date = request.form['interview_date']

        cur = mysql.connection.cursor()

        cur.execute("""
            INSERT INTO placements
            (company_name, job_role, package, eligibility_cgpa, interview_date)
            VALUES(%s,%s,%s,%s,%s)
        """, (
            company_name,
            job_role,
            package,
            eligibility_cgpa,
            interview_date
        ))

        mysql.connection.commit()
        cur.close()

        return redirect('/view_companies')

    return render_template('add_company.html')
@app.route('/view_companies')
def view_companies():

    if 'logged_in' not in session:
        return redirect('/login')

    cur = mysql.connection.cursor()

    cur.execute("""
        SELECT *
        FROM placements
        ORDER BY interview_date ASC
    """)

    companies = cur.fetchall()

    cur.close()

    return render_template(
        'view_companies.html',
        companies=companies
    )
@app.route('/apply_placement', methods=['GET', 'POST'])
def apply_placement():

    if 'logged_in' not in session:
        return redirect('/login')

    cur = mysql.connection.cursor()

    if request.method == 'POST':

        student_id = request.form['student_id']
        company_id = request.form['company_id']
        status = request.form['status']

        cur.execute("""
            INSERT INTO placement_applications
            (student_id, company_id, status)
            VALUES(%s,%s,%s)
        """, (
            student_id,
            company_id,
            status
        ))

        mysql.connection.commit()

        return redirect('/placement_status')

    cur.execute("SELECT id,name FROM students")
    students = cur.fetchall()

    cur.execute("SELECT id,company_name FROM placements")
    companies = cur.fetchall()

    cur.close()

    return render_template(
        'apply_placement.html',
        students=students,
        companies=companies
    )
@app.route('/placement_status')
def placement_status():

    if 'logged_in' not in session:
        return redirect('/login')

    cur = mysql.connection.cursor()

    cur.execute("""
        SELECT
            placement_applications.id,
            students.name,
            placements.company_name,
            placement_applications.status

        FROM placement_applications

        JOIN students
        ON placement_applications.student_id = students.id

        JOIN placements
        ON placement_applications.company_id = placements.id
    """)

    records = cur.fetchall()

    cur.close()

    return render_template(
        'placement_status.html',
        records=records
    )
@app.route('/download_id/<int:id>')
def download_id(id):

    if 'logged_in' not in session:
        return redirect('/login')

    cur = mysql.connection.cursor()

    cur.execute(
        "SELECT * FROM students WHERE id=%s",
        (id,)
    )

    student = cur.fetchone()

    cur.close()

    pdf_name = f"ID_Card_{student[1]}.pdf"

    doc = SimpleDocTemplate(pdf_name)

    styles = getSampleStyleSheet()

    elements = []

    elements.append(
        Paragraph(
            "<b>STUDENT ID CARD</b>",
            styles['Title']
        )
    )

    elements.append(
        Paragraph(
            f"Name : {student[1]}",
            styles['Normal']
        )
    )

    elements.append(
        Paragraph(
            f"Email : {student[2]}",
            styles['Normal']
        )
    )

    elements.append(
        Paragraph(
            f"Department : {student[3]}",
            styles['Normal']
        )
    )

    elements.append(
        Paragraph(
            f"Year : {student[4]}",
            styles['Normal']
        )
    )

    doc.build(elements)

    return send_file(
        pdf_name,
        as_attachment=True
    )


if __name__ == '__main__':
    app.run(debug=True)
