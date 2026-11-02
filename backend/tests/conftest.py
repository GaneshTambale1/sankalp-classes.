import pytest
from werkzeug.security import generate_password_hash
from app import create_app
from app.extensions import db
from app.models import (User,Student,Teacher,AcademicClass,Batch,Subject,ClassSubject,
    TeacherAssignment,Examination,ExaminationSubject,GradeSetting)
from datetime import date

@pytest.fixture()
def app():
    app=create_app({'TESTING':True,'SQLALCHEMY_DATABASE_URI':'sqlite:///:memory:',
        'JWT_SECRET_KEY':'test-secret-string-that-is-long-enough','SECRET_KEY':'test-secret-secret-secret-secret'})
    with app.app_context():
        db.create_all()
        admin=User(email='admin@example.test',full_name='Admin',role='admin',password_hash=generate_password_hash('SecurePassword123!'))
        teacher=User(email='teacher@example.test',full_name='Teacher',role='teacher',password_hash=generate_password_hash('SecurePassword123!'))
        student=User(email='student@example.test',full_name='Student',role='student',password_hash=generate_password_hash('SecurePassword123!'))
        other=User(email='other@example.test',full_name='Other',role='student',password_hash=generate_password_hash('SecurePassword123!'))
        db.session.add_all([admin,teacher,student,other]);db.session.flush()
        cls=AcademicClass(name='Class 10');sub=Subject(name='Mathematics')
        db.session.add_all([cls,sub]);db.session.flush()
        batch=Batch(name='Morning',class_id=cls.id)
        db.session.add(batch);db.session.flush()
        t=Teacher(user_id=teacher.id,code='TCH-1001')
        s=Student(user_id=student.id,code='STU-1001',class_id=cls.id,batch_id=batch.id)
        s2=Student(user_id=other.id,code='STU-1002',class_id=cls.id,batch_id=batch.id)
        db.session.add_all([t,s,s2]);db.session.flush()
        db.session.add(ClassSubject(class_id=cls.id,subject_id=sub.id))
        db.session.add(TeacherAssignment(teacher_id=t.id,class_id=cls.id,batch_id=batch.id,subject_id=sub.id))
        exam=Examination(name='Unit Test 1',academic_year='2026-27',class_id=cls.id,batch_id=batch.id)
        db.session.add(exam);db.session.flush()
        db.session.add(ExaminationSubject(examination_id=exam.id,subject_id=sub.id,max_marks=100,passing_marks=35))
        db.session.commit()
        yield app
        db.session.remove();db.drop_all()

@pytest.fixture()
def client(app):return app.test_client()

@pytest.fixture()
def auth(client):
    def login(email):
        r=client.post('/api/v1/auth/login',json={'email':email,'password':'SecurePassword123!'})
        assert r.status_code==200,r.json
        return {'Authorization':f"Bearer {r.json['access_token']}"}
    return {'admin':login('admin@example.test'),'teacher':login('teacher@example.test'),
        'student':login('student@example.test'),'other':login('other@example.test')}
