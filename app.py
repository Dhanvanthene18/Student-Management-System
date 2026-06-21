from datetime import date
from flask import Flask, render_template, request, redirect, session
from flask_mysqldb import MySQL

app = Flask(__name__)
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
    return render_template('index.html')


# Login Page
@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']

        if username == 'admin' and password == 'admin123':

           session['logged_in'] = True
        cur = mysql.connection.cursor()

        cur.execute("SELECT COUNT(*) FROM students")

        total_students = cur.fetchone()[0]

        cur.close()

        return render_template(
         'dashboard.html',
         total_students=total_students
    )

        return "Invalid Credentials"

    return render_template('login.html')


# Add Student
@app.route('/add_student', methods=['GET', 'POST'])
def add_student():
    if 'logged_in' not in session:
      return redirect('/login')

    if request.method == 'POST':

        name = request.form['name']
        email = request.form['email']
        department = request.form['department']
        year = request.form['year']

        cur = mysql.connection.cursor()

        cur.execute(
            "INSERT INTO students(name, email, department, year) VALUES(%s, %s, %s, %s)",
            (name, email, department, year)
        )

        mysql.connection.commit()
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
from datetime import date

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
if __name__ == '__main__':
    app.run(debug=True)
