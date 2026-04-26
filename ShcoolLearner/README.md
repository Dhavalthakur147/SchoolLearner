# SchoolLearner - Online Learning Management System

SchoolLearner is a Flask-based online learning management system for students and admins. It supports subject-wise MCQ quizzes, one-line questions, student analytics, result history, admin question management, uploaded marks, AI/Wikipedia help chatbot, and a clean green-white responsive UI.

## Features

- Student registration and login
- Admin login and admin dashboard
- Subject-wise MCQ quizzes
- One-line question practice
- Quiz result saving and progress tracking
- Student analysis dashboard with charts
- Quiz result history page
- PDF result report download
- Admin question add, edit, delete, and subject-wise management
- Admin marks/result upload
- Search and filter for subjects, questions, results, and recent activity
- Notification strip for quiz/result/admin updates
- AI chatbot with math solving and Wikipedia summaries
- Responsive green-white UI with rounded cards and soft shadows

## Tech Stack

- Backend: Flask
- Authentication: Flask-Login
- Database: MySQL
- Frontend: HTML, CSS, JavaScript
- Charts: Chart.js CDN
- Static assets: `static/`
- Templates: `templates/`

## Project Structure

```text
SchoolLearner/
├── app.py
├── db.py
├── requirements.txt
├── vercel.json
├── README.md
├── modules/
│   ├── computer_questions.py
│   ├── english_questions.py
│   ├── gujarati_questions.py
│   ├── mathematics_questions.py
│   ├── one_line_questions.py
│   ├── science_questions.py
│   └── social_science_questions.py
├── static/
│   ├── logo.png
│   ├── home.css
│   ├── styles.css
│   └── js/
│       ├── main.js
│       ├── one_line.js
│       └── quiz.js
└── templates/
    ├── admin.html
    ├── base.html
    ├── index.html
    ├── login.html
    ├── one_line_template.html
    ├── quiz_template.html
    ├── register.html
    ├── student_dashboard.html
    └── student_results.html
```

## Database Configuration

The app uses MySQL. Database connection values are read from environment variables in `db.py`.

Default values:

```text
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=
DB_NAME=schoollearn
```

Create a MySQL database before running:

```sql
CREATE DATABASE schoollearn;
```

Or import the ready database script:

```bash
mysql -u root -p < database.sql
```

The application automatically ensures required tables, default subjects, default admin, and default student when `app.py` starts.

## Installation

1. Create and activate a virtual environment.

```bash
python -m venv .venv
.venv\Scripts\activate
```

2. Install dependencies.

```bash
pip install -r requirements.txt
```

3. Configure MySQL environment variables if your database settings are different.

```bash
set DB_HOST=localhost
set DB_PORT=3306
set DB_USER=root
set DB_PASSWORD=your_password
set DB_NAME=schoollearn
```

4. Run the app.

```bash
python app.py
```

5. Open the website.

```text
http://127.0.0.1:5000
```

## Default Accounts

Admin:

```text
Email: admin@schoollearn.com
Password: admin@123
```

Default student:

```text
Email: dhaval@gmail.com
Password: dhaval@2004
```

## Main Pages

| Page | URL |
| --- | --- |
| Home | `/` |
| Student login | `/student-login` |
| Admin login | `/admin-login` |
| Register | `/register` |
| Student dashboard | `/profile` |
| Student result history | `/student/results` |
| Result PDF download | `/student/results/pdf` |
| Admin dashboard | `/admin` |
| MCQ quiz | `/quiz/<subject>` |
| One-line practice | `/one-line/<subject>` |

Supported subject keys:

```text
computer
math
science
english
gujarati
social-science
```

## API Routes

| API | Method | Purpose |
| --- | --- | --- |
| `/api/questions/<subject>` | GET | Load MCQ questions |
| `/api/one-line-questions/<subject>` | GET | Load one-line questions |
| `/api/quiz/progress` | POST | Save quiz score |
| `/api/student/analytics` | GET | Student analytics data |
| `/api/student/results` | GET | Student uploaded result analytics |
| `/api/profile` | POST | Update student profile |
| `/api/chatbot` | POST | AI chatbot reply |
| `/api/leaderboard` | GET | Quiz leaderboard |

## Admin Features

Admins can:

- View total users and total questions
- Enable or disable subject quizzes
- Add new custom MCQ questions
- Edit custom MCQ questions
- Delete base or custom questions
- Search/filter question list
- Upload student marks
- View uploaded result analytics
- Search/filter student result records
- Manage users and admin role status

Note: `ADMIN_VIEW_ONLY` is currently set in `app.py`. If it is `True`, some admin actions are blocked.

## Student Features

Students can:

- Register and login
- Attempt MCQ quizzes
- Practice one-line questions
- View dashboard analytics
- View latest score and average score
- View subject-wise performance
- View recent activity
- View result history
- Download result PDF
- Update profile details
- Use chatbot for study help, math answers, and Wikipedia summaries

## AI Chatbot

The chatbot supports:

- Basic study guidance
- Quiz and dashboard help
- Math expression solving, for example `7 + 4 = ?`
- Wikipedia summaries for general questions

The chatbot uses Python standard library requests to call Wikipedia. If internet access is unavailable, Wikipedia answers may not work.

## Frontend Notes

Global styles are in:

```text
static/styles.css
```

Home page styles are in:

```text
static/home.css
```

JavaScript files:

```text
static/js/main.js
static/js/quiz.js
static/js/one_line.js
```

The UI uses:

- White and green theme
- Rounded cards
- Soft shadows
- Responsive layouts
- Hover effects
- Fixed bottom-right developer credit

## Security Notes

Implemented security basics:

- Password hashing with Werkzeug
- Flask-Login session handling
- Email validation
- Minimum password length
- Login/register error messages
- HTTP-only session cookie setting
- SameSite session cookie setting

Recommended future improvements:

- CSRF protection for forms
- Rate limiting for login attempts
- Stronger password policy
- Production secret key from environment variable
- HTTPS-only cookies in production

## Deployment Notes

For production deployment:

- Set a strong `app.secret_key` from an environment variable
- Configure MySQL environment variables
- Use HTTPS
- Set `FLASK_ENV=production`
- Verify `vercel.json` or hosting platform configuration
- Do not expose database credentials in source code

## Code Quality Notes

Current organization:

- `app.py` contains Flask routes, schema setup, analytics, and helpers
- `db.py` contains MySQL connection logic
- `modules/` contains subject question banks
- `templates/` contains Jinja HTML templates
- `static/` contains CSS, JavaScript, and images

Recommended future refactor:

- Move routes into Flask blueprints
- Move schema setup into migration files
- Move analytics helpers into a service module
- Move chatbot logic into a separate module
- Add automated tests for quiz scoring and admin question management

## Developer

Developed by Dhaval Pandor.
