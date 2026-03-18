from flask import Flask, render_template, request
import sqlite3
import json

app = Flask(__name__)

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
            duration REAL
        )
    """)

    conn.commit()
    conn.close()

init_db()

# ---------------- LOAD PROBLEMS ----------------

with open("problems.json") as f:
    problems = json.load(f)

# ---------------- HOME ----------------

@app.route("/")
def home():

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM submissions")
    total_submissions = cursor.fetchone()[0]

    cursor.execute("SELECT AVG(duration) FROM submissions")
    avg_time = cursor.fetchone()[0]

    if avg_time is None:
        avg_time = 0

    cursor.execute("SELECT * FROM submissions")
    submissions = cursor.fetchall()

    conn.close()

    # get selected problem
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
        avg_time=round(avg_time,2),
        problems_solved=total_submissions
    )

# ---------------- RUN CODE ----------------

@app.route("/run", methods=["POST"])
def run_code():

    user_code = request.form.get("code")
    index = request.form.get("problem_index")

    problem = problems[int(index)] if index else problems[0]

    results = []
    passed = 0
    total = 0

    try:
        local_scope = {}
        exec(user_code, {}, local_scope)

        func_name = problem["function_name"]

        if func_name in local_scope:

            func = local_scope[func_name]

            for inp, expected in problem["test_cases"]:
                total += 1
                if func(inp) == expected:
                    results.append("Pass")
                    passed += 1
                else:
                    results.append("Fail")

            for inp, expected in problem["hidden_cases"]:
                total += 1
                if func(inp) == expected:
                    passed += 1

        else:
            return "Function not found"

    except Exception as e:
        return str(e)

    return f"Results: {results} | Score: {passed}/{total}"

# ---------------- SUBMIT ----------------

@app.route("/submit", methods=["POST"])
def submit():

    user_code = request.form.get("code")
    duration = request.form.get("duration")
    username = request.form.get("username","guest")

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO submissions (username, code, duration) VALUES (?, ?, ?)",
        (username, user_code, duration)
    )

    conn.commit()
    conn.close()

    return "Submitted!"

# ---------------- PROBLEM LIST ----------------

@app.route("/problems")
def problem_list():
    return render_template("problems.html", problems=problems)

# ---------------- LEADERBOARD ----------------

@app.route("/leaderboard")
def leaderboard():

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT username, COUNT(*) 
        FROM submissions 
        GROUP BY username 
        ORDER BY COUNT(*) DESC
    """)

    data = cursor.fetchall()
    conn.close()

    return render_template("leaderboard.html", leaderboard=data)

# ---------------- LOGIN ----------------

@app.route("/login", methods=["GET","POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username,password)
        )

        user = cursor.fetchone()
        conn.close()

        if user:
            return "Login success"
        else:
            return "Invalid login"

    return render_template("login.html")

# ---------------- SIGNUP ----------------

@app.route("/signup", methods=["GET","POST"])
def signup():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO users (username,password) VALUES (?,?)",
            (username,password)
        )

        conn.commit()
        conn.close()

        return "Signup success"

    return render_template("signup.html")

# ---------------- RUN ----------------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)