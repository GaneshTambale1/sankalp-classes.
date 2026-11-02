# SANKALP CLASSES — Installation and Deployment Guide

## A. Local development (Windows, VS Code)

Requirements: Python 3.11+ (3.13 suggested), Node **22.22.3+** or Node 24 supported by Angular 22, Git, Docker Desktop, VS Code.

1. Unzip `sankalp-classes.zip`. Open the `sankalp-classes` folder in VS Code.
2. Open a terminal and run `docker compose up -d db` to start a local Postgres database on port 5432.
3. In the `backend` folder, create a Python venv, activate it, run `pip install -r requirements.txt`.
4. Copy `.env.example` to `.env`, then replace both secrets with random strings (`python -c "import secrets; print(secrets.token_urlsafe(48))"` twice).
5. Run `flask db upgrade`, `python manage.py seed-settings`, `python manage.py create-admin`.
6. Run `flask --app run run --port 5000 --debug`. Test `http://127.0.0.1:5000/health`.
7. In a separate terminal `cd frontend && npm install && npm start`. Open `http://localhost:4200`.

The frontend uses `http://localhost:5000/api/v1` defined in `frontend/src/environments/environment.ts`. The backend permits this through `FRONTEND_ORIGIN`.

## B. Free database — Neon PostgreSQL

1. Create a new project at https://console.neon.tech/.
2. Create the database **sankalp_classes** (or keep the Neon default name and use its URL).
3. Copy the **pooled PostgreSQL connection URL** (Neon SSL is normally required; keep `?sslmode=require` as supplied). Protect credentials.
4. `DATABASE_URL` should be the full URL, e.g. `postgresql://USER:PASSWORD@HOST/sankalp_classes?sslmode=require`. The Flask app converts `postgresql://` to `postgresql+psycopg://` automatically.
5. From your local `backend` venv, configure `.env` with that Neon URL and run:

```bash
flask db upgrade
python manage.py seed-settings
python manage.py create-admin
```

This provisions the schema and your first admin on Neon without requiring access to a remote shell. Do **not** use the local Docker database credentials for Neon.

## C. Flask API — Render (testing / small demo)

1. Push the repository to a **private GitHub repository** (never commit real `.env` files).
2. Open https://dashboard.render.com/ -> New -> Web Service. Choose the repository.
3. Configure: Root directory `backend`, runtime Python, instance type Free (only if permitted for your usage).
4. Build command: `pip install -r requirements.txt`.
5. Start command:

```bash
sh -c "flask db upgrade && python manage.py seed-settings && exec gunicorn --bind 0.0.0.0:$PORT --workers 2 --timeout 90 run:app"
```

6. Set the following environment variables (no surrounding quote characters):

| Variable | Value |
|---|---|
| `APP_ENV` | `production` |
| `PYTHON_VERSION` | `3.13.5` |
| `DATABASE_URL` | Neon PostgreSQL URL (SSL) |
| `SECRET_KEY` | Strong random secret, at least 32 characters |
| `JWT_SECRET_KEY` | Different strong random secret, at least 32 characters |
| `FRONTEND_ORIGIN` | Exact frontend URL, e.g. `https://sankalp-classes.pages.dev` |
| `PUBLIC_FRONTEND_URL` | Same frontend URL |

7. Deploy and verify `https://YOUR-RENDER-SERVICE.onrender.com/health` returns JSON containing `status: ok`.
8. Create the admin from your local PC using the same Neon `DATABASE_URL`, **not** through a public API endpoint.

**Why migrations are in Start Command:** Render's pre-deploy command is not available for Free web instances. The included `render.yaml` applies migrations at startup. Use a controlled migration/release process before moving to a multi-instance production plan.

**Important:** Render Free spins down after 15 minutes idle; cold start may take ~1 minute. It has an ephemeral filesystem. There is no permanent local disk for uploaded images. It is **not recommended by Render for production apps**. Avoid using it for real student data without evaluating an appropriate paid hosting plan.

## D. Angular frontend — Cloudflare Pages (recommended free static option)

1. Change `frontend/src/environments/environment.ts` to:

```ts
export const environment = {
  apiUrl: 'https://YOUR-RENDER-SERVICE.onrender.com/api/v1'
};
```

2. Commit and push. Open https://dash.cloudflare.com/ -> **Workers & Pages** -> Create application -> Pages -> import Git repository.
3. Build **root directory**: `frontend`.
4. Build command: `npm install && npm run build` (or just `npm run build` if dependency installation is automatic).
5. Output directory: `dist/frontend/browser`.
6. Set the build environment Node version to **22.22.3+ or compatible Node 24**. Verify build image availability.
7. Deploy, use the `*.pages.dev` URL. Angular SPA redirects are in `frontend/public/_redirects` and copied into the build output.
8. Update Render environment `FRONTEND_ORIGIN` and `PUBLIC_FRONTEND_URL` to the final exact Cloudflare URL, then redeploy Render.
9. Open site, log in, and verify students/attendance endpoints in browser network tab.

## E. Angular frontend — Vercel (personal testing or paid commercial use)

Vercel Hobby is **for personal, noncommercial use only**. A live paid coaching institute is commercial, so **do not use Vercel Hobby for that deployment**; use an eligible Vercel paid plan or an appropriate alternative.

1. Push repository; import into https://vercel.com/new.
2. Set Root Directory `frontend`, Framework Preset `Other`, Build Command `npm run build`, Output Directory `dist/frontend/browser`.
3. `frontend/vercel.json` includes a fallback rewrite to `/index.html` for Angular routes.
4. Configure the public API URL in `environment.ts`, commit and redeploy (this setting is compiled into the frontend).
5. Update Render `FRONTEND_ORIGIN` and `PUBLIC_FRONTEND_URL` to your deployed HTTPS Vercel URL.

## F. GitHub (initial push)

Run in the unzipped repository root:

```bash
git init
git add .
git commit -m "Initial Sankalp Classes application"
git branch -M main
git remote add origin https://github.com/YOUR_ACCOUNT/YOUR_PRIVATE_REPOSITORY.git
git push -u origin main
```

Create the private repository first, without a README, and replace the placeholder URL. Confirm with `git status` that you are **not** tracking `.env`, private keys, or database dumps.

## G. PostgreSQL backups

Use a secure shell with `pg_dump` installed and the Neon connection URL available as an environment variable:

```bash
pg_dump "$DATABASE_URL" --format=custom --no-owner --file=sankalp-backup.dump
```

To restore **into a separate empty test database** (never blindly overwrite live production):

```bash
pg_restore --dbname="$RESTORE_DATABASE_URL" --no-owner --clean --if-exists sankalp-backup.dump
```

On Windows PowerShell, use `$env:DATABASE_URL` rather than `$DATABASE_URL`; see PostgreSQL documentation for `pg_dump` tooling and SSL. Store backups encrypted and restrict access.

## H. Password resets and email

For password recovery, set `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, and `SMTP_FROM` in the backend environment. Reset tokens expire after 30 minutes and are stored hashed. **Render Free blocks outbound SMTP ports 25, 465, and 587**, so this path will not deliver mail there. Use a compatible transactional email HTTPS API integration or move to a suitable hosting plan before promising password recovery to users. For now, the administrator can reset a student/teacher password through the edit form.

## I. Common issues

- **`connection refused`** — Postgres container not ready or `DATABASE_URL` wrong. Run `docker compose ps` and `docker compose logs db`.
- **`ModuleNotFoundError: flask`** — activate the `.venv`, then install `requirements.txt`.
- **`ng: command not found`** — `npm install` in `frontend`, then `npm start` (local CLI is used).
- **Node version incompatible** — upgrade to Node.js 22.22.3+ or supported Node 24+.
- **CORS error** — set Render `FRONTEND_ORIGIN` to the frontend origin without trailing slash and redeploy.
- **`401`** — login again; access tokens expire after two hours and are invalidated on logout.
- **`403`** — the account lacks permission or the teacher is not assigned the batch/subject.
- **Empty dashboard** — create academic records and enter attendance/marks; statistics are not mocked.
- **`404` when refreshing a frontend page** — SPA fallback must be enabled (`_redirects` or Vercel rewrite).
- **Failed migration** — verify database URL and network access, then check Alembic revision using `flask db current`.

## J. Production readiness

For an active institute: replace demo hosting where necessary, configure HTTPS, backups and retention policies; establish a breach-response plan, access logs, enrollment history rules, monitoring, automated deployment testing, secure token storage, and independent security review. Do not upload actual children's data until these controls are in place.
