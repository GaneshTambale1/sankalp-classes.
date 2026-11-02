"""Idempotent, local-only seed data for the SANKALP CLASSES application.

Usage (from backend/, with .venv activated):
    python seed_demo.py

Never run against real student data or production. Existing records are not overwritten.
"""
import getpass
import os
import sys
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import inspect
from werkzeug.security import generate_password_hash

load_dotenv(Path(__file__).resolve().parent / '.env')

from app import create_app
from app.extensions import db
from app.models import (
    AcademicClass, Attendance, AuditLog, Batch, ClassSubject, Examination,
    ExaminationSubject, GradeSetting, Mark, Setting, Student, StudentBatch,
    Subject, Teacher, TeacherAssignment, User,
)

DEMO_USERS = [
    ('admin', 'Sankalp Demo Administrator', 'demo.admin@sankalp.example', None, None),
    ('teacher', 'Anjali Kulkarni', 'demo.math@sankalp.example', 'TCH-DEMO-MATH', 'M.Sc Mathematics'),
    ('teacher', 'Priya Deshpande', 'demo.science@sankalp.example', 'TCH-DEMO-SCI', 'M.Sc Chemistry'),
    ('teacher', 'Rahul Patil', 'demo.junior@sankalp.example', 'TCH-DEMO-JR', 'M.Sc Physics'),
]

STUDENTS = [
    # full name, email, stable ID, class name, batch name, father's name, active, DOB
    ('Ganesh Tambale', 'ganeshtambale480@gmail.com', 'STU-DEMO-GANESH', 'Class 12', 'Demo Science - Morning', 'Ramesh Tambale', True, '2009-07-14'),
    ('Aarav Patil', 'demo.aarav@sankalp.example', 'STU-DEMO-AARAV', 'Class 12', 'Demo Science - Morning', 'Sanjay Patil', True, '2009-01-12'),
    ('Sneha Jadhav', 'demo.sneha@sankalp.example', 'STU-DEMO-SNEHA', 'Class 12', 'Demo Science - Morning', 'Mahesh Jadhav', True, '2009-04-05'),
    ('Vikram Pawar', 'demo.vikram@sankalp.example', 'STU-DEMO-VIKRAM', 'Class 12', 'Demo Science - Morning', 'Dinesh Pawar', True, '2008-12-18'),
    ('Riya Shinde', 'demo.riya@sankalp.example', 'STU-DEMO-RIYA', 'Class 12', 'Demo Science - Morning', 'Nitin Shinde', True, '2009-09-09'),
    ('Aditya More', 'demo.aditya@sankalp.example', 'STU-DEMO-ADITYA', 'Class 12', 'Demo Science - Evening', 'Ganesh More', True, '2009-08-15'),
    ('Pooja Kale', 'demo.pooja@sankalp.example', 'STU-DEMO-POOJA', 'Class 12', 'Demo Science - Evening', 'Suresh Kale', True, '2009-03-29'),
    ('Karan Bhosale', 'demo.karan@sankalp.example', 'STU-DEMO-KARAN', 'Class 12', 'Demo Science - Evening', 'Prakash Bhosale', False, '2008-11-30'),
    ('Neha Joshi', 'demo.neha@sankalp.example', 'STU-DEMO-NEHA', 'Class 11', 'Demo XI - Morning', 'Milind Joshi', True, '2010-01-19'),
    ('Omkar Chavan', 'demo.omkar@sankalp.example', 'STU-DEMO-OMKAR', 'Class 11', 'Demo XI - Morning', 'Pravin Chavan', True, '2010-05-11'),
]

GRADE_RANGES = [(90, 'A+'), (80, 'A'), (70, 'B+'), (60, 'B'), (50, 'C'), (35, 'D'), (0, 'F')]
SUBJECT_NAMES = ('Mathematics', 'Physics', 'Chemistry', 'Biology', 'English')


def audit(actor_id, action, entity, entity_id, details=None):
    db.session.add(AuditLog(actor_id=actor_id, action=action, entity=entity, entity_id=entity_id, details=details or {'source': 'seed_demo.py'}))


def ensure_user(role, name, email, password, create_password=True):
    obj = User.query.filter_by(email=email.lower()).first()
    if obj:
        if obj.role != role:
            raise RuntimeError(f'Email {email} already exists with role {obj.role}, not {role}. No changes committed.')
        return obj, False
    obj = User(email=email.lower(), role=role, full_name=name,
               password_hash=generate_password_hash(password), active=True)
    db.session.add(obj)
    db.session.flush()
    return obj, True


def ensure_subject(name):
    obj = Subject.query.filter_by(name=name).first()
    if not obj:
        obj = Subject(name=name, description='Demo subject')
        db.session.add(obj)
        db.session.flush()
    return obj


def ensure_class(name):
    obj = AcademicClass.query.filter_by(name=name).first()
    if not obj:
        obj = AcademicClass(name=name, description='Higher secondary academic program')
        db.session.add(obj)
        db.session.flush()
    return obj


def ensure_batch(name, cls, timing):
    obj = Batch.query.filter_by(name=name, class_id=cls.id).first()
    if not obj:
        today = date.today()
        obj = Batch(name=name, class_id=cls.id, start_date=date(2026, 6, 1),
                    end_date=date(2027, 4, 30), timings=timing)
        db.session.add(obj)
        db.session.flush()
    return obj


def ensure_teacher(user, code, qualification, actor_id):
    obj = Teacher.query.filter_by(user_id=user.id).first()
    if obj:
        return obj
    existing = Teacher.query.filter_by(code=code).first()
    if existing:
        raise RuntimeError(f'Teacher code {code} already belongs to another record.')
    obj = Teacher(code=code, user_id=user.id, qualification=qualification,
                  joining_date=date(2025, 6, 10), mobile='', address='Demo record - Maharashtra')
    db.session.add(obj)
    db.session.flush()
    audit(actor_id, 'create', 'teacher', obj.id)
    return obj


def ensure_student(record, user, classes, batches, actor_id):
    name, email, code, class_name, batch_name, father, active, dob = record
    cls = classes[class_name]
    batch = batches[(class_name, batch_name)]
    obj = Student.query.filter_by(user_id=user.id).first()
    if obj:
        if obj.class_id != cls.id or obj.batch_id != batch.id:
            raise RuntimeError(f'Existing student {email} is not assigned to {class_name} / {batch_name}. '
                               'Seed canceled to protect the existing enrollment.')
        return obj
    if Student.query.filter_by(code=code).first():
        raise RuntimeError(f'Student code {code} already belongs to another account.')
    obj = Student(code=code, user_id=user.id, class_id=cls.id, batch_id=batch.id,
                  father_name=father, mother_name='Demo Parent', gender='Male' if name in (
                      'Ganesh Tambale', 'Aarav Patil', 'Vikram Pawar', 'Aditya More', 'Karan Bhosale', 'Omkar Chavan') else 'Female',
                  dob=date.fromisoformat(dob), guardian_mobile='',
                  address='Demo address, Maharashtra', admission_date=date(2026, 6, 10))
    db.session.add(obj)
    db.session.flush()
    db.session.add(StudentBatch(student_id=obj.id, batch_id=batch.id, started_on=date(2026, 6, 10)))
    if not active:
        user.active = False
    audit(actor_id, 'create', 'student', obj.id)
    return obj


def ensure_assignment(teacher, cls, batch, subject):
    obj = TeacherAssignment.query.filter_by(teacher_id=teacher.id, batch_id=batch.id, subject_id=subject.id).first()
    if not obj:
        db.session.add(TeacherAssignment(teacher_id=teacher.id, class_id=cls.id,
                                         batch_id=batch.id, subject_id=subject.id))


def ensure_exam(name, cls, batch, start, end, subjects, published=False):
    obj = Examination.query.filter_by(name=name, academic_year='2026-27',
                                      class_id=cls.id, batch_id=batch.id).first()
    if not obj:
        obj = Examination(name=name, academic_year='2026-27', class_id=cls.id,
                          batch_id=batch.id, exam_type='Demo Test',
                          start_date=start, end_date=end,
                          description='Sample data for system testing', published=False)
        db.session.add(obj)
        db.session.flush()
    for subject in subjects:
        config = ExaminationSubject.query.filter_by(examination_id=obj.id, subject_id=subject.id).first()
        if not config:
            db.session.add(ExaminationSubject(examination_id=obj.id, subject_id=subject.id,
                                              max_marks=Decimal('100'), passing_marks=Decimal('35')))
    db.session.flush()
    return obj


def add_mark(student, exam, subject, score, updated_by):
    if Mark.query.filter_by(student_id=student.id, examination_id=exam.id, subject_id=subject.id).first():
        return False
    db.session.add(Mark(student_id=student.id, examination_id=exam.id,
                        subject_id=subject.id, obtained=Decimal(str(score)),
                        remarks='Demo assessment', updated_by=updated_by))
    audit(updated_by, 'upsert', 'marks', student.id,
          {'source': 'seed_demo.py', 'examination_id': exam.id, 'subject_id': subject.id, 'obtained': str(score)})
    return True


def add_attendance(student, batch, day, status, updated_by):
    if Attendance.query.filter_by(student_id=student.id, date=day).first():
        return False
    obj = Attendance(student_id=student.id, batch_id=batch.id, date=day,
                     status=status, updated_by=updated_by)
    db.session.add(obj)
    audit(updated_by, 'upsert', 'attendance', student.id,
          {'source': 'seed_demo.py', 'date': day.isoformat(), 'status': status})
    return True


def main():
    if os.environ.get('APP_ENV', '').lower() in ('production', 'prod'):
        sys.exit('Refusing to seed production (APP_ENV=production).')
    app = create_app()
    db_uri = app.config['SQLALCHEMY_DATABASE_URI']
    from sqlalchemy.engine import make_url
    parsed = make_url(db_uri)
    if parsed.get_backend_name() != 'sqlite' and parsed.host not in ('localhost', '127.0.0.1', '::1'):
        sys.exit('Refusing remote database. Use a LOCAL development database for demo data.')
    with app.app_context():
        tables = set(inspect(db.engine).get_table_names())
        needed = {'users', 'students', 'classes', 'batches', 'teachers', 'attendance',
                  'examinations', 'examination_subjects', 'marks'}
        if not needed.issubset(tables):
            sys.exit('Database tables missing. First run: flask db upgrade')
        print('Database:', parsed.render_as_string(hide_password=True))
        print('Demo data is only for a LOCAL test database. Existing users and records will not be overwritten.')
        password = getpass.getpass('Choose demo login password for NEW accounts (minimum 12 characters): ')
        if len(password) < 12 or password.isspace():
            sys.exit('Password must contain at least 12 nonblank characters.')
        try:
            admin, _ = ensure_user('admin', DEMO_USERS[0][1], DEMO_USERS[0][2], password)
            for minimum, grade in GRADE_RANGES:
                if not GradeSetting.query.filter_by(min_percentage=minimum).first():
                    db.session.add(GradeSetting(min_percentage=minimum, grade=grade))
            for key, value in {'institute_name': 'SANKALP CLASSES', 'academic_year': '2026-27',
                               'attendance_warning_threshold': '75', 'timezone': 'Asia/Kolkata'}.items():
                if db.session.get(Setting, key) is None:
                    db.session.add(Setting(key=key, value=value))

            classes = {name: ensure_class(name) for name in ('Class 12', 'Class 11')}
            subjects = {name: ensure_subject(name) for name in SUBJECT_NAMES}
            for cls_name in classes:
                for sub_name in SUBJECT_NAMES if cls_name == 'Class 12' else SUBJECT_NAMES[:3]:
                    if db.session.get(ClassSubject, (classes[cls_name].id, subjects[sub_name].id)) is None:
                        db.session.add(ClassSubject(class_id=classes[cls_name].id, subject_id=subjects[sub_name].id))
            batches = {}
            for cls_name, batch_name, timing in (
                ('Class 12', 'Demo Science - Morning', '07:00 AM - 10:00 AM'),
                ('Class 12', 'Demo Science - Evening', '05:00 PM - 08:00 PM'),
                ('Class 11', 'Demo XI - Morning', '10:30 AM - 12:30 PM'),
            ):
                batches[(cls_name, batch_name)] = ensure_batch(batch_name, classes[cls_name], timing)

            teachers = {}
            for role, name, email, code, qualification in DEMO_USERS[1:]:
                user, _ = ensure_user(role, name, email, password)
                teachers[email] = ensure_teacher(user, code, qualification, admin.id)
            math_teacher = teachers['demo.math@sankalp.example']
            science_teacher = teachers['demo.science@sankalp.example']
            junior_teacher = teachers['demo.junior@sankalp.example']
            for name in ('Demo Science - Morning', 'Demo Science - Evening'):
                batch = batches[('Class 12', name)]
                for subject_name in SUBJECT_NAMES:
                    chosen = math_teacher if subject_name in ('Mathematics', 'Physics') else science_teacher
                    ensure_assignment(chosen, classes['Class 12'], batch, subjects[subject_name])
            batch11 = batches[('Class 11', 'Demo XI - Morning')]
            for subject_name in SUBJECT_NAMES[:3]:
                ensure_assignment(junior_teacher, classes['Class 11'], batch11, subjects[subject_name])

            students = {}
            for record in STUDENTS:
                name, email, *_ = record
                user, _ = ensure_user('student', name, email, password)
                students[name] = ensure_student(record, user, classes, batches, admin.id)

            # Attendance: 20 recent teaching days (Mon-Sat), with present/absent/leave variation.
            today = date.today()
            days = []
            cur = today - timedelta(days=1)
            while len(days) < 20:
                if cur.weekday() < 6:
                    days.append(cur)
                cur -= timedelta(days=1)
            days.reverse()
            for name, student in students.items():
                if not student.user.active:
                    continue
                for i, when in enumerate(days):
                    if name == 'Vikram Pawar':
                        status = 'present' if i % 5 in (0, 2, 4) else 'absent'
                    elif name == 'Ganesh Tambale':
                        status = 'leave' if i in (3, 12) else 'absent' if i in (7, 15) else 'present'
                    elif name in ('Aarav Patil', 'Neha Joshi'):
                        status = 'present' if i % 10 != 4 else 'absent'
                    elif name == 'Pooja Kale':
                        status = 'leave' if i in (5, 16) else 'absent' if i in (8, 11, 13) else 'present'
                    else:
                        status = 'present' if i % 6 != 2 else 'absent'
                    add_attendance(student, db.session.get(Batch, student.batch_id), when, status, admin.id)

            cls12 = classes['Class 12']
            morning = batches[('Class 12', 'Demo Science - Morning')]
            evening = batches[('Class 12', 'Demo Science - Evening')]
            main_subs = [subjects[x] for x in SUBJECT_NAMES]
            unit = ensure_exam('DEMO - Unit Test 1 (Published)', cls12, morning,
                               today - timedelta(days=24), today - timedelta(days=23), main_subs)
            evening_exam = ensure_exam('DEMO - Monthly Test (Published)', cls12, evening,
                                       today - timedelta(days=16), today - timedelta(days=15), main_subs)
            draft = ensure_exam('DEMO - Practice Test (Unpublished)', cls12, morning,
                                today - timedelta(days=5), today - timedelta(days=4), main_subs)
            upcoming = ensure_exam('DEMO - Upcoming Test', cls12, morning,
                                   today + timedelta(days=10), today + timedelta(days=11), main_subs)
            class11_exam = ensure_exam('DEMO - Class 11 Unit Test (Published)', classes['Class 11'], batch11,
                                       today - timedelta(days=13), today - timedelta(days=12),
                                       [subjects[x] for x in SUBJECT_NAMES[:3]])
            # Scores per subject: Math, Physics, Chemistry, Biology, English.
            scores = {
                'Ganesh Tambale': (92, 88, 84, 90, 86),
                'Aarav Patil': (98, 93, 96, 91, 95),
                'Sneha Jadhav': (74, 81, 78, 83, 86),
                'Vikram Pawar': (28, 31, 40, 29, 44),
                'Riya Shinde': (66, 70, 72, 64, 75),
                'Aditya More': (89, 84, 82, 78, 88),
                'Pooja Kale': (59, 68, 71, 63, 74),
                'Neha Joshi': (91, 85, 88),
                'Omkar Chavan': (56, 62, 67),
            }
            for name, score_set in scores.items():
                student = students[name]
                exam = unit if student.batch_id == morning.id else evening_exam if student.batch_id == evening.id else class11_exam
                exam_subjects = main_subs if exam != class11_exam else [subjects[x] for x in SUBJECT_NAMES[:3]]
                for subject, score in zip(exam_subjects, score_set):
                    add_mark(student, exam, subject, score, admin.id)
            # Draft exam intentionally has incomplete marks: students must NOT see this result.
            add_mark(students['Ganesh Tambale'], draft, subjects['Mathematics'], 94, admin.id)
            add_mark(students['Ganesh Tambale'], draft, subjects['Physics'], 91, admin.id)

            db.session.flush()
            for exam in (unit, evening_exam, class11_exam):
                all_active = Student.query.join(User).filter(Student.class_id == exam.class_id,
                                                              Student.batch_id == exam.batch_id,
                                                              User.active.is_(True)).all()
                subject_ids = {x.subject_id for x in ExaminationSubject.query.filter_by(examination_id=exam.id)}
                complete = bool(all_active) and bool(subject_ids) and all(subject_ids.issubset({m.subject_id for m in Mark.query.filter_by(student_id=s.id, examination_id=exam.id)}) for s in all_active)
                if complete:
                    exam.published = True
                else:
                    print(f'WARNING: {exam.name} kept unpublished because other active students lack marks.')
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise

        print('\nDemo data loaded successfully (existing data preserved).')
        print('Ganesh Tambale: ganeshtambale480@gmail.com  |  Class 12 / Demo Science - Morning')
        print('Admin:          demo.admin@sankalp.example')
        print('Teacher (Math): demo.math@sankalp.example')
        print('Teacher (Sci):  demo.science@sankalp.example')
        print('Teacher (XI):   demo.junior@sankalp.example')
        print('Student:        demo.aarav@sankalp.example')
        print('All NEW demo accounts use the password you entered. Existing account passwords are unchanged.')
        print('Includes: 2 classes, 3 batches, 5 subjects, 3 teachers, 10 students, attendance, 5 exams, marks, PDF-ready results, audit logs.')
        print('Ganesh published result: 440/500 = 88%, grade A, PASS.')
        print('Ganesh attendance: 16 present, 2 absent, 2 leave = 88.89%.')
        print('Open http://localhost:4200 to log in.\n')


if __name__ == '__main__':
    main()
