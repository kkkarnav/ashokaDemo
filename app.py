from flask import Flask, request, render_template_string
import pandas as pd

students_path = "./major_minor/students.csv"

df = pd.read_csv(students_path)

app = Flask(__name__)

@app.route('/')
def index():
    return render_template_string('''
        <form action="/result" method="post">
            Major: <input type="text" name="major"><br>
            Minor: <input type="text" name="minor"><br>
            Program: <input type="text" name="program"><br>
            Graduation Year: <input type="text" name="grad"><br>
            <input type="submit" value="Submit">
        </form>
    ''')


@app.route('/result', methods=['POST'])
def result():
    major = request.form['major'].upper()
    minor = request.form['minor'].upper()
    program = request.form['program'].upper()
    grad = int(request.form['grad'])

    if grad > 2024:
        count = df[(df["program"] == program) & (df["major"] == major) & (df["minor"] == minor) & (df["grad"] < grad)].shape[0]
        # names = ", ".join(df[(df["program"] == program) & (df["major"] == major) & (df["minor"] == minor) & (df["grad"] < grad)]["name"])
        this_year = df[(df["program"] == program) & (df["major"] == major) & (df["minor"] == minor) & ((df["grad"] == grad) | ((df["grad"] < grad) & (df["status"] == "Enrolled")))].shape[0]
    else:
        count = df[(df["program"] == program) & (df["major"] == major) & (df["minor"] == minor) & (df["status"] == "Graduated") & (df["grad"] < grad)].shape[0]
        # names = ", ".join(df[(df["program"] == program) & (df["major"] == major) & (df["minor"] == minor) & (df["status"] == "Graduated") & (df["grad"] < grad)])
        this_year = df[(df["program"] == program) & (df["major"] == major) & (df["minor"] == minor) & (df["status"] == "Graduated") & (df["grad"] == grad)].shape[0]

    count += 1

    num_suffix = "th"
    if count % 10 == 1 and count % 100 != 11:
        num_suffix = "st"
    elif count % 10 == 2 and count % 100 != 12:
        num_suffix = "nd"
    elif count % 10 == 3 and count % 100 != 13:
        num_suffix = "rd"

    prefix = "You were the "
    suffix = ""
    if grad > 2024:
        if this_year > 1:
            prefix = "You will be the (joint) "
            suffix = f"{this_year-1} students will share this achievement with you."
        else:
            prefix = "You will be the "
    elif grad <= 2024 and this_year > 1:
        prefix = "You were the (joint) "
        suffix = f"{this_year-1} students shared this achievement with you."

    if count == 1:
        return f"Hmmm are you sure you exist? Nobody's ever graduated with those credentials :p"

    return f"{prefix}{count}{num_suffix} student to ever graduate with a {major} major and {minor} minor from Ashoka!</br> {suffix}"


if __name__ == '__main__':
    app.run(debug=True)
