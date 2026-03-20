from flask import Flask, render_template, request, session, redirect
import sqlite3
import json

app = Flask(__name__)
app.secret_key = "supersecretkey"

# ---------------- DATABASE ----------------

def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            password TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            code TEXT,
            duration REAL,
            status TEXT
        )
    """)

    conn.commit()
    conn.close()

init_db()

# ---------------- LOAD PROBLEMS ----------------

with open("problems.json") as f:
    problems = json.load(f)

# ---------------- AI FEEDBACK ----------------

def get_ai_feedback(code):
    return "💡 AI feedback coming soon!"

# ---------------- CODE EXECUTION ----------------

def evaluate_code(user_code):
    try:
        local_scope = {}
        exec(user_code, {}, local_scope)

        if len(local_scope) == 0:
            return "❌ No function found"

        func = list(local_scope.values())[0]

        test_cases = [
            ([3, 5, 1, 8, 2], 8),
            ([1, 2, 3], 3),
            ([9, 7, 5], 9),
            ([10], 10)
        ]

        for inp, expected in test_cases:
            try:
                result = func(inp)
            except Exception:
                return f"❌ Error on input {inp}"

            if result != expected:
                return f"Failed ❌ (Input: {inp}, Expected: {expected}, Got: {result})"

        return "Passed ✅"

    except Exception as e:
        return f"❌ Code Error: {str(e)}"

# ---------------- HOME ----------------

@app.route("/")
def home():

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM submissions")
    total_submissions = cursor.fetchone()[0]

    cursor.execute("SELECT AVG(duration) FROM submissions")
    avg_time = cursor.fetchone()[0] or 0

    cursor.execute("SELECT * FROM submissions")
    submissions = cursor.fetchall()

    conn.close()

    index = request.args.get("problem")
    if index:
        problem = problems[int(index)]
    else:
        problem = problems[0]

    return render_template(
        "index.html",
        problem=problem,
        problems=problems,
        submissions=submissions,
        total_submissions=total_submissions,
        avg_time=round(avg_time, 2),
        problems_solved=total_submissions,
        feedback="",
        username=session.get("username")
    )

# ---------------- RUN CODE ----------------

@app.route("/run", methods=["POST"])
def run_code():

    user_code = request.form.get("code")

    try:
        local_scope = {}
        exec(user_code, {}, local_scope)

        if len(local_scope) == 0:
            return "⚠️ No function found."

        func = list(local_scope.values())[0]
        result = func([3,5,1,8,2])

        return f"✅ Output: {result}"

    except Exception as e:
        return f"❌ Error: {str(e)}"

# ---------------- SUBMIT ----------------

@app.route("/submit", methods=["POST"])
def submit():

    user_code = request.form.get("code")
    duration = request.form.get("duration")

    # 🔥 session username
    username = session.get("username", "guest")

    status = evaluate_code(user_code)
    feedback = get_ai_feedback(user_code)

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO submissions (username, code, duration, status) VALUES (?, ?, ?, ?)",
        (username, user_code, duration, status)
    )

    conn.commit()
    conn.close()

    return render_template(
        "index.html",
        feedback=feedback,
        result=status,
        problem=problems[0],
        problems=problems,
        username=username
    )

# ---------------- LEADERBOARD ----------------

@app.route("/leaderboard")
def leaderboard():

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT username, COUNT(*) as score 
        FROM submissions 
        WHERE status = 'Passed ✅'
        GROUP BY username 
        ORDER BY score DESC
    """)

    data = cursor.fetchall()
    conn.close()

    return render_template("leaderboard.html", data=data)

# ---------------- LOGIN ----------------

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username, password)
        )

        user = cursor.fetchone()
        conn.close()

        if user:
            session["username"] = username
            return redirect("/")
        else:
            return "Invalid credentials"

    return render_template("login.html")

# ---------------- LOGOUT ----------------

@app.route("/logout")
def logout():
    session.pop("username", None)
    return redirect("/")

# ---------------- SIGNUP ----------------

@app.route("/signup", methods=["GET", "POST"])
def signup():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO users (username,password) VALUES (?,?)",
            (username, password)
        )

        conn.commit()
        conn.close()

        return redirect("/login")

    return render_template("signup.html")

# ---------------- RUN APP ----------------

import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)