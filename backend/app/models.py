from datetime import datetime, timezone
from sqlalchemy import UniqueConstraint, Index
from sqlalchemy.orm import validates
from .extensions import db


def now():
    return datetime.now(timezone.utc)


class Timed:
    created_at = db.Column(db.DateTime(timezone=True), default=now, nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), default=now, onupdate=now, nullable=False)


class User(db.Model, Timed):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(20), nullable=False, index=True)
    active = db.Column(db.Boolean, default=True, nullable=False)
    __table_args__ = (db.CheckConstraint("role IN ('admin','teacher','student')", name='ck_user_role'),)


class AcademicClass(db.Model, Timed):
    __tablename__ = 'classes'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    description = db.Column(db.Text, default='')
    active = db.Column(db.Boolean, default=True, nullable=False)


class Batch(db.Model, Timed):
    __tablename__ = 'batches'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'), nullable=False, index=True)
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    timings = db.Column(db.String(100), default='')
    active = db.Column(db.Boolean, default=True, nullable=False)
    __table_args__ = (UniqueConstraint('name', 'class_id', name='uq_batch_class'),)


class Teacher(db.Model, Timed):
    __tablename__ = 'teachers'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(25), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    mobile = db.Column(db.String(20), default='')
    address = db.Column(db.Text, default='')
    qualification = db.Column(db.String(150), default='')
    joining_date = db.Column(db.Date)
    user = db.relationship('User')


class Student(db.Model, Timed):
    __tablename__ = 'students'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(25), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'), nullable=False, index=True)
    batch_id = db.Column(db.Integer, db.ForeignKey('batches.id'), nullable=False, index=True)
    father_name = db.Column(db.String(150), default='')
    mother_name = db.Column(db.String(150), default='')
    gender = db.Column(db.String(20), default='')
    dob = db.Column(db.Date)
    mobile = db.Column(db.String(20), default='')
    guardian_mobile = db.Column(db.String(20), default='')
    address = db.Column(db.Text, default='')
    admission_date = db.Column(db.Date)
    user = db.relationship('User')


class StudentBatch(db.Model):
    __tablename__ = 'student_batches'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False, index=True)
    batch_id = db.Column(db.Integer, db.ForeignKey('batches.id'), nullable=False)
    started_on = db.Column(db.Date, nullable=False)
    ended_on = db.Column(db.Date)
    __table_args__ = (UniqueConstraint('student_id','batch_id','started_on', name='uq_enrollment'),)


class Subject(db.Model, Timed):
    __tablename__ = 'subjects'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text, default='')
    active = db.Column(db.Boolean, default=True, nullable=False)


class ClassSubject(db.Model):
    __tablename__ = 'class_subjects'
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'), primary_key=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), primary_key=True)


class TeacherAssignment(db.Model):
    __tablename__ = 'teacher_assignments'
    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id'), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'), nullable=False)
    batch_id = db.Column(db.Integer, db.ForeignKey('batches.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    __table_args__ = (UniqueConstraint('teacher_id','batch_id','subject_id', name='uq_teacher_subject_batch'),)


class Attendance(db.Model, Timed):
    __tablename__ = 'attendance'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False, index=True)
    batch_id = db.Column(db.Integer, db.ForeignKey('batches.id'), nullable=False)
    date = db.Column(db.Date, nullable=False, index=True)
    status = db.Column(db.String(12), nullable=False)
    updated_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    __table_args__ = (UniqueConstraint('student_id','date', name='uq_student_attendance_day'), db.CheckConstraint("status IN ('present','absent','leave')",name='ck_attendance_status'))


class Examination(db.Model, Timed):
    __tablename__ = 'examinations'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    academic_year = db.Column(db.String(12), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'), nullable=False)
    batch_id = db.Column(db.Integer, db.ForeignKey('batches.id'))
    exam_type = db.Column(db.String(60), default='Test')
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    description = db.Column(db.Text, default='')
    published = db.Column(db.Boolean, default=False, nullable=False)


class ExaminationSubject(db.Model):
    __tablename__ = 'examination_subjects'
    id = db.Column(db.Integer, primary_key=True)
    examination_id = db.Column(db.Integer, db.ForeignKey('examinations.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    max_marks = db.Column(db.Numeric(8, 2), nullable=False)
    passing_marks = db.Column(db.Numeric(8, 2), nullable=False)
    __table_args__ = (UniqueConstraint('examination_id','subject_id', name='uq_exam_subject'),db.CheckConstraint('max_marks > 0 AND passing_marks >= 0 AND passing_marks <= max_marks',name='ck_exam_mark_limits'))


class Mark(db.Model, Timed):
    __tablename__ = 'marks'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False, index=True)
    examination_id = db.Column(db.Integer, db.ForeignKey('examinations.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    obtained = db.Column(db.Numeric(8,2), nullable=False)
    remarks = db.Column(db.Text, default='')
    updated_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    __table_args__ = (UniqueConstraint('student_id','examination_id','subject_id',name='uq_student_exam_subject'),db.CheckConstraint('obtained >= 0',name='ck_nonnegative_marks'))


class GradeSetting(db.Model):
    __tablename__ = 'grade_settings'
    id = db.Column(db.Integer, primary_key=True)
    min_percentage = db.Column(db.Integer, unique=True, nullable=False)
    grade = db.Column(db.String(5), nullable=False)


class Setting(db.Model):
    __tablename__ = 'settings'
    key = db.Column(db.String(100), primary_key=True)
    value = db.Column(db.Text, nullable=False)


class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    id = db.Column(db.Integer, primary_key=True)
    actor_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    action = db.Column(db.String(50), nullable=False)
    entity = db.Column(db.String(80), nullable=False)
    entity_id = db.Column(db.Integer)
    details = db.Column(db.JSON, nullable=False, default=dict)
    created_at = db.Column(db.DateTime(timezone=True), default=now, nullable=False)


class TokenBlocklist(db.Model):
    __tablename__ = 'token_blocklist'
    jti = db.Column(db.String(40), primary_key=True)
    created_at = db.Column(db.DateTime(timezone=True), default=now)


class PasswordReset(db.Model):
    __tablename__ = 'password_resets'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    token_hash = db.Column(db.String(64), unique=True, nullable=False)
    expires_at = db.Column(db.DateTime(timezone=True), nullable=False)
    used = db.Column(db.Boolean, nullable=False, default=False)
