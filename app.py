import json
import os
import uuid

from flask import (
    Flask,
    redirect,
    render_template,
    render_template_string,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__)

# For this local class demo only.
app.secret_key = "civicconnect-demo-change-this-key"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "12345678"

app.config["UPLOAD_FOLDER"] = os.path.join(app.root_path, "static", "uploads")
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024

ALLOWED_IMAGE_TYPES = {"png", "jpg", "jpeg", "gif", "webp"}
ALLOWED_STATUSES = {"Submitted", "In Progress", "Resolved"}


def save_reports(reports):
    reports_file = os.path.join(app.root_path, "reports.json")
    with open(reports_file, "w", encoding="utf-8") as file:
        json.dump(reports, file, indent=2, ensure_ascii=False)


def load_reports():
    reports_file = os.path.join(app.root_path, "reports.json")

    if not os.path.exists(reports_file):
        return []

    with open(reports_file, "r", encoding="utf-8") as file:
        reports = json.load(file)

    # Add IDs and statuses to reports created before status tracking.
    changed = False
    for report in reports:
        if not report.get("id"):
            report["id"] = uuid.uuid4().hex
            changed = True
        if not report.get("status"):
            report["status"] = "Submitted"
            changed = True

    if changed:
        save_reports(reports)

    return reports


def load_users():
    users_file = os.path.join(app.root_path, "users.json")

    if not os.path.exists(users_file):
        return []

    with open(users_file, "r", encoding="utf-8") as file:
        return json.load(file)


def save_users(users):
    users_file = os.path.join(app.root_path, "users.json")

    with open(users_file, "w", encoding="utf-8") as file:
        json.dump(users, file, indent=2, ensure_ascii=False)


@app.route("/", methods=["GET", "POST"])
def login():
    error = ""

    if request.method == "POST":
        user_name = request.form.get("user_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        users = load_users()
        user = next(
            (item for item in users if item["email"] == email),
            None,
        )

        if user:
            if check_password_hash(user["password_hash"], password):
                session.clear()
                session["user_name"] = user["user_name"]
                session["email"] = user["email"]
                return redirect(url_for("home"))

            error = "That email already has an account. Check the password and try again."

        elif user_name and email and password:
            users.append({
                "user_name": user_name,
                "email": email,
                "password_hash": generate_password_hash(password),
            })
            save_users(users)

            session.clear()
            session["user_name"] = user_name
            session["email"] = email
            return redirect(url_for("home"))

        else:
            error = "Please enter a user name, email, and password."

    return render_template_string("""
    <!doctype html>
    <html lang="en">
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <title>CivicConnect | Login</title>
      <style>
        * { box-sizing: border-box; }
        body {
          margin: 0; min-height: 100vh; display: grid; place-items: center;
          font-family: Arial, sans-serif; background: #eef5f3; color: #17332f;
        }
        .card {
          width: min(400px, calc(100% - 36px)); padding: 36px;
          background: white; border-radius: 20px;
          box-shadow: 0 18px 50px #17332f18;
        }
        .brand { color: #087f68; font-weight: bold; }
        h1 { margin: 24px 0 8px; font-size: 32px; }
        .sub { margin: 0 0 26px; color: #66807a; line-height: 1.5; }
        label { display: block; margin: 17px 0 7px; font-weight: bold; font-size: 14px; }
        input {
          width: 100%; padding: 13px 14px; border: 1px solid #d5e2de;
          border-radius: 10px; font-size: 15px;
        }
        button {
          width: 100%; margin-top: 24px; padding: 14px; border: 0;
          border-radius: 10px; background: #087f68; color: white;
          font-size: 16px; font-weight: bold; cursor: pointer;
        }
        .foot { margin-top: 20px; text-align: center; color: #718780; font-size: 13px; }
        .error { color: #b42318; }
        .admin-link {
          position: fixed; top: 22px; right: 24px;
          color: #087f68; font-weight: bold; text-decoration: none;
        }
      </style>
    </head>
    <body>
      <a class="admin-link" href="/admin-login">Admin login</a>
      <main class="card">
        <div class="brand">🌿 CivicConnect</div>
        <h1>Welcome back</h1>
        <p class="sub">First use creates your account. Next time, use the same email and password.</p>
        <form method="post">
          <label for="user_name">User name</label>
          <input id="user_name" name="user_name" type="text"
                 placeholder="Choose a user name" required>

          <label for="email">Email address</label>
          <input id="email" name="email" type="email"
                 placeholder="you@example.com" required>

          <label for="password">Password</label>
          <input id="password" name="password" type="password"
                 placeholder="Choose a password" required>

          <button type="submit">Continue</button>
        </form>
        {% if error %}<p class="error">{{ error }}</p>{% endif %}
        <div class="foot">A better neighborhood starts with us.</div>
      </main>
    </body>
    </html>
    """, error=error)


@app.route("/home")
def home():
    user_name = session.get("user_name")
    email = session.get("email")

    if not email:
        return redirect(url_for("login"))

    reports = load_reports()

    return render_template_string("""
    <!doctype html>
    <html lang="en">
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <title>CivicConnect | Home</title>
      <style>
        * { box-sizing: border-box; }
        body { margin: 0; font-family: Arial, sans-serif; background: #f5f8f7; color: #19332f; }
        header {
          display: flex; justify-content: space-between; align-items: center;
          padding: 20px 7%; background: white; border-bottom: 1px solid #e5eeeb;
        }
        .brand { color: #087f68; font-size: 21px; font-weight: bold; }
        .nav-link { color: #087f68; font-weight: bold; text-decoration: none; margin-left: 16px; }
        main { max-width: 1100px; margin: 42px auto; padding: 0 24px; }
        .welcome {
          padding: 42px; border-radius: 22px; color: white;
          background: linear-gradient(120deg, #087f68, #20a889);
        }
        .welcome small { text-transform: uppercase; letter-spacing: 1.5px; opacity: .85; }
        .welcome h1 { margin: 12px 0; font-size: clamp(30px, 5vw, 46px); }
        .welcome p { max-width: 600px; line-height: 1.6; }
        .button {
          display: inline-block; margin-top: 12px; padding: 13px 18px;
          border-radius: 9px; background: white; color: #087f68;
          text-decoration: none; font-weight: bold;
        }
        .section-title { margin: 36px 0 16px; }
        .cards { display: grid; grid-template-columns: repeat(3, 1fr); gap: 18px; }
        .card, .activity {
          padding: 24px; background: white; border: 1px solid #e5eeeb;
          border-radius: 16px;
        }
        .icon { font-size: 27px; }
        .card h3 { margin: 14px 0 8px; }
        .card p { color: #6a807a; line-height: 1.5; }
        .activity { margin-top: 24px; }
        .report-card {
          margin-top: 16px; padding: 18px; border: 1px solid #e5eeeb;
          border-radius: 12px; background: #f8fbfa;
        }
        .report-card img {
          display: block; width: 100%; max-height: 320px; margin-top: 12px;
          border-radius: 10px; object-fit: cover;
        }
        .status {
          display: inline-block; padding: 6px 10px; border-radius: 16px;
          background: #e1f8ee; color: #087f68;
        }
        @media (max-width: 700px) {
          header { padding: 18px 22px; }
          main { margin: 24px auto; }
          .welcome { padding: 28px; }
          .cards { grid-template-columns: 1fr; }
        }
      </style>
    </head>
    <body>
      <header>
        <div class="brand">🌿 CivicConnect</div>
        <div>
          <span>Welcome, {{ user_name }}</span>
          <a class="nav-link" href="{{ url_for('dashboard') }}">My Dashboard</a>
          <a class="nav-link" href="{{ url_for('logout') }}">Log out</a>
        </div>
      </header>

      <main>
        <section class="welcome">
          <small>Your community, connected</small>
          <h1>Let’s make our neighborhood better.</h1>
          <p>Share local issues, support community ideas, and see the progress happening around you.</p>
          <a class="button" href="{{ url_for('report') }}">＋ Report a local issue</a>
        </section>

        <h2 class="section-title">What would you like to do?</h2>
        <section class="cards">
          <article class="card"><div class="icon">📍</div><h3>Report an issue</h3>
            <p>Tell your community about a pothole, broken streetlight, or other local concern.</p></article>
          <article class="card"><div class="icon">🤝</div><h3>Support an idea</h3>
            <p>Find neighborhood suggestions and support improvements you care about.</p></article>
          <article class="card"><div class="icon">📊</div><h3>Track progress</h3>
            <p>Stay informed as community concerns move toward a solution.</p></article>
        </section>

        <section class="activity">
          <h2>Community updates</h2>
          {% if reports %}
            {% for report in reports %}
              <article class="report-card">
                <h3>{{ report.title }}</h3>
                <p><strong>Category:</strong> {{ report.category }}</p>
                <p><strong>Location:</strong> {{ report.location }}</p>
                <p>{{ report.description }}</p>
                <p><strong>Reported by:</strong> {{ report.author_name or "Community member" }}</p>
                <p><strong>Status:</strong> <span class="status">{{ report.status or "Submitted" }}</span></p>
                {% if report.photo_url %}
                  <img src="{{ report.photo_url }}" alt="Photo for {{ report.title }}">
                {% endif %}
              </article>
            {% endfor %}
          {% else %}
            <p>Submit a local report to get the conversation started.</p>
          {% endif %}
        </section>
      </main>
    </body>
    </html>
    """, reports=reports, user_name=user_name)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/dashboard")
def dashboard():
    user_name = session.get("user_name")
    email = session.get("email")

    if not email:
        return redirect(url_for("login"))

    reports = load_reports()
    my_reports = [
        report for report in reports
        if (report.get("author_email") or "").lower() == email.lower()
    ]
    report_count = len(my_reports)

    if report_count <= 3:
        rank = "Fresher"
    elif report_count <= 10:
        rank = "Civic MVP"
    else:
        rank = "Community Superhero"

    reporter_totals = {}
    for report in reports:
        reporter_email = (report.get("author_email") or "").strip().lower()
        reporter_name = (report.get("author_name") or "Community member").strip()

        if not reporter_email:
            continue

        if reporter_email not in reporter_totals:
            reporter_totals[reporter_email] = {
                "user_name": reporter_name,
                "report_count": 0,
            }

        reporter_totals[reporter_email]["report_count"] += 1

    leaderboard = sorted(
        reporter_totals.values(),
        key=lambda reporter: reporter["report_count"],
        reverse=True,
    )[:3]

    return render_template(
        "dashboard.html",
        user_name=user_name,
        email=email,
        rank=rank,
        report_count=report_count,
        reports=reports,
        leaderboard=leaderboard,
    )


@app.route("/admin-login", methods=["GET", "POST"])
def admin_login():
    error = ""

    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session.clear()
            session["is_admin"] = True
            return redirect(url_for("admin_dashboard"))

        error = "Incorrect admin username or password."

    return render_template_string("""
    <!doctype html>
    <html lang="en">
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <title>Admin sign in | CivicConnect</title>
      <style>
        * { box-sizing: border-box; }
        body {
          margin: 0; min-height: 100vh; display: grid; place-items: center;
          font-family: Arial, sans-serif; background: #eef5f3; color: #19332f;
        }
        main {
          width: min(400px, calc(100% - 36px)); padding: 32px;
          background: white; border-radius: 18px;
          box-shadow: 0 12px 35px #17332f18;
        }
        label { display: block; margin: 16px 0 6px; font-weight: bold; }
        input {
          width: 100%; padding: 12px; border: 1px solid #cbdad5;
          border-radius: 8px; font-size: 16px;
        }
        button {
          width: 100%; margin-top: 20px; padding: 12px; border: 0;
          border-radius: 8px; background: #087f68; color: white;
          font-size: 16px; font-weight: bold; cursor: pointer;
        }
        .error { color: #b42318; }
      </style>
    </head>
    <body>
      <main>
        <h1>Admin sign in</h1>
        <form method="post">
          <label for="username">Username</label>
          <input id="username" name="username" required>
          <label for="password">Password</label>
          <input id="password" name="password" type="password" required>
          <button type="submit">Sign in</button>
        </form>
        {% if error %}<p class="error">{{ error }}</p>{% endif %}
      </main>
    </body>
    </html>
    """, error=error)


@app.route("/admin")
def admin_dashboard():
    if not session.get("is_admin"):
        return redirect(url_for("admin_login"))

    return render_template_string("""
    <!doctype html>
    <html lang="en">
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <title>Admin review | CivicConnect</title>
      <style>
        * { box-sizing: border-box; }
        body {
          margin: 0; padding: 28px 16px; font-family: Arial, sans-serif;
          color: #19332f; background: linear-gradient(135deg, #e2f7ed, #e8efff);
        }
        main { max-width: 950px; margin: 20px auto; }
        header, article {
          margin-bottom: 18px; padding: 24px; background: white;
          border-radius: 16px; box-shadow: 0 8px 24px #17332f12;
        }
        header {
          display: flex; justify-content: space-between; align-items: center;
          background: linear-gradient(120deg, #087f68, #20a889); color: white;
        }
        header a { color: white; }
        article { border: 1px solid #e5eeeb; }
        article img {
          display: block; width: 100%; max-height: 360px; margin: 14px 0;
          border-radius: 10px; object-fit: cover;
        }
        label { display: block; margin: 14px 0 6px; font-weight: bold; }
        select, button {
          padding: 10px 12px; border: 1px solid #cbdad5;
          border-radius: 8px; font: inherit;
        }
        button {
          border: 0; background: #087f68; color: white;
          font-weight: bold; cursor: pointer;
        }
      </style>
    </head>
    <body>
      <main>
        <header>
          <div>
            <h1>CivicConnect admin</h1>
            <p>Review community reports and update their progress.</p>
          </div>
          <a href="{{ url_for('admin_logout') }}">Sign out</a>
        </header>

        {% if reports %}
          {% for report in reports %}
            <article>
              <h2>{{ report.title }}</h2>
              <p><strong>Category:</strong> {{ report.category }}</p>
              <p><strong>Location:</strong> {{ report.location }}</p>
              <p><strong>Description:</strong> {{ report.description }}</p>
              <p><strong>Reported by:</strong> {{ report.author_name or "Community member" }}</p>
              <p><strong>Email:</strong> {{ report.author_email or "Not provided" }}</p>
              <p><strong>Current status:</strong> {{ report.status or "Submitted" }}</p>
              {% if report.photo_url %}
                <img src="{{ report.photo_url }}" alt="Photo for {{ report.title }}">
              {% endif %}
              <form action="{{ url_for('update_status') }}" method="post">
                <input type="hidden" name="report_id" value="{{ report.id }}">
                <label for="status-{{ report.id }}">Update status</label>
                <select id="status-{{ report.id }}" name="status">
                  <option value="Submitted" {% if report.status == "Submitted" %}selected{% endif %}>Submitted</option>
                  <option value="In Progress" {% if report.status == "In Progress" %}selected{% endif %}>In Progress</option>
                  <option value="Resolved" {% if report.status == "Resolved" %}selected{% endif %}>Resolved</option>
                </select>
                <button type="submit">Save status</button>
              </form>
            </article>
          {% endfor %}
        {% else %}
          <article><p>There are no reports to review yet.</p></article>
        {% endif %}
      </main>
    </body>
    </html>
    """, reports=load_reports())


@app.route("/admin-logout")
def admin_logout():
    session.clear()
    return redirect(url_for("admin_login"))


@app.route("/update-status", methods=["POST"])
def update_status():
    if not session.get("is_admin"):
        return redirect(url_for("admin_login"))

    report_id = request.form.get("report_id", "")
    new_status = request.form.get("status", "")

    if new_status in ALLOWED_STATUSES:
        reports = load_reports()

        for report in reports:
            if report.get("id") == report_id:
                report["status"] = new_status
                break

        save_reports(reports)

    return redirect(url_for("admin_dashboard"))


@app.route("/report", methods=["GET", "POST"])
def report():
    user_name = session.get("user_name")
    email = session.get("email")

    if not email:
        return redirect(url_for("login"))

    if request.method == "GET":
        return render_template(
            "report.html",
            user_name=user_name,
            email=email,
        )

    title = request.form.get("title", "").strip()
    category = request.form.get("category", "").strip()
    location = request.form.get("location", "").strip()
    description = request.form.get("description", "").strip()

    photo_url = None
    photo = request.files.get("photo")

    if photo and photo.filename:
        safe_name = secure_filename(photo.filename)
        extension = safe_name.rsplit(".", 1)[-1].lower() if "." in safe_name else ""

        if extension not in ALLOWED_IMAGE_TYPES:
            return "Please upload a PNG, JPG, GIF, or WEBP image.", 400

        unique_name = f"{uuid.uuid4().hex}_{safe_name}"
        os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
        photo.save(os.path.join(app.config["UPLOAD_FOLDER"], unique_name))
        photo_url = url_for("static", filename=f"uploads/{unique_name}")

    reports = load_reports()
    reports.append({
        "id": uuid.uuid4().hex,
        "title": title,
        "category": category,
        "location": location,
        "description": description,
        "photo_url": photo_url,
        "author_name": user_name,
        "author_email": email,
        "status": "Submitted",
    })
    save_reports(reports)

    return render_template_string("""
    <!doctype html>
    <html lang="en">
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <title>Report received | CivicConnect</title>
      <style>
        body {
          margin: 0; min-height: 100vh; padding: 32px 16px;
          font-family: Arial, sans-serif; color: #17332f;
          background: linear-gradient(135deg, #d9f7e9, #dcecff, #fff0d8);
        }
        main {
          max-width: 680px; margin: 30px auto; padding: 34px;
          background: white; border-radius: 22px;
          box-shadow: 0 18px 50px #17332f20;
        }
        .badge {
          display: inline-block; padding: 9px 14px; border-radius: 20px;
          color: #087f68; background: #e1f8ee; font-weight: bold;
        }
        .details {
          margin-top: 24px; padding: 20px; border-radius: 14px;
          background: #f3f8ff; line-height: 1.7;
        }
        .photo {
          display: block; width: 100%; max-height: 600px;
          margin-top: 22px; border-radius: 14px; object-fit: cover;
        }
        a {
          display: inline-block; margin: 22px 12px 0 0; padding: 12px 16px;
          border-radius: 9px; background: #087f68; color: white;
          text-decoration: none; font-weight: bold;
        }
      </style>
    </head>
    <body>
      <main>
        <div class="badge">✓ Report received</div>
        <h1>Thanks for helping your community, {{ user_name }}!</h1>
        <p>Your report has been saved with status <strong>Submitted</strong>.</p>
        <section class="details">
          <strong>Issue:</strong> {{ title }}<br>
          <strong>Category:</strong> {{ category }}<br>
          <strong>Location:</strong> {{ location }}<br>
          <strong>Description:</strong> {{ description }}
        </section>
        {% if photo_url %}
          <img class="photo" src="{{ photo_url }}" alt="Photo attached to the report">
        {% else %}
          <p>No photo was attached.</p>
        {% endif %}
        <a href="{{ url_for('home') }}">Back to home</a>
        <a href="{{ url_for('dashboard') }}">My dashboard</a>
      </main>
    </body>
    </html>
    """,
    user_name=user_name,
    title=title,
    category=category,
    location=location,
    description=description,
    photo_url=photo_url)


if __name__ == "__main__":
    app.run(debug=True)