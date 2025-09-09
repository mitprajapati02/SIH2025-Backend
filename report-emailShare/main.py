from flask import Flask, render_template, request, send_file
from flask_mail import Mail, Message
import pandas as pd
from datetime import datetime
import io

from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

app = Flask(__name__)

# === Email Configuration ===
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'krishnaprajapat8814@gmail.com'  # <-- Change to your Gmail
app.config['MAIL_PASSWORD'] = 'lwsl etdi yudq vdfa'    # <-- Change to your Gmail App Password
app.config['MAIL_DEFAULT_SENDER'] = 'krishnaprajapat8814@gmail.com'

mail = Mail(app)

# === Home Page ===
@app.route('/')
def index():
    # Dummy data loading and merging (replace with your actual CSV reading code)
    marks = pd.read_csv('data/marks.csv')
    atd = pd.read_csv('data/attendance.csv')
    fees = pd.read_csv('data/fees.csv')

    merged_df = marks.merge(atd, on='student_id').merge(fees, on='student_id')

    merged_df['attendance_percent'] = ((merged_df['days_present'] / merged_df['total_days']) * 100).round(2)
    merged_df['marks_percent'] = ((merged_df['Total'] / merged_df['Out_of']) * 100).round(2)

    def marks_risk(data):
        total = data['Total']
        out_of = data['Out_of']
        if total < (out_of * 0.4):
            return 'High'
        elif total < (out_of * 0.6):
            return 'Moderate'
        else:
            return 'Safe'

    merged_df['marks_risk'] = merged_df.apply(marks_risk, axis=1)

    def get_risk_reasons(row):
        reasons = []
        if row['marks_risk'] in ['High', 'Moderate']:
            reasons.append('Low Marks')
        if row['attendance_percent'] < 75:
            reasons.append('Low Attendance')
        if row['Fees_Status'] != 'Paid':
            reasons.append('Fee Issues')
        return ', '.join(reasons) if reasons else 'None'

    merged_df['risk_reasons'] = merged_df.apply(get_risk_reasons, axis=1)

    def overall_risk(row):
        risk_score = 0
        if row['marks_risk'] == 'High':
            risk_score += 2
        elif row['marks_risk'] == 'Moderate':
            risk_score += 1
        if row['attendance_percent'] < 75:
            risk_score += 2
        elif row['attendance_percent'] < 85:
            risk_score += 1
        if row['Fees_Status'] != 'Paid':
            risk_score += 2

        if risk_score >= 5:
            return 'High'
        elif risk_score >= 2:
            return 'Moderate'
        else:
            return 'Safe'

    merged_df['overall_risk'] = merged_df.apply(overall_risk, axis=1)

    merged_df.to_csv('data/merged_data.csv', index=False)
    students = merged_df.to_dict(orient='records')

    return render_template('index.html', students=students)

# === PDF Generator ===
def generate_pdf_report_in_memory(df):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []

    styles = getSampleStyleSheet()
    elements.append(Paragraph("At-Risk Students Report", styles['Title']))
    elements.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
    elements.append(Paragraph("<br/><br/>", styles['Normal']))

    report_df = df[['student_id', 'Name', 'marks_percent', 'attendance_percent', 'Fees_Status', 'risk_reasons']]
    data = [report_df.columns.tolist()] + report_df.values.tolist()

    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))

    elements.append(table)
    doc.build(elements)
    buffer.seek(0)
    return buffer

# === Send Report via Email from Form ===
@app.route('/send-report', methods=['POST'])
def send_report_email_form():
    email = request.form.get('email')
    if not email:
        return "Email is required.", 400

    df = pd.read_csv('data/merged_data.csv')
    df['risk_reasons'] = df['risk_reasons'].fillna('None')
    at_risk_df = df[df['risk_reasons'] != 'None']

    if at_risk_df.empty:
        return "No at-risk students found.", 400

    pdf_buffer = generate_pdf_report_in_memory(at_risk_df)

    try:
        print(f"[INFO] Sending email to: {email}")
        print(f"[INFO] PDF size: {len(pdf_buffer.getvalue()) / 1024:.2f} KB")

        pdf_buffer.seek(0)  # Make sure buffer position is at start

        msg = Message(
            subject='At-Risk Students Report',
            recipients=[email],
            body=f'Report generated on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
        )
        msg.attach(
            filename=f"at_risk_students_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            content_type="application/pdf",
            data=pdf_buffer.getvalue()
        )
        mail.send(msg)

        print("[INFO] Email sent successfully")
        return f"✅ Report successfully sent to {email}"
    except Exception as e:
        print(f"[ERROR] Email sending failed: {e}")
        return f"❌ Error sending email: {str(e)}", 500

if __name__ == '__main__':
    app.run(debug=True)
