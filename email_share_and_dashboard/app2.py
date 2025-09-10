from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd

app = Flask(__name__)
CORS(app)


def read_file_to_df(f):
    if f is None:
        return pd.DataFrame()
    fname = f.filename.lower()
    if fname.endswith((".xlsx", ".xls")):
        return pd.read_excel(f)
    else:
        return pd.read_csv(f)


def calculate_risk(attendance, marks, fee_status, min_attendance, min_marks, fee_condition):
    # High risk
    if (attendance < min_attendance - 10) or (marks < min_marks - 10) or (fee_status.lower() == "overdue"):
        return "High"
    # Medium risk
    if (attendance < min_attendance) or (marks < min_marks) or (
        fee_condition == "due" and fee_status.lower() in ["due", "overdue"]
    ):
        return "Medium"
    # Low risk
    return "Low"


@app.route("/dropout", methods=["POST"])
def dropout():
    try:
        # 1. Get uploaded files
        attendance_file = request.files.get("attendance")
        marks_file = request.files.get("marks")
        fees_file = request.files.get("fees")

        # 2. Read into DataFrames
        attendance_df = read_file_to_df(attendance_file)
        marks_df = read_file_to_df(marks_file)
        fees_df = read_file_to_df(fees_file)

        # 3. Clean column names
        attendance_df.columns = attendance_df.columns.str.strip()
        marks_df.columns = marks_df.columns.str.strip()
        fees_df.columns = fees_df.columns.str.strip()

        # 4. Merge on roll_no + name
        df = attendance_df.merge(marks_df, on=["roll_no", "name"]).merge(fees_df, on=["roll_no", "name"])

        # 5. Get filters
        min_attendance = int(request.form.get("min_attendance", 75))
        min_marks = int(request.form.get("min_marks", 35))
        fee_condition = request.form.get("fee_status", "due").lower()
        mentor_name = request.form.get("mentor_name", "Unknown")
        mentor_email = request.form.get("mentor_email", "unknown@example.com")

        # 6. Detect subjects
        mark_cols = [c for c in df.columns if "_marks" in c]
        attendance_cols = [c for c in df.columns if "_attendance" in c]

        # 7. Compute averages
        df["avg_marks"] = df[mark_cols].mean(axis=1)
        df["avg_attendance"] = df[attendance_cols].mean(axis=1)

        # 8. Risk level
        df["risk_level"] = df.apply(
            lambda row: calculate_risk(
                row["avg_attendance"], row["avg_marks"], row["fee_status"],
                min_attendance, min_marks, fee_condition
            ),
            axis=1
        )

        # 9. Stats
        total_students = int(len(df))
        high_risk = int((df["risk_level"] == "High").sum())
        dropout_percentage = round((high_risk / total_students) * 100, 2)

        if dropout_percentage <= 25:
            overall_status = "Healthy"
        elif dropout_percentage <= 50:
            overall_status = "Moderate"
        else:
            overall_status = "Critical"

        # 10. Convert dataframe rows to Python-native dicts
        students_data = df.to_dict(orient="records")
        for student in students_data:
            for k, v in student.items():
                if isinstance(v, (pd._libs.missing.NAType, type(pd.NA))):
                    student[k] = None
                elif isinstance(v, (pd.Series, pd.DataFrame)):
                    student[k] = str(v)
                elif hasattr(v, "item"):  # numpy types like int64, float64
                    student[k] = v.item()

        # 11. Build response
        response = {
            "mentor": {
                "name": mentor_name,
                "email": mentor_email
            },
            "filters": {
                "min_attendance": min_attendance,
                "min_marks": min_marks,
                "fee_status": fee_condition
            },
            "summary": {
                "total_students": total_students,
                "high_risk_students": high_risk,
                "dropout_percentage": float(dropout_percentage),
                "overall_status": overall_status
            },
            "students": students_data
        }

        return jsonify(response)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
