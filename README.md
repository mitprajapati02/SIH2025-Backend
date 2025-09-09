# SIH2025-Backend

this is repo for SIH2025-Backend

# make repo for pyton and note environment

📊 Data Insights Dashboard APIs

This project provides a set of APIs that work on a given dataset to deliver insights, notifications, and a visual dashboard for mentors and administrators.

🚀 Features

Email Mentors – Notify mentors about student performance or risk indicators.

Export Output – Generate downloadable reports from filtered or processed data.

Filter & Dashboard – Display a color-coded dashboard that highlights trends and alerts.

🛠 API Endpoints
1. 📧 Email Mentors

Endpoint:

GET /get_risk_students


Description:
Sends an automated email to a mentor with details about their assigned students (performance, alerts, etc.).

Request Body Example:

{
  "mentorId": "M123",
  "subject": "Student Progress Report",
  "message": "3 students are at academic risk this week."
}


Response Example:

{
  "status": "success",
  "sentTo": "mentor123@college.edu"
}

2. 📂 Export Output

Endpoint:

GET /


Description:
Exports processed data in CSV/Excel/JSON format for offline analysis or record-keeping.

Query Parameters:

format (optional): csv, excel, json (default: csv)

filter (optional): dataset filters

Example:

GET /api/export?format=csv&filter=atRiskStudents


Response:

File download (CSV/Excel/JSON)

3. 📊 Filter & Color-Coded Dashboard

Endpoint:

GET /


Description:
Displays a filtered dataset in a color-coded dashboard:

🟢 Green → Safe / Good progress

🟡 Yellow → Needs attention

🔴 Red → At risk

Query Parameters:

filter: category or condition (attendance, grades, fees, etc.)

range: optional time range

Example:

GET /api/dashboard?filter=grades&range=last30days


Response Example:

{
  "dashboard": [
    { "student": "Amit", "status": "safe", "color": "green" },
    { "student": "Priya", "status": "needs_attention", "color": "yellow" },
    { "student": "Rahul", "status": "at_risk", "color": "red" }
  ]
}

📂 Dataset

All APIs work on a given set of student/academic data, which typically includes:

Student details (ID, name, email, mentorId)

Academic performance (marks, attendance, etc.)

Alerts and risk indicators

⚙ Tech Stack

Backend: Node.js + Express

Database: SQLite / MongoDB (configurable)

Utilities: Nodemailer (for emails), JSON2CSV / ExcelJS (for exports), Chart.js / D3.js (for dashboard)

📌 How to Run

Clone the repo:

git clone https://github.com/your-repo/data-dashboard.git
cd data-dashboard


Install dependencies:

pip install dependency_name


Start the server:

python main.py


Access the APIs at:

http://localhost:5000/

✨ Future Enhancements

Role-based access (mentor, admin, student)

Predictive analytics using AI/ML models

Real-time notifications (SMS / WhatsApp)
