# SANKALP CLASSES — Institute Management

A responsive education management application with a **standalone Angular 22 frontend**, **Flask REST API**, **SQLAlchemy/Alembic migrations**, and **PostgreSQL**. Role-based interfaces for administrators, teachers and students.

> **Release status:** Source-code starter / functional core implementation. Not a security-audited or fully validated production release. Dependencies could not be installed in the build environment, so end-to-end runtime testing and Angular compilation must be performed on your workstation before exposing student data. See `docs/DEPLOYMENT.md` and `docs/LIMITATIONS.md`.

## Delivered functionality

- Admin-created accounts, password hashing, JWT bearer authentication, role enforcement on APIs, token revocation, optional SMTP reset links.
- Student and teacher management, deactivation, classes, batches, subjects, class subjects, teaching assignments, student enrollment history.
- Admin/teacher attendance entry (present/absent/leave), unique student/day constraint, edit via bulk upsert, attendance percentages excluding leave.
- Exams, exam subjects (maximum and passing marks), teacher-scoped bulk marks entry, validation, configurable grades, published result cards and PDFs.
- Database-backed dashboards, basic Chart.js monthly attendance trend, CSV report exports, settings, basic API catalog at `/api/v1/openapi.json`.
- Responsive Bootstrap navigation and feature pages, migration baseline, Docker Compose PostgreSQL, Render/Vercel/Cloudflare configurations.

**Not included in this release:** photo uploads and persistent file storage, printable student profiles, comprehensive subject/class analytics, pagination on large attendance/marks grids, advanced filtering/sorting and scheduling, comprehensive audit history UI, automated email provider integration for Render, or a commercial production readiness/security certification. These are documented gaps, not delivered features.

## Quick start (local development)

Install **Python 3.11–3.13**, **Node.js 22.22.3+ (or supported Node 24+)**, **Docker Desktop** and **Git**.

### 1. Start PostgreSQL

```bash
docker compose up -d db
```

### 2. Start Flask

Linux/macOS:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
flask db upgrade
python manage.py seed-settings
python manage.py create-admin
flask --app run run --port 5000 --debug
```

Windows PowerShell:

```powershell
cd backend
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
flask db upgrade
python manage.py seed-settings
python manage.py create-admin
flask --app run run --port 5000 --debug
```

Use a strong random `SECRET_KEY` and `JWT_SECRET_KEY` in `backend/.env` (even on your laptop). Ensure PostgreSQL is running first. The example database user/password are strictly for development.

### 3. Start Angular (second terminal)

```bash
cd frontend
npm install
npm start
```

Visit **http://localhost:4200**, log in with the admin you created. Flask health check: **http://localhost:5000/health**.

### 4. Create initial academic records

Create in this order:

1. Classes, then batches.
2. Subjects, then Class Subjects.
3. Teachers, then Teacher Assignments (class, batch, subject).
4. Students (class, batch and accounts).
5. Examinations and Exam Subjects (maximum/passing marks).
6. Record attendance and enter marks; publish exam results after checking completeness.

## Project directories

```text
sankalp-classes/
  backend/
    app/{__init__.py,extensions.py,models.py,api.py}
    migrations/{env.py,versions/0001_initial.py}
    tests/{conftest.py,test_flows.py}
    .env.example  manage.py  run.py  requirements.txt
  frontend/
    src/app/{core,pages,app.component.ts,app.routes.ts}
    src/environments/environment.ts
    src/styles.scss  angular.json  package.json  vercel.json
  docs/{DEPLOYMENT.md,LIMITATIONS.md}
  docker-compose.yml  render.yaml  README.md
```

## Tests

```bash
cd backend
pytest -q
```

```bash
cd frontend
npm run build
```

Run test and smoke-test all roles on a disposable DB before creating actual student records. See deployment guide for Neon, Render, Cloudflare Pages, Vercel, backups, and SSL/CORS.

## API highlights

`POST /api/v1/auth/login`, `POST /api/v1/auth/logout`, `GET /api/v1/auth/me`, `GET /api/v1/dashboard/{role}`, `GET/POST /api/v1/students`, `GET/POST /api/v1/teachers`, `GET/POST /api/v1/{classes,batches,subjects,examinations,...}`, `POST /api/v1/attendance/bulk`, `POST /api/v1/marks/bulk`, `GET /api/v1/results/{student_id}/{exam_id}`, `GET /api/v1/results/{student_id}/{exam_id}/pdf`, `GET /api/v1/reports/{attendance,marks}.csv`.

Authorization is enforced by Flask. Tokens are held in browser sessionStorage; for high-risk production use, strengthen browser token handling (e.g. same-origin HttpOnly cookies, CSRF), introduce centralized auditing, and commission a security assessment. Never commit `.env` or actual student records.
