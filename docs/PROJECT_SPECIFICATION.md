# MASTER PROJECT PROMPT

# SANKALP CLASSES

## Student Attendance, Marks and Institute Management System

Act as a senior software architect, expert Angular developer, Python Flask backend developer, PostgreSQL database architect, UI/UX designer and DevOps engineer.

Your task is to design and develop a complete, professional, responsive and production-conscious web application named **SANKALP CLASSES**.

This application will be used by a coaching institute to manage students, teachers, classes, batches, subjects, daily attendance, examinations, marks, results and academic performance.

The application must be fully functional, database-driven, secure, modular, maintainable and deployable using free-tier hosting services wherever available.

Do not build only a frontend prototype. Develop a complete working application with frontend, backend, database, authentication, authorization, APIs and deployment documentation.

---

# 1. TECHNOLOGY STACK

Use the following technologies.

## Frontend

- Angular (latest stable compatible release)
- TypeScript
- HTML5
- SCSS
- Bootstrap 5
- Bootstrap Icons
- Angular Router
- Angular Reactive Forms
- Angular HttpClient
- Chart.js
- RxJS

Use Angular standalone components and a feature-based architecture.

## Backend

- Python 3
- Flask
- Flask REST API
- Flask-SQLAlchemy
- SQLAlchemy ORM
- Flask-Migrate
- Flask-JWT-Extended or secure cookie-based authentication
- Flask-CORS
- Flask-Limiter
- Marshmallow or equivalent request validation

## Database

- PostgreSQL
- Alembic migrations
- Proper relational database design

## Development Tools

- Visual Studio Code
- Git
- GitHub
- Postman
- Angular CLI
- Python virtual environment

## Deployment

- Angular: Vercel
- Flask: PythonAnywhere or Render, depending on free-tier compatibility
- PostgreSQL: Neon or another compatible PostgreSQL provider

All hosting must be selected based on currently available free plans. Do not assume free services offer unlimited resources or permanent database storage.

---

# 2. PROJECT OBJECTIVE

Develop a centralized student management platform for Sankalp Classes.

The system should allow the administrator and teachers to manage students, record attendance, enter examination marks and generate performance reports.

The system must support multiple classes, multiple batches, multiple subjects and multiple teachers.

The application should be easy to use even for staff members with limited technical knowledge.

---

# 3. BRAND IDENTITY AND DESIGN

Application name: SANKALP CLASSES

Create a modern, premium educational institute management interface.

## Visual identity

Primary color: Navy Blue (#142B4F)

Secondary color: Blue (#2563EB)

Accent color: Light Blue (#DBEAFE)

Background: #F8FAFC

Cards: White

Text: Dark Navy / Slate

Success: Green

Warning: Amber

Danger: Red

Use a clean, professional typography system.

## Design requirements

- Professional admin dashboard.
- Modern sidebar navigation.
- Responsive header.
- Clean cards and tables.
- Rounded corners.
- Subtle shadows.
- Consistent spacing.
- Attractive icons.
- Professional forms.
- Search and filtering.
- Pagination.
- Toast notifications.
- Confirmation dialogs.
- Skeleton loading states.
- Empty states.
- Error states.
- Mobile responsive layouts.

Create a reusable design system.

Do not use a generic or outdated admin dashboard template.

The application should look like a modern commercial SaaS education management platform.

---

# 4. USER ROLES AND PERMISSIONS

Create three user roles.

## ADMIN

Admin has complete access.

Permissions:

- Dashboard access.
- Create and manage students.
- Create and manage teachers.
- Manage classes.
- Manage batches.
- Manage subjects.
- Assign teachers.
- Manage attendance.
- Manage examinations.
- Manage marks.
- Generate results.
- Generate reports.
- Manage users.
- Manage application settings.
- View all records.

## TEACHER

Teacher permissions:

- Login.
- View assigned classes.
- View assigned batches.
- View assigned students.
- Mark attendance.
- Edit attendance according to permissions.
- Enter marks for assigned subjects.
- View examination details.
- View student performance.
- Generate permitted reports.

Teachers must not access admin-only pages or APIs.

## STUDENT

Student permissions:

- Secure login.
- View own profile.
- View own attendance.
- View attendance percentage.
- View examination results.
- View subject-wise marks.
- Download available result reports.

Students must never access another student's private records.

Implement authorization in the backend, not only in Angular.

---

# 5. AUTHENTICATION SYSTEM

Create a complete authentication module.

Pages:

- Login.
- Logout.
- Forgot password.
- Reset password.
- Unauthorized access.
- Session expiration.

Requirements:

- Secure password hashing.
- Secure token or cookie authentication.
- Password validation.
- Role-based access.
- Login rate limiting.
- Session expiration.
- Logout invalidation.
- Secure password reset workflow.
- Protected Angular routes.
- Flask authorization decorators.

Use secure HttpOnly cookies with appropriate SameSite and Secure settings where practical, and implement CSRF protection for cookie-authenticated requests.

Never store plain-text passwords.

Do not provide public registration.

Admin creates teacher and student accounts.

---

# 6. ADMIN DASHBOARD

Create an attractive dashboard with real database statistics.

## Statistics cards

- Total Students.
- Active Students.
- Inactive Students.
- Total Teachers.
- Total Classes.
- Total Batches.
- Today's Present Students.
- Today's Absent Students.
- Overall Attendance Percentage.

## Charts

1. Monthly attendance trend.
2. Class-wise attendance comparison.
3. Subject-wise average marks.
4. Examination performance.
5. Student grade distribution.

## Dashboard sections

- Recently added students.
- Recent attendance records.
- Upcoming examinations.
- Recent examination results.
- Top-performing students.
- Students with low attendance.

## Quick actions

- Add Student.
- Add Teacher.
- Mark Attendance.
- Create Examination.
- Enter Marks.
- View Reports.

All dashboard values must come from actual database queries.

Never display fake production statistics.

---

# 7. STUDENT MANAGEMENT MODULE

Create a complete student management system.

## Student fields

- Student ID (automatically generated).
- Full Name.
- Father's Name.
- Mother's Name.
- Gender.
- Date of Birth.
- Mobile Number.
- Parent/Guardian Mobile.
- Email.
- Address.
- Admission Date.
- Class.
- Batch.
- Profile Photograph.
- Status (Active/Inactive).

## Features

- Add student.
- Edit student.
- View student details.
- Deactivate student.
- Search students.
- Filter by class.
- Filter by batch.
- Filter by status.
- Sort records.
- Pagination.
- Export CSV.
- Print student information.

## Student profile

Create a detailed student profile page with tabs:

1. Personal Information.
2. Academic Information.
3. Attendance History.
4. Examination History.
5. Marks and Results.

Display attendance percentage and academic performance.

Generate unique student IDs automatically.

Prevent accidental duplicate records.

Preserve historical attendance and examination records when students are deactivated.

---

# 8. TEACHER MANAGEMENT MODULE

Teacher fields:

- Teacher ID.
- Full Name.
- Mobile Number.
- Email.
- Address.
- Qualification.
- Joining Date.
- Assigned Subjects.
- Assigned Classes.
- Login Account.
- Status.

Features:

- Add teacher.
- Edit teacher.
- View teacher.
- Deactivate teacher.
- Assign subjects.
- Assign classes and batches.
- View teaching assignments.
- View teacher activity.

---

# 9. CLASS AND BATCH MANAGEMENT

Create separate class and batch management pages.

## Classes

- Class ID.
- Class Name.
- Description.
- Status.

## Batches

- Batch ID.
- Batch Name.
- Associated Class.
- Start Date.
- End Date.
- Timings.
- Assigned Teacher.
- Status.

Features:

- Add classes.
- Edit classes.
- Add batches.
- Edit batches.
- Assign students.
- Assign teachers.
- View student counts.
- View batch schedules.
- Deactivate batches.

Support multiple batches within the same class.

Maintain historical class and batch associations.

---

# 10. SUBJECT MANAGEMENT

Features:

- Add subjects.
- Edit subjects.
- Delete subjects where safe.
- Assign subjects to classes.
- Assign teachers to subjects.
- View subject details.

Example subjects:

- Mathematics.
- Physics.
- Chemistry.
- Biology.
- English.
- Science.

Subjects must be configurable.

---

# 11. ATTENDANCE MANAGEMENT

This is one of the most important modules.

Create a fast and user-friendly attendance interface.

## Attendance workflow

Step 1: Select class.

Step 2: Select batch.

Step 3: Select attendance date.

Step 4: Load active students.

Step 5: Display students in a table.

Step 6: Mark attendance.

Step 7: Save attendance.

## Attendance statuses

- Present.
- Absent.
- Leave.

## Attendance features

- Mark all present.
- Mark individual students.
- Mark absent students.
- Mark approved leave.
- Edit attendance.
- Save attendance in bulk.
- Search students.
- Filter students.
- View attendance history.
- View daily attendance.
- View monthly attendance.
- View class-wise attendance.
- View student-wise attendance.
- Export attendance to CSV.
- Print attendance report.

## Attendance validation

Prevent duplicate attendance records for the same student and date.

Use a unique database constraint.

Only authorized teachers and admins can modify attendance.

Record which user created or updated attendance.

## Attendance percentage

Use:

Attendance Percentage = Present Days / Total Applicable Attendance Days × 100

Approved leave should not be counted as an absent day and should be excluded from the applicable attendance denominator.

Display:

- Total applicable days.
- Present days.
- Absent days.
- Leave days.
- Attendance percentage.

Create configurable attendance warning thresholds.

For example:

- Above 90%: Good.
- 75–90%: Average.
- Below 75%: Low attendance.

Make these thresholds configurable.

---

# 12. EXAMINATION MANAGEMENT

Create an examination management module.

Fields:

- Examination ID.
- Examination Name.
- Academic Year.
- Class.
- Batch applicability where appropriate.
- Examination Type.
- Start Date.
- End Date.
- Description.
- Status.

Example examinations:

- Unit Test 1.
- Unit Test 2.
- Monthly Test.
- Midterm Examination.
- Final Examination.

Features:

- Create examination.
- Edit examination.
- Delete examination if no historical results exist.
- Assign subjects.
- Configure maximum marks.
- Configure passing marks.
- View examination schedule.
- Track result publication status.

---

# 13. MARKS MANAGEMENT

Create a simple bulk marks-entry system.

## Workflow

1. Select class.
2. Select batch where applicable.
3. Select examination.
4. Select subject.
5. Load students.
6. Enter marks.
7. Validate marks.
8. Save records.

## Marks fields

- Student.
- Examination.
- Subject.
- Maximum Marks.
- Obtained Marks.
- Passing Marks.
- Remarks.
- Entered By.
- Updated At.

## Features

- Bulk marks entry.
- Individual marks editing.
- Search students.
- Filter records.
- Validate marks.
- Prevent duplicate entries.
- Automatic total calculation.
- Automatic percentage calculation.
- Automatic grade calculation.
- Automatic pass/fail calculation.

## Validation

Obtained marks must not exceed maximum marks.

Marks cannot be negative.

Marks must be associated with the correct examination, student and subject.

Prevent duplicate marks for the same student, examination and subject.

---

# 14. GRADE MANAGEMENT

Default grading system:

- 90–100: A+
- 80–89: A
- 70–79: B+
- 60–69: B
- 50–59: C
- 35–49: D
- Below 35: F

Make grade ranges configurable through admin settings.

Use consistent grade calculations across results, reports and dashboards.

Support examinations with different maximum marks.

---

# 15. STUDENT RESULT MANAGEMENT

Create a professional report card for each student.

The report card should include:

SANKALP CLASSES

- Student Name.
- Student ID.
- Class.
- Batch.
- Examination Name.
- Academic Year.
- Subject-wise maximum marks.
- Subject-wise obtained marks.
- Subject-wise percentage.
- Subject-wise grade.
- Total Obtained Marks.
- Total Maximum Marks.
- Overall Percentage.
- Overall Grade.
- Pass/Fail Status.
- Teacher Remarks.

Features:

- View result.
- Print result.
- Download PDF.
- Search by student.
- Filter by examination.
- Publish results.
- Restrict unpublished results from students.

PDF generation should work with the deployed environment.

---

# 16. REPORT MANAGEMENT

Create a complete reports module.

## Attendance reports

- Daily attendance.
- Monthly attendance.
- Student-wise attendance.
- Class-wise attendance.
- Batch-wise attendance.
- Absentee reports.
- Low attendance reports.

## Academic reports

- Examination results.
- Subject-wise average marks.
- Class-wise performance.
- Batch-wise performance.
- Top performers.
- Students below passing marks.
- Grade distribution.

## Export options

- CSV.
- Printable HTML.
- PDF where appropriate.

Provide useful filters and date ranges.

Reports must use actual database data.

---

# 17. STUDENT FEE MANAGEMENT – OPTIONAL MODULE

Design the architecture so that fee management can be added later.

Potential features:

- Monthly fee records.
- Fee amount.
- Payment date.
- Paid/Pending status.
- Outstanding balance.
- Payment history.
- Receipt generation.

Do not make fee management mandatory for the initial release.

---

# 18. APPLICATION SETTINGS

Create an admin settings page.

Settings:

- Institute Name.
- Institute Logo.
- Institute Address.
- Contact Number.
- Email.
- Academic Year.
- Attendance Threshold.
- Grade Configuration.
- Result Settings.
- Time Zone.
- Date Format.

All settings must be configurable.

---

# 19. ANGULAR FRONTEND ARCHITECTURE

Build the frontend using Angular standalone components.

Suggested structure:

frontend/ src/ app/ core/ auth/ guards/ interceptors/ services/

```
  shared/
    components/
    directives/
    pipes/
    models/

  features/
    dashboard/
    students/
    teachers/
    classes/
    batches/
    subjects/
    attendance/
    examinations/
    marks/
    results/
    reports/
    settings/

  app.component.ts
  app.config.ts
  app.routes.ts

assets/
  images/
  icons/

environments/

```

Requirements:

- Use lazy-loaded routes.
- Use Angular services.
- Use typed API models.
- Use Reactive Forms.
- Use reusable components.
- Use route guards.
- Use HTTP interceptors.
- Implement proper loading and error states.
- Avoid unnecessary duplicate API requests.
- Keep components small and maintainable.
- Follow Angular best practices.

Create separate dashboards and navigation menus based on user role.

---

# 20. FLASK BACKEND ARCHITECTURE

Suggested structure:

backend/ app/ **init**.py config.py extensions.py

```
models/
  user.py
  student.py
  teacher.py
  class_model.py
  batch.py
  subject.py
  attendance.py
  examination.py
  marks.py
  settings.py

routes/
  auth/
  dashboard/
  students/
  teachers/
  classes/
  batches/
  subjects/
  attendance/
  examinations/
  marks/
  results/
  reports/
  settings/

services/
schemas/
utils/

```

migrations/ tests/ requirements.txt run.py

Requirements:

- Use Flask application factory.
- Use Blueprints.
- Use SQLAlchemy.
- Use migrations.
- Use service-layer architecture.
- Validate incoming requests.
- Return consistent JSON.
- Handle exceptions centrally.
- Implement pagination.
- Implement filtering.
- Use transactions for bulk operations.

---

# 21. DATABASE DESIGN

Create PostgreSQL database:

sankalp_classes

Create normalized tables:

1. users
2. students
3. teachers
4. classes
5. batches
6. student_batches
7. subjects
8. class_subjects
9. teacher_assignments
10. attendance
11. examinations
12. examination_subjects
13. marks
14. grade_settings
15. settings
16. audit_logs

Define:

- Primary keys.
- Foreign keys.
- Unique constraints.
- Indexes.
- Relationships.
- Appropriate nullable fields.
- Created timestamps.
- Updated timestamps.

Use database transactions.

Prevent orphan records.

Preserve academic history.

Implement audit logging for important operations such as attendance changes, marks modifications and user management.

Create database migration files.

Provide sample development data separately from production data.

---

# 22. REST API DESIGN

Use a versioned API prefix:

/api/v1/

Example endpoints:

Authentication:

- POST /api/v1/auth/login
- POST /api/v1/auth/logout
- GET /api/v1/auth/me
- POST /api/v1/auth/forgot-password
- POST /api/v1/auth/reset-password

Students:

- GET /api/v1/students
- POST /api/v1/students
- GET /api/v1/students/{id}
- PUT /api/v1/students/{id}
- DELETE /api/v1/students/{id}

Attendance:

- GET /api/v1/attendance
- POST /api/v1/attendance/bulk
- GET /api/v1/attendance/student/{id}
- PUT /api/v1/attendance/{id}

Marks:

- GET /api/v1/marks
- POST /api/v1/marks/bulk
- PUT /api/v1/marks/{id}

Examinations:

- GET /api/v1/examinations
- POST /api/v1/examinations
- PUT /api/v1/examinations/{id}

Dashboard:

- GET /api/v1/dashboard/admin
- GET /api/v1/dashboard/teacher
- GET /api/v1/dashboard/student

Implement endpoints for all other modules.

Use correct HTTP status codes.

Use consistent JSON response structures.

Do not expose sensitive database information in API responses.

Generate API documentation using OpenAPI or Swagger.

---

# 23. SECURITY REQUIREMENTS

Implement:

- Secure password hashing.
- Role-based access control.
- Secure authentication.
- CSRF protection for cookie-based authentication.
- Secure cookies.
- CORS allowlisting.
- SQL injection protection.
- XSS prevention.
- Server-side validation.
- File upload restrictions.
- Login rate limiting.
- Password reset security.
- Environment-based secrets.
- Audit logging.
- HTTPS in production.
- Secure error handling.

Do not trust user roles supplied by Angular.

Always verify authorization on the Flask backend.

Never expose secrets in GitHub repositories.

Do not allow students to access other students' records.

---

# 24. FREE DEPLOYMENT ARCHITECTURE

Prepare the application for independent deployment.

## Frontend

Deploy Angular on Vercel.

Requirements:

- Production build.
- SPA routing configuration.
- Environment-specific API URL.
- HTTPS.
- Proper error handling.

## Backend

Deploy Flask using PythonAnywhere or Render depending on the currently supported free plan.

Requirements:

- Production WSGI server.
- Production environment variables.
- PostgreSQL connection.
- Secure CORS.
- Health-check endpoint.
- Logging.
- Database migrations.

## Database

Use Neon PostgreSQL or another PostgreSQL-compatible provider.

Requirements:

- Database connection string through environment variables.
- SSL database connections when required.
- Connection pooling compatible with hosting.
- Migration instructions.
- Backup and restore instructions.

## Important deployment rules

Do not assume that:

- Free instances never sleep.
- Free databases are permanent.
- Free hosting offers unlimited storage.
- Background workers are always available.

Avoid requiring background workers or scheduled jobs for core functionality.

Create clear deployment documentation.

---

# 25. PROJECT CONFIGURATION AND ENVIRONMENT VARIABLES

Provide:

Frontend:

- Production API URL.
- Development API URL.

Backend:

- SECRET_KEY.
- DATABASE_URL.
- JWT_SECRET_KEY if JWT is used.
- FRONTEND_ORIGIN.
- FLASK_ENV.
- UPLOAD_FOLDER.
- MAX_CONTENT_LENGTH.

Create .env.example files.

Never commit actual .env files.

---

# 26. TESTING

Implement backend unit and integration tests.

Test:

- Login.
- Logout.
- Role permissions.
- Student CRUD.
- Teacher CRUD.
- Class management.
- Attendance creation.
- Duplicate attendance prevention.
- Attendance percentage.
- Examination creation.
- Marks validation.
- Duplicate marks prevention.
- Grade calculation.
- Result generation.
- API authorization.
- Error handling.

Implement frontend tests for:

- Login forms.
- Navigation.
- Route guards.
- Reactive form validation.
- API integration.
- Attendance entry.
- Marks entry.
- Responsive interface.

Test the complete application before deployment.

---

# 27. REQUIRED DOCUMENTATION

Generate a comprehensive README.md.

Include:

1. Project overview.
2. Technology stack.
3. System architecture.
4. Prerequisites.
5. Local installation.
6. Angular setup.
7. Flask setup.
8. PostgreSQL setup.
9. Database migrations.
10. Admin account creation.
11. Running frontend.
12. Running backend.
13. API documentation.
14. Testing.
15. GitHub setup.
16. Frontend deployment.
17. Backend deployment.
18. Database deployment.
19. Production environment variables.
20. Backup and restore.
21. Common errors and solutions.

---

# 28. DEVELOPMENT EXECUTION PLAN

Build the application incrementally.

PHASE 1: Project initialization, Git setup, database architecture and environment configuration.

PHASE 2: Flask application factory, PostgreSQL integration, database models and migrations.

PHASE 3: Authentication, roles, permissions and account management.

PHASE 4: Angular application setup, design system, routing and navigation.

PHASE 5: Admin dashboard.

PHASE 6: Student and teacher management.

PHASE 7: Class, batch and subject management.

PHASE 8: Attendance management.

PHASE 9: Examination and marks management.

PHASE 10: Results and PDF reports.

PHASE 11: Analytics, reporting and settings.

PHASE 12: Security testing, integration testing and bug fixing.

PHASE 13: GitHub integration and free deployment.

Do not generate the entire project as one enormous unstructured response.

Complete one phase at a time.

After each phase:

- List the files created.
- Provide complete source code.
- Explain how to run it.
- Explain how to test it.
- Fix any errors before moving to the next phase.

Do not leave TODO placeholders for required functionality.

Do not claim that a feature works unless it has been implemented.

---

# 29. FINAL ACCEPTANCE CRITERIA

The project is complete only when:

1. Admin can securely log in.
2. Teachers can securely log in.
3. Students can securely log in.
4. Admin can manage students.
5. Admin can manage teachers.
6. Admin can manage classes and batches.
7. Admin can manage subjects.
8. Teachers can mark attendance.
9. Attendance is stored in PostgreSQL.
10. Attendance percentages are calculated correctly.
11. Admin can create examinations.
12. Teachers can enter marks.
13. Marks are validated.
14. Grades are calculated correctly.
15. Student results can be generated.
16. Reports can be downloaded.
17. Role-based permissions work.
18. The application works on desktop and mobile.
19. The frontend communicates with the real backend.
20. The application can be deployed using the documented hosting configuration.

FINAL INSTRUCTION:

Build SANKALP CLASSES as a professional, reliable and secure full-stack educational management platform.

Prioritize functional correctness, database integrity, maintainability, usability, security and affordable deployment.

Start with Phase 1. Do not skip architectural planning or database design.

Provide complete, runnable code and exact terminal commands.

Ask for clarification only when a genuinely essential requirement is missing. Otherwise, use sensible defaults and document them.