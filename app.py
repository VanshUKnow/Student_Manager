from flask import Flask, render_template, request, redirect, url_for, flash, Response
import mysql.connector
import io
import csv

app = Flask(__name__)

db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'root1234', 
    'database': 'student_db'
}

def get_db_connection():
    try:
        conn = mysql.connector.connect(**db_config)
        return conn
    except mysql.connector.Error as err:
        print(f"Error connecting to database: {err}")
        return None

def init_db():
    """Initializes the database and table if they don't exist."""
    try:
        conn = mysql.connector.connect(
            host=db_config['host'],
            user=db_config['user'],
            password=db_config['password']
        )
        cursor = conn.cursor()
        
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_config['database']}")
        
        conn.database = db_config['database']
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS students (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                subject VARCHAR(100) NOT NULL,
                grade FLOAT NOT NULL
            )
        """)
        
        conn.commit()
        cursor.close()
        conn.close()
        print("Database initialized successfully.")
    except mysql.connector.Error as err:
        print(f"Database initialization error: {err}")

init_db()

@app.route('/')
def index():
    conn = get_db_connection()
    if not conn:
        return "Database connection failed", 500
    
    cursor = conn.cursor(dictionary=True) 
    cursor.execute("SELECT * FROM students")
    students = cursor.fetchall()
    
    total_students = len(students)
    avg_grade = 0
    if total_students > 0:
        total_grade = sum(student['grade'] for student in students)
        avg_grade = round(total_grade / total_students, 2)
    
    cursor.close()
    conn.close()
    
    return render_template('index.html', students=students, total=total_students, avg=avg_grade)

@app.route('/add', methods=('GET', 'POST'))
def add_student():
    if request.method == 'POST':
        name = request.form['name']
        subject = request.form['subject']
        grade = request.form['grade']

        if not name or not subject or not grade:
            flash('All fields are required!', 'error')
        else:
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute('INSERT INTO students (name, subject, grade) VALUES (%s, %s, %s)',
                               (name, subject, float(grade)))
                conn.commit()
                cursor.close()
                conn.close()
                flash('Student added successfully!', 'success')
                return redirect(url_for('index'))
            except mysql.connector.Error as err:
                flash(f'Error adding student: {err}', 'error')

    return render_template('edit.html') 

@app.route('/edit/<int:id>', methods=('GET', 'POST'))
def edit_student(id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    if request.method == 'POST':
        name = request.form['name']
        subject = request.form['subject']
        grade = request.form['grade']

        if not name or not subject or not grade:
            flash('All fields are required!', 'error')
        else:
            try:
                cursor.execute('UPDATE students SET name = %s, subject = %s, grade = %s WHERE id = %s',
                               (name, subject, float(grade), id))
                conn.commit()
                flash('Student details updated!', 'success')
                cursor.close()
                conn.close()
                return redirect(url_for('index'))
            except mysql.connector.Error as err:
                flash(f'Error updating student: {err}', 'error')
    
    cursor.execute('SELECT * FROM students WHERE id = %s', (id,))
    student = cursor.fetchone()
    cursor.close()
    conn.close()

    if student is None:
        flash('Student not found!', 'error')
        return redirect(url_for('index'))

    return render_template('edit.html', student=student)

@app.route('/delete/<int:id>')
def delete_student(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('DELETE FROM students WHERE id = %s', (id,))
        conn.commit()
        flash('Student record deleted.', 'success')
    except mysql.connector.Error as err:
        flash(f'Error deleting record: {err}', 'error')
    finally:
        cursor.close()
        conn.close()
    
    return redirect(url_for('index'))

@app.route('/search')
def search():
    query = request.args.get('q', '')
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    sql_query = "SELECT * FROM students WHERE name LIKE %s OR subject LIKE %s"
    search_param = f"%{query}%"
    cursor.execute(sql_query, (search_param, search_param))
    students = cursor.fetchall()
    
    total_students = len(students)
    avg_grade = 0
    if total_students > 0:
        total_grade = sum(student['grade'] for student in students)
        avg_grade = round(total_grade / total_students, 2)

    cursor.close()
    conn.close()
    
    return render_template('index.html', students=students, total=total_students, avg=avg_grade, search_query=query)

@app.route('/export')
def export_to_excel():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM students")
    students = cursor.fetchall()
    cursor.close()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow(['ID', 'Name', 'Subject', 'Grade'])
    
    for student in students:
        writer.writerow([student['id'], student['name'], student['subject'], student['grade']])
    
    output.seek(0)
    
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=students_report.csv"}
    )

if __name__ == '__main__':
    app.run(debug=True)
