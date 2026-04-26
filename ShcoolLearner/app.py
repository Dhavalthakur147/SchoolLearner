import os
import sys
import uuid
import json
import ast
import operator
import re
import urllib.parse
import urllib.request
from flask import Flask, Response, request, jsonify, render_template, redirect, url_for, flash
from flask_cors import CORS
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timezone
from db import get_connection as get_db_connection, initialize_database_from_sql

# Add modul directory to path BEFORE importing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'modul'))

# Now import the question modules
try:
    from modules.computer_questions import get_questions as get_computer_questions
    from modules.mathematics_questions import get_questions as get_math_questions
    from modules.science_questions import get_questions as get_science_questions
    from modules.english_questions import get_questions as get_english_questions
    from modules.gujarati_questions import get_questions as get_gujarati_questions
    from modules.social_science_questions import get_questions as get_social_science_questions
    from modules.one_line_questions import get_one_line_questions
except ImportError as e:
    print(f"Warning: Could not import question modules: {e}")
    # Provide dummy functions if imports fail
    def get_computer_questions():
        return []
    def get_math_questions():
        return []
    def get_science_questions():
        return []
    def get_english_questions():
        return []
    def get_gujarati_questions():
        return []
    def get_social_science_questions():
        return []
    def get_one_line_questions(subject=None):
        return [] if subject else {}

# Initialize Flask app
app = Flask(__name__, 
    template_folder='templates',  # Ensure templates are in a 'templates' folder
    static_folder='static'        # Static files folder
)

# Configure Flask app
app.secret_key = "dhaval@2004"
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    SESSION_COOKIE_SECURE=os.getenv('FLASK_ENV') == 'production',
)

# Configure Jinja2
app.jinja_env.auto_reload = True
app.config['TEMPLATES_AUTO_RELOAD'] = True

# Enable CORS
CORS(app, supports_credentials=True)

# Simple User class for Flask-Login
class User(UserMixin):
    def __init__(self, id, username, email):
        self.id = id
        self.username = username
        self.email = email
        self.password_hash = ""
        self.grade = ""
        self.school = ""
        self.joined_at = datetime.now(timezone.utc)
        self.is_admin = False
        self.progress = {}
        self.avatar_url = ""

ADMIN_EMAILS = {"pandordhaval05@gmail.com"}
DEFAULT_ADMIN_PASSWORD = "admin@123"
DEFAULT_USER_EMAIL = "dhaval@gmail.com"
DEFAULT_USER_PASSWORD = "dhaval@2004"
ADMIN_VIEW_ONLY = True  # Set to True to disable admin actions and make dashboard view-only
SHOW_ADMIN_PANEL = os.getenv('SHOW_ADMIN_PANEL', '1').lower() in {'1', 'true', 'yes', 'on'}

QUIZ_SUBJECTS = {
    'computer': 'Computer',
    'math': 'Mathematics',
    'mathematics': 'Mathematics',
    'science': 'Science',
    'english': 'English',
    'gujarati': 'Gujarati',
    'social-science': 'Social Science',
    'social_science': 'Social Science',
}
ADMIN_SUBJECT_KEYS = ['computer', 'math', 'science', 'english', 'gujarati', 'social-science']
SUBJECT_KEY_TO_NAME = {key: QUIZ_SUBJECTS[key] for key in ADMIN_SUBJECT_KEYS}


def db_fetch_one(query, params=None):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(query, params or ())
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return row


def db_fetch_all(query, params=None):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(query, params or ())
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows


def db_execute(query, params=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(query, params or ())
    conn.commit()
    last_id = cursor.lastrowid
    cursor.close()
    conn.close()
    return last_id


def db_execute_many(query, params_list):
    if not params_list:
        return 0
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.executemany(query, params_list)
    conn.commit()
    rowcount = cursor.rowcount
    cursor.close()
    conn.close()
    return rowcount


def build_user_from_student_row(row):
    if not row:
        return None
    user = User(f"student:{row['student_id']}", row['full_name'], row['email'])
    user.password_hash = row.get('password_hash', '')
    user.grade = row.get('grade') or ''
    user.school = row.get('school') or ''
    user.avatar_url = row.get('avatar_url') or ''
    user.joined_at = row.get('created_at') or datetime.now(timezone.utc)
    user.is_admin = False
    return user


def build_user_from_admin_row(row):
    if not row:
        return None
    user = User(f"admin:{row['admin_id']}", row['username'], row['email'])
    user.password_hash = row.get('password_hash', '')
    user.grade = 'N/A'
    user.school = 'SchoolLearn'
    user.joined_at = row.get('created_at') or datetime.now(timezone.utc)
    user.is_admin = True
    return user


def parse_user_id(user_id):
    if not user_id:
        return None, None
    if ':' in user_id:
        prefix, raw = user_id.split(':', 1)
        try:
            return prefix, int(raw)
        except ValueError:
            return prefix, None
    try:
        return 'student', int(user_id)
    except ValueError:
        return None, None


def get_subject_map():
    rows = db_fetch_all(
        "SELECT subject_id, subject_key, subject_name, is_enabled FROM subject"
    )
    return {row['subject_key']: row for row in rows}


def ensure_subjects():
    for key, name in SUBJECT_KEY_TO_NAME.items():
        db_execute(
            "INSERT INTO subject (subject_key, subject_name, is_enabled) "
            "VALUES (%s, %s, 1) "
            "ON DUPLICATE KEY UPDATE subject_name = VALUES(subject_name)",
            (key, name)
        )


def ensure_base_questions_seeded():
    subjects = get_subject_map()
    seed_rows = []
    for key in ADMIN_SUBJECT_KEYS:
        subject = subjects.get(key)
        if not subject:
            continue
        base_questions = get_base_questions_for_subject(key)
        for idx, q in enumerate(base_questions):
            base_key = f"{key}:{idx}"
            options = list(q.get('options') or [])
            while len(options) < 4:
                options.append('')
            seed_rows.append((
                subject['subject_id'],
                q.get('question', ''),
                options[0],
                options[1],
                options[2],
                options[3],
                int(q.get('answer', 0)),
                q.get('explanation', ''),
                'base',
                base_key
            ))
    db_execute_many(
        "INSERT IGNORE INTO question "
        "(subject_id, question_text, option_a, option_b, option_c, option_d, answer_index, explanation, source, base_key) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
        seed_rows
    )


def ensure_default_admin():
    # Always ensure a built-in admin exists for first-time login.
    if not get_admin_by_email('admin@schoollearn.com'):
        db_execute(
            "INSERT INTO admin (username, email, password_hash) VALUES (%s, %s, %s)",
            ('Admin', 'admin@schoollearn.com', generate_password_hash(DEFAULT_ADMIN_PASSWORD))
        )

    # Also ensure any emails in ADMIN_EMAILS are present as admin users.
    for email in sorted(ADMIN_EMAILS):
        if get_admin_by_email(email):
            continue
        db_execute(
            "INSERT INTO admin (username, email, password_hash) VALUES (%s, %s, %s)",
            (email.split('@')[0], email, generate_password_hash(DEFAULT_ADMIN_PASSWORD))
        )


def ensure_default_user():
    existing_user = get_student_by_email(DEFAULT_USER_EMAIL)
    if existing_user:
        db_execute(
            "UPDATE student SET password_hash = %s WHERE student_id = %s",
            (generate_password_hash(DEFAULT_USER_PASSWORD), existing_user['student_id'])
        )
        ADMIN_EMAILS.discard(DEFAULT_USER_EMAIL)
        return

    db_execute(
        "INSERT INTO student (full_name, email, password_hash, grade, school) "
        "VALUES (%s, %s, %s, %s, %s)",
        ('Dhaval', DEFAULT_USER_EMAIL, generate_password_hash(DEFAULT_USER_PASSWORD), '10th', 'SchoolLearn')
    )
    ADMIN_EMAILS.discard(DEFAULT_USER_EMAIL)


# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'student_login'

def get_student_by_email(email):
    return db_fetch_one("SELECT * FROM student WHERE email = %s", (email,))


def get_student_by_id(student_id):
    return db_fetch_one("SELECT * FROM student WHERE student_id = %s", (student_id,))


def get_admin_by_email(email):
    return db_fetch_one("SELECT * FROM admin WHERE email = %s", (email,))


def get_admin_by_id(admin_id):
    return db_fetch_one("SELECT * FROM admin WHERE admin_id = %s", (admin_id,))


def email_in_use(email):
    return bool(get_student_by_email(email) or get_admin_by_email(email))


def get_all_users_for_admin():
    students = db_fetch_all("SELECT * FROM student ORDER BY created_at DESC")
    admins = db_fetch_all("SELECT * FROM admin ORDER BY created_at DESC")
    admin_emails = {row['email'].lower() for row in admins if row.get('email')}
    users = [
        build_user_from_student_row(row)
        for row in students
        if row.get('email', '').lower() not in admin_emails
    ]
    users.extend(build_user_from_admin_row(row) for row in admins)
    return sorted(users, key=lambda u: u.joined_at, reverse=True)


def is_admin_user(user):
    return bool(user and getattr(user, 'is_admin', False))


def normalize_subject(subject):
    return subject.lower().strip()


def canonical_subject(subject):
    normalized = normalize_subject(subject)
    if normalized == 'mathematics':
        return 'math'
    if normalized == 'social_science':
        return 'social-science'
    return normalized


def parse_iso_datetime(value):
    if isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(str(value))
    except Exception:
        return datetime.now(timezone.utc)


def percentage_from_marks(score, total):
    if total <= 0:
        return 0
    return round((score / total) * 100, 1)


def sanitize_avatar_url(value):
    url = (value or '').strip()
    if not url:
        return ''
    if len(url) > 500:
        return ''
    lowered = url.lower()
    allowed = (
        lowered.startswith('http://')
        or lowered.startswith('https://')
        or lowered.startswith('/static/')
    )
    return url if allowed else ''


def is_valid_email(email):
    return bool(re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', email or ''))


def is_strong_password(password):
    return len(password or '') >= 6


def fetch_wikipedia_summary(query):
    search_term = (query or '').strip()
    if not search_term:
        return None

    encoded_query = urllib.parse.quote(search_term)
    search_url = (
        "https://en.wikipedia.org/w/api.php"
        f"?action=query&list=search&srsearch={encoded_query}&format=json&srlimit=1"
    )
    headers = {
        'User-Agent': 'SchoolLearnerStudentChatbot/1.0',
        'Accept': 'application/json',
    }

    try:
        search_request = urllib.request.Request(search_url, headers=headers)
        with urllib.request.urlopen(search_request, timeout=4) as response:
            search_data = json.loads(response.read().decode('utf-8'))

        results = search_data.get('query', {}).get('search', [])
        if not results:
            return None

        title = results[0].get('title', '').strip()
        if not title:
            return None

        summary_url = (
            "https://en.wikipedia.org/api/rest_v1/page/summary/"
            f"{urllib.parse.quote(title)}"
        )
        summary_request = urllib.request.Request(summary_url, headers=headers)
        with urllib.request.urlopen(summary_request, timeout=4) as response:
            summary_data = json.loads(response.read().decode('utf-8'))

        summary = (summary_data.get('extract') or '').strip()
        page_url = summary_data.get('content_urls', {}).get('desktop', {}).get('page', '')
        if not summary:
            return None

        if len(summary) > 520:
            summary = summary[:520].rsplit(' ', 1)[0] + '...'

        return {
            'title': title,
            'summary': summary,
            'url': page_url,
        }
    except Exception:
        return None


def should_search_wikipedia(message):
    lowered = (message or '').lower()
    wikipedia_words = ('wikipedia', 'wiki', 'who is', 'what is', 'tell me about', 'explain')
    return any(word in lowered for word in wikipedia_words)


def clean_wikipedia_query(message):
    query = (message or '').strip()
    lowered = query.lower()
    prefixes = (
        'wikipedia',
        'wiki',
        'who is',
        'what is',
        'tell me about',
        'explain',
    )
    for prefix in prefixes:
        if lowered.startswith(prefix):
            query = query[len(prefix):].strip(" :-?")
            break
    return query or message


def format_wikipedia_reply(wiki_result):
    source = f"\n\nSource: {wiki_result['url']}" if wiki_result.get('url') else ''
    return f"{wiki_result['title']}: {wiki_result['summary']}{source}"


def solve_math_expression(message):
    expression = (message or '').strip().lower()
    replacements = {
        '×': '*',
        'x': '*',
        '÷': '/',
        'plus': '+',
        'minus': '-',
        'into': '*',
        'multiply': '*',
        'multiplied by': '*',
        'divided by': '/',
    }
    for old, new in replacements.items():
        expression = expression.replace(old, new)

    allowed_chars = set('0123456789+-*/(). %')
    expression = expression.replace('=', ' ').replace('?', ' ')
    expression = ''.join(char for char in expression if char in allowed_chars).strip()

    if not expression or not any(char.isdigit() for char in expression):
        return None
    if not any(op in expression for op in '+-*/%'):
        return None

    allowed_ops = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Mod: operator.mod,
        ast.USub: operator.neg,
        ast.UAdd: operator.pos,
    }

    def evaluate(node):
        if isinstance(node, ast.Expression):
            return evaluate(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in allowed_ops:
            return allowed_ops[type(node.op)](evaluate(node.left), evaluate(node.right))
        if isinstance(node, ast.UnaryOp) and type(node.op) in allowed_ops:
            return allowed_ops[type(node.op)](evaluate(node.operand))
        raise ValueError('Unsupported math expression')

    try:
        result = evaluate(ast.parse(expression, mode='eval'))
    except Exception:
        return None

    if isinstance(result, float) and result.is_integer():
        result = int(result)

    return f"{message.strip()} Answer: {result}"


def build_student_chatbot_reply(message, user):
    text = (message or '').strip()
    lowered = text.lower()

    if not text:
        return "Ask me about subjects, quizzes, marks, dashboard, or how to study for your next test."

    math_answer = solve_math_expression(text)
    if math_answer:
        return math_answer

    if should_search_wikipedia(text):
        wiki_result = fetch_wikipedia_summary(clean_wikipedia_query(text))
        if wiki_result:
            return format_wikipedia_reply(wiki_result)

    student_name = getattr(user, 'username', '') or 'student'
    subject_matches = [
        name for key, name in SUBJECT_KEY_TO_NAME.items()
        if key in lowered or name.lower() in lowered
    ]

    if any(word in lowered for word in ('hello', 'hi', 'hey', 'kem cho', 'namaste')):
        return f"Hi {student_name}! I can help you choose a subject, understand quiz results, or make a quick study plan."

    if any(word in lowered for word in ('subject', 'subjects', 'course', 'courses')):
        subjects = ', '.join(SUBJECT_KEY_TO_NAME.values())
        return f"You can practice these subjects: {subjects}. Pick the subject you feel least confident in and complete one quiz first."

    if any(word in lowered for word in ('quiz', 'test', 'mcq', 'question', 'practice')):
        if subject_matches:
            subject = subject_matches[0]
            return f"For {subject}, start with one quiz, review every wrong answer, then retry after 20 minutes. Focus on accuracy first, speed second."
        return "For quiz practice, choose one subject, attempt the MCQs, note weak topics, and revise those before taking another quiz."

    if any(word in lowered for word in ('marks', 'score', 'result', 'percentage', 'rank', 'leaderboard')):
        if not getattr(user, 'is_authenticated', False):
            return "Please log in as a student to see your marks, quiz results, percentage, and leaderboard details."
        analytics = calculate_student_analytics(user)
        total = analytics.get('total_quizzes', 0)
        average = analytics.get('avg_score', 0)
        subject_performance = analytics.get('subject_performance') or []
        best_subject = subject_performance[0].get('subject') if subject_performance else 'not available yet'
        return f"Your dashboard tracks quiz attempts, average score, and subject progress. Right now it shows {total} quizzes, {average}% average, and best subject: {best_subject}."

    if any(word in lowered for word in ('dashboard', 'profile', 'pdf', 'download')):
        return "Use the Profile page to update grade, school, and photo. You can also download your result PDF from the dashboard."

    if any(word in lowered for word in ('study', 'learn', 'plan', 'revision', 'revise', 'tips')):
        return "Try this plan: 25 minutes study, 5 minutes break, then 10 MCQs. Write down only the mistakes and revise that list before your next quiz."

    if any(word in lowered for word in ('math', 'mathematics')):
        return "For Mathematics, solve examples step by step first. After each quiz, redo only the wrong sums without looking at the answer."

    if 'science' in lowered:
        return "For Science, make short notes for formulas, definitions, and diagrams. Practice MCQs after each topic so concepts stay fresh."

    if 'english' in lowered:
        return "For English, revise grammar rules with examples, then practice vocabulary and comprehension questions daily."

    if 'gujarati' in lowered:
        return "For Gujarati, read the lesson once, note hard words, then practice grammar and literature questions separately."

    if 'computer' in lowered or 'programming' in lowered:
        return "For Computer, understand the concept first, then practice small examples. For programming, trace code line by line."

    if 'social' in lowered or 'history' in lowered or 'geography' in lowered or 'civics' in lowered:
        return "For Social Science, use timelines for history, maps for geography, and short point-wise notes for civics."

    wiki_result = fetch_wikipedia_summary(clean_wikipedia_query(text))
    if wiki_result:
        return format_wikipedia_reply(wiki_result)

    return "I could not find a reliable answer for that. Please ask with a little more detail, like 'What is photosynthesis?' or 'Explain gravity'."


def get_marks_for_user(user):
    prefix, student_id = parse_user_id(user.id)
    if prefix != 'student' or not student_id:
        return []
    return db_fetch_all(
        "SELECT m.mark_id AS id, m.student_id, s.full_name AS student_name, s.email AS student_email, "
        "m.exam_name, m.subject_name AS subject, m.score, m.total, m.percentage, m.remarks, "
        "m.recorded_at, m.uploaded_by, m.uploaded_at "
        "FROM marks m "
        "JOIN student s ON m.student_id = s.student_id "
        "WHERE m.student_id = %s "
        "ORDER BY m.recorded_at DESC",
        (student_id,)
    )


def get_marks_for_admin():
    return db_fetch_all(
        "SELECT m.mark_id AS id, m.student_id, s.full_name AS student_name, s.email AS student_email, "
        "m.exam_name, m.subject_name AS subject, m.score, m.total, m.percentage, m.remarks, "
        "m.recorded_at, m.uploaded_by, m.uploaded_at "
        "FROM marks m "
        "JOIN student s ON m.student_id = s.student_id "
        "ORDER BY m.recorded_at DESC"
    )


def get_student_quiz_history(user):
    prefix, student_id = parse_user_id(user.id)
    if prefix != 'student' or not student_id:
        return []
    rows = get_quiz_results_for_student(student_id)
    history = []
    for item in rows:
        attempted_at = parse_iso_datetime(str(item.get('attempted_at', '')))
        history.append({
            'subject': item.get('subject_name') or item.get('subject_key'),
            'score': int(item.get('score', 0)),
            'total_questions': int(item.get('total_questions', 0)),
            'percentage': float(item.get('percentage', 0)),
            'attempted_at': item.get('attempted_at'),
            'attempted_at_display': attempted_at.strftime('%Y-%m-%d %H:%M UTC'),
        })
    return history


def get_student_notifications(user):
    notifications = []
    subjects = get_subject_map()
    enabled_subjects = [
        row.get('subject_name') for row in subjects.values()
        if row.get('is_enabled', 1)
    ]
    if enabled_subjects:
        notifications.append({
            'title': 'Quizzes available',
            'message': f"{len(enabled_subjects)} subjects are ready for practice.",
            'type': 'quiz',
        })

    if getattr(user, 'is_authenticated', False) and not is_admin_user(user):
        history = get_student_quiz_history(user)
        if history:
            latest = history[0]
            notifications.append({
                'title': 'Latest result generated',
                'message': f"{latest['subject']}: {latest['score']}/{latest['total_questions']} ({latest['percentage']}%).",
                'type': 'result',
            })
        marks = get_marks_for_user(user)
        if marks:
            latest_mark = marks[0]
            notifications.append({
                'title': 'Admin update',
                'message': f"{latest_mark.get('exam_name', 'Exam')} result uploaded for {latest_mark.get('subject', 'General')}.",
                'type': 'admin',
            })
    else:
        notifications.append({
            'title': 'Welcome to SchoolLearner',
            'message': 'Login to track results, analytics, and personalized progress.',
            'type': 'admin',
        })

    return notifications[:5]


def build_dashboard_summary(analytics, result_analytics, history, available_subjects):
    subject_performance = analytics.get('subject_performance') or []
    latest_attempt = history[0] if history else None
    best_subject = subject_performance[0] if subject_performance else None
    weak_subject = subject_performance[-1] if subject_performance else None
    completed_subjects = len(subject_performance)
    total_subjects = max(1, len(available_subjects))
    coverage = round((completed_subjects / total_subjects) * 100, 1)

    if latest_attempt:
        latest_score = latest_attempt.get('percentage', 0)
    else:
        latest_score = 0

    if analytics.get('total_quizzes', 0) == 0:
        recommendation = "Start with any available subject and complete your first quiz."
        status = "Getting started"
    elif weak_subject:
        recommendation = f"Revise {weak_subject.get('subject')} next and retry a short quiz."
        status = "Keep improving"
    else:
        recommendation = "Continue practicing to unlock subject-wise insights."
        status = "Building progress"

    subject_name_to_key = {name: key for key, name in SUBJECT_KEY_TO_NAME.items()}
    recommended_subject_key = 'math'
    if weak_subject and weak_subject.get('subject') in subject_name_to_key:
        recommended_subject_key = subject_name_to_key[weak_subject.get('subject')]
    elif available_subjects:
        recommended_subject_key = available_subjects[0].get('key', 'math')

    return {
        'latest_score': latest_score,
        'latest_subject': latest_attempt.get('subject') if latest_attempt else 'No attempt yet',
        'best_subject': best_subject.get('subject') if best_subject else 'No data yet',
        'best_subject_average': best_subject.get('average') if best_subject else 0,
        'focus_subject': weak_subject.get('subject') if weak_subject else 'Start practicing',
        'focus_average': weak_subject.get('average') if weak_subject else 0,
        'subject_coverage': coverage,
        'available_subject_count': len(available_subjects),
        'result_records': result_analytics.get('total_records', 0),
        'status': status,
        'recommendation': recommendation,
        'recommended_subject_key': recommended_subject_key,
    }


def get_quiz_results_for_student(student_id):
    return db_fetch_all(
        "SELECT r.result_id, r.score, r.total_questions, r.percentage, r.attempted_at, "
        "s.subject_key, s.subject_name "
        "FROM result r "
        "JOIN subject s ON r.subject_id = s.subject_id "
        "WHERE r.student_id = %s "
        "ORDER BY r.attempted_at DESC",
        (student_id,)
    )


def get_quiz_leaderboard(limit=10):
    limit = max(1, min(int(limit or 10), 50))
    return db_fetch_all(
        "SELECT s.student_id, s.full_name AS student_name, "
        "COUNT(r.result_id) AS attempts, "
        "ROUND(AVG(r.percentage), 1) AS average_percentage, "
        "ROUND(MAX(r.percentage), 1) AS best_percentage "
        "FROM result r "
        "JOIN student s ON r.student_id = s.student_id "
        "GROUP BY s.student_id, s.full_name "
        "HAVING COUNT(r.result_id) > 0 "
        "ORDER BY average_percentage DESC, best_percentage DESC, attempts DESC "
        "LIMIT %s",
        (limit,)
    )


def pdf_escape(text):
    return str(text).replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def build_simple_pdf(lines, title="SchoolLearn Report"):
    page_size = 44
    chunks = [lines[i:i + page_size] for i in range(0, len(lines), page_size)] or [[]]

    objects = []
    page_count = len(chunks)
    first_page_obj = 3
    font_obj = first_page_obj + (page_count * 2)

    objects.append("<< /Type /Catalog /Pages 2 0 R >>".encode("latin-1"))
    kids = " ".join(f"{first_page_obj + i * 2} 0 R" for i in range(page_count))
    objects.append(f"<< /Type /Pages /Kids [{kids}] /Count {page_count} >>".encode("latin-1"))

    for idx, chunk in enumerate(chunks):
        page_obj = first_page_obj + idx * 2
        content_obj = page_obj + 1
        objects.append(
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            f"/Resources << /Font << /F1 {font_obj} 0 R >> >> "
            f"/Contents {content_obj} 0 R >>".encode("latin-1")
        )

        stream_lines = [
            "BT",
            "/F1 12 Tf",
            "50 760 Td",
            "14 TL",
            f"({pdf_escape(title)} - Page {idx + 1}) Tj",
            "T*",
            "T*",
        ]
        for line in chunk:
            stream_lines.append(f"({pdf_escape(line)}) Tj")
            stream_lines.append("T*")
        stream_lines.append("ET")
        stream_data = "\n".join(stream_lines).encode("latin-1", errors="replace")
        objects.append(
            f"<< /Length {len(stream_data)} >>\nstream\n".encode("latin-1")
            + stream_data
            + b"\nendstream"
        )

    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")

    output = bytearray()
    output.extend(b"%PDF-1.4\n")
    offsets = [0]
    for index, obj_data in enumerate(objects, start=1):
        offsets.append(len(output))
        output.extend(f"{index} 0 obj\n".encode("latin-1"))
        output.extend(obj_data)
        output.extend(b"\nendobj\n")

    xref_start = len(output)
    output.extend(f"xref\n0 {len(objects) + 1}\n".encode("latin-1"))
    output.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        output.extend(f"{offset:010d} 00000 n \n".encode("latin-1"))
    output.extend(
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_start}\n%%EOF".encode("latin-1")
    )
    return bytes(output)


def calculate_result_analytics_for_user(user):
    entries = get_marks_for_user(user)
    total_records = len(entries)
    if not total_records:
        return {
            'total_records': 0,
            'average_percentage': 0,
            'best_percentage': 0,
            'total_scored': 0,
            'total_possible': 0,
            'subject_summary': [],
            'recent_results': [],
        }

    total_scored = sum(float(item.get('score', 0)) for item in entries)
    total_possible = sum(float(item.get('total', 0)) for item in entries)
    percentages = [float(item.get('percentage', 0)) for item in entries]
    average_percentage = round(sum(percentages) / total_records, 1)
    best_percentage = round(max(percentages), 1)

    subject_rollup = {}
    for item in entries:
        subject = item.get('subject', 'General')
        row = subject_rollup.setdefault(subject, {
            'subject': subject,
            'attempts': 0,
            'total_percentage': 0.0,
            'best_percentage': 0.0,
        })
        pct = float(item.get('percentage', 0))
        row['attempts'] += 1
        row['total_percentage'] += pct
        row['best_percentage'] = max(row['best_percentage'], pct)

    subject_summary = []
    for row in subject_rollup.values():
        subject_summary.append({
            'subject': row['subject'],
            'attempts': row['attempts'],
            'average_percentage': round(row['total_percentage'] / row['attempts'], 1),
            'best_percentage': round(row['best_percentage'], 1),
        })
    subject_summary.sort(key=lambda item: item['average_percentage'], reverse=True)

    recent_results = []
    for item in entries[:8]:
        recorded_at = parse_iso_datetime(str(item.get('recorded_at', '')))
        recent_results.append({
            **item,
            'recorded_at_display': recorded_at.strftime('%Y-%m-%d %H:%M UTC')
        })

    return {
        'total_records': total_records,
        'average_percentage': average_percentage,
        'best_percentage': best_percentage,
        'total_scored': round(total_scored, 1),
        'total_possible': round(total_possible, 1),
        'subject_summary': subject_summary,
        'recent_results': recent_results,
    }


def calculate_admin_result_analytics():
    entries = get_marks_for_admin()
    total_records = len(entries)
    if not total_records:
        return {
            'total_records': 0,
            'unique_students': 0,
            'overall_average': 0,
            'subject_summary': [],
            'recent_entries': [],
        }

    overall_average = round(
        sum(float(item.get('percentage', 0)) for item in entries) / total_records,
        1
    )
    unique_students = len({item.get('student_id') for item in entries if item.get('student_id')})

    subject_rollup = {}
    for item in entries:
        subject = item.get('subject', 'General')
        row = subject_rollup.setdefault(subject, {
            'subject': subject,
            'records': 0,
            'total_percentage': 0.0,
            'best_percentage': 0.0,
        })
        pct = float(item.get('percentage', 0))
        row['records'] += 1
        row['total_percentage'] += pct
        row['best_percentage'] = max(row['best_percentage'], pct)

    subject_summary = []
    for row in subject_rollup.values():
        subject_summary.append({
            'subject': row['subject'],
            'records': row['records'],
            'average_percentage': round(row['total_percentage'] / row['records'], 1),
            'best_percentage': round(row['best_percentage'], 1),
        })
    subject_summary.sort(key=lambda item: item['average_percentage'], reverse=True)

    recent_entries = []
    for item in entries[:12]:
        recorded_at = parse_iso_datetime(str(item.get('recorded_at', '')))
        recent_entries.append({
            **item,
            'recorded_at_display': recorded_at.strftime('%Y-%m-%d %H:%M UTC')
        })

    return {
        'total_records': total_records,
        'unique_students': unique_students,
        'overall_average': overall_average,
        'subject_summary': subject_summary,
        'recent_entries': recent_entries,
    }


def calculate_student_analytics(user):
    prefix, student_id = parse_user_id(user.id)
    if prefix != 'student' or not student_id:
        return {
            'total_quizzes': 0,
            'total_questions': 0,
            'total_correct': 0,
            'avg_score': 0,
            'overall_accuracy': 0,
            'recent_attempts': [],
            'subject_performance': [],
        }

    attempts = get_quiz_results_for_student(student_id)

    total_quizzes = len(attempts)
    total_questions = sum(int(item.get('total_questions', 0)) for item in attempts)
    total_correct = sum(int(item.get('score', 0)) for item in attempts)
    avg_score = round(
        sum(float(item.get('percentage', 0)) for item in attempts) / total_quizzes,
        1
    ) if total_quizzes else 0
    overall_accuracy = round((total_correct / total_questions) * 100, 1) if total_questions else 0

    subject_rollup = {}
    for item in attempts:
        subject_key = item.get('subject_key') or ''
        subject_name = item.get('subject_name') or subject_key
        if subject_key not in ADMIN_SUBJECT_KEYS:
            continue
        entry = subject_rollup.setdefault(subject_name, {
            'subject': subject_name,
            'attempts': 0,
            'average': 0.0,
            'best': 0.0,
            'total': 0.0,
        })
        percentage = float(item.get('percentage', 0))
        entry['attempts'] += 1
        entry['total'] += percentage
        entry['best'] = max(entry['best'], percentage)

    for entry in subject_rollup.values():
        entry['average'] = round(entry['total'] / entry['attempts'], 1) if entry['attempts'] else 0

    subject_performance = sorted(
        subject_rollup.values(),
        key=lambda item: item['average'],
        reverse=True
    )

    recent_attempts = []
    for item in attempts[:8]:
        attempted_at = parse_iso_datetime(str(item.get('attempted_at', '')))
        recent_attempts.append({
            'id': f"attempt-{item.get('result_id')}",
            'subject': item.get('subject_key'),
            'subject_title': item.get('subject_name'),
            'score': int(item.get('score', 0)),
            'total_questions': int(item.get('total_questions', 0)),
            'percentage': float(item.get('percentage', 0)),
            'attempted_at': item.get('attempted_at'),
            'attempted_at_display': attempted_at.strftime('%Y-%m-%d %H:%M UTC')
        })

    return {
        'total_quizzes': total_quizzes,
        'total_questions': total_questions,
        'total_correct': total_correct,
        'avg_score': avg_score,
        'overall_accuracy': overall_accuracy,
        'recent_attempts': recent_attempts,
        'subject_performance': subject_performance,
    }


def get_base_questions_for_subject(subject):
    key = canonical_subject(subject)
    if key == 'computer':
        return get_computer_questions()
    if key == 'math':
        return get_math_questions()
    if key == 'science':
        return get_science_questions()
    if key == 'english':
        return get_english_questions()
    if key == 'gujarati':
        return get_gujarati_questions()
    if key == 'social-science':
        return get_social_science_questions()
    return []


def get_questions_for_subject(subject):
    key = canonical_subject(subject)
    subjects = get_subject_map()
    subject_row = subjects.get(key)
    if not subject_row:
        return []

    rows = db_fetch_all(
        "SELECT question_id, question_text, option_a, option_b, option_c, option_d, "
        "answer_index, explanation, source, base_key "
        "FROM question WHERE subject_id = %s AND is_deleted = 0 "
        "ORDER BY question_id ASC",
        (subject_row['subject_id'],)
    )

    base_questions = get_base_questions_for_subject(key) or []
    questions = []
    for row in rows:
        source = row.get('source') or 'custom'
        qid = row.get('base_key') if source == 'base' else f"q-{row.get('question_id')}"
        explanation = row.get('explanation') or ''
        if not explanation and source == 'base':
            base_key = row.get('base_key') or ''
            if ':' in base_key:
                _, index_text = base_key.split(':', 1)
                try:
                    base_idx = int(index_text)
                    if 0 <= base_idx < len(base_questions):
                        explanation = base_questions[base_idx].get('explanation', '') or ''
                except ValueError:
                    pass
        questions.append({
            '_qid': qid,
            '_source': source,
            'question': row.get('question_text'),
            'options': [row.get('option_a'), row.get('option_b'), row.get('option_c'), row.get('option_d')],
            'answer': int(row.get('answer_index', 0)),
            'explanation': explanation,
        })
    return questions


def get_question_counts():
    rows = db_fetch_all(
        "SELECT s.subject_key, COUNT(*) AS total "
        "FROM question q "
        "JOIN subject s ON q.subject_id = s.subject_id "
        "WHERE q.is_deleted = 0 "
        "GROUP BY s.subject_key"
    )
    counts = {row['subject_key']: int(row['total']) for row in rows}
    for key in ADMIN_SUBJECT_KEYS:
        counts.setdefault(key, 0)
    return counts


@login_manager.user_loader
def load_user(user_id):
    prefix, raw_id = parse_user_id(user_id)
    if not raw_id:
        return None
    if prefix == 'admin':
        return build_user_from_admin_row(get_admin_by_id(raw_id))
    if prefix == 'student':
        return build_user_from_student_row(get_student_by_id(raw_id))
    return None


@login_manager.unauthorized_handler
def unauthorized():
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Authentication required'}), 401
    return redirect(url_for('student_login'))


@app.before_request
def hide_admin_panel_routes():
    if SHOW_ADMIN_PANEL:
        return None
    # Allow admin login even when the admin panel is hidden.
    if request.path == '/admin-login':
        return None
    if request.path == '/admin' or request.path.startswith('/admin/'):
        return "Not Found", 404

# Inject common template variables (e.g. current year for footer and current_user)
@app.context_processor
def inject_now_and_user():
    return {
        'now': datetime.now(timezone.utc),
        'current_user': current_user,
        'show_admin_panel': SHOW_ADMIN_PANEL,
        'notifications': get_student_notifications(current_user),
    }


initialize_database_from_sql()
ensure_subjects()
ensure_base_questions_seeded()
ensure_default_admin()
ensure_default_user()

# Routes
@app.route('/')
def home():
    return render_template("index.html")


@app.route('/login', methods=['GET', 'POST'])
def login():
    return student_login()


@app.route('/student-login', methods=['GET', 'POST'])
def student_login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        if not is_valid_email(email) or not password:
            flash('Enter a valid email and password.', 'error')
            return render_template('login.html', login_mode='student'), 400

        if get_admin_by_email(email):
            flash('This account is admin. Use Admin Login.', 'error')
            return render_template('login.html', login_mode='student'), 403

        student_row = get_student_by_email(email)
        user = build_user_from_student_row(student_row)
        if not user or not check_password_hash(user.password_hash, password):
            flash('Invalid email or password.', 'error')
            return render_template('login.html', login_mode='student'), 401

        login_user(user)
        flash('Logged in successfully.', 'success')
        return redirect(url_for('profile'))

    return render_template('login.html', login_mode='student')


@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        if not is_valid_email(email) or not password:
            flash('Enter a valid email and password.', 'error')
            return render_template('login.html', login_mode='admin'), 400

        admin_row = get_admin_by_email(email)
        is_known_admin_email = email == 'admin@schoollearn.com' or email in ADMIN_EMAILS
        if not admin_row and is_known_admin_email:
            db_execute(
                "INSERT INTO admin (username, email, password_hash) VALUES (%s, %s, %s)",
                (email.split('@')[0], email, generate_password_hash(DEFAULT_ADMIN_PASSWORD))
            )
            admin_row = get_admin_by_email(email)

        user = build_user_from_admin_row(admin_row)

        if not user or not check_password_hash(user.password_hash, password):
            # Allow the default admin password to recover a mismatched hash.
            if user and is_known_admin_email and password == DEFAULT_ADMIN_PASSWORD:
                db_execute(
                    "UPDATE admin SET password_hash = %s WHERE admin_id = %s",
                    (generate_password_hash(DEFAULT_ADMIN_PASSWORD), admin_row['admin_id'])
                )
            else:
                flash('Invalid email or password.', 'error')
                return render_template('login.html', login_mode='admin'), 401

        if not is_admin_user(user):
            flash('Admin account required.', 'error')
            return render_template('login.html', login_mode='admin'), 403

        login_user(user)
        flash('Admin login successful.', 'success')
        return redirect(url_for('admin_dashboard'))

    return render_template('login.html', login_mode='admin')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('fullName', '').strip()
        email = request.form.get('email', '').strip().lower()
        grade = request.form.get('grade', '').strip()
        school = request.form.get('school', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirmPassword', '')

        if not username or not email or not password:
            flash('Name, email, and password are required.', 'error')
            return render_template('register.html'), 400

        if not is_valid_email(email):
            flash('Enter a valid email address.', 'error')
            return render_template('register.html'), 400

        if not is_strong_password(password):
            flash('Password must be at least 6 characters long.', 'error')
            return render_template('register.html'), 400

        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('register.html'), 400

        if email_in_use(email):
            flash('An account with this email already exists.', 'error')
            return render_template('register.html'), 409

        new_id = db_execute(
            "INSERT INTO student (full_name, email, password_hash, grade, school) "
            "VALUES (%s, %s, %s, %s, %s)",
            (username, email, generate_password_hash(password), grade, school)
        )
        student_row = get_student_by_id(new_id)
        user = build_user_from_student_row(student_row)

        login_user(user)
        flash('Registration successful.', 'success')
        return redirect(url_for('profile'))

    return render_template('register.html')


@app.route('/profile')
@login_required
def profile():
    analytics = calculate_student_analytics(current_user)
    result_analytics = calculate_result_analytics_for_user(current_user)
    leaderboard = get_quiz_leaderboard(limit=10)
    history = get_student_quiz_history(current_user)
    subjects_map = get_subject_map()
    available_subjects = [
        {'key': key, 'name': name}
        for key, name in SUBJECT_KEY_TO_NAME.items()
        if subjects_map.get(key, {}).get('is_enabled', 1)
    ]
    dashboard_summary = build_dashboard_summary(
        analytics,
        result_analytics,
        history,
        available_subjects,
    )
    return render_template(
        'student_dashboard.html',
        analytics=analytics,
        result_analytics=result_analytics,
        leaderboard=leaderboard,
        latest_attempt=history[0] if history else None,
        available_subjects=available_subjects,
        dashboard_summary=dashboard_summary,
    )


@app.route('/student/results')
@login_required
def student_result_history():
    if is_admin_user(current_user):
        flash('Student result history is available for student accounts.', 'error')
        return redirect(url_for('home'))

    return render_template(
        'student_results.html',
        quiz_history=get_student_quiz_history(current_user),
        uploaded_results=get_marks_for_user(current_user),
    )


@app.route('/api/student/analytics', methods=['GET'])
@login_required
def student_analytics():
    return jsonify(calculate_student_analytics(current_user))


@app.route('/api/student/results', methods=['GET'])
@login_required
def student_results():
    return jsonify(calculate_result_analytics_for_user(current_user))


@app.route('/api/profile', methods=['POST'])
@login_required
def update_profile():
    if is_admin_user(current_user):
        return jsonify({'error': 'Student account required'}), 403

    payload = request.get_json(silent=True) or {}
    grade = (payload.get('grade') or '').strip()[:32]
    school = (payload.get('school') or '').strip()[:255]
    avatar_url = sanitize_avatar_url(payload.get('avatar_url'))

    prefix, student_id = parse_user_id(current_user.id)
    if prefix != 'student' or not student_id:
        return jsonify({'error': 'Invalid student account'}), 400

    db_execute(
        "UPDATE student SET grade = %s, school = %s, avatar_url = %s WHERE student_id = %s",
        (grade, school, avatar_url, student_id)
    )

    return jsonify({
        'message': 'Profile updated',
        'profile': {
            'grade': grade,
            'school': school,
            'avatar_url': avatar_url,
        }
    })


@app.route('/api/chatbot', methods=['POST'])
def student_chatbot():
    if current_user.is_authenticated and is_admin_user(current_user):
        return jsonify({'error': 'Student account required'}), 403

    payload = request.get_json(silent=True) or {}
    message = (payload.get('message') or '').strip()

    if len(message) > 500:
        return jsonify({'error': 'Message is too long'}), 400

    return jsonify({
        'reply': build_student_chatbot_reply(message, current_user)
    })


@app.route('/api/leaderboard', methods=['GET'])
def leaderboard_api():
    limit = request.args.get('limit', 10)
    try:
        limit = int(limit)
    except (TypeError, ValueError):
        limit = 10
    return jsonify(get_quiz_leaderboard(limit=limit))


@app.route('/student/results/pdf', methods=['GET'])
@login_required
def student_results_pdf():
    if is_admin_user(current_user):
        flash('This download is available for student accounts.', 'error')
        return redirect(url_for('home'))

    analytics = calculate_student_analytics(current_user)
    results = calculate_result_analytics_for_user(current_user)
    marks = get_marks_for_user(current_user)
    generated_at = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')

    lines = [
        f"Student: {current_user.username}",
        f"Email: {current_user.email}",
        f"Generated: {generated_at}",
        "",
        "Quiz Summary",
        f"Quizzes Taken: {analytics['total_quizzes']}",
        f"Average Score: {analytics['avg_score']}%",
        f"Overall Accuracy: {analytics['overall_accuracy']}%",
        "",
        "Uploaded Results Summary",
        f"Records: {results['total_records']}",
        f"Average Result: {results['average_percentage']}%",
        f"Best Result: {results['best_percentage']}%",
        "",
        "Recent Uploaded Results",
    ]

    if not marks:
        lines.append("No uploaded results found.")
    else:
        for item in marks[:20]:
            when = parse_iso_datetime(str(item.get('recorded_at', ''))).strftime('%Y-%m-%d')
            lines.append(
                f"{when} | {item.get('exam_name', 'Exam')} | {item.get('subject', 'General')} | "
                f"{item.get('score', 0)}/{item.get('total', 0)} ({item.get('percentage', 0)}%)"
            )

    pdf_bytes = build_simple_pdf(lines, title="SchoolLearn Student Result Report")
    filename = f"schoollearn-results-{current_user.username.replace(' ', '-').lower()}.pdf"
    return Response(
        pdf_bytes,
        mimetype='application/pdf',
        headers={
            'Content-Disposition': f'attachment; filename="{filename}"',
            'Content-Length': str(len(pdf_bytes)),
        }
    )


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('home'))


@app.route('/admin')
@login_required
def admin_dashboard():
    if not is_admin_user(current_user):
        flash('Admin access only.', 'error')
        return redirect(url_for('home'))

    managed_users = get_all_users_for_admin()
    selected_subject = canonical_subject(request.args.get('subject', 'math'))
    if selected_subject not in ADMIN_SUBJECT_KEYS:
        selected_subject = 'math'

    counts = get_question_counts()
    quiz_counts = {
        'Computer': counts.get('computer', 0),
        'Mathematics': counts.get('math', 0),
        'Science': counts.get('science', 0),
        'English': counts.get('english', 0),
        'Gujarati': counts.get('gujarati', 0),
        'Social Science': counts.get('social-science', 0),
    }
    total_questions = sum(quiz_counts.values())

    subjects = get_subject_map()
    canonical_quiz_status = {
        key: bool(subjects.get(key, {}).get('is_enabled', 1))
        for key in ADMIN_SUBJECT_KEYS
    }

    result_analytics = calculate_admin_result_analytics()

    return render_template(
        'admin.html',
        managed_users=managed_users,
        quiz_counts=quiz_counts,
        total_questions=total_questions,
        canonical_quiz_status=canonical_quiz_status,
        admin_subjects=[(k, QUIZ_SUBJECTS[k]) for k in ADMIN_SUBJECT_KEYS],
        selected_subject=selected_subject,
        selected_subject_questions=get_questions_for_subject(selected_subject),
        result_analytics=result_analytics
    )


@app.route('/admin/marks/upload', methods=['POST'])
@login_required
def admin_upload_marks():
    if not is_admin_user(current_user):
        flash('Admin access only.', 'error')
        return redirect(url_for('home'))

    email = request.form.get('student_email', '').strip().lower()
    exam_name = request.form.get('exam_name', '').strip()
    subject = request.form.get('subject', '').strip() or 'General'
    exam_date = request.form.get('exam_date', '').strip()
    remarks = request.form.get('remarks', '').strip()

    try:
        score = float(request.form.get('score', '0'))
        total = float(request.form.get('total', '0'))
    except ValueError:
        flash('Score and total must be numeric.', 'error')
        return redirect(url_for('admin_dashboard'))

    if not email or not exam_name or total <= 0:
        flash('Student email, exam name, and total marks are required.', 'error')
        return redirect(url_for('admin_dashboard'))

    if score < 0 or score > total:
        flash('Score must be between 0 and total marks.', 'error')
        return redirect(url_for('admin_dashboard'))

    if get_admin_by_email(email):
        flash('Marks can only be uploaded for student accounts.', 'error')
        return redirect(url_for('admin_dashboard'))

    student_row = get_student_by_email(email)
    if not student_row:
        flash('Student not found for provided email.', 'error')
        return redirect(url_for('admin_dashboard'))

    recorded_at = datetime.utcnow()
    if exam_date:
        try:
            recorded_at = datetime.fromisoformat(exam_date)
        except ValueError:
            pass

    db_execute(
        "INSERT INTO marks (student_id, exam_name, subject_name, score, total, percentage, remarks, "
        "recorded_at, uploaded_by, uploaded_at) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
        (
            student_row['student_id'],
            exam_name,
            subject,
            round(score, 1),
            round(total, 1),
            percentage_from_marks(score, total),
            remarks,
            recorded_at,
            current_user.email,
            datetime.utcnow(),
        )
    )

    flash('Marks uploaded successfully.', 'success')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/users/<user_id>/delete', methods=['POST'])
@login_required
def admin_delete_user(user_id):
    if not is_admin_user(current_user):
        flash('Admin access only.', 'error')
        return redirect(url_for('home'))
    if ADMIN_VIEW_ONLY:
        flash('Admin dashboard is in view-only mode.', 'error')
        return redirect(url_for('admin_dashboard'))

    if user_id == current_user.id:
        flash('You cannot delete your own admin account.', 'error')
        return redirect(url_for('admin_dashboard'))

    prefix, raw_id = parse_user_id(user_id)
    if prefix == 'admin' and raw_id:
        db_execute("DELETE FROM admin WHERE admin_id = %s", (raw_id,))
        flash('Admin deleted.', 'success')
    elif raw_id:
        db_execute("DELETE FROM student WHERE student_id = %s", (raw_id,))
        flash('User deleted.', 'success')
    else:
        flash('User not found.', 'error')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/users/<user_id>/toggle-admin', methods=['POST'])
@login_required
def admin_toggle_user_admin(user_id):
    if not is_admin_user(current_user):
        flash('Admin access only.', 'error')
        return redirect(url_for('home'))
    if ADMIN_VIEW_ONLY:
        flash('Admin dashboard is in view-only mode.', 'error')
        return redirect(url_for('admin_dashboard'))

    if user_id == current_user.id:
        flash('You cannot change your own admin role.', 'error')
        return redirect(url_for('admin_dashboard'))

    prefix, raw_id = parse_user_id(user_id)
    if prefix == 'student' and raw_id:
        student = get_student_by_id(raw_id)
        if not student:
            flash('User not found.', 'error')
            return redirect(url_for('admin_dashboard'))
        if get_admin_by_email(student['email']):
            flash('User is already an admin.', 'error')
            return redirect(url_for('admin_dashboard'))
        db_execute(
            "INSERT INTO admin (username, email, password_hash) VALUES (%s, %s, %s)",
            (student['full_name'], student['email'], student['password_hash'])
        )
        flash('User role updated.', 'success')
    elif prefix == 'admin' and raw_id:
        admin_row = get_admin_by_id(raw_id)
        if not admin_row:
            flash('User not found.', 'error')
            return redirect(url_for('admin_dashboard'))
        if not get_student_by_email(admin_row['email']):
            db_execute(
                "INSERT INTO student (full_name, email, password_hash, grade, school) "
                "VALUES (%s, %s, %s, %s, %s)",
                (admin_row['username'], admin_row['email'], admin_row['password_hash'], '', '')
            )
        db_execute("DELETE FROM admin WHERE admin_id = %s", (raw_id,))
        flash('User role updated.', 'success')
    else:
        flash('User not found.', 'error')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/quiz/<subject>/toggle', methods=['POST'])
@login_required
def admin_toggle_quiz(subject):
    if not is_admin_user(current_user):
        flash('Admin access only.', 'error')
        return redirect(url_for('home'))
    if ADMIN_VIEW_ONLY:
        flash('Admin dashboard is in view-only mode.', 'error')
        return redirect(url_for('admin_dashboard'))

    key = canonical_subject(subject)
    subjects = get_subject_map()
    if key not in subjects:
        flash('Invalid subject.', 'error')
        return redirect(url_for('admin_dashboard'))

    new_value = request.form.get('enabled') == '1'
    db_execute(
        "UPDATE subject SET is_enabled = %s WHERE subject_key = %s",
        (1 if new_value else 0, key)
    )

    flash(f'Quiz status for {QUIZ_SUBJECTS[key]} updated.', 'success')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/questions/add', methods=['POST'])
@login_required
def admin_add_question():
    if not is_admin_user(current_user):
        flash('Admin access only.', 'error')
        return redirect(url_for('home'))

    subject = canonical_subject(request.form.get('subject', ''))
    if subject not in ADMIN_SUBJECT_KEYS:
        flash('Invalid subject.', 'error')
        return redirect(url_for('admin_dashboard'))

    question_text = request.form.get('question', '').strip()
    options = [
        request.form.get('option_a', '').strip(),
        request.form.get('option_b', '').strip(),
        request.form.get('option_c', '').strip(),
        request.form.get('option_d', '').strip(),
    ]
    explanation = request.form.get('explanation', '').strip()
    try:
        answer = int(request.form.get('answer', '-1'))
    except ValueError:
        answer = -1

    if not question_text or any(not opt for opt in options):
        flash('Question and all 4 options are required.', 'error')
        return redirect(url_for('admin_dashboard', subject=subject))

    if answer < 0 or answer > 3:
        flash('Select a valid correct option.', 'error')
        return redirect(url_for('admin_dashboard', subject=subject))

    subjects = get_subject_map()
    subject_row = subjects.get(subject)
    if not subject_row:
        flash('Subject not found.', 'error')
        return redirect(url_for('admin_dashboard'))

    db_execute(
        "INSERT INTO question (subject_id, question_text, option_a, option_b, option_c, option_d, "
        "answer_index, explanation, source) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'custom')",
        (
            subject_row['subject_id'],
            question_text,
            options[0],
            options[1],
            options[2],
            options[3],
            answer,
            explanation,
        )
    )

    flash('Question added successfully.', 'success')
    return redirect(url_for('admin_dashboard', subject=subject))


@app.route('/admin/questions/edit', methods=['POST'])
@login_required
def admin_edit_question():
    if not is_admin_user(current_user):
        flash('Admin access only.', 'error')
        return redirect(url_for('home'))

    subject = canonical_subject(request.form.get('subject', ''))
    qid = request.form.get('qid', '').strip()
    if subject not in ADMIN_SUBJECT_KEYS or not qid.startswith('q-'):
        flash('Only custom questions can be edited.', 'error')
        return redirect(url_for('admin_dashboard', subject=subject or 'math'))

    try:
        qid_value = int(qid.split('-', 1)[1])
        answer = int(request.form.get('answer', '-1'))
    except ValueError:
        flash('Invalid question update.', 'error')
        return redirect(url_for('admin_dashboard', subject=subject))

    question_text = request.form.get('question', '').strip()
    options = [
        request.form.get('option_a', '').strip(),
        request.form.get('option_b', '').strip(),
        request.form.get('option_c', '').strip(),
        request.form.get('option_d', '').strip(),
    ]
    explanation = request.form.get('explanation', '').strip()

    if not question_text or any(not opt for opt in options) or answer < 0 or answer > 3:
        flash('Question, options, and valid answer are required.', 'error')
        return redirect(url_for('admin_dashboard', subject=subject))

    db_execute(
        "UPDATE question SET question_text = %s, option_a = %s, option_b = %s, option_c = %s, "
        "option_d = %s, answer_index = %s, explanation = %s "
        "WHERE question_id = %s AND source = 'custom'",
        (
            question_text,
            options[0],
            options[1],
            options[2],
            options[3],
            answer,
            explanation,
            qid_value,
        )
    )

    flash('Question updated successfully.', 'success')
    return redirect(url_for('admin_dashboard', subject=subject))


@app.route('/admin/questions/delete', methods=['POST'])
@login_required
def admin_delete_question():
    if not is_admin_user(current_user):
        flash('Admin access only.', 'error')
        return redirect(url_for('home'))

    subject = canonical_subject(request.form.get('subject', ''))
    qid = request.form.get('qid', '').strip()
    source = request.form.get('source', '').strip()
    if subject not in ADMIN_SUBJECT_KEYS or not qid or source not in ('base', 'custom'):
        flash('Invalid request.', 'error')
        return redirect(url_for('admin_dashboard'))

    changed = False
    if source == 'base':
        db_execute(
            "UPDATE question SET is_deleted = 1 WHERE base_key = %s",
            (qid,)
        )
        changed = True
    else:
        if qid.startswith('q-'):
            try:
                qid_value = int(qid.split('-', 1)[1])
            except ValueError:
                qid_value = None
        else:
            qid_value = None
        if qid_value:
            db_execute(
                "UPDATE question SET is_deleted = 1 WHERE question_id = %s",
                (qid_value,)
            )
            changed = True

    if changed:
        flash('Question deleted successfully.', 'success')
    else:
        flash('Question not found.', 'error')

    return redirect(url_for('admin_dashboard', subject=subject))


@app.route('/api/quiz/progress', methods=['POST'])
@login_required
def save_quiz_progress():
    payload = request.get_json(silent=True) or {}
    subject = canonical_subject(payload.get('subject', ''))
    if subject not in ADMIN_SUBJECT_KEYS:
        return jsonify({'error': 'Invalid subject'}), 400

    try:
        score = int(payload.get('score', 0))
        total_questions = int(payload.get('total_questions', 0))
    except (TypeError, ValueError):
        return jsonify({'error': 'Invalid score payload'}), 400

    if total_questions <= 0:
        return jsonify({'error': 'total_questions must be greater than 0'}), 400

    score = max(0, min(score, total_questions))
    percentage = round((score / total_questions) * 100, 1)

    subjects = get_subject_map()
    subject_row = subjects.get(subject)
    prefix, student_id = parse_user_id(current_user.id)
    if not subject_row or prefix != 'student' or not student_id:
        return jsonify({'error': 'Invalid user or subject'}), 400

    attempted_at = datetime.utcnow()
    result_id = db_execute(
        "INSERT INTO result (student_id, subject_id, score, total_questions, percentage, attempted_at) "
        "VALUES (%s, %s, %s, %s, %s, %s)",
        (student_id, subject_row['subject_id'], score, total_questions, percentage, attempted_at)
    )

    attempt = {
        'id': f'attempt-{result_id}',
        'subject': subject,
        'subject_title': QUIZ_SUBJECTS[subject],
        'score': score,
        'total_questions': total_questions,
        'percentage': percentage,
        'attempted_at': attempted_at.isoformat(),
    }

    return jsonify({
        'message': 'Quiz progress saved',
        'attempt': attempt
    }), 201

# API Endpoints for questions
@app.route('/api/questions/<subject>', methods=['GET'])
def get_questions(subject):
    try:
        subject = canonical_subject(subject)
        questions = []
        mode = (request.args.get('mode') or 'random').strip().lower()
        try:
            count = int(request.args.get('count', 10))
        except (TypeError, ValueError):
            count = 10
        count = max(1, min(count, 50))

        if subject not in ADMIN_SUBJECT_KEYS:
            return jsonify({'error': 'Invalid subject'}), 400

        try:
            subjects = get_subject_map()
        except Exception:
            subjects = {}

        subject_row = subjects.get(subject)
        if subject_row and not subject_row.get('is_enabled', 1):
            return jsonify({'error': 'This quiz is disabled by admin'}), 403

        if subject_row:
            questions = get_questions_for_subject(subject)

        if not questions:
            base_questions = get_base_questions_for_subject(subject) or []
            normalized = []
            for idx, q in enumerate(base_questions):
                options = list(q.get('options') or [])
                while len(options) < 4:
                    options.append('')
                normalized.append({
                    '_qid': q.get('id') or f"base-{subject}-{idx}",
                    '_source': 'base',
                    'question': q.get('question', ''),
                    'options': options[:4],
                    'answer': int(q.get('answer', 0)),
                    'explanation': q.get('explanation', '') or '',
                })
            questions = normalized

        if mode == 'random':
            import random
            random.shuffle(questions)

        questions = questions[:min(count, len(questions))]
        return jsonify(questions)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/one-line-questions/<subject>', methods=['GET'])
def one_line_questions_api(subject):
    try:
        subject = canonical_subject(subject)
        if subject not in ADMIN_SUBJECT_KEYS:
            return jsonify({'error': 'Invalid subject'}), 400

        questions = list(get_one_line_questions(subject) or [])
        mode = (request.args.get('mode') or 'random').strip().lower()
        try:
            count = int(request.args.get('count', 10))
        except (TypeError, ValueError):
            count = 10
        count = max(1, min(count, 50))

        if mode == 'random':
            import random
            random.shuffle(questions)

        normalized = []
        for idx, question in enumerate(questions[:min(count, len(questions))]):
            normalized.append({
                '_qid': question.get('id') or f"one-line-{subject}-{idx}",
                'question': question.get('question', ''),
                'answer': question.get('answer', ''),
                'explanation': question.get('explanation', '') or '',
            })

        return jsonify(normalized)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Serve quiz pages
@app.route('/quiz/<subject>')
def quiz_page(subject):
    subject = canonical_subject(subject)
    if subject not in QUIZ_SUBJECTS:
        return "Invalid subject", 404

    subjects = get_subject_map()
    subject_row = subjects.get(subject)
    if subject_row and not subject_row.get('is_enabled', 1):
        flash('This quiz is currently disabled by admin.', 'error')
        return redirect(url_for('home'))

    return render_template(
        'quiz_template.html',
        subject=subject,
        subject_title=QUIZ_SUBJECTS[subject]
    )


@app.route('/one-line/<subject>')
def one_line_page(subject):
    subject = canonical_subject(subject)
    if subject not in QUIZ_SUBJECTS:
        return "Invalid subject", 404

    return render_template(
        'one_line_template.html',
        subject=subject,
        subject_title=QUIZ_SUBJECTS[subject]
    )

if __name__ == '__main__':
    # Create necessary directories
    import os
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    
    # Run the app
    app.run(debug=True, port=5000)
