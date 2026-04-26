# Render Deployment Guide for SchoolLearner

This guide explains how to deploy the SchoolLearner Flask project on Render.

## 1. Prepare Project

Make sure these files exist:

```text
app.py
db.py
requirements.txt
render.yaml
.python-version
templates/
static/
modules/
```

Install dependencies locally and test first:

```bash
pip install -r requirements.txt
python app.py
```

Open:

```text
http://127.0.0.1:5000
```

## 2. Production Server

Render needs a production WSGI server. `gunicorn` is already included in `requirements.txt`.

```text
gunicorn==22.0.0
```

After adding it, install again locally:

```bash
pip install -r requirements.txt
```

## 3. Create GitHub Repository

Push your project to GitHub.

```bash
git init
git add .
git commit -m "Initial SchoolLearner project"
git branch -M main
git remote add origin YOUR_GITHUB_REPO_URL
git push -u origin main
```

## 4. Create Render Web Service

1. Go to Render:

```text
https://render.com
```

2. Login or create an account.

3. Click `New +`.

4. Select `Web Service`.

5. Connect your GitHub repository.

6. Select the SchoolLearner repository.

## 5. Render Web Service Settings

Use these settings, or deploy using the included `render.yaml` blueprint:

```text
Name: schoollearner
Runtime: Python 3
Branch: main
Build Command: pip install -r requirements.txt
Start Command: gunicorn app:app
```

Important:

```text
app:app
```

Means:

- First `app` = `app.py` file
- Second `app` = Flask app variable inside `app.py`

## 6. Database Setup

SchoolLearner uses MySQL.

Render does not provide managed MySQL directly in the normal free web service flow. You can use:

- Railway MySQL
- PlanetScale
- Aiven MySQL
- Clever Cloud MySQL
- Any external MySQL database

Create a MySQL database named:

```text
schoollearn
```

## 7. Add Environment Variables on Render

In Render dashboard:

1. Open your web service.
2. Go to `Environment`.
3. Add these variables:

```text
DB_HOST=your_mysql_host
DB_PORT=3306
DB_USER=your_mysql_username
DB_PASSWORD=your_mysql_password
DB_NAME=schoollearn
FLASK_ENV=production
SHOW_ADMIN_PANEL=1
```

```text
SECRET_KEY=your_strong_secret_key
PYTHON_VERSION=3.11.11
```

## 8. Deploy

Click:

```text
Create Web Service
```

Render will:

1. Clone your GitHub repository
2. Install requirements
3. Run the start command
4. Give you a live URL

Example URL:

```text
https://schoollearner.onrender.com
```

## 9. First Run

When the app starts, it automatically checks and creates required database tables.

Default admin:

```text
Email: admin@schoollearn.com
Password: admin@123
```

Default student:

```text
Email: dhaval@gmail.com
Password: dhaval@2004
```

## 10. Common Render Errors

### Error: No module named gunicorn

Fix:

Add this to `requirements.txt`:

```text
gunicorn
```

Then commit and push again.

### Error: Application failed to start

Check:

```text
Start Command: gunicorn app:app
```

Also check Render logs.

### Error: Database connection failed

Check environment variables:

```text
DB_HOST
DB_PORT
DB_USER
DB_PASSWORD
DB_NAME
```

Also check that your external MySQL database allows connections from Render.

### Error: Static files not loading

Check that files are inside:

```text
static/
```

Flask serves static files using:

```python
static_folder='static'
```

## 11. Update Deployment

After making changes locally:

```bash
git add .
git commit -m "Update SchoolLearner"
git push
```

Render will automatically redeploy if auto-deploy is enabled.

## 12. Production Checklist

Before final deployment:

- Debug mode off
- MySQL environment variables added
- `gunicorn` added to requirements
- Start command is `gunicorn app:app`
- Static files are committed
- `logo.png` is inside `static/`
- Admin login tested
- Student login tested
- Quiz tested
- Result dashboard tested
- AI chatbot tested
- Mobile responsive view tested

## 13. Final Render Settings Summary

```text
Build Command:
pip install -r requirements.txt

Start Command:
gunicorn app:app

Environment Variables:
DB_HOST
DB_PORT
DB_USER
DB_PASSWORD
DB_NAME
FLASK_ENV
SHOW_ADMIN_PANEL
SECRET_KEY
```

## Developer

Developed by Dhaval Pandor.
