from flask import Flask, render_template, request
import sqlite3
import json
from openai import OpenAI

app = Flask(__name__)

client = OpenAI(api_key="YOUR_NEW_API_KEY_HERE")

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
    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": "You are a coding mentor."},
                {"role": "user", "content": f"Review this Python code:\n{code}"}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"AI error: {str(e)}"

# ---------------- CODE EXECUTION ----------------

def evaluate_code(user_code):
    try:
        local_scope = {}
        exec(user_code, {}, local_scope)

        if len(local_scope) == 0:
            return "❌ No function found"

        func = list(local_scope.values())[0]

        # Test case
        test_input = [3, 5, 1, 8, 2]
        expected_output = 8

        try:
            result = func(test_input)

            if result == expected_output:
                return "Passed ✅"
            else:
                return f"Failed ❌ (Expected {expected_output}, Got {result})"

        except Exception:
            return "❌ Error while executing function"

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
        feedback=""
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

# ---------------- SUBMIT (FIXED 🔥) ----------------

@app.route("/submit", methods=["POST"])
def submit():

    user_code = request.form.get("code")
    duration = request.form.get("duration")
    username = request.form.get("username", "guest")

    # 🔥 Evaluate code
    status = evaluate_code(user_code)

    # 🔥 AI Feedback
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
        problems=problems
    )

# ---------------- PROBLEMS ----------------

@app.route("/problems")
def problems_page():
    return render_template("problems.html", problems=problems)

# ---------------- LEADERBOARD ----------------

@app.route("/leaderboard")
def leaderboard():

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT username, COUNT(*) as score 
        FROM submissions 
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
            return "Login successful!"
        else:
            return "Invalid credentials"

    return render_template("login.html")

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

        return "Signup successful!"

    return render_template("signup.html")

# ---------------- RUN APP ----------------

if __name__ == "__main__":
    app.run(debug=True)