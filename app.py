from flask import Flask, render_template, request, session, redirect
import sqlite3
import json

app = Flask(__name__)
app.secret_key = "supersecretkey"

# ---------------- LOAD PROBLEMS ----------------

with open("problems.json") as f:
    all_problems = json.load(f)

# ---------------- AI HINT SYSTEM ----------------

def get_hint(code, problem):

    if problem["function_name"] not in code:
        return f"💡 Define function '{problem['function_name']}' first"

    if "for" not in code and "while" not in code:
        return "💡 Try using a loop"

    if "max" in problem["title"].lower() and "max(" not in code:
        return "💡 Python has built-in max() function"

    if "sum" in problem["title"].lower() and "sum(" not in code:
        return "💡 Try using sum() function"

    if "return" not in code:
        return "💡 Don't forget to return the result"

    return "✅ Good approach! Try handling edge cases."

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

# ---------------- HINT ROUTE ----------------

@app.route("/hint", methods=["POST"])
def hint():
    code = request.form.get("code")
    index = int(request.form.get("problem_index", 0))

    problem = all_problems[index]

    hint = get_hint(code, problem)

    return hint

# ---------------- EVALUATE ----------------

# ---------------- EVALUATE ----------------

def evaluate_code(user_code, problem):
    try:
        local_scope = {}
        exec(user_code, {}, local_scope)

        func = local_scope.get(problem["function_name"])

        if not func:
            return "❌ Function not found"

        for inp, expected in problem["test_cases"] + problem["hidden_cases"]:
            try:
                result = func(inp)
            except Exception as e:
                return f"❌ Runtime Error on input {inp}: {str(e)}"

            if result != expected:
                return (
                    f"❌ Failed\n"
                    f"Input: {inp}\n"
                    f"Your Output: {result}\n"
                    f"Expected: {expected}"
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

    if status == "Passed ✅":
        next_index = index + 1
        if next_index >= len(all_problems):
            return render_template(
                "index.html",
                problem=problem,
                problems=all_problems,
                current_index=index,
                result="🎉 All problems completed!",
                username=username
            )
    else:
        next_index = index

    return render_template(
        "index.html",
        problem=all_problems[next_index],
        problems=all_problems,
        current_index=next_index,
        result=status,
        username=username
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