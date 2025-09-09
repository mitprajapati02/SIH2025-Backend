from flask import Flask, render_template, jsonify, send_file
from flask_mail import Mail, Message
import pandas as pd
import os
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
import numpy as np
import io

app = Flask(__name__)

# Email Configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'  # Gmail SMTP server
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'your_email@gmail.com'  # Your email
app.config['MAIL_PASSWORD'] = 'your_app_password'     # Your app password
app.config['MAIL_DEFAULT_SENDER'] = 'your_email@gmail.com'

mail = Mail(app)

@app.route('/')
def index():
    marks = pd.read_csv('data/marks.csv')
    atd = pd.read_csv('data/attendance.csv')
    fees = pd.read_csv('data/fees.csv')

    merged_df = marks.merge(atd, on='student_id').merge(fees, on='student_id')

    merged_df['attendance_percent'] = ((merged_df['days_present'] / merged_df['total_days']) * 100).round(2)
    merged_df['marks_percent'] = ((merged_df['Total'] / merged_df['Out_of']) * 100).round(2)

    def marks_risk(data):
        stu_marks = data['Total']
        sub_total = data['Out_of']
        critical = (sub_total * 40) / 100
        mod = (sub_total * 60) / 100

        if stu_marks < critical:
            return 'High'
        elif stu_marks < mod:
            return 'Moderate'
        else:
            return 'Safe'

    merged_df['marks_risk'] = merged_df.apply(marks_risk, axis=1)
    
    # Add risk reasons
    merged_df['risk_reasons'] = ''
    
    for index, row in merged_df.iterrows():
        reasons = []
        
        if row['marks_risk'] in ['High', 'Moderate']:
            reasons.append("Low Marks")
        if row['attendance_percent'] < 75:
            reasons.append("Low Attendance")
        if row['Fees_Status'] != 'Paid':
            reasons.append("Fee Issues")
            
        merged_df.at[index, 'risk_reasons'] = ', '.join(reasons) if reasons else 'None'
    
    merged_df.to_csv('data/merged_data.csv', index=False)
    students = merged_df.to_dict(orient='records')

    return render_template('index.html', students=students)

# API endpoint for React frontend
@app.route('/api/students')
def api_students():
    df = pd.read_csv('data/merged_data.csv')
    # Replace NaN values with 'None'
    df['risk_reasons'] = df['risk_reasons'].fillna('None')
    return jsonify(df.to_dict(orient='records'))

# Direct PDF download of at-risk students
@app.route('/report')
def download_report():
    df = pd.read_csv('data/merged_data.csv')
    
    # Replace NaN values with 'None' and filter at-risk students
    df['risk_reasons'] = df['risk_reasons'].fillna('None')
    at_risk_df = df[df['risk_reasons'] != 'None']
    
    # Check if there are any at-risk students
    if at_risk_df.empty:
        return "No at-risk students found."
    
    # Generate PDF report in memory
    pdf_buffer = generate_pdf_report_in_memory(at_risk_df)
    
    # Return the PDF as download
    return send_file(
        pdf_buffer,
        as_attachment=True,
        download_name=f"at_risk_students_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
        mimetype='application/pdf'
    )

# Send PDF via Email
@app.route('/send-report/<email>')
def send_report_email(email):
    df = pd.read_csv('data/merged_data.csv')
    
    # Replace NaN values with 'None' and filter at-risk students
    df['risk_reasons'] = df['risk_reasons'].fillna('None')
    at_risk_df = df[df['risk_reasons'] != 'None']
    
    # Check if there are any at-risk students
    if at_risk_df.empty:
        return "No at-risk students found."
    
    # Generate PDF report in memory
    pdf_buffer = generate_pdf_report_in_memory(at_risk_df)
    
    try:
        # Create email message
        msg = Message(
            subject='At-Risk Students Report',
            recipients=[email],  # Receiver's email
            body=f'Please find attached the at-risk students report generated on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
        )
        
        # Attach PDF
        msg.attach(
            filename=f"at_risk_students_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            content_type="application/pdf",
            data=pdf_buffer.getvalue()
        )
        
        # Send email
        mail.send(msg)
        return f"Report successfully sent to {email}"
    
    except Exception as e:
        return f"Error sending email: {str(e)}"

# PDF generation function - IN MEMORY
def generate_pdf_report_in_memory(df):
    # Create a buffer (in-memory file)
    buffer = io.BytesIO()
    
    # Create PDF in memory
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    
    # Add a title
    from reportlab.platypus import Paragraph
    from reportlab.lib.styles import getSampleStyleSheet
    
    styles = getSampleStyleSheet()
    title = Paragraph("At-Risk Students Report", styles['Title'])
    elements.append(title)
    elements.append(Paragraph("<br/>", styles['Normal']))  # Add some space
    
    # Add generation date
    date_text = Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal'])
    elements.append(date_text)
    elements.append(Paragraph("<br/>", styles['Normal']))
    
    # Prepare data for PDF table
    report_df = df[['student_id', 'Name', 'marks_percent', 'attendance_percent', 'Fees_Status', 'risk_reasons']]
    
    # Convert DataFrame to list of lists for table
    data = [report_df.columns.tolist()] + report_df.values.tolist()
    
    # Create table
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
    
    # Move buffer pointer to beginning
    buffer.seek(0)
    return buffer

if __name__ == '__main__':
    app.run(debug=True)