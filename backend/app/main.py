from fastapi import FastAPI, APIRouter, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates  # Updated import
from pydantic import BaseModel
from typing import List, Dict
import uvicorn
import os
from fastapi import Request  # Add Request import

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

# Importing submodules
'''from modules.questions.questions import get_questions
from modules.assessment.assessment import assess_security
from modules.analytics.analytics import get_iot_analytics'''


class ReportRequest(BaseModel):
    answers: List[str]
    user_feedback: str


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Render the home page with the educational resources"""
    return templates.TemplateResponse("index.html", {"request": request, "title": "IoT Security Web App"})


@app.get("/assessment", response_class=HTMLResponse)
async def assessment_page(request: Request):
    """Render the assessment page with questions"""
    questions = get_questions()
    return templates.TemplateResponse("assessment.html", {"request": request, "questions": questions, "title": "Security Assessment"})


@app.post("/submit-assessment", response_class=JSONResponse)
async def submit_assessment(report_request: ReportRequest):
    """Process and evaluate the assessment answers"""
    score, feedback = assess_security(report_request.answers)
    report = {
        "score": score,
        "feedback": feedback,
        "user_feedback": report_request.user_feedback
    }

    # Store the report in cloud or database
    store_report(report)

    return JSONResponse(content=report)


'''@app.get("/analytics", response_class=HTMLResponse)
async def analytics_page(request: Request):
    """Render the analytics page"""
    data = get_iot_analytics()
    return templates.TemplateResponse("analytics.html", {"request": request, "data": data, "title": "IoT Analytics"})


@app.post("/security-assessment")
async def security_assessment(answers: List[str]):
    result = assess_security(answers)
    return JSONResponse(content=result)


@app.get("/real-time-assessment")
async def real_time_assessment():
    """Simulate real-time assessment"""
    result = perform_real_time_assessment()  # Assuming this function is defined
    return JSONResponse(content=result)


@app.post("/watson-security-insights")
async def watson_security_insights(image_path: str):
    insights = get_security_insights_from_watson(image_path)  # Assuming this function is defined
    return JSONResponse(content=insights)


@app.post("/generate-report", response_class=JSONResponse)
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
    print(f"Report saved to {report_file_path}")'''


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)