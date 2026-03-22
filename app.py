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

try:
    with open("problems.json") as f:
        problems = json.load(f)
except:
    problems = [
        {
            "title": "Find Maximum",
            "description": "Return maximum number from list",
            "difficulty": "Easy",
            "function_name": "find_max",
            "test_cases": [[[3,5,1,8,2],8]],
            "hidden_cases": []
        }
    ]

# ---------------- AI FEEDBACK ----------------

def get_ai_feedback(code):
    return "💡 AI feedback coming soon!"

# ---------------- CODE EXECUTION ----------------

def evaluate_code(user_code, problem):
    try:
        local_scope = {}
        exec(user_code, {}, local_scope)

        func_name = problem["function_name"]

        if func_name not in local_scope:
            return f"❌ Function '{func_name}' not found"

        func = local_scope[func_name]

        test_cases = problem["test_cases"] + problem["hidden_cases"]

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

    index = int(request.args.get("problem", 0))
    problem = problems[index]

    return render_template(
        "index.html",
        problem=problem,
        problems=problems,
        current_index=index,
        username=session.get("username")
    )

# ---------------- RUN CODE ----------------

@app.route("/run", methods=["POST"])
def run_code():

    user_code = request.form.get("code")
    index = int(request.form.get("problem_index", 0))
    problem = problems[index]

    try:
        local_scope = {}
        exec(user_code, {}, local_scope)

        func = local_scope.get(problem["function_name"])

        if not func:
            return "⚠️ Function not found"

        result = func(problem["test_cases"][0][0])

        return f"✅ Output: {result}"

    except Exception as e:
        return f"❌ Error: {str(e)}"

# ---------------- SUBMIT ----------------

@app.route("/submit", methods=["POST"])
def submit():

    user_code = request.form.get("code")
    index = int(request.form.get("problem_index", 0))
    problem = problems[index]

    username = session.get("username", "guest")

    # Evaluate
    status = evaluate_code(user_code, problem)
    feedback = get_ai_feedback(user_code)

    # Auto next problem
    if status == "Passed ✅":
        next_index = index + 1
        if next_index >= len(problems):
         return render_template(
        "index.html",
        problem=problem,
        problems=problems,
        current_index=index,
        result="🎉 All problems completed!",
        feedback="Great job!",
        username=username
    )
    else:
        next_index = index

    # Save to DB
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO submissions (username, code, duration, status) VALUES (?, ?, ?, ?)",
        (username, user_code, 0, status)
    )

    conn.commit()
    conn.close()

    return render_template(
        "index.html",
        problem=problems[next_index],
        problems=problems,
        current_index=next_index,
        result=status,
        feedback=feedback,
        username=username
    )

@app.route("/profile")
def profile():
    username = session.get("username")
    return render_template("profile.html", username=username)
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

if __name__ == "__main__":
    app.run(debug=True)