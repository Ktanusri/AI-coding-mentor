from flask import Flask, render_template, request, session, redirect
import sqlite3
import json

app = Flask(__name__)
app.secret_key = "supersecretkey"

# ---------------- LOAD PROBLEMS ----------------

with open("problems.json") as f:
    all_problems = json.load(f)

# ---------------- HOME ----------------

@app.route("/")
def home():

    difficulty = request.args.get("difficulty", "All")
    category = request.args.get("category", "All")

    problems = all_problems

    # filter by difficulty
    if difficulty != "All":
        problems = [p for p in problems if p["difficulty"] == difficulty]

    # filter by category
    if category != "All":
        problems = [p for p in problems if p.get("category", "General") == category]

    index = int(request.args.get("problem", 0))

    if index >= len(problems):
        index = 0

    problem = problems[index]

    return render_template(
        "index.html",
        problem=problem,
        problems=problems,
        current_index=index,
        difficulty=difficulty,
        category=category,
        username=session.get("username")
    )

# ---------------- RUN ----------------

@app.route("/run", methods=["POST"])
def run_code():

    user_code = request.form.get("code")
    index = int(request.form.get("problem_index", 0))
    difficulty = request.form.get("difficulty", "All")
    category = request.form.get("category", "All")

    problems = all_problems

    if difficulty != "All":
        problems = [p for p in problems if p["difficulty"] == difficulty]

    if category != "All":
        problems = [p for p in problems if p.get("category", "General") == category]

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
                return f"Failed ❌ (Input: {inp}, Expected: {expected}, Got: {result})"

        return "Passed ✅"

    except Exception as e:
        return f"❌ Code Error: {str(e)}"

# ---------------- SUBMIT ----------------

@app.route("/submit", methods=["POST"])
def submit():

    user_code = request.form.get("code")
    index = int(request.form.get("problem_index", 0))
    difficulty = request.form.get("difficulty", "All")
    category = request.form.get("category", "All")

    problems = all_problems

    if difficulty != "All":
        problems = [p for p in problems if p["difficulty"] == difficulty]

    if category != "All":
        problems = [p for p in problems if p.get("category", "General") == category]

    problem = problems[index]

    username = session.get("username", "guest")

    status = evaluate_code(user_code, problem)

    if status == "Passed ✅":
        next_index = index + 1
        if next_index >= len(problems):
            return render_template(
                "index.html",
                problem=problem,
                problems=problems,
                current_index=index,
                difficulty=difficulty,
                category=category,
                result="🎉 All problems completed!",
                username=username
            )
    else:
        next_index = index

    return render_template(
        "index.html",
        problem=problems[next_index],
        problems=problems,
        current_index=next_index,
        difficulty=difficulty,
        category=category,
        result=status,
        username=username
    )

# ---------------- LOGIN ----------------

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        user = cursor.fetchone()
        conn.close()

        if user:
            session["username"] = username
            return redirect("/")
        else:
            return "Invalid credentials"

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("username", None)
    return redirect("/")

@app.route("/signup", methods=["GET", "POST"])
def signup():

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        cursor.execute("INSERT INTO users (username,password) VALUES (?,?)", (username, password))
        conn.commit()
        conn.close()

        return redirect("/login")

    return render_template("signup.html")

if __name__ == "__main__":
    app.run(debug=True)