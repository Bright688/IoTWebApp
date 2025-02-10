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
import sqlite3

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

# Initialize SQLite Database
# ----------------------------------------------------------------------
# The database file will be named "reports.db" and stored in the current directory.
DB_PATH = "reports.db"
conn = sqlite3.connect(DB_PATH, check_same_thread=False)  # Disable thread check for simplicity
cursor = conn.cursor()

# Create a table to store reports if it doesn't exist.
cursor.execute('''
    CREATE TABLE IF NOT EXISTS reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE,
        pdf_data BLOB,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')
conn.commit()

# Function to find a font file dynamically (searches the current working directory)
def find_font_file(font_name="DejaVuSans.ttf"):
    for root, _, files in os.walk(os.getcwd()):
        if font_name in files:
            return os.path.join(root, font_name)
    raise FileNotFoundError(f"Font file '{font_name}' not found in project directory.")

# Locate fonts dynamically
FONT_PATH = find_font_file("DejaVuSans.ttf")
BOLD_FONT_PATH = find_font_file("DejaVuSans-Bold.ttf")
EMOJI_FONT_PATH = find_font_file("NotoEmoji.ttf")

@app.get("/score", response_class=HTMLResponse)
async def show_score(
    request: Request, 
    score: int = 0, 
    first_name: str = "",  
    last_name: str = "",   
    email: str = ""
):
    # Calculate percentage (assuming total score is 10)
    percentage = (score / 10) * 100

    # -------------------------------
    # 1. Generate a chart for display (as base64)
    # -------------------------------
    fig, ax = plt.subplots(figsize=(8, 4), subplot_kw={'projection': 'polar'})
    ax.set_thetamin(0)
    ax.set_thetamax(180)
    theta = np.linspace(0, np.pi, 100)
    ax.fill_between(theta[0:30], 0.8, 1, color='red', alpha=0.3)
    ax.fill_between(theta[30:70], 0.8, 1, color='yellow', alpha=0.3)
    ax.fill_between(theta[70:], 0.8, 1, color='green', alpha=0.3)
    needle_angle = np.pi * percentage / 100
    ax.plot([0, needle_angle], [0, 0.9], color='black', linewidth=2)
    ax.text(np.pi/2, 0.2, f'{int(percentage)}', ha='center', va='center', fontsize=20)
    ax.set_rticks([])
    tick_angles = np.linspace(0, np.pi, 6)
    ax.set_xticks(tick_angles)
    ax.set_xticklabels(['0', '20', '40', '60', '80', '100'])
    ax.set_title('', pad=20)
    img_buf = io.BytesIO()
    plt.savefig(img_buf, format='png', bbox_inches='tight', transparent=True)
    img_buf.seek(0)
    img_base64 = base64.b64encode(img_buf.read()).decode('utf-8')
    plt.close()

    # -------------------------------
    # 2. Generate the PDF Report
    # -------------------------------
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Register fonts for Unicode support
    pdf.add_font("DejaVu", "", FONT_PATH, uni=True)
    pdf.add_font("DejaVu", "B", BOLD_FONT_PATH, uni=True)
    pdf.add_font("NotoEmoji", "", EMOJI_FONT_PATH, uni=True)

    # Add report title and user info
    pdf.set_font("DejaVu", "B", 16)
    pdf.cell(190, 10, "IoT Security Quiz Report", ln=True, align="C")
    pdf.set_font("DejaVu", "B", 12)
    pdf.ln(10)
    pdf.cell(190, 10, f"Name: {first_name} {last_name}", ln=True)
    pdf.cell(190, 10, f"Email: {email}", ln=True)
    pdf.cell(190, 10, f"Percentage: {percentage:.1f}%", ln=True)

    # Generate a separate chart for the PDF (if needed)
    fig_pdf, ax_pdf = plt.subplots(figsize=(8, 4), subplot_kw={'projection': 'polar'})
    ax_pdf.set_thetamin(0)
    ax_pdf.set_thetamax(180)
    theta_pdf = np.linspace(0, np.pi, 100)
    ax_pdf.fill_between(theta_pdf[:30], 0.8, 1, color='red', alpha=0.3)
    ax_pdf.fill_between(theta_pdf[30:70], 0.8, 1, color='yellow', alpha=0.3)
    ax_pdf.fill_between(theta_pdf[70:], 0.8, 1, color='green', alpha=0.3)
    needle_angle_pdf = np.pi * percentage / 100
    ax_pdf.plot([0, needle_angle_pdf], [0, 0.9], color='black', linewidth=2)
    ax_pdf.text(np.pi/2, 0.2, f'{int(percentage)}%', ha='center', va='center', fontsize=20)
    ax_pdf.set_rticks([])
    ax_pdf.set_xticks(np.linspace(0, np.pi, 6))
    ax_pdf.set_xticklabels(['0', '20', '40', '60', '80', '100'])
    ax_pdf.set_title('', pad=20)
    chart_path_pdf = f"/tmp/{first_name}_{last_name}_chart_pdf.png"
    plt.savefig(chart_path_pdf, format='png', bbox_inches='tight', transparent=True)
    plt.close(fig_pdf)
    pdf.ln(10)
    pdf.image(chart_path_pdf, x=50, w=100)
    if os.path.exists(chart_path_pdf):
        os.remove(chart_path_pdf)

    #Add quiz questions/answers here if needed
    user_key = f"{first_name}_{last_name}"
    user_answers = user_responses.get(user_key, ["No Answer"] * len(questions))
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

    # -------------------------------
    # 3. Save the PDF to a BytesIO buffer and retrieve its bytes
    # -------------------------------
    pdf_output = io.BytesIO()
    pdf.output(pdf_output)
    pdf_output.seek(0)
    pdf_bytes = pdf_output.getvalue()  # Now pdf_bytes is defined

    # -------------------------------
    # 4. Save the PDF Report to SQLite (using the email as a unique key)
    # -------------------------------
    cursor.execute(
        "INSERT OR REPLACE INTO reports (email, pdf_data) VALUES (?, ?)",
        (email, pdf_bytes)
    )
    conn.commit()

    # Create a URL for retrieving the report via the /get_report endpoint.
    # Provide report URL with user info
    report_url = f"/download_report?first_name={quote(first_name)}&last_name={quote(last_name)}&email={quote(email)}&score={score}&percentage={percentage:.2f}"

    # -------------------------------
    # 5. Render the Score Page with the Report Link
    # -------------------------------
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

@app.get("/download_report")
async def download_report(first_name: str, last_name: str, email: str, score: int, percentage: float):
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
    pdf.cell(190, 10, f"Email: {email}", ln=True)
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

@app.get("/report", response_class=HTMLResponse)
async def report(request: Request):
    return templates.TemplateResponse("report.html", {"request": request})

@app.get("/get_report")
async def get_report(email: str):
    cursor.execute("SELECT pdf_data FROM reports WHERE email = ?", (email,))
    row = cursor.fetchone()
    if row is None:
        return {"error": "Report not found for the given email."}
    pdf_data = row[0]
    return Response(
        pdf_data,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={email}_quiz_report.pdf"}
    )

# Dummy Vulnerability Analysis Function
# ----------------------------------------------------------------------
def perform_vulnerability_analysis():
    vulnerabilities = []
    # Dummy device configuration for demonstration purposes:
    device_config = {
        "device_id": "iot1234",
        "encryption": "none",           # "none" means no encryption
        "firmware_version": "1.0.0",      # outdated firmware
        "bandwidth": "low",             # low bandwidth configuration
        "default_password": True,       # device still uses the default password
    }
    if device_config["encryption"] == "none":
        vulnerabilities.append("No encryption detected. Data in transit is exposed.")
    if device_config["default_password"]:
        vulnerabilities.append("Device is using a default password. Change it immediately.")
    if device_config["firmware_version"] < "1.2.0":  # simple version comparison
        vulnerabilities.append("Firmware is outdated and may have known vulnerabilities.")
    if device_config["bandwidth"] == "low":
        vulnerabilities.append("Low bandwidth settings may delay security updates and patching.")
    return vulnerabilities

# ----------------------------------------------------------------------
# Realistic Vulnerability Analysis Function
# ----------------------------------------------------------------------
def perform_vulnerability_analysis():
    """
    Performs vulnerability analysis on an IoT device configuration and returns
    a dictionary with detailed information for each vulnerability.
    """
    vulnerabilities = {
        "No Encryption": {
            "description": "Data in transit is not encrypted, leaving it vulnerable to interception.",
            "analysis": (
                "Without encryption, attackers can easily intercept and tamper with the data exchanged "
                "between the device and the network. This can lead to data breaches and unauthorized access."
            ),
            "best_practices": (
                "• Implement strong encryption protocols such as AES-256 or TLS.\n"
                "• Ensure all communications use end-to-end encryption.\n"
                "• Regularly audit encryption configurations and update them as necessary."
            )
        },
        "Default Credentials": {
            "description": "The device is using default credentials.",
            "analysis": (
                "Default usernames and passwords are widely known and can be easily exploited by attackers, "
                "leading to unauthorized access to the device."
            ),
            "best_practices": (
                "• Change default credentials immediately upon deployment.\n"
                "• Enforce strong password policies and consider using multi-factor authentication (MFA).\n"
                "• Regularly review and update credentials."
            )
        },
        "Outdated Firmware": {
            "description": "Firmware is outdated and may contain known security vulnerabilities.",
            "analysis": (
                "Outdated firmware often lacks critical security patches and updates, leaving the device susceptible "
                "to known exploits and attacks."
            ),
            "best_practices": (
                "• Regularly update the firmware to the latest version provided by the manufacturer.\n"
                "• Enable automatic updates if available, or schedule periodic manual updates.\n"
                "• Monitor vendor security advisories for critical patches."
            )
        },
        "Weak Authentication": {
            "description": "The device uses weak or basic authentication methods.",
            "analysis": (
                "Weak authentication mechanisms can be easily bypassed by attackers using brute-force or credential stuffing "
                "attacks, compromising device security."
            ),
            "best_practices": (
                "• Implement robust authentication mechanisms such as token-based or certificate-based authentication.\n"
                "• Utilize multi-factor authentication (MFA) to add an extra layer of security.\n"
                "• Enforce strict password policies and account lockout rules."
            )
        },
        "Insecure Open Ports": {
            "description": "The device has unnecessary or insecure open ports.",
            "analysis": (
                "Open ports, especially those running insecure protocols (like FTP or Telnet), increase the device's attack surface "
                "and can be exploited by attackers to gain access."
            ),
            "best_practices": (
                "• Close all unnecessary ports and disable unused services.\n"
                "• Secure required ports using firewalls, VPNs, or intrusion detection systems.\n"
                "• Regularly scan the network to identify and remediate insecure open ports."
            )
        }
    }
    return vulnerabilities

# ----------------------------------------------------------------------
# Endpoint: Security Guidance (with Vulnerability Analysis)
# ----------------------------------------------------------------------
@app.get("/security_guidance", response_class=HTMLResponse)
async def security_guidance(request: Request):
    # Guidance data for best practices and tips
    guidance = {
        "overview": "Below are best practices and tips to help secure low bandwidth IoT devices:",
        "best_practices": [
            "Use strong encryption protocols optimized for low-bandwidth environments.",
            "Regularly update firmware and software to patch vulnerabilities.",
            "Disable unused services and close unnecessary ports.",
            "Implement network segmentation to isolate IoT devices.",
            "Enforce secure authentication and change default credentials."
        ],
        "tips": [
            "Utilize lightweight encryption algorithms to reduce overhead.",
            "Compress data before transmission to save bandwidth.",
            "Monitor network traffic and set up alerts for anomalies."
        ]
    }
    
    # Run vulnerability analysis (realistic function)
    vulnerabilities = perform_vulnerability_analysis()
    
    # Pass all data to the template
    return templates.TemplateResponse("security_guidance.html", {
        "request": request,
        "guidance": guidance,
        "vulnerabilities": vulnerabilities
    })

 #Comparative Analysis of IoT Protocols
# ----------------------------------------------------------------------
def compare_iot_protocols():
    """
    Returns a dictionary comparing common IoT protocols.
    Each protocol is compared by its description, key features, advantages, disadvantages, and use cases.
    """
    protocols = {
        "CoAP": {
            "description": (
                "The Constrained Application Protocol (CoAP) is designed specifically for resource-constrained "
                "devices and low-power, lossy networks. It is lightweight, UDP-based, and supports multicast."
            ),
            "features": ["Lightweight", "UDP-based", "Multicast support", "Low overhead"],
            "advantages": [
                "Efficient for low bandwidth and constrained networks",
                "Designed for simple IoT devices",
                "Easy integration with RESTful interfaces"
            ],
            "disadvantages": [
                "UDP does not guarantee delivery; reliability must be managed at the application level",
                "Less mature ecosystem compared to MQTT or HTTP",
                "Security relies on DTLS, which adds complexity"
            ],
            "use_cases": ["Smart lighting", "Environmental monitoring", "Industrial automation"]
        },
        "MQTT": {
            "description": (
                "Message Queuing Telemetry Transport (MQTT) is a lightweight messaging protocol based on a publish/subscribe model. "
                "It is designed for low-bandwidth, high-latency, or unreliable networks."
            ),
            "features": ["TCP-based", "Publish/Subscribe", "Multiple QoS levels", "Small code footprint"],
            "advantages": [
                "Reliable messaging with QoS guarantees",
                "Efficient for real-time, asynchronous communication",
                "Widely adopted in IoT ecosystems"
            ],
            "disadvantages": [
                "Requires a broker, adding an extra component",
                "TCP overhead can be higher than UDP-based protocols",
                "Not as efficient for multicast scenarios"
            ],
            "use_cases": ["Remote monitoring", "Home automation", "Connected vehicles"]
        },
        "HTTP": {
            "description": (
                "Hypertext Transfer Protocol (HTTP) is the foundation of data communication on the web and is used "
                "by many IoT devices despite not being optimized for constrained environments."
            ),
            "features": ["TCP-based", "Stateless", "Well-understood", "Secure when used with TLS"],
            "advantages": [
                "Mature protocol with extensive tooling and support",
                "Robust security features when used with HTTPS",
                "Broad interoperability with web services"
            ],
            "disadvantages": [
                "Higher overhead compared to protocols designed for IoT",
                "Statelessness can lead to inefficient communication in some scenarios",
                "Not optimized for extremely resource-constrained devices"
            ],
            "use_cases": ["Web services", "Standard API communications", "Applications requiring robust security"]
        }
    }
    return protocols

# ----------------------------------------------------------------------
# Endpoint: Comparative Analysis of IoT Protocols
# ----------------------------------------------------------------------
@app.get("/iot_protocol_comparison", response_class=HTMLResponse)
async def iot_protocol_comparison(request: Request):
    protocols = compare_iot_protocols()
    return templates.TemplateResponse("iot_protocol_comparison.html", {
        "request": request,
        "protocols": protocols
    })



if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)