import requests
import json
from pprint import pprint as pprint
import statistics
import matplotlib.pyplot as plt
import numpy as np


def grab_sysgen(session_id, ashoka_email):
    url = "https://ams.ashoka.edu.in/Contents/Masters/ViewstudentDirectory.aspx/GetStudentList"
    headers = {    }
    post_data = json.dumps(
        {
            "XMLData": "<tbl><tr><ProgrammeSysGenId></ProgrammeSysGenId><SessionSysGenId"
                       "></SessionSysGenId "
                       "><ScheduleSysGenId></ScheduleSysGenId><CourseSysGenId></CourseSysGenId><LSNo></LSNo><DSNo"
                       "></DSNo><SearchByText>" + ashoka_email + "</SearchByText></tr></tbl>",
            "ListType": "All",
        }
    )
    try:
        response = requests.post(url, data=post_data, headers=headers)
        return str(response.content).split('\\\\"UserSysGenId\\\\": \\\\"')[1][0:11]
    except:
        return "0000000000"


def grab_grade(session_id, ashoka_email, sysgen_id, force_request, file_name):
    if not force_request:
        with open(file_name, 'r') as file:
            file_objects = json.load(file)
            for student_index, student_object in enumerate(file_objects["data"]):
                if ashoka_email in student_object["AshokaEmailID"] or ashoka_email in student_object["Name"]:
                    print("Found in file!")
                    return student_object

    print(f"Sending request for ID {sysgen_id}...")
    url = "https://ams.ashoka.edu.in/Services/MasterServices.asmx/GetCourseReport"

    headers = {    }
    post_data = json.dumps(
        {"xml": "<tbl><tr><UserSysGenId>" + sysgen_id + "</UserSysGenId></tr></tbl>"}
    )

    response = requests.post(url, data=post_data, headers=headers)

    return (
        parse_grade(response.content.replace(b"\\r", b"").replace(b"\\n", b"").replace(b'\\"', b'"'))
    )


def parse_grade(json_string):
    json_data = {}
    json_string = str(json_string)[2:]
    if "ProgrammeSysGenId" not in json_string:
        return None

    json_data["ProgrammeSysGenId"] = json_string.split('ProgrammeSysGenId": "')[1].split('",      "Name"')[0]
    json_data["Name"] = json_string.split('Name": "')[1].split('",      "CurrentCGPA"')[0]
    json_data["CurrentCGPA"] = json_string.split('CurrentCGPA": "')[1].split('",      "MajorCGPA"')[0]
    json_data["MajorCGPA"] = json_string.split('MajorCGPA": "')[1].split('",      "OVERALL_CREDITS"')[0]
    json_data["AshokaID"] = json_string.split('AshokaId": "')[1].split('",      "AshokaEmailId"')[0]
    json_data["AshokaEmailID"] = json_string.split('AshokaEmailId": "')[1].split('",      "ProgrammeSysGenId"')[0]

    semesters = json_string.split('"CourseCode"')[0].split('"Semester":')[1:-1]
    json_data["semesters"] = []
    for semester in semesters:
        semester_json = {}
        semester_json["semester"] = (
            semester.split(' "')[1].split('",      "Status')[0].strip('",     ')
        )
        semester_json["GPA"] = float(
            semester.split('"GPA": "')[1].split('",      "SemesterCGPA')[0]
        )
        semester_json["CGPA"] = float(
            semester.split('"SemesterCGPA": "')[1].split('",      "Deans_List"')[0]
        )
        semester_json["Dean's List"] = (
            True
            if "Dean"
               in semester.split('"Deans_List": "')[1].split(
                '"    },    {      "ScheduleSysGenId'
            )[0]
            else False
        )
        json_data["semesters"].append(semester_json)

    courses = json_string.split('"Table3": [')[1].split("ScheduleSysGenId")[1:]
    json_data["courses"] = []
    for course in courses:
        course_json = {}
        course_json["CourseSysGenId"] = course.split('"CourseSysGenId": "')[1].split(
            '",      "Semester"'
        )[0]
        course_json["semester"] = course.split('"Semester": "')[1].split(
            '",      "CourseCode"'
        )[0]
        course_json["code"] = course.split('"CourseCode": "')[1].split(
            '",      "CourseName"'
        )[0]
        course_json["name"] = course.split('"CourseName": "')[1].split(
            '",      "Grade'
        )[0]
        course_json["grade"] = course.split('"Grade": "')[1].split(
            '",      "CountinCredits"'
        )[0]
        json_data["courses"].append(course_json)

    return json_data


def update_file(file_name, new_object, email):
    with open(file_name, 'r') as file:
        file_objects = json.load(file)

    for student_index, student_object in enumerate(file_objects["data"]):

        if new_object["AshokaEmailID"] == student_object["AshokaEmailID"] or new_object["Name"] in student_object["Name"]:
            if student_object == new_object:
                return "Exists in file!"

            else:
                file_objects["data"][student_index] = new_object
                with open(file_name, 'w') as file:
                    json.dump(file_objects, file, indent=4)
                return "Updated in file!"

    else:
        file_objects["data"].append(new_object)
        with open(file_name, 'w') as file:
            json.dump(file_objects, file, indent=4)
        return "Appended to file!"


def generate_ranking(file_name):
    with open(file_name, 'r') as file:
        students = json.load(file)["data"]

    pairs = []
    for student in students:
        if "ug24" in student["AshokaEmailID"] or "" in [x["name"] for x in student["courses"]]:
            pairs.append((student["Name"], student["CurrentCGPA"]))

    data = [float(x[1]) for x in pairs]
    print(f"Mean: {statistics.mean(data):.2f}")
    print(f"Median: {statistics.median(data):.2f}")
    print(f"Mode: {statistics.mode(data):.2f}")
    print(f"Std Dev: {statistics.stdev(data):.2f}")
    print(f"Variance: {statistics.variance(data):.2f}")
    # plt.plot(np.array(sorted(data)[10:]))
    # plt.show()
    # plt.hist(np.array(sorted(data)[10:]), bins=20, edgecolor='black')
    # plt.show()

    return sorted(pairs, reverse=True, key=lambda x: x[1])


def generate_course_grades(file_name, course_name, semester):
    with open(file_name, 'r') as file:
        file_objects = json.load(file)

    grades = []
    for student in file_objects["data"]:
        for course in student["courses"]:

            if course_name in course["name"] and semester in course["semester"]:
                grades.append((course["grade"], student["Name"], course["semester"]))
                break

    map = {'A': 4, 'A-': 3.7, 'B+': 3.3, 'B': 3, 'B-': 2.7, 'C+': 2.3, 'C': 2, 'C-': 1.7, 'D+': 1.3, 'D': 1, 'D-': 0.7, 'F': 0, 'WF': 0}
    data = [map[x[0]] for x in grades if x[0] not in ['P', 'TP', 'TC', 'W', 'I', 'AU']]
    print(f"Mean: {statistics.mean(data):.2f}")
    print(f"Median: {statistics.median(data):.2f}")
    print(f"Mode: {statistics.mode(data):.2f}")
    print(f"Std Dev: {statistics.stdev(data):.2f}")
    print(f"Variance: {statistics.variance(data):.2f}")

    return sorted(grades, reverse=False, key=lambda x: x[0])


def update_all(session_id, force_request, file_name):
    with open(file_name, 'r') as file:
        file_objects = json.load(file)

    for student_index, student_object in enumerate(file_objects["data"]):
        student_sysgen = grab_sysgen(session_id, student_object["AshokaEmailID"])
        student_grades = grab_grade(session_id, student_object["AshokaEmailID"], student_sysgen, force_request, file_name)
        pprint(student_grades)
        print(update_file(file_name, student_grades, student_object["AshokaEmailID"]))
        print("\n\n")


def main():
    force_request = 1
    file_name = "D:/code/scripts/ams_grades/student_grades.json"
    session_id = ""

    email = ""

    student_sysgen = grab_sysgen(session_id, email)
    student_grades = grab_grade(session_id, email, student_sysgen, force_request, file_name)

    ranking = generate_ranking("./ams_grades/student_grades.json")
    pprint([(ranking.index(x)+1, x) for x in ranking])
    course = generate_course_grades(file_name, "GIS 1", "Monsoon 2023")
    pprint(course)

    pprint(student_grades)
    # update_all(session_id, force_request, file_name)

    print(update_file(file_name, student_grades, email))


if __name__ == "__main__":
    main()
