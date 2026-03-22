from flask import Flask, render_template, request, session, redirect
import sqlite3
import json

app = Flask(__name__)
app.secret_key = "supersecretkey"

# ---------------- LOAD PROBLEMS ----------------

with open("problems.json") as f:
    all_problems = json.load(f)

# ---------------- PROGRESS CALC ----------------

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

    accuracy = 0
    if total > 0:
        accuracy = int((solved / total) * 100)

    return solved, total, accuracy

# ---------------- AI HINT ----------------

def get_hint(code, problem):

    if problem["function_name"] not in code:
        return f"💡 Define function '{problem['function_name']}' first"

    if "for" not in code and "while" not in code:
        return "💡 Try using a loop"

    if "max" in problem["title"].lower() and "max(" not in code:
        return "💡 Use max() function"

    if "sum" in problem["title"].lower() and "sum(" not in code:
        return "💡 Try sum() function"

    if "return" not in code:
        return "💡 Don't forget to return value"

    return "✅ Good approach! Handle edge cases."

# ---------------- HOME ----------------

@app.route("/")
def home():

    difficulty = request.args.get("difficulty", "All")
    category = request.args.get("category", "All")

    problems = all_problems

    if difficulty != "All":
        problems = [p for p in problems if p["difficulty"] == difficulty]

    if category != "All":
        problems = [p for p in problems if p.get("category", "General") == category]

    index = int(request.args.get("problem", 0))
    if index >= len(problems):
        index = 0

    problem = problems[index]

    username = session.get("username", "guest")
    solved, total, accuracy = get_progress(username)

    return render_template(
        "index.html",
        problem=problem,
        problems=problems,
        current_index=index,
        difficulty=difficulty,
        category=category,
        username=username,
        solved=solved,
        total=total,
        accuracy=accuracy
    )

# ---------------- RUN ----------------

@app.route("/run", methods=["POST"])
def run_code():

    user_code = request.form.get("code")
    index = int(request.form.get("problem_index", 0))

    problem = all_problems[index]

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

# ---------------- HINT ----------------

@app.route("/hint", methods=["POST"])
def hint():
    code = request.form.get("code")
    index = int(request.form.get("problem_index", 0))

    problem = all_problems[index]
    return get_hint(code, problem)

# ---------------- EVALUATE ----------------

def evaluate_code(user_code, problem):
    try:
        local_scope = {}
        exec(user_code, {}, local_scope)

        func = local_scope.get(problem["function_name"])

        if not func:
            return "❌ Function not found"

        for inp, expected in problem["test_cases"] + problem["hidden_cases"]:
            result = func(inp)
            if result != expected:
                return (
                    f"❌ Failed\nInput: {inp}\nYour Output: {result}\nExpected: {expected}"
                )

        return "Passed ✅"

    except Exception as e:
        return f"❌ Code Error: {str(e)}"

# ---------------- SUBMIT ----------------

@app.route("/submit", methods=["POST"])
def submit():

    user_code = request.form.get("code")
    index = int(request.form.get("problem_index", 0))
    problem = all_problems[index]

    username = session.get("username", "guest")

    status = evaluate_code(user_code, problem)

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO submissions (username, code, duration, status) VALUES (?, ?, ?, ?)",
        (username, user_code, 0, status)
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

    return render_template(
        "index.html",
        problem=all_problems[next_index],
        problems=all_problems,
        current_index=next_index,
        result=status,
        username=username,
        solved=solved,
        total=total,
        accuracy=accuracy
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