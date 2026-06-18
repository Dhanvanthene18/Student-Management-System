from flask import Flask, render_template, request
from flask_mysqldb import MySQL

app = Flask(__name__)

# MySQL Configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'DG@1847'
app.config['MYSQL_DB'] = 'student_management'

mysql = MySQL(app)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']

        if username == 'admin' and password == 'admin123':
            return render_template('dashboard.html')

        return "Invalid Credentials"

    return render_template('login.html')
@app.route('/add_student', methods=['GET', 'POST'])
def add_student():

    if request.method == 'POST':

        name = request.form['name']
        email = request.form['email']
        department = request.form['department']
        year = request.form['year']

        cur = mysql.connection.cursor()

        cur.execute(
            "INSERT INTO students(name,email,department,year) VALUES(%s,%s,%s,%s)",
            (name, email, department, year)
        )

        mysql.connection.commit()
        cur.close()

        from flask import redirect

        return redirect('/view_students')
        return render_template('add_student.html')
@app.route('/view_students')
def view_students():

    cur = mysql.connection.cursor()

    cur.execute("SELECT * FROM students")

    students = cur.fetchall()

    cur.close()

    return render_template(
        'view_students.html',
        students=students
    )
@app.route('/delete_student/<int:id>')
def delete_student(id):

    cur = mysql.connection.cursor()

    cur.execute(
        "DELETE FROM students WHERE id=%s",
        (id,)
    )

    mysql.connection.commit()
    cur.close()

    return "Student Deleted Successfully"

if __name__ == '__main__':
    app.run(debug=True)
@app.route('/delete_student/<int:id>')
def delete_student(id):

    cur = mysql.connection.cursor()

    cur.execute("DELETE FROM students WHERE id=%s", (id,))

    mysql.connection.commit()

    cur.close()

    return redirect('/view_students')
