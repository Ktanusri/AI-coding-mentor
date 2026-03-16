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
"title":"Find Maximum",
"description":"Write a function that returns the maximum number from a list.",
"difficulty":"Easy",
"example_input":"[3,5,1,8,2]",
"example_output":"8"
},

{
"title":"Sum of Array",
"description":"Return the sum of numbers in a list.",
"difficulty":"Easy",
"example_input":"[1,2,3,4]",
"example_output":"10"
},

{
"title":"Palindrome Check",
"description":"Check if a string is a palindrome.",
"difficulty":"Medium",
"example_input":"madam",
"example_output":"True"
},

{
"title":"Second Largest Number",
"description":"Find the second largest number in a list.",
"difficulty":"Medium",
"example_input":"[4,7,1,9,3]",
"example_output":"7"
},

{
"title":"Longest Word",
"description":"Return the longest word in a sentence.",
"difficulty":"Hard",
"example_input":"AI coding mentor project",
"example_output":"project"
}

]

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

    problem = random.choice(problems)

    return render_template(
        "index.html",
        problem=problem,
        submissions=submissions,
        total_submissions=total_submissions,
        avg_time=round(avg_time,2),
        problems_solved=total_submissions
    )


@app.route("/submit", methods=["POST"])
def submit():

    user_code = request.form.get("code")
    duration = request.form.get("duration")

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO submissions (code, duration) VALUES (?, ?)",
        (user_code, duration)
    )

    conn.commit()
    conn.close()

    feedback = "Code submitted successfully!"

    return render_template(
        "index.html",
        feedback=feedback
    )

@app.route("/run", methods=["POST"])
def run_code():
    user_code = request.form.get("code")

    output = ""

    try:
        local_scope = {}
        exec(user_code, {}, local_scope)

        if "find_max" in local_scope:
            result = local_scope["find_max"]([3,5,1,8,2])
            output = str(result)
        else:
            output = "Function find_max not found."

    except Exception as e:
        output = str(e)

    return output

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)