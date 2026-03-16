from flask import Flask, render_template, request
import sqlite3
import random

app = Flask(__name__)

def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT,
            duration REAL
        )
    """)
    conn.commit()
    conn.close()

init_db()

problems = [
    {
        "title": "Find Maximum",
        "description": "Write a function that returns the maximum number from a list.",
        "example_input": "[3,5,1,8,2]",
        "example_output": "8"
    },
    {
        "title": "Sum of Array",
        "description": "Return the sum of numbers in a list.",
        "example_input": "[1,2,3,4]",
        "example_output": "10"
    },
    {
        "title": "Palindrome Check",
        "description": "Check if a string is a palindrome.",
        "example_input": '"madam"',
        "example_output": "True"
    }
]

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/practice")
def practice():
    problem = random.choice(problems)
    return render_template("practice.html", problem=problem)

@app.route("/submit", methods=["POST"])
def submit():
    user_code = request.form.get("code")
    duration = request.form.get("duration")
    feedback = "Code received."
    hint = ""

    if "max" not in user_code:
        hint = "Hint: Try using max() to find the largest number."
    elif "sum" in user_code:
        hint = "Hint: sum() is useful for adding list elements."
    elif "[::-1]" in user_code:
        hint = "Hint: Good use of slicing to reverse a string."
    else:
        hint = "Hint: Think about Python built-in functions."

    test_cases = [
        ([3, 5, 1, 8, 2], 8),
        ([10, 4, 7], 10),
        ([1], 1)
    ]

    results = []
    local_scope = {}

    try:
        exec(user_code, {}, local_scope)
        if "find_max" in local_scope:
            find_max = local_scope["find_max"]
            for arr, expected in test_cases:
                result = find_max(arr)
                if result == expected:
                    results.append("Passed")
                else:
                    results.append("Failed")
        else:
            feedback = "Function 'find_max' not found in your code."
    except Exception as e:
        feedback = str(e)
        results = []

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO submissions (code, duration) VALUES (?, ?)",
        (user_code, duration)
    )
    conn.commit()
    conn.close()

    return render_template(
        "feedback.html",
        feedback=feedback,
        results=results,
        hint=hint
    )

@app.route("/dashboard")
def dashboard():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM submissions")
    total_submissions = cursor.fetchone()[0]

    cursor.execute("SELECT id FROM submissions")
    rows = cursor.fetchall()
    submission_ids = [row[0] for row in rows]

    streak = total_submissions

    cursor.execute("SELECT AVG(duration) FROM submissions")
    avg_time = cursor.fetchone()[0]
    if avg_time is None:
        avg_time = 0

    if avg_time < 30:
        difficulty = "Hard"
    elif avg_time < 90:
        difficulty = "Medium"
    else:
        difficulty = "Easy"

    problems_solved = total_submissions

    if problems_solved < 3:
        skill_level = "Beginner"
    elif problems_solved < 6:
        skill_level = "Improving"
    else:
        skill_level = "Advanced"

    conn.close()

    return render_template(
        "dashboard.html",
        total_submissions=total_submissions,
        streak=streak,
        submission_ids=submission_ids,
        avg_time=round(avg_time, 2),
        difficulty=difficulty,
        problems_solved=problems_solved,
        skill_level=skill_level
    )

@app.route("/history")
def history():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM submissions")
    submissions = cursor.fetchall()
    conn.close()
    return render_template("history.html", submissions=submissions)

@app.route("/journey")
def journey():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM submissions")
    submissions = cursor.fetchall()
    conn.close()
    return render_template("journey.html", submissions=submissions)

    if __name__ == "__main__":
     app.run(host="0.0.0.0", port=5000)