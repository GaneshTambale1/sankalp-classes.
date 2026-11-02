import os
import getpass
from dotenv import load_dotenv
load_dotenv()
from werkzeug.security import generate_password_hash
from app import create_app
from app.extensions import db
from app.models import User, GradeSetting, Setting

app = create_app()

with app.app_context():
    import sys
    if len(sys.argv) < 2 or sys.argv[1] not in ('create-admin','seed-settings'):
        print('Usage: python manage.py create-admin | seed-settings');sys.exit(2)
    if sys.argv[1] == 'create-admin':
        email = input('Admin email: ').strip().lower()
        name = input('Admin full name: ').strip()
        password = getpass.getpass('Admin password (12+ characters): ')
        if not name or '@' not in email or len(password)<12: raise SystemExit('Invalid name, email or password')
        if User.query.filter_by(email=email).first():raise SystemExit('Email already exists')
        db.session.add(User(email=email,full_name=name,password_hash=generate_password_hash(password),role='admin'))
    else:
        for minimum, grade in [(90,'A+'),(80,'A'),(70,'B+'),(60,'B'),(50,'C'),(35,'D'),(0,'F')]:
            if not GradeSetting.query.filter_by(min_percentage=minimum).first(): db.session.add(GradeSetting(min_percentage=minimum,grade=grade))
        for key, value in {'institute_name':'SANKALP CLASSES','academic_year':'2026-27','attendance_warning_threshold':'75','institute_address':'','contact_number':'','email':'','timezone':'Asia/Kolkata'}.items():
            if not db.session.get(Setting,key):db.session.add(Setting(key=key,value=value))
    db.session.commit()
    print('Done.')
