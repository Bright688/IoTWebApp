from fastapi import FastAPI, APIRouter, Depends, Form, Response, Query
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates  # Updated import
from pydantic import BaseModel
from typing import List, Dict
import uvicorn
import pdfkit
import os
from fastapi import Request  # Add Request import
import matplotlib.pyplot as plt
import numpy as np
import io
import base64
from urllib.parse import quote
from fpdf import FPDF

# Initialize the FastAPI app
app = FastAPI()

# Check if the static directory exists
static_dir = "frontend/static"
if not os.path.exists(static_dir):
    raise RuntimeError(f"Directory '{static_dir}' does not exist")

# Setting up the Jinja2 template engine (use FastAPI's Jinja2Templates instead of manual setup)
templates = Jinja2Templates(directory="frontend/templates")

# Mount static files directory to serve JS, CSS, and assets
app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Render the home page with the educational resources"""
    return templates.TemplateResponse("index.html", {"request": request, "title": "IoT Security Web App"})

# IoT Security Quiz Questions
questions = [
    {"question": "Which of the following is a common IoT security vulnerability?", "options": ["Weak authentication", "Strong encryption", "Frequent updates", "Data isolation"], "answer": "Weak authentication"},
    {"question": "Which organization provides resources on identifying cybersecurity risks of IoT devices?", "options": ["CISA", "OWASP", "CERT", "NCSC"], "answer": "CISA"},
    {"question": "What is a primary concern of IoT botnets?", "options": ["Data storage", "Device hijacking", "Firmware updates", "Encryption"], "answer": "Device hijacking"},
    {"question": "What technique is commonly used to mitigate DoS attacks in IoT networks?", "options": ["Device isolation", "Network segmentation", "Increasing bandwidth", "Disabling encryption"], "answer": "Network segmentation"},
    {"question": "Which cybersecurity course platform offers training on IoT security fundamentals?", "options": ["Udemy", "Cybrary", "ISACA", "SANS"], "answer": "Cybrary"},
    {"question": "Which company offers solutions to secure IoT devices against firmware attacks?", "options": ["Fortinet", "Synopsys", "Palo Alto Networks", "IoT Security Foundation"], "answer": "Fortinet"},
    {"question": "What is one of the key benefits of cloud integration with IoT devices?", "options": ["Real-time analysis", "Increased device lifespan", "Reduced energy consumption", "Cost savings"], "answer": "Real-time analysis"},
    {"question": "Which cloud platform provides a scalable service for IoT device management?", "options": ["AWS IoT Core", "Google Cloud IoT", "Azure IoT Hub", "All of the above"], "answer": "All of the above"},
    {"question": "What is the primary goal of IoT security audits?", "options": ["To identify and fix vulnerabilities", "To increase device power", "To collect performance data", "To track device location"], "answer": "To identify and fix vulnerabilities"},
    {"question": "Which technology enhances IoT security by reducing latency in time-sensitive applications?", "options": ["Cloud computing", "Edge computing", "Blockchain", "VPNs"], "answer": "Edge computing"}
]

# Load a Unicode font
FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed.ttf"  # Adjust this path if needed


# Temporary storage (use database in production)
user_responses = {}

# Serve quiz form
@app.get("/assessment", response_class=HTMLResponse)
async def serve_quiz(request: Request):
    return templates.TemplateResponse("assessment.html", {"request": request, "questions": questions})

@app.post("/submit")
async def submit_quiz(
    request: Request,
    first_name: str = Form(...),  
    last_name: str = Form(...),   
    email: str = Form(...),
    q0: str = Form(""),
    q1: str = Form(""),
    q2: str = Form(""),
    q3: str = Form(""),
    q4: str = Form(""),
    q5: str = Form(""),
    q6: str = Form(""),
    q7: str = Form(""),
    q8: str = Form(""),
    q9: str = Form("")
):
    user_answers = [q0, q1, q2, q3, q4, q5, q6, q7, q8, q9]
    correct_answers = [q["answer"] for q in questions]
    score = sum(1 for i in range(len(questions)) if user_answers[i] == correct_answers[i])
    
    # Calculate percentage
    percentage = (score / 10) * 100
    
     # Store user answers
    user_responses[f"{first_name}_{last_name}"] = user_answers
    
    # Redirect with URL encoding
    return RedirectResponse(
        url=f"/score?score={score}&percentage={percentage:.2f}&first_name={quote(first_name)}&last_name={quote(last_name)}&email={quote(email)}", 
        status_code=303
    )

@app.get("/score", response_class=HTMLResponse)
async def show_score(
    request: Request, 
    score: int = 0, 
    first_name: str = "",  
    last_name: str = "",   
    email: str = ""
):
    # Calculate percentage
    percentage = (score / 10) * 100

    # Generate chart for the score
    fig, ax = plt.subplots(figsize=(8, 4), subplot_kw={'projection': 'polar'})

    # Set the angle limits
    ax.set_thetamin(0)
    ax.set_thetamax(180)

    # Create the color bands
    theta = np.linspace(0, np.pi, 100)
    ax.fill_between(theta[0:30], 0.8, 1, color='red', alpha=0.3)
    ax.fill_between(theta[30:70], 0.8, 1, color='yellow', alpha=0.3)
    ax.fill_between(theta[70:], 0.8, 1, color='green', alpha=0.3)

    # Add the needle
    needle_angle = np.pi * percentage / 100
    ax.plot([0, needle_angle], [0, 0.9], color='black', linewidth=2)

    # Add the score in the center
    ax.text(np.pi/2, 0.2, f'{int(percentage)}', ha='center', va='center', fontsize=20)

    # Customize the chart
    ax.set_rticks([])  
    tick_angles = np.linspace(0, np.pi, 6)
    ax.set_xticks(tick_angles)
    ax.set_xticklabels(['0', '20', '40', '60', '80', '100'])
    ax.set_title('', pad=20)

    # Save the chart to a buffer
    img_buf = io.BytesIO()
    plt.savefig(img_buf, format='png', bbox_inches='tight', transparent=True)
    img_buf.seek(0)
    img_base64 = base64.b64encode(img_buf.read()).decode('utf-8')
    plt.close()

    # Provide report URL with user info
    report_url = f"/download_report?first_name={quote(first_name)}&last_name={quote(last_name)}&score={score}&percentage={percentage:.2f}"

    return templates.TemplateResponse(
        "score.html",
        {
            "request": request,
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "percentage": percentage,
            "chart": img_base64,
            "report_url": report_url
        }
    )

# Function to find the font file dynamically
def find_font_file(font_name="DejaVuSans.ttf"):
    for root, _, files in os.walk(os.getcwd()):
        if font_name in files:
            return os.path.join(root, font_name)
    raise FileNotFoundError(f"Font file '{font_name}' not found in project directory.")


# Locate fonts dynamically
FONT_PATH = find_font_file("DejaVuSans.ttf")
BOLD_FONT_PATH = find_font_file("DejaVuSans-Bold.ttf")
EMOJI_FONT_PATH = find_font_file("NotoEmoji.ttf")


@app.get("/download_report")
async def download_report(first_name: str, last_name: str, score: int, percentage: float):
    user_key = f"{first_name}_{last_name}"
    user_answers = user_responses.get(user_key, ["No Answer"] * len(questions))

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    

    # Register fonts dynamically
    pdf.add_font("DejaVu", "", FONT_PATH, uni=True)
    pdf.add_font("DejaVu", "B", BOLD_FONT_PATH, uni=True)
    pdf.add_font("NotoEmoji", "", EMOJI_FONT_PATH, uni=True)
    
    # Set title
    pdf.set_font("DejaVu", "B", 16)
    pdf.cell(190, 10, "IoT Security Quiz Report", ln=True, align="C")

    # User Info
    pdf.set_font("DejaVu", "B", 12)
    pdf.ln(10)
    pdf.cell(190, 10, f"Name: {first_name} {last_name}", ln=True)
    pdf.cell(190, 10, f"Percentage: {percentage:.1f}%", ln=True)

    # Generate the score chart
    fig, ax = plt.subplots(figsize=(8, 4), subplot_kw={'projection': 'polar'})

    # Set angle limits
    ax.set_thetamin(0)
    ax.set_thetamax(180)

    # Color bands for performance
    theta = np.linspace(0, np.pi, 100)
    ax.fill_between(theta[:30], 0.8, 1, color='red', alpha=0.3)  # 0-30%
    ax.fill_between(theta[30:70], 0.8, 1, color='yellow', alpha=0.3)  # 30-70%
    ax.fill_between(theta[70:], 0.8, 1, color='green', alpha=0.3)  # 70-100%

    # Needle indicating performance
    needle_angle = np.pi * percentage / 100
    ax.plot([0, needle_angle], [0, 0.9], color='black', linewidth=2)

    # Add score in center
    ax.text(np.pi/2, 0.2, f'{int(percentage)}%', ha='center', va='center', fontsize=20)

    # Customize chart appearance
    ax.set_rticks([])
    ax.set_xticks(np.linspace(0, np.pi, 6))
    ax.set_xticklabels(['0', '20', '40', '60', '80', '100'])
    ax.set_title('', pad=20)

    # Save chart as an image file
    chart_path = f"/tmp/{first_name}_{last_name}_chart.png"
    plt.savefig(chart_path, format='png', bbox_inches='tight', transparent=True)
    plt.close()

    # Add chart to PDF
    pdf.ln(10)
    pdf.image(chart_path, x=50, w=100)


    # Quiz Questions & Answers
    pdf.ln(10)
    pdf.set_font("DejaVu", "B", 14)
    pdf.cell(190, 10, "Quiz Questions & Answers", ln=True)

    pdf.set_font("DejaVu", "", 12)
    options_labels = ['A', 'B', 'C', 'D']

    for index, q in enumerate(questions, start=1):
        pdf.ln(5)
        pdf.multi_cell(190, 7, f"{index}. {q['question']}", ln=True)

        # Display options properly
        for i, option in enumerate(q["options"]):
            pdf.cell(10, 6, f"{options_labels[i]}) ", ln=False)
            pdf.cell(180, 6, option, ln=True)

        # Display User's Selected Answer & Status with Colored Arrows
        user_choice = user_answers[index - 1] if index - 1 < len(user_answers) else "No Answer"

        pdf.set_font("DejaVu", "B", 12)
        # Display User's Selected Answer & Status with Colored Arrows and Emojis
        if user_choice == q['answer']:
            pdf.set_text_color(0, 128, 0)  # Green for correct
            
            # Write text before emoji with DejaVu Bold
            pdf.set_font("DejaVu", "B", 12)
            pdf.cell(190, 7, f"   ➜ Your Answer: {user_choice} ", ln=0)
            
            # Write emoji using NotoEmoji
            pdf.set_font("NotoEmoji", "", 12)
            pdf.cell(10, 7, "✅", ln=0)
            
            # Write the remainder of the message using DejaVu Bold again
            pdf.set_font("DejaVu", "B", 12)
            pdf.cell(0, 7, " (Correct)", ln=1)
        else:
            pdf.set_text_color(255, 0, 0)  # Red for incorrect
            
            # Write text before emoji with DejaVu Bold
            pdf.set_font("DejaVu", "B", 12)
            pdf.cell(190, 7, f"   ➜ Your Answer: {user_choice} ", ln=0)
            
            # Write emoji using NotoEmoji
            pdf.set_font("NotoEmoji", "", 12)
            pdf.cell(10, 7, "❌", ln=0)
            
            # Write the remainder of the message using DejaVu Bold again
            pdf.set_font("DejaVu", "B", 12)
            pdf.cell(0, 7, " (Incorrect)", ln=1)
            
        pdf.set_text_color(0, 0, 0)  # Reset color to black
        pdf.set_font("DejaVu", "", 12)

    
    # Save PDF to a buffer
    pdf_output = io.BytesIO()
    pdf.output(pdf_output)
    pdf_output.seek(0)

    # Clean up the temp image file
    if os.path.exists(chart_path):
        os.remove(chart_path)

    return Response(pdf_output.read(), media_type="application/pdf", headers={
        "Content-Disposition": f"attachment; filename={first_name}_{last_name}_quiz_report.pdf"
    })

'''@app.post("/generate-report", response_class=JSONResponse)
async def generate_report(report_request: ReportRequest):
    """Generate a report based on the user's answers"""
    score, feedback = assess_security(report_request.answers)
    report = {
        "score": score,
        "feedback": feedback,
        "user_feedback": report_request.user_feedback
    }
    # Store report in database or cloud storage (e.g., AWS S3, Google Cloud Storage)
    # Simulating report storage in a file
    report_file_path = f"reports/{report['score']}_report.json"
    with open(report_file_path, 'w') as f:
        f.write(str(report))

    return JSONResponse(content={"message": "Report generated successfully", "file_path": report_file_path})


# API to serve security-related tips
@app.get("/tips", response_class=JSONResponse)
async def get_security_tips():
    """Provides security tips for IoT devices"""
    tips = [
        "Always use strong passwords and change them regularly.",
        "Ensure firmware and software are updated to patch vulnerabilities.",
        "Encrypt sensitive data both in transit and at rest.",
        "Use secure protocols like HTTPS, CoAP, and MQTT for communication.",
        "Monitor network activity to detect abnormal behaviors."
    ]
    return JSONResponse(content={"security_tips": tips})


# Helper function to store reports (e.g., in a cloud service or database)
def store_report(report: Dict):
    """Simulate report storage (to be replaced with actual cloud/db storage logic)"""
    report_dir = "reports"
    if not os.path.exists(report_dir):
        os.mkdir(report_dir)

    report_file_path = os.path.join(report_dir, f"report_{report['score']}.json")
    with open(report_file_path, 'w') as file:
        file.write(str(report))
    print(f"Report saved to {report_file_path}")

'''

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)