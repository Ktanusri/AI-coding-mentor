from flask import Flask, render_template, request, session, redirect
import sqlite3
import json
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = "supersecretkey"

# ---------------- LOAD PROBLEMS ----------------

with open("problems.json") as f:
    all_problems = json.load(f)

# ---------------- INIT DB ----------------

def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            code TEXT,
            status TEXT,
            date TEXT
        )
    """)

    conn.commit()
    conn.close()

init_db()

# ---------------- PROGRESS ----------------

def get_progress(username):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT COUNT(*) FROM submissions WHERE username=? AND status='Passed ✅'",
        (username,)
    )
    solved = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM submissions WHERE username=?",
        (username,)
    )
    total = cursor.fetchone()[0]

    conn.close()

    accuracy = int((solved / total) * 100) if total > 0 else 0
    return solved, total, accuracy

# ---------------- STREAK ----------------

def get_streak(username):

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT DISTINCT date FROM submissions
        WHERE username=? AND status='Passed ✅'
        ORDER BY date DESC
    """, (username,))

    dates = cursor.fetchall()
    conn.close()

    if not dates:
        return 0

    streak = 0
    today = datetime.today().date()

    for i, row in enumerate(dates):
        d = datetime.strptime(row[0], "%Y-%m-%d").date()

        if i == 0:
            if d == today or d == today - timedelta(days=1):
                streak = 1
            else:
                break
        else:
            if d == prev_day - timedelta(days=1):
                streak += 1
            else:
                break

        prev_day = d

    return streak

# ---------------- HOME ----------------

@app.route("/")
def home():

    index = int(request.args.get("problem", 0))
    if index >= len(all_problems):
        index = 0

    problem = all_problems[index]

    username = session.get("username", "guest")

    solved, total, accuracy = get_progress(username)
    streak = get_streak(username)

    return render_template(
        "index.html",
        problem=problem,
        problems=all_problems,
        current_index=index,
        username=username,
        solved=solved,
        total=total,
        accuracy=accuracy,
        streak=streak
    )

# ---------------- RUN ----------------

@app.route("/run", methods=["POST"])
def run_code():
    code = request.form.get("code")
    index = int(request.form.get("problem_index", 0))
    problem = all_problems[index]

    try:
        local_scope = {}
        exec(code, {}, local_scope)
        func = local_scope.get(problem["function_name"])

        if not func:
            return "⚠️ Function not found"

        result = func(problem["test_cases"][0][0])
        return f"✅ Output: {result}"

    except Exception as e:
        return f"❌ Error: {str(e)}"

# ---------------- HINT ----------------

@app.route("/hint", methods=["POST"])
def hint():
    code = request.form.get("code")
    index = int(request.form.get("problem_index", 0))
    problem = all_problems[index]

    if problem["function_name"] not in code:
        return f"💡 Define function '{problem['function_name']}'"

    if "for" not in code:
        return "💡 Try loop"

    return "💡 Think logically step by step"

# ---------------- EVALUATE ----------------

def evaluate_code(code, problem):
    try:
        local_scope = {}
        exec(code, {}, local_scope)
        func = local_scope.get(problem["function_name"])

        if not func:
            return "❌ Function not found"

        for inp, expected in problem["test_cases"] + problem["hidden_cases"]:
            result = func(inp)
            if result != expected:
                return f"❌ Failed\nInput: {inp}\nExpected: {expected}\nGot: {result}"

        return "Passed ✅"

    except Exception as e:
        return f"❌ Error: {str(e)}"

# ---------------- SUBMIT ----------------

@app.route("/submit", methods=["POST"])
def submit():

    code = request.form.get("code")
    index = int(request.form.get("problem_index", 0))
    problem = all_problems[index]

    username = session.get("username", "guest")

    status = evaluate_code(code, problem)

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    today = datetime.today().strftime("%Y-%m-%d")

    cursor.execute(
        "INSERT INTO submissions (username, code, status, date) VALUES (?, ?, ?, ?)",
        (username, code, status, today)
    )

    conn.commit()
    conn.close()

    if status == "Passed ✅":
        next_index = index + 1
        if next_index >= len(all_problems):
            next_index = index
    else:
        next_index = index

    solved, total, accuracy = get_progress(username)
    streak = get_streak(username)

    return render_template(
        "index.html",
        problem=all_problems[next_index],
        problems=all_problems,
        current_index=next_index,
        result=status,
        username=username,
        solved=solved,
        total=total,
        accuracy=accuracy,
        streak=streak
    )

# ---------------- LOGIN ----------------

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        session["username"] = request.form["username"]
        return redirect("/")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("username", None)
    return redirect("/")

@app.route("/signup")
def signup():
    return render_template("signup.html")

if __name__ == "__main__":
    app.run(debug=True)