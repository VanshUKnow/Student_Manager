from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///grades.db'
app.config['SECRET_KEY'] = 'dev_secret_key_change_in_production'
db = SQLAlchemy(app)

# Database Model
class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    grade = db.Column(db.Float, nullable=False)
    
    def __repr__(self):
        return f'<Student {self.name}>'

# Create database tables
with app.app_context():
    db.create_all()

# Routes
@app.route('/')
def index():
    students = Student.query.all()
    total_students = len(students)
    avg_grade = 0
    if total_students > 0:
        avg_grade = sum([s.grade for s in students]) / total_students
    
    return render_template('index.html', students=students, total=total_students, avg=round(avg_grade, 2))

@app.route('/add', methods=['GET', 'POST'])
def add_student():
    if request.method == 'POST':
        try:
            name = request.form.get('name').strip()
            subject = request.form.get('subject').strip()
            grade = float(request.form.get('grade'))
            
            if not name or not subject:
                flash('Name and Subject are required!', 'error')
                return redirect(url_for('add_student'))
            
            if grade < 0 or grade > 100:
                flash('Grade must be between 0 and 100!', 'error')
                return redirect(url_for('add_student'))
            
            new_student = Student(name=name, subject=subject, grade=grade)
            db.session.add(new_student)
            db.session.commit()
            flash(f'Student {name} added successfully!', 'success')
            return redirect(url_for('index'))
        except ValueError:
            flash('Invalid grade value!', 'error')
    
    return render_template('edit.html', student=None)

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_student(id):
    student = Student.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            student.name = request.form.get('name').strip()
            student.subject = request.form.get('subject').strip()
            student.grade = float(request.form.get('grade'))
            
            if not student.name or not student.subject:
                flash('Name and Subject are required!', 'error')
                return redirect(url_for('edit_student', id=id))
            
            if student.grade < 0 or student.grade > 100:
                flash('Grade must be between 0 and 100!', 'error')
                return redirect(url_for('edit_student', id=id))
            
            db.session.commit()
            flash('Student updated successfully!', 'success')
            return redirect(url_for('index'))
        except ValueError:
            flash('Invalid grade value!', 'error')
    
    return render_template('edit.html', student=student)

@app.route('/delete/<int:id>')
def delete_student(id):
    student = Student.query.get_or_404(id)
    name = student.name
    db.session.delete(student)
    db.session.commit()
    flash(f'Student {name} deleted successfully!', 'success')
    return redirect(url_for('index'))

@app.route('/search')
def search():
    query = request.args.get('q', '').strip()
    if query:
        students = Student.query.filter(
            (Student.name.ilike(f'%{query}%')) | 
            (Student.subject.ilike(f'%{query}%'))
        ).all()
    else:
        students = []
    
    return render_template('index.html', students=students, search_query=query)

if __name__ == '__main__':
    app.run(debug=True)
