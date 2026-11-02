import csv
import hashlib
import io
import os
import re
import secrets
import smtplib
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from email.message import EmailMessage
from functools import wraps
from zoneinfo import ZoneInfo
from flask import Blueprint, jsonify, request, Response, current_app, send_file
from flask_jwt_extended import create_access_token, get_jwt, get_jwt_identity, jwt_required
from sqlalchemy import func, or_, and_
from sqlalchemy.exc import IntegrityError
from werkzeug.security import check_password_hash, generate_password_hash
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from .extensions import db, limiter
from .models import (User, AcademicClass, Batch, Teacher, Student, StudentBatch, Subject,
    ClassSubject, TeacherAssignment, Attendance, Examination, ExaminationSubject,
    Mark, GradeSetting, Setting, AuditLog, TokenBlocklist, PasswordReset)

api=Blueprint('api', __name__)


def error(message, status=400):
    return jsonify(error=message),status


def body():
    data=request.get_json(silent=True)
    if not isinstance(data,dict): raise ValueError('A JSON object is required')
    return data


def require_keys(data,*keys):
    for key in keys:
        if data.get(key) is None or (isinstance(data.get(key),str) and not data[key].strip()):
            raise ValueError(f'{key} is required')


def number(value, name='value'):
    try:
        v=Decimal(str(value))
        if not v.is_finite():raise ValueError()
        return v
    except (InvalidOperation,ValueError,TypeError):raise ValueError(f'Invalid {name}')


def day(value):
    if not value:return None
    try: return date.fromisoformat(value)
    except (TypeError, ValueError):raise ValueError('Date must be YYYY-MM-DD')


def integer(value,name='id'):
    try:
        n=int(value)
        if n<1:raise ValueError()
        return n
    except (ValueError,TypeError):raise ValueError(f'Invalid {name}')


def parse_bool(value):
    if not isinstance(value,bool):raise ValueError('Expected a true/false value')
    return value


def serialize(obj):
    result={}
    for column in obj.__table__.columns:
        value=getattr(obj,column.name)
        if column.name in ('password_hash','token_hash'):continue
        if isinstance(value,(date,datetime)):value=value.isoformat()
        if isinstance(value,Decimal):value=float(value)
        result[column.name]=value
    if isinstance(obj,(Teacher,Student)):
        result.update(email=obj.user.email,full_name=obj.user.full_name,active=obj.user.active)
    return result


def actor():
    return db.session.get(User,int(get_jwt_identity()))


def roles(*allowed):
    def decorator(fn):
        @wraps(fn)
        @jwt_required()
        def wrapper(*args,**kwargs):
            user=actor()
            if not user or not user.active:return error('Account disabled or unavailable',403)
            if user.role not in allowed:return error('Permission denied',403)
            return fn(*args,**kwargs)
        return wrapper
    return decorator


def log(action,entity,entity_id=None,details=None):
    db.session.add(AuditLog(actor_id=int(get_jwt_identity()),action=action,entity=entity,entity_id=entity_id,details=details or {}))


def teacher_id():
    teacher=Teacher.query.filter_by(user_id=actor().id).first()
    return teacher.id if teacher else -1


def can_teach(batch_id,subject_id=None):
    if actor().role=='admin':return True
    q=TeacherAssignment.query.filter_by(teacher_id=teacher_id(),batch_id=batch_id)
    if subject_id is not None:q=q.filter_by(subject_id=subject_id)
    return db.session.query(q.exists()).scalar()


def is_student(student_id):
    return Student.query.filter_by(id=student_id,user_id=actor().id).first() is not None


def local_today():
    configured=db.session.get(Setting,'timezone')
    try:return datetime.now(ZoneInfo(configured.value if configured else 'Asia/Kolkata')).date()
    except (ValueError,KeyError):return date.today()


def attendance_summary(student_id):
    counts=dict(db.session.query(Attendance.status,func.count(Attendance.id)).filter(Attendance.student_id==student_id).group_by(Attendance.status).all())
    present=counts.get('present',0); absent=counts.get('absent',0); leave=counts.get('leave',0)
    denominator=present+absent
    return dict(present=present,absent=absent,leave=leave,applicable_days=denominator,percentage=round(present*100/denominator,2) if denominator else 0)


def grade(percent):
    entry=GradeSetting.query.filter(GradeSetting.min_percentage<=percent).order_by(GradeSetting.min_percentage.desc()).first()
    if entry:return entry.grade
    for bound,value in [(90,'A+'),(80,'A'),(70,'B+'),(60,'B'),(50,'C'),(35,'D')]:
        if percent>=bound:return value
    return 'F'


def result_for(student,exam):
    entries=ExaminationSubject.query.filter_by(examination_id=exam.id).order_by(ExaminationSubject.subject_id).all()
    scores={m.subject_id:m for m in Mark.query.filter_by(student_id=student.id,examination_id=exam.id).all()}
    subjects=[];total=Decimal('0');maximum=Decimal('0');passed=True
    for entry in entries:
        m=scores.get(entry.subject_id)
        if not m:passed=False
        value=m.obtained if m else None
        percentage=float(value*100/entry.max_marks) if value is not None else None
        s=db.session.get(Subject,entry.subject_id)
        subjects.append(dict(subject=s.name if s else str(entry.subject_id),subject_id=entry.subject_id,
            obtained=float(value) if value is not None else None,max_marks=float(entry.max_marks),
            passing_marks=float(entry.passing_marks),percentage=round(percentage,2) if percentage is not None else None,
            grade=grade(percentage) if percentage is not None else '-',passed=value is not None and value>=entry.passing_marks))
        maximum+=entry.max_marks
        if value is not None:total+=value
        if value is None or value<entry.passing_marks:passed=False
    pct=float(total*100/maximum) if maximum else 0
    return dict(student=serialize(student),exam=serialize(exam),subjects=subjects,
        obtained=float(total),maximum=float(maximum),percentage=round(pct,2),grade=grade(pct),
        status=('Pass' if passed else 'Fail') if entries else 'Pending',complete=bool(entries) and len(scores)>=len(entries))


def csv_safe(value):
    text=str(value or '')
    return "'"+text if text and text[0] in ('=', '+', '-', '@', '\t', '\r') else text


def unique_code(prefix,model):
    # Sequence based on allocated primary key; set after flush.
    return f'{prefix}-{secrets.token_hex(5).upper()}'


@api.post('/auth/login')
@limiter.limit('5 per minute')
def login():
    try:
        data=body();require_keys(data,'email','password')
        user=User.query.filter_by(email=data['email'].strip().lower()).first()
        if not user or not user.active or not check_password_hash(user.password_hash,data['password']):
            return error('Invalid email or password',401)
        return jsonify(access_token=create_access_token(identity=str(user.id)),user=serialize(user))
    except ValueError as exc:return error(str(exc))


@api.post('/auth/logout')
@roles('admin','teacher','student')
def logout():
    db.session.add(TokenBlocklist(jti=get_jwt()['jti']))
    db.session.commit()
    return jsonify(message='Logged out')


@api.get('/auth/me')
@roles('admin','teacher','student')
def me():return jsonify(user=serialize(actor()))


@api.post('/auth/forgot-password')
@limiter.limit('3 per hour')
def forgot():
    try:
        data=body();require_keys(data,'email')
        user=User.query.filter_by(email=data['email'].strip().lower(),active=True).first()
        host=os.getenv('SMTP_HOST');sender=os.getenv('SMTP_FROM')
        if user and host and sender:
            raw=secrets.token_urlsafe(40)
            reset=PasswordReset(user_id=user.id,token_hash=hashlib.sha256(raw.encode()).hexdigest(),expires_at=datetime.now(timezone.utc)+timedelta(minutes=30))
            db.session.add(reset);db.session.commit()
            url=os.getenv('PUBLIC_FRONTEND_URL','http://localhost:4200').rstrip('/')+'/reset-password?token='+raw
            msg=EmailMessage();msg['From']=sender;msg['To']=user.email;msg['Subject']='Sankalp Classes - Reset your password'
            msg.set_content('Your reset link (valid 30 minutes):\n'+url+'\nIf you did not request this, ignore this email.')
            try:
                with smtplib.SMTP(host,int(os.getenv('SMTP_PORT','587')),timeout=12) as server:
                    server.starttls()
                    if os.getenv('SMTP_USERNAME'):server.login(os.getenv('SMTP_USERNAME'),os.getenv('SMTP_PASSWORD',''))
                    server.send_message(msg)
            except Exception:
                current_app.logger.exception('Password reset email delivery failed')
        return jsonify(message='If this account exists and email delivery is configured, you will receive reset instructions.')
    except ValueError as exc:return error(str(exc))


@api.post('/auth/reset-password')
@limiter.limit('5 per hour')
def reset_password():
    try:
        data=body();require_keys(data,'token','password')
        if len(data['password'])<12:return error('Password must contain at least 12 characters')
        digest=hashlib.sha256(data['token'].encode()).hexdigest()
        item=PasswordReset.query.filter_by(token_hash=digest,used=False).first()
        if not item or item.expires_at.replace(tzinfo=timezone.utc)<datetime.now(timezone.utc):return error('Invalid or expired token',400)
        user=db.session.get(User,item.user_id)
        user.password_hash=generate_password_hash(data['password']);item.used=True
        db.session.commit()
        return jsonify(message='Password updated; please sign in')
    except ValueError as exc:return error(str(exc))


@api.get('/meta')
@roles('admin','teacher','student')
def meta():
    def options(cls,label='name'):
        return [dict(id=x.id,name=getattr(x,label)) for x in cls.query.order_by(cls.id).all()]
    if actor().role=='student':return jsonify(classes=[],batches=[],subjects=[],teachers=[],students=[],examinations=[])
    allowed_batches=None
    if actor().role=='teacher':allowed_batches={x.batch_id for x in TeacherAssignment.query.filter_by(teacher_id=teacher_id()).all()}
    batches=Batch.query.all() if allowed_batches is None else Batch.query.filter(Batch.id.in_(allowed_batches)).all()
    students=Student.query.join(User).filter(User.active.is_(True)).all() if allowed_batches is None else Student.query.join(User).filter(User.active.is_(True),Student.batch_id.in_(allowed_batches)).all()
    exams=Examination.query.all() if allowed_batches is None else Examination.query.filter(or_(Examination.batch_id.in_(allowed_batches),Examination.batch_id.is_(None))).all()
    return jsonify(classes=options(AcademicClass),batches=[dict(id=b.id,name=b.name,class_id=b.class_id) for b in batches],
        subjects=options(Subject),teachers=[dict(id=t.id,name=t.user.full_name) for t in Teacher.query.all()] if actor().role=='admin' else [],
        students=[dict(id=s.id,name=s.user.full_name,batch_id=s.batch_id,class_id=s.class_id,code=s.code) for s in students],
        examinations=[dict(id=e.id,name=e.name,class_id=e.class_id,batch_id=e.batch_id,published=e.published) for e in exams])

# Explicit field allowlists prevent mass-assignment of roles, ownership, or audit fields.
RESOURCE_FIELDS={
 'classes':(AcademicClass,{'name':'str','description':'str','active':'bool'},['name']),
 'batches':(Batch,{'name':'str','class_id':'id','start_date':'date','end_date':'date','timings':'str','active':'bool'},['name','class_id']),
 'subjects':(Subject,{'name':'str','description':'str','active':'bool'},['name']),
 'examinations':(Examination,{'name':'str','academic_year':'str','class_id':'id','batch_id':'id','exam_type':'str','start_date':'date','end_date':'date','description':'str','published':'bool'},['name','academic_year','class_id']),
 'teacher-assignments':(TeacherAssignment,{'teacher_id':'id','class_id':'id','batch_id':'id','subject_id':'id'},['teacher_id','class_id','batch_id','subject_id']),
 'examination-subjects':(ExaminationSubject,{'examination_id':'id','subject_id':'id','max_marks':'num','passing_marks':'num'},['examination_id','subject_id','max_marks','passing_marks']),
 'class-subjects':(ClassSubject,{'class_id':'id','subject_id':'id'},['class_id','subject_id']),
}


def checked_fields(data,fields):
    result={}
    for key,typ in fields.items():
        if key not in data:continue
        value=data[key]
        if value in ('',None) and typ in ('id','date','str'):
            result[key]=None if typ in ('id','date') else ''
        elif typ=='date':result[key]=day(value)
        elif typ=='id':result[key]=integer(value,key)
        elif typ=='num':result[key]=number(value,key)
        elif typ=='bool':result[key]=parse_bool(value)
        elif typ=='str':
            if not isinstance(value,str) or len(value)>500:raise ValueError(f'Invalid {key}')
            result[key]=value.strip()
    return result


def validate_reference(resource,values):
    if resource in ('batches','teacher-assignments','examinations'):
        class_id=values.get('class_id')
        if class_id and not db.session.get(AcademicClass,class_id):raise ValueError('Class does not exist')
    if resource=='batches':
        if values.get('start_date') and values.get('end_date') and values['end_date']<values['start_date']:
            raise ValueError('End date precedes start date')
    if resource in ('examinations','teacher-assignments'):
        batch_id=values.get('batch_id')
        if batch_id:
            batch=db.session.get(Batch,batch_id)
            if not batch:raise ValueError('Batch does not exist')
            if values.get('class_id') and batch.class_id!=values['class_id']:
                raise ValueError('Batch does not belong to class')
    if resource=='teacher-assignments':
        if not db.session.get(Teacher,values['teacher_id']):raise ValueError('Teacher does not exist')
        if not db.session.get(Subject,values['subject_id']):raise ValueError('Subject does not exist')
        if not db.session.get(ClassSubject,{'class_id':values['class_id'],'subject_id':values['subject_id']}):
            raise ValueError('Assign the subject to this class first')
    if resource=='examination-subjects':
        exam=db.session.get(Examination,values['examination_id'])
        if not exam:raise ValueError('Examination does not exist')
        if not db.session.get(ClassSubject,{'class_id':exam.class_id,'subject_id':values['subject_id']}):
            raise ValueError('Subject must belong to the examination class')
        if values['max_marks']<=0 or values['passing_marks']<0 or values['passing_marks']>values['max_marks']:
            raise ValueError('Invalid maximum or passing marks')
    if resource=='class-subjects':
        if not db.session.get(AcademicClass,values['class_id']) or not db.session.get(Subject,values['subject_id']):
            raise ValueError('Class or subject not found')


@api.route('/<resource>',methods=['GET','POST'])
@roles('admin','teacher')
def generic_collection(resource):
    if resource not in RESOURCE_FIELDS:return error('Unknown resource',404)
    cls,fields,required=RESOURCE_FIELDS[resource]
    if request.method=='GET':
        if actor().role!='admin':
            if resource not in ('classes','batches','subjects','examinations','examination-subjects'):
                return error('Admin permission required',403)
        query=cls.query
        if actor().role=='teacher':
            allowed={r.batch_id for r in TeacherAssignment.query.filter_by(teacher_id=teacher_id()).all()}
            if resource=='batches':query=query.filter(Batch.id.in_(allowed))
            if resource=='examinations':
                class_ids={x.class_id for x in TeacherAssignment.query.filter_by(teacher_id=teacher_id())}
                query=query.filter(or_(Examination.batch_id.in_(allowed),and_(Examination.batch_id.is_(None),Examination.class_id.in_(class_ids))))
            if resource=='examination-subjects':
                class_ids={x.class_id for x in TeacherAssignment.query.filter_by(teacher_id=teacher_id())}
                exams=[e.id for e in Examination.query.filter(or_(Examination.batch_id.in_(allowed),and_(Examination.batch_id.is_(None),Examination.class_id.in_(class_ids)))).all()]
                query=query.filter(ExaminationSubject.examination_id.in_(exams))
        keyword=request.args.get('q','').strip()
        if keyword and 'name' in fields:query=query.filter(getattr(cls,'name').ilike(f'%{keyword}%'))
        try:page=max(1,int(request.args.get('page',1)));size=min(100,max(1,int(request.args.get('size',20))))
        except ValueError:return error('Invalid pagination')
        total=query.count();items=query.order_by(*[col.asc() for col in cls.__mapper__.primary_key]).offset((page-1)*size).limit(size).all()
        return jsonify(items=[serialize(x) for x in items],total=total,page=page,size=size)
    if actor().role!='admin':return error('Admin permission required',403)
    try:
        payload=body();values=checked_fields(payload,fields)
        require_keys(values,*required)
        validate_reference(resource,values)
        if resource=='examinations' and values.get('published'):raise ValueError('Configure exam subjects and enter marks before publishing results')
        obj=cls(**values);db.session.add(obj);db.session.flush()
        log('create',resource,obj.id if hasattr(obj,'id') else None)
        db.session.commit()
        return jsonify(item=serialize(obj)),201
    except ValueError as exc:db.session.rollback();return error(str(exc))


@api.route('/<resource>/<int:item_id>',methods=['GET','PUT','DELETE'])
@roles('admin','teacher')
def generic_detail(resource,item_id):
    if resource not in RESOURCE_FIELDS:return error('Unknown resource',404)
    cls,fields,required=RESOURCE_FIELDS[resource]
    if resource=='class-subjects':return error('Use class-subjects collection for composite keys',400)
    obj=db.session.get(cls,item_id)
    if not obj:return error('Not found',404)
    if actor().role=='teacher' and request.method=='GET':
        if resource not in ('classes','batches','subjects','examinations','examination-subjects'):
            return error('Permission denied',403)
        if resource=='batches' and not can_teach(obj.id):return error('Permission denied',403)
        if resource=='examinations':
            if obj.batch_id and not can_teach(obj.batch_id):return error('Permission denied',403)
            if obj.batch_id is None and not TeacherAssignment.query.filter_by(teacher_id=teacher_id(),class_id=obj.class_id).first():return error('Permission denied',403)
        if resource=='examination-subjects':
            exam=db.session.get(Examination,obj.examination_id)
            if exam and exam.batch_id and not can_teach(exam.batch_id,obj.subject_id):return error('Permission denied',403)
            if exam and exam.batch_id is None and not TeacherAssignment.query.filter_by(teacher_id=teacher_id(),class_id=exam.class_id,subject_id=obj.subject_id).first():return error('Permission denied',403)
    elif actor().role=='teacher':return error('Admin permission required',403)
    if request.method=='GET':return jsonify(item=serialize(obj))
    if request.method=='DELETE':
        if resource in ('classes','batches','subjects','examinations'):
            if resource=='classes':obj.active=False
            elif resource=='batches':obj.active=False
            elif resource=='subjects':obj.active=False
            elif resource=='examinations':
                if Mark.query.filter_by(examination_id=obj.id).first():return error('Results exist; cannot delete examination',409)
                db.session.delete(obj)
        else:db.session.delete(obj)
        log('delete',resource,item_id)
        db.session.commit()
        return jsonify(message='Updated')
    try:
        values=checked_fields(body(),fields)
        all_values={k:getattr(obj,k) for k in fields}
        all_values.update(values)
        validate_reference(resource,all_values)
        if resource=='examination-subjects' and Mark.query.filter_by(examination_id=obj.examination_id,subject_id=obj.subject_id).first():
            if {'max_marks','passing_marks','subject_id','examination_id'} & values.keys():
                return error('Cannot alter grading criteria after marks are entered',409)
        if resource=='examinations' and values.get('published') and not obj.published:
            exam_subjects=ExaminationSubject.query.filter_by(examination_id=obj.id).all()
            if not exam_subjects:raise ValueError('Configure examination subjects before publishing')
            students_q=Student.query.join(User).filter(Student.class_id==obj.class_id,User.active.is_(True))
            if obj.batch_id:students_q=students_q.filter(Student.batch_id==obj.batch_id)
            students=students_q.all()
            if not students:raise ValueError('No active students are enrolled for this exam')
            ids={x.subject_id for x in exam_subjects}
            for student in students:
                marked={m.subject_id for m in Mark.query.filter_by(student_id=student.id,examination_id=obj.id).all()}
                if not ids.issubset(marked):raise ValueError('All configured subject marks must be entered for every student before publication')
        for k,v in values.items():setattr(obj,k,v)
        log('update',resource,item_id,{'fields':list(values)})
        db.session.commit();return jsonify(item=serialize(obj))
    except ValueError as exc:db.session.rollback();return error(str(exc))


def person_upsert(kind,obj=None):
    data=body();is_new=obj is None
    if is_new:require_keys(data,'full_name','email','password')
    if 'password' in data and data['password'] and len(str(data['password']))<12:
        raise ValueError('Password must contain at least 12 characters')
    if 'email' in data and not re.fullmatch(r'[^@\s]+@[^@\s]+\.[^@\s]+',str(data['email'])):
        raise ValueError('Invalid email')
    if not is_new:
        person=obj;user=obj.user
    else:
        user=User(role=kind,full_name=data['full_name'].strip(),email=data['email'].strip().lower(),password_hash=generate_password_hash(data['password']))
        db.session.add(user);db.session.flush()
        person=Student(user_id=user.id,code=unique_code('STU',Student)) if kind=='student' else Teacher(user_id=user.id,code=unique_code('TCH',Teacher))
        db.session.add(person)
    if 'full_name' in data:
        if not str(data['full_name']).strip():raise ValueError('Name is required')
        user.full_name=data['full_name'].strip()
    if 'email' in data:user.email=data['email'].strip().lower()
    if 'active' in data:user.active=parse_bool(data['active'])
    if data.get('password'):user.password_hash=generate_password_hash(data['password'])
    allowed={'mobile','address','qualification','joining_date'} if kind=='teacher' else {
        'class_id','batch_id','father_name','mother_name','gender','dob','mobile','guardian_mobile','address','admission_date'}
    old_batch=person.batch_id if not is_new and kind=='student' else None
    for key in allowed & data.keys():
        value=data[key]
        if key.endswith('_date') or key=='dob':value=day(value)
        elif key.endswith('_id'):value=integer(value,key)
        else:
            if value is not None and (not isinstance(value,str) or len(value)>500):raise ValueError('Invalid '+key)
            value=value or ''
        setattr(person,key,value)
    if kind=='student':
        if not person.class_id or not person.batch_id:raise ValueError('class_id and batch_id are required')
        batch=db.session.get(Batch,person.batch_id)
        if not batch or batch.class_id!=person.class_id:raise ValueError('Batch and class mismatch')
        if is_new or old_batch!=person.batch_id:
            if old_batch:
                old=StudentBatch.query.filter_by(student_id=person.id,ended_on=None).first()
                if old:old.ended_on=local_today()
            db.session.flush()
            db.session.add(StudentBatch(student_id=person.id,batch_id=person.batch_id,started_on=local_today()))
    db.session.flush()
    log('create' if is_new else 'update',kind,person.id)
    db.session.commit()
    return serialize(person)


@api.route('/students',methods=['GET','POST'])
@roles('admin','teacher')
def students():
    if request.method=='POST':
        if actor().role!='admin':return error('Admin only',403)
        try:return jsonify(item=person_upsert('student')),201
        except ValueError as exc:db.session.rollback();return error(str(exc))
    q=Student.query.join(User)
    if actor().role=='teacher':
        ids=[x.batch_id for x in TeacherAssignment.query.filter_by(teacher_id=teacher_id()).all()]
        q=q.filter(Student.batch_id.in_(ids))
    if request.args.get('batch_id'):q=q.filter(Student.batch_id==integer(request.args['batch_id']))
    if request.args.get('class_id'):q=q.filter(Student.class_id==integer(request.args['class_id']))
    if request.args.get('status')=='active':q=q.filter(User.active.is_(True))
    if request.args.get('status')=='inactive':q=q.filter(User.active.is_(False))
    if request.args.get('q'):
        term=f"%{request.args['q'][:100]}%";q=q.filter(or_(User.full_name.ilike(term),Student.code.ilike(term)))
    page=max(1,int(request.args.get('page',1)));size=min(100,max(1,int(request.args.get('size',20))))
    return jsonify(items=[serialize(x) for x in q.order_by(Student.id.desc()).offset((page-1)*size).limit(size)],total=q.count(),page=page,size=size)


@api.route('/students/<int:student_id>',methods=['GET','PUT','DELETE'])
@roles('admin','teacher','student')
def student_detail(student_id):
    obj=db.session.get(Student,student_id)
    if not obj:return error('Student not found',404)
    if actor().role=='student' and not is_student(student_id):return error('Permission denied',403)
    if actor().role=='teacher' and not can_teach(obj.batch_id):return error('Permission denied',403)
    if request.method=='GET':return jsonify(item=serialize(obj),attendance=attendance_summary(student_id))
    if actor().role!='admin':return error('Admin permission required',403)
    if request.method=='DELETE':
        obj.user.active=False;log('deactivate','student',student_id);db.session.commit();return jsonify(message='Student deactivated')
    try:return jsonify(item=person_upsert('student',obj))
    except ValueError as exc:db.session.rollback();return error(str(exc))


@api.route('/teachers',methods=['GET','POST'])
@roles('admin')
def teachers():
    if request.method=='POST':
        try:return jsonify(item=person_upsert('teacher')),201
        except ValueError as exc:db.session.rollback();return error(str(exc))
    q=Teacher.query.join(User)
    if request.args.get('q'):q=q.filter(User.full_name.ilike(f"%{request.args['q'][:100]}%"))
    page=max(1,int(request.args.get('page',1)));size=min(100,max(1,int(request.args.get('size',20))))
    return jsonify(items=[serialize(x) for x in q.order_by(Teacher.id.desc()).offset((page-1)*size).limit(size)],total=q.count(),page=page,size=size)


@api.route('/teachers/<int:teacher_id>',methods=['GET','PUT','DELETE'])
@roles('admin')
def teacher_detail(teacher_id):
    obj=db.session.get(Teacher,teacher_id)
    if not obj:return error('Teacher not found',404)
    if request.method=='GET':return jsonify(item=serialize(obj))
    if request.method=='DELETE':obj.user.active=False;log('deactivate','teacher',teacher_id);db.session.commit();return jsonify(message='Teacher deactivated')
    try:return jsonify(item=person_upsert('teacher',obj))
    except ValueError as exc:db.session.rollback();return error(str(exc))

@api.get('/attendance')
@roles('admin','teacher','student')
def attendance_list():
    q=Attendance.query
    if actor().role=='student':
        own=Student.query.filter_by(user_id=actor().id).first()
        q=q.filter(Attendance.student_id==(own.id if own else -1))
    elif actor().role=='teacher':
        ids=[t.batch_id for t in TeacherAssignment.query.filter_by(teacher_id=teacher_id())]
        q=q.filter(Attendance.batch_id.in_(ids))
    if request.args.get('student_id'):q=q.filter(Attendance.student_id==integer(request.args['student_id']))
    if request.args.get('batch_id'):q=q.filter(Attendance.batch_id==integer(request.args['batch_id']))
    if request.args.get('date'):q=q.filter(Attendance.date==day(request.args['date']))
    if actor().role=='student' and request.args.get('student_id') and not is_student(int(request.args['student_id'])):
        return error('Permission denied',403)
    items=q.order_by(Attendance.date.desc(),Attendance.student_id).limit(2000).all()
    return jsonify(items=[serialize(a) for a in items])


@api.post('/attendance/bulk')
@roles('admin','teacher')
def attendance_bulk():
    try:
        data=body();require_keys(data,'date','batch_id','records')
        target=day(data['date']);batch_id=integer(data['batch_id'])
        if target>local_today():raise ValueError('Cannot mark future attendance')
        if not can_teach(batch_id):return error('Not assigned to this batch',403)
        if not isinstance(data['records'],list) or not data['records'] or len(data['records'])>300:
            raise ValueError('Supply 1–300 attendance entries')
        seen=set();updates=[]
        for row in data['records']:
            student_id=integer(row.get('student_id'),'student_id');status=row.get('status')
            if student_id in seen:raise ValueError('Duplicate student in request')
            seen.add(student_id)
            if status not in ('present','absent','leave'):raise ValueError('Invalid attendance status')
            student=db.session.get(Student,student_id)
            if not student or not student.user.active or student.batch_id!=batch_id:
                raise ValueError('Student is not active in selected batch')
            updates.append((student_id,status))
        for student_id,status in updates:
            record=Attendance.query.filter_by(student_id=student_id,date=target).first()
            if not record:
                record=Attendance(student_id=student_id,date=target,batch_id=batch_id,status=status,updated_by=actor().id)
                db.session.add(record)
            else:
                record.status=status;record.updated_by=actor().id;record.batch_id=batch_id
            log('upsert','attendance',student_id,{'date':target.isoformat(),'status':status})
        db.session.commit();return jsonify(saved=len(updates))
    except (ValueError,TypeError) as exc:db.session.rollback();return error(str(exc))


@api.get('/attendance/student/<int:student_id>')
@roles('admin','teacher','student')
def student_attendance(student_id):
    student=db.session.get(Student,student_id)
    if not student:return error('Student not found',404)
    if actor().role=='student' and not is_student(student_id):return error('Permission denied',403)
    if actor().role=='teacher' and not can_teach(student.batch_id):return error('Permission denied',403)
    return jsonify(summary=attendance_summary(student_id),items=[serialize(x) for x in Attendance.query.filter_by(student_id=student_id).order_by(Attendance.date.desc()).limit(1000)])


@api.get('/marks')
@roles('admin','teacher','student')
def marks_list():
    q=Mark.query
    if actor().role=='student':
        own=Student.query.filter_by(user_id=actor().id).first()
        q=q.filter(Mark.student_id==(own.id if own else -1)).join(Examination,Mark.examination_id==Examination.id).filter(Examination.published.is_(True))
    elif actor().role=='teacher':
        teacher=teacher_id()
        pairs={(x.batch_id,x.subject_id) for x in TeacherAssignment.query.filter_by(teacher_id=teacher)}
        if not pairs:return jsonify(items=[])
        q=q.join(Student,Mark.student_id==Student.id).filter(or_(*[and_(Student.batch_id==batch,Mark.subject_id==subject) for batch,subject in pairs]))
    if request.args.get('examination_id'):q=q.filter(Mark.examination_id==integer(request.args['examination_id']))
    if request.args.get('subject_id'):q=q.filter(Mark.subject_id==integer(request.args['subject_id']))
    if request.args.get('student_id'):
        sid=integer(request.args['student_id'])
        if actor().role=='student' and not is_student(sid):return error('Permission denied',403)
        q=q.filter(Mark.student_id==sid)
    return jsonify(items=[serialize(m) for m in q.order_by(Mark.student_id).limit(2000)])


@api.post('/marks/bulk')
@roles('admin','teacher')
def marks_bulk():
    try:
        data=body();require_keys(data,'examination_id','subject_id','records')
        exam=db.session.get(Examination,integer(data['examination_id']))
        subject_id=integer(data['subject_id'])
        if not exam:return error('Examination not found',404)
        if exam.published:return error('Unpublish results before editing marks',409)
        config=ExaminationSubject.query.filter_by(examination_id=exam.id,subject_id=subject_id).first()
        if not config:return error('Subject not configured for examination',400)
        if not isinstance(data['records'],list) or not data['records'] or len(data['records'])>300:
            raise ValueError('Supply 1–300 mark entries')
        updates=[];seen=set()
        for row in data['records']:
            sid=integer(row.get('student_id'),'student_id')
            if sid in seen:raise ValueError('Duplicate student in request')
            seen.add(sid)
            student=db.session.get(Student,sid)
            if not student or not student.user.active or student.class_id!=exam.class_id or (exam.batch_id and student.batch_id!=exam.batch_id):
                raise ValueError('Student is not in the examination class/batch')
            if not can_teach(student.batch_id,subject_id):return error('Not assigned to teach this subject and batch',403)
            value=number(row.get('obtained'),'obtained marks')
            if value<0 or value>config.max_marks:raise ValueError('Obtained marks must be between 0 and maximum marks')
            if len(str(row.get('remarks','')))>1000:raise ValueError('Remarks too long')
            updates.append((sid,value,str(row.get('remarks',''))))
        for sid,value,remarks in updates:
            record=Mark.query.filter_by(student_id=sid,examination_id=exam.id,subject_id=subject_id).first()
            if not record:
                record=Mark(student_id=sid,examination_id=exam.id,subject_id=subject_id,obtained=value,updated_by=actor().id,remarks=remarks)
                db.session.add(record)
            else:record.obtained=value;record.remarks=remarks;record.updated_by=actor().id
            log('upsert','marks',sid,{'examination_id':exam.id,'subject_id':subject_id,'obtained':str(value)})
        db.session.commit()
        return jsonify(saved=len(updates))
    except (ValueError,TypeError) as exc:db.session.rollback();return error(str(exc))


@api.get('/results/<int:student_id>/<int:exam_id>')
@roles('admin','teacher','student')
def result(student_id,exam_id):
    student=db.session.get(Student,student_id);exam=db.session.get(Examination,exam_id)
    if not student or not exam:return error('Student or examination not found',404)
    if student.class_id!=exam.class_id or (exam.batch_id and exam.batch_id!=student.batch_id):
        return error('Student is not in this examination',404)
    if actor().role=='student' and not is_student(student_id):return error('Permission denied',403)
    if actor().role=='student' and not exam.published:return error('Results not published',403)
    if actor().role=='teacher' and not can_teach(student.batch_id):return error('Permission denied',403)
    return jsonify(result=result_for(student,exam))


@api.get('/results/<int:student_id>/<int:exam_id>/pdf')
@roles('admin','teacher','student')
def result_pdf(student_id,exam_id):
    student=db.session.get(Student,student_id);exam=db.session.get(Examination,exam_id)
    if not student or not exam:return error('Not found',404)
    if student.class_id!=exam.class_id or (exam.batch_id and exam.batch_id!=student.batch_id):return error('Not found',404)
    if actor().role=='student' and (not is_student(student_id) or not exam.published):return error('Permission denied',403)
    if actor().role=='teacher' and not can_teach(student.batch_id):return error('Permission denied',403)
    r=result_for(student,exam);buf=io.BytesIO();p=canvas.Canvas(buf,pagesize=A4)
    p.setTitle('Sankalp Classes Result')
    y=795
    p.setFont('Helvetica-Bold',18);p.drawString(48,y,'SANKALP CLASSES');y-=33
    p.setFont('Helvetica',12);p.drawString(48,y,f"Student: {student.user.full_name} ({student.code})");y-=23
    p.drawString(48,y,f"Examination: {exam.name} | Academic Year: {exam.academic_year}");y-=30
    p.setFont('Helvetica-Bold',10);p.drawString(48,y,'Subject');p.drawString(270,y,'Obtained');p.drawString(365,y,'Maximum');p.drawString(455,y,'Grade');y-=20
    p.setFont('Helvetica',10)
    for line in r['subjects']:
        p.drawString(48,y,line['subject'][:35]);p.drawString(270,y,str(line['obtained'] if line['obtained'] is not None else '-'))
        p.drawString(365,y,str(line['max_marks']));p.drawString(455,y,line['grade']);y-=20
        if y<100:p.showPage();y=780
    y-=14;p.setFont('Helvetica-Bold',12)
    p.drawString(48,y,f"Total: {r['obtained']} / {r['maximum']}    {r['percentage']}%    Grade: {r['grade']}    {r['status']}")
    p.showPage();p.save();buf.seek(0)
    return send_file(buf,mimetype='application/pdf',as_attachment=True,download_name=f'result-{student.code}-{exam.id}.pdf')


@api.get('/dashboard/<role>')
@roles('admin','teacher','student')
def dashboard(role):
    user=actor()
    if role!=user.role:return error('Permission denied',403)
    if role=='student':
        student=Student.query.filter_by(user_id=user.id).first()
        if not student:return jsonify(stats={})
        exams=[e for e in Examination.query.filter_by(class_id=student.class_id,published=True).all() if not e.batch_id or e.batch_id==student.batch_id]
        return jsonify(stats={'attendance':attendance_summary(student.id),'published_exams':len(exams)},student=serialize(student))
    if role=='teacher':
        assigned=TeacherAssignment.query.filter_by(teacher_id=teacher_id()).all()
        batch_ids={a.batch_id for a in assigned}
        return jsonify(stats={'assigned_batches':len(batch_ids),'assigned_subjects':len({a.subject_id for a in assigned}),
            'students':Student.query.join(User).filter(Student.batch_id.in_(batch_ids),User.active.is_(True)).count()})
    students=Student.query.count();active=Student.query.join(User).filter(User.active.is_(True)).count()
    today=local_today();att=Attendance.query.filter_by(date=today)
    monthly=db.session.query(func.date_trunc('month',Attendance.date),Attendance.status,func.count(Attendance.id)).group_by(func.date_trunc('month',Attendance.date),Attendance.status).order_by(func.date_trunc('month',Attendance.date)).limit(60).all() if db.engine.dialect.name=='postgresql' else []
    trend=[{'month':str(m)[:7],'status':s,'count':c} for m,s,c in monthly]
    threshold=75
    setting=db.session.get(Setting,'attendance_warning_threshold')
    if setting:
        try:threshold=float(setting.value)
        except ValueError:pass
    return jsonify(stats={'total_students':students,'active_students':active,'inactive_students':students-active,
        'total_teachers':Teacher.query.count(),'total_classes':AcademicClass.query.count(),
        'total_batches':Batch.query.count(),'attendance_warning_threshold':threshold,'today_present':att.filter_by(status='present').count(),
        'today_absent':att.filter_by(status='absent').count(),
        'attendance_percentage':round(100*Attendance.query.filter_by(status='present').count()/max(1,Attendance.query.filter(Attendance.status!='leave').count()),2)},
        monthly_attendance=trend,recent_students=[serialize(s) for s in Student.query.order_by(Student.id.desc()).limit(5)],
        upcoming_examinations=[serialize(e) for e in Examination.query.filter(Examination.start_date>=today).order_by(Examination.start_date).limit(5)],
        low_attendance=[{'student_id':s.id,'name':s.user.full_name,'percentage':attendance_summary(s.id)['percentage']} for s in Student.query.join(User).filter(User.active.is_(True)).limit(200) if attendance_summary(s.id)['applicable_days']>=3 and attendance_summary(s.id)['percentage']<threshold][:10])


@api.route('/settings',methods=['GET','PUT'])
@roles('admin')
def settings():
    if request.method=='GET':return jsonify(items={s.key:s.value for s in Setting.query.all()},grades=[serialize(s) for s in GradeSetting.query.order_by(GradeSetting.min_percentage.desc())])
    try:
        data=body();allowed={'institute_name','institute_address','contact_number','email','academic_year','attendance_warning_threshold','timezone','date_format'}
        for k,v in data.get('items',{}).items():
            if k not in allowed or not isinstance(v,str) or len(v)>500:raise ValueError('Invalid setting: '+k)
            record=db.session.get(Setting,k)
            if record:record.value=v
            else:db.session.add(Setting(key=k,value=v))
        if 'grades' in data:
            grades=data['grades']
            if not isinstance(grades,list) or not grades or len(grades)>15:raise ValueError('Invalid grade ranges')
            mins=[g.get('min_percentage') for g in grades]
            if 0 not in mins or len(set(mins))!=len(mins):raise ValueError('Grade ranges must include 0 and be unique')
            for g in grades:
                if not isinstance(g['min_percentage'],int) or not (0<=g['min_percentage']<=100) or not isinstance(g.get('grade'),str) or not (1<=len(g['grade'])<=5):raise ValueError('Invalid grade')
            GradeSetting.query.delete()
            for g in grades:db.session.add(GradeSetting(min_percentage=g['min_percentage'],grade=g['grade']))
        log('update','settings');db.session.commit();return jsonify(message='Settings saved')
    except (ValueError,TypeError,KeyError) as exc:db.session.rollback();return error(str(exc))


@api.get('/reports/attendance.csv')
@roles('admin','teacher')
def attendance_csv():
    q=Attendance.query
    if actor().role=='teacher':
        ids=[x.batch_id for x in TeacherAssignment.query.filter_by(teacher_id=teacher_id())]
        q=q.filter(Attendance.batch_id.in_(ids))
    if request.args.get('batch_id'):q=q.filter(Attendance.batch_id==integer(request.args['batch_id']))
    if request.args.get('from'):q=q.filter(Attendance.date>=day(request.args['from']))
    if request.args.get('to'):q=q.filter(Attendance.date<=day(request.args['to']))
    output=io.StringIO();writer=csv.writer(output);writer.writerow(['Date','Student ID','Student Name','Batch ID','Status'])
    for a in q.order_by(Attendance.date.desc()).limit(10000):
        s=db.session.get(Student,a.student_id)
        writer.writerow([a.date.isoformat(),csv_safe(s.code) if s else '',csv_safe(s.user.full_name) if s else '',a.batch_id,a.status])
    return Response(output.getvalue(),mimetype='text/csv',headers={'Content-Disposition':'attachment; filename=attendance.csv'})


@api.get('/reports/marks.csv')
@roles('admin','teacher')
def marks_csv():
    q=Mark.query
    if actor().role=='teacher':
        assignments=TeacherAssignment.query.filter_by(teacher_id=teacher_id()).all()
        pairs={(a.batch_id,a.subject_id) for a in assignments}
        # Include only marks where student-batch AND subject are assigned together.
        rows=[m for m in q.limit(10000) if (db.session.get(Student,m.student_id).batch_id,m.subject_id) in pairs]
    else:rows=q.limit(10000).all()
    output=io.StringIO();writer=csv.writer(output);writer.writerow(['Student','Examination','Subject','Obtained','Maximum','Percentage','Grade'])
    for mark in rows:
        student=db.session.get(Student,mark.student_id);exam=db.session.get(Examination,mark.examination_id)
        sub=db.session.get(Subject,mark.subject_id)
        info=ExaminationSubject.query.filter_by(examination_id=mark.examination_id,subject_id=mark.subject_id).first()
        if not info:continue
        pct=float(mark.obtained*100/info.max_marks)
        writer.writerow([csv_safe(student.user.full_name),csv_safe(exam.name),csv_safe(sub.name),str(mark.obtained),str(info.max_marks),round(pct,2),grade(pct)])
    return Response(output.getvalue(),mimetype='text/csv',headers={'Content-Disposition':'attachment; filename=marks.csv'})


@api.get('/openapi.json')
def openapi():
    return jsonify(openapi='3.0.3',info={'title':'SANKALP CLASSES API','version':'1.0.0'},servers=[{'url':'/api/v1'}],
        paths={re.sub(r'<(?:int:)?([^>]+)>',r'{\1}',path):{method.lower():{'summary':endpoint,'responses':{'200':{'description':'Successful response'}}} for method in methods if method not in ('HEAD','OPTIONS')} for path,methods,endpoint in
          [(str(rule.rule).replace('/api/v1',''),rule.methods or set(),rule.endpoint) for rule in current_app.url_map.iter_rules() if rule.rule.startswith('/api/v1') and rule.rule!='/api/v1/openapi.json']})

@api.get('/results/available')
@roles('student')
def available_results():
    student=Student.query.filter_by(user_id=actor().id).first()
    if not student:return error('Student profile not found',404)
    exams=Examination.query.filter_by(class_id=student.class_id,published=True).all()
    return jsonify(student=dict(id=student.id,name=student.user.full_name,code=student.code),
        examinations=[dict(id=e.id,name=e.name) for e in exams if e.batch_id is None or e.batch_id==student.batch_id])
