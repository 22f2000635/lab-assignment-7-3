<!DOCTYPE html>
from flask import Flask, request, redirect, render_template_string

from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///week7 database.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Models
class Student(db.Model):
    __tablename__ = 'student'
    student_id = db.Column(db.Integer, primary_key=True)
    roll_number = db.Column(db.String, unique=True, nullable=False)
    first_name = db.Column(db.String, nullable=False)
    last_name = db.Column(db.String)

class Course(db.Model):
    __tablename__ = 'course'
    course_id = db.Column(db.Integer, primary_key=True)
    course_code = db.Column(db.String, unique=True, nullable=False)
    course_name = db.Column(db.String, nullable=False)
    course_description = db.Column(db.String)

class Enrollments(db.Model):
    __tablename__ = 'enrollments'
    enrollment_id = db.Column(db.Integer, primary_key=True)
    estudent_id = db.Column(db.Integer, db.ForeignKey('student.student_id'), nullable=False)
    ecourse_id = db.Column(db.Integer, db.ForeignKey('course.course_id'), nullable=False)

# Helpers HTML wrappers
def base_html(title, body):
    return f"""<!DOCTYPE html>
<html>
<head><title>{title}</title></head>
<body>
{body}
</body>
</html>"""

@app.route('/')
def index():
    students = Student.query.all()
    rows = ""
    for idx, s in enumerate(students, 1):
        rows += f"""
        <tr>
        <td>{idx}</td>
        <td><a href="/student/{s.student_id}">{s.roll_number}</a></td>
        <td>{s.first_name}</td>
        <td>{s.last_name}</td>
        <td>
        <a href="/student/{s.student_id}/update">Update</a>
        <a href="/student/{s.student_id}/delete">Delete</a>
        </td>
        </tr>"""
    if not students:
        table_content = "<p>No students found. Add the students now!</p>"
    else:
        table_content = ""

    html = f"""
    <h1>Students list</h1>
    <a href="/courses" style="float:right">Go to Courses</a>
    <br>
    {table_content}
    <table id="all-students">
    <tr>
    <th>SNo</th>
    <th>Roll Number</th>
    <th>First Name</th>
    <th>Last Name</th>
    <th>Actions</th>
    </tr>
    {rows}
    </table>
    <a href="/student/create">+ Add Student</a>
    """
    return base_html("Home", html)

# ----- Student Create -----
@app.route('/student/create', methods=['GET','POST'])
def student_create():
    if request.method == 'GET':
        html = """
        <h1>Add a Student</h1>
        <form action="/student/create" method="POST" id="create-student-form">
        <div>
        <label>Roll Number:</label>
        <input type="text" name="roll" required />
        </div>
        <div>
        <label>First Name:</label>
        <input type="text" name="f_name" required />
        </div>
        <div>
        <label>Last Name:</label>
        <input type="text" name="l_name" />
        </div>
        <div>
        <input type="submit" value = "Submit">
        </div>
        </form>
        """
        return base_html("Add Student", html)
    else:
        roll = request.form.get('roll','').strip()
        f_name = request.form.get('f_name','').strip()
        l_name = request.form.get('l_name','').strip()
        existing = Student.query.filter_by(roll_number=roll).first()
        if existing:
            html = """
            <p>Student already exists. Please use different Roll Number !!</p>
            <a href="/">Go Home</a>
            """
            return base_html("Error", html)
        new_s = Student(roll_number=roll, first_name=f_name, last_name=l_name)
        db.session.add(new_s)
        db.session.commit()
        return redirect('/')

@app.route('/student/<int:student_id>/update', methods=['GET','POST'])
def student_update(student_id):
    student = Student.query.get_or_404(student_id)
    courses = Course.query.all()
    if request.method == 'GET':
        options = ""
        for c in courses:
            options += f'<option value="{c.course_id}">{c.course_name}</option>\n'
        html = f"""
        <h1>Update Student</h1>
        <form action="/student/{student_id}/update" method="POST" id="update-student-form">
        <div>
        <label>Roll Number:</label>
        <input type="text" name="roll" value="{student.roll_number}" disabled />
        </div>
        <div>
        <label>First Name:</label>
        <input type="text" name="f_name" value="{student.first_name}" required />
        </div>
        <div>
        <label>Last Name:</label>
        <input type="text" name="l_name" value="{student.last_name or ''}"/>
        </div>
        <div>
        <label for="courses">Select Course: </label>
        <select name="course" id="course">
        {options}
        </select>
        </div>
        <div>
        <input type="submit" value = "Update">
        </div>
        </form>
        """
        return base_html("Update Student", html)
    else:
        f_name = request.form.get('f_name','').strip()
        l_name = request.form.get('l_name','').strip()
        course_id = request.form.get('course')
        student.first_name = f_name
        student.last_name = l_name
        # handle enrollment
        if course_id:
            try:
                cid = int(course_id)
                # check if already enrolled
                exists = Enrollments.query.filter_by(estudent_id=student_id, ecourse_id=cid).first()
                if not exists:
                    en = Enrollments(estudent_id=student_id, ecourse_id=cid)
                    db.session.add(en)
            except:
                pass
        db.session.commit()
        return redirect('/')

@app.route('/student/<int:student_id>/delete')
def student_delete(student_id):
    Enrollments.query.filter_by(estudent_id=student_id).delete()
    Student.query.filter_by(student_id=student_id).delete()
    db.session.commit()
    return redirect('/')

@app.route('/student/<int:student_id>')
def student_detail(student_id):
    student = Student.query.get_or_404(student_id)
    enrolls = Enrollments.query.filter_by(estudent_id=student_id).all()
    # build enrollment rows
    enroll_rows = ""
    course_data = []
    for idx, en in enumerate(enrolls, 1):
        course = Course.query.get(en.ecourse_id)
        if course:
            course_data.append((idx, course, en))
    # tables
    detail_table = f"""
    <table id="student-detail">
    <thead>
    <tr>
    <th>Roll Number</th>
    <th>First Name</th>
    <th>Last Name</th>
    </tr>
    </thead>
    <tbody>
    <tr>
    <td>{student.roll_number}</td>
    <td>{student.first_name}</td>
    <td>{student.last_name}</td>
    </tr>
    </tbody>
    </table>
    """
    enrollment_table = ""
    if course_data:
        rows = ""
        for idx, course, en in course_data:
            rows += f"""
            <tr>
            <td>{idx}</td>
            <td>{course.course_code}</td>
            <td>{course.course_name}</td>
            <td>{course.course_description or ''}</td>
            <td>
            <a href="/student/{student_id}/withdraw/{course.course_id}">Withdraw</a>
            </td>
            </tr>"""
        enrollment_table = f"""
        <h2>Enrollment list</h2>
        <table id="student-enrollments">
        <thead>
        <tr>
        <th>SNo</th>
        <th>Course Code</th>
        <th>Course Name</th>
        <th>Course Description</th>
        <th>Actions</th>
        </tr>
        </thead>
        <tbody>
        {rows}
        </tbody>
        </table>
        """
    html = f"""
    <h1>Student Details</h1>
    {detail_table}
    {enrollment_table}
    <br>
    <a href="/">Go Back</a>
    """
    return base_html("Student Details", html)

@app.route('/student/<int:student_id>/withdraw/<int:course_id>')
def withdraw(student_id, course_id):
    Enrollments.query.filter_by(estudent_id=student_id, ecourse_id=course_id).delete()
    db.session.commit()
    return redirect('/')

# ----- Courses -----
@app.route('/courses')
def courses_list():
    courses = Course.query.all()
    rows = ""
    for idx, c in enumerate(courses, 1):
        rows += f"""
        <tr>
        <td>{idx}</td>
        <td><a href="/course/{c.course_id}">{c.course_code}</a></td>
        <td>{c.course_name}</td>
        <td>{c.course_description or ''}</td>
        <td>
        <a href="/course/{c.course_id}/update">Update</a>
        <a href="/course/{c.course_id}/delete">Delete</a>
        </td>
        </tr>"""
    msg = ""
    if not courses:
        msg = "<p>No courses found. Add the courses now!</p>"
    html = f"""
    <h1>Courses list</h1>
    <a href="/" style="float:right">Go to Students</a>
    <br>
    {msg}
    <table id="all-courses">
    <tr>
    <th>SNo</th>
    <th>Course Code</th>
    <th>Course Name</th>
    <th>Course Description</th>
    <th>Actions</th>
    </tr>
    {rows}
    </table>
    <a href="/course/create">+ Add Course</a>
    """
    return base_html("Courses", html)

@app.route('/course/create', methods=['GET','POST'])
def course_create():
    if request.method == 'GET':
        html = """
        <h1>Add a Course</h1>
        <form action="/course/create" method="POST" id="create-course-form">
        <div>
        <label>Course Code:</label>
        <input type="text" name="code" required />
        </div>
        <div>
        <label>Course Name:</label>
        <input type="text" name="c_name" required />
        </div>
        <div>
        <label>Course Description:</label>
        <input type="text" name="desc" />
        </div>
        <div>
        <input type="submit" value = "Submit">
        </div>
        </form>
        """
        return base_html("Add Course", html)
    else:
        code = request.form.get('code','').strip()
        c_name = request.form.get('c_name','').strip()
        desc = request.form.get('desc','').strip()
        existing = Course.query.filter_by(course_code=code).first()
        if existing:
            html = """
            <p>Course already exists. Please create a different course !!</p>
            <a href="/courses">Go Home</a>
            """
            return base_html("Error", html)
        new_c = Course(course_code=code, course_name=c_name, course_description=desc)
        db.session.add(new_c)
        db.session.commit()
        return redirect('/courses')

@app.route('/course/<int:course_id>/update', methods=['GET','POST'])
def course_update(course_id):
    course = Course.query.get_or_404(course_id)
    if request.method == 'GET':
        html = f"""
        <h1>Update Course</h1>
        <form action="/course/{course_id}/update" method="POST" id="update-course-form">
        <div>
        <label>Course Code:</label>
        <input type="text" name="code" value="{course.course_code}" disabled />
        </div>
        <div>
        <label>Course Name:</label>
        <input type="text" name="c_name" value="{course.course_name}" required />
        </div>
        <div>
        <label>Course Description:</label>
        <input type="text" name="desc" value="{course.course_description or ''}"/>
        </div>
        <div>
        <input type="submit" value = "Submit">
        </div>
        </form>
        """
        return base_html("Update Course", html)
    else:
        c_name = request.form.get('c_name','').strip()
        desc = request.form.get('desc','').strip()
        course.course_name = c_name
        course.course_description = desc
        db.session.commit()
        return redirect('/courses')

@app.route('/course/<int:course_id>/delete')
def course_delete(course_id):
    Enrollments.query.filter_by(ecourse_id=course_id).delete()
    Course.query.filter_by(course_id=course_id).delete()
    db.session.commit()
    return redirect('/')

@app.route('/course/<int:course_id>')
def course_detail(course_id):
    course = Course.query.get_or_404(course_id)
    enrolls = Enrollments.query.filter_by(ecourse_id=course_id).all()
    # course detail table
    detail_table = f"""
    <table id="course-detail">
    <thead>
    <tr>
    <th>Course Code</th>
    <th>Course Name</th>
    <th>Course Description</th>
    </tr>
    </thead>
    <tbody>
    <tr>
    <td>{course.course_code}</td>
    <td>{course.course_name}</td>
    <td>{course.course_description or ''}</td>
    </tr>
    </tbody>
    </table>
    """
    rows = ""
    for idx, en in enumerate(enrolls, 1):
        student = Student.query.get(en.estudent_id)
        if student:
            rows += f"""
            <tr>
            <td>{idx}</td>
            <td>{student.roll_number}</td>
            <td>{student.first_name}</td>
            <td>{student.last_name}</td>
            </tr>"""
    enrollment_table = f"""
    <h2>Enrollment list</h2>
    <table id="course-table">
    <thead>
    <tr>
    <th>SNo</th>
    <th>Roll Number</th>
    <th>Student First Name</th>
    <th>Student Last Name</th>
    </tr>
    </thead>
    <tbody>
    {rows}
    </tbody>
    </table>
    """
    html = f"""
    <h1>Course Details</h1>
    {detail_table}
    {enrollment_table}
    <br>
    <a href="/courses">Go Back</a>
    """
    return base_html("Course Details", html)

if __name__ == '__main__':
    app.run(debug=True)
