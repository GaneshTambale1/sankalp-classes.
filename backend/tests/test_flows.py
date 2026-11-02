from datetime import date

BASE='/api/v1'

def test_health_and_auth(client,auth):
    assert client.get('/health').status_code==200
    assert client.get(BASE+'/students').status_code==401
    assert client.post(BASE+'/auth/login',json={'email':'admin@example.test','password':'wrong'}).status_code==401
    assert client.get(BASE+'/auth/me',headers=auth['student']).json['user']['role']=='student'


def test_teacher_cannot_create_student_or_classes(client,auth):
    assert client.post(BASE+'/students',headers=auth['teacher'],json={}).status_code==403
    assert client.post(BASE+'/classes',headers=auth['teacher'],json={'name':'Class 9'}).status_code==403
    assert client.get(BASE+'/teachers',headers=auth['student']).status_code==403


def test_students_isolated(client,auth):
    assert client.get(BASE+'/students/1',headers=auth['other']).status_code==403
    assert client.get(BASE+'/attendance/student/1',headers=auth['other']).status_code==403
    assert client.get(BASE+'/results/1/1',headers=auth['student']).status_code==403  # unpublished


def test_attendance_upsert_and_leave_exclusion(client,auth):
    d=date.today().isoformat()
    payload={'date':d,'batch_id':1,'records':[{'student_id':1,'status':'present'},{'student_id':2,'status':'leave'}]}
    assert client.post(BASE+'/attendance/bulk',headers=auth['teacher'],json=payload).status_code==200
    first=client.get(BASE+'/attendance/student/1',headers=auth['student']).json
    assert first['summary']['present']==1
    assert first['summary']['percentage']==100
    assert client.get(BASE+'/attendance/student/2',headers=auth['admin']).json['summary']['applicable_days']==0
    payload['records'][0]['status']='absent'
    assert client.post(BASE+'/attendance/bulk',headers=auth['admin'],json=payload).status_code==200
    records=client.get(BASE+'/attendance',headers=auth['admin']).json['items']
    assert len(records)==2  # unique student/day, updated in place
    assert client.get(BASE+'/attendance/student/1',headers=auth['student']).json['summary']['percentage']==0


def test_invalid_and_valid_marks(client,auth):
    data={'examination_id':1,'subject_id':1,'records':[{'student_id':1,'obtained':101}]}
    assert client.post(BASE+'/marks/bulk',headers=auth['teacher'],json=data).status_code==400
    data['records'][0]['obtained']=87
    assert client.post(BASE+'/marks/bulk',headers=auth['teacher'],json=data).status_code==200
    result=client.get(BASE+'/results/1/1',headers=auth['admin']).json['result']
    assert result['percentage']==87
    assert result['grade']=='A'
    assert result['status']=='Pass'
    assert client.get(BASE+'/results/1/1',headers=auth['student']).status_code==403
    assert client.put(BASE+'/examinations/1',headers=auth['admin'],json={'published':True}).status_code==400  # not all enrolled students have marks
    data['records']=[{'student_id':2,'obtained':67}]
    assert client.post(BASE+'/marks/bulk',headers=auth['teacher'],json=data).status_code==200
    assert client.put(BASE+'/examinations/1',headers=auth['admin'],json={'published':True}).status_code==200
    assert client.get(BASE+'/results/1/1',headers=auth['student']).status_code==200
    response=client.get(BASE+'/results/1/1/pdf',headers=auth['student'])
    assert response.status_code==200 and response.mimetype=='application/pdf'
    assert client.post(BASE+'/marks/bulk',headers=auth['teacher'],json=data).status_code==409


def test_teacher_cannot_mark_unassigned_batch(client,auth):
    assert client.post(BASE+'/attendance/bulk',headers=auth['teacher'],json={'date':date.today().isoformat(),'batch_id':999,'records':[{'student_id':1,'status':'present'}]}).status_code==403


def test_logout_revokes_token(client,auth):
    assert client.post(BASE+'/auth/logout',headers=auth['admin']).status_code==200
    assert client.get(BASE+'/auth/me',headers=auth['admin']).status_code==401


def test_admin_creates_student(client,auth):
    response=client.post(BASE+'/students',headers=auth['admin'],json={
        'full_name':'New Student','email':'new@example.test','password':'AnotherSecurePassword123!',
        'class_id':1,'batch_id':1,'guardian_mobile':'9876543210'})
    assert response.status_code==201,response.json
    assert response.json['item']['code'].startswith('STU-')
    assert response.json['item']['email']=='new@example.test'
    assert client.get(BASE+'/students',headers=auth['admin']).json['total']==3


def test_reports_are_real_data(client,auth):
    assert client.get(BASE+'/reports/attendance.csv',headers=auth['admin']).status_code==200
    assert client.get(BASE+'/reports/marks.csv',headers=auth['teacher']).status_code==200
