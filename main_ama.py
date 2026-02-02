import base64
import logging
import os
import uuid
from datetime import datetime
from io import BytesIO

try:
    import humanize
except Exception:  # pragma: no cover - optional
    humanize = None

try:
    import requests
except Exception:  # pragma: no cover - optional
    requests = None
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Form, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# Use centralized DB helpers and models
from core.database import get_db, malaysia_tz
from models.questions import Question

try:
    from PIL import Image
except Exception:  # pragma: no cover - optional
    Image = None
from sqlalchemy.orm import Session

from schemas.questions import QuestionCreate

load_dotenv()

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development, adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
# Expose current year to all templates (used by footer)
try:
    templates.env.globals["year"] = datetime.now().year
except Exception:
    # fallback if templates.env is not available at import time
    pass

security = HTTPBasic()

# Get credentials from env file
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
DATABASE_URL = os.getenv("DATABASE_URL")


# Get credentials for Telegram Bot

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


def get_current_user(credentials: HTTPBasicCredentials = Depends(security)):
    if (
        credentials.username == ADMIN_USERNAME
        and credentials.password == ADMIN_PASSWORD
    ):
        return credentials.username
    raise HTTPException(status_code=401, detail="Unauthorized")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/ask", response_class=HTMLResponse)
async def ask(request: Request):
    return templates.TemplateResponse("ask.html", {"request": request})


@app.post("/api/questions")
async def create_question(question: QuestionCreate, db: Session = Depends(get_db)):
    try:
        # prevent exact duplicate submissions (case-insensitive, stripped)
        normalized = question.content.strip().lower()
        existing = db.query(Question).filter(Question.content != None).all()
        for q in existing:
            if q.content and q.content.strip().lower() == normalized:
                return {"success": False, "message": "Duplicate question"}

        question_id = str(uuid.uuid4())
        db_question = Question(id=question_id, content=question.content)
        db.add(db_question)
        db.commit()
        db.refresh(db_question)

        # Send telegram request
        send_telegram_notification(
            f"📩 New question received:\n\n📝 <b>Question:</b> {question.content}"
        )

        return {
            "success": True,
            "message": "Question submitted successfully",
            "questionId": question_id,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


def send_telegram_notification(message: str):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logging.warning("Telegram credentials not set.")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}

    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to send Telegram message: {e}")


@app.get("/admin", response_class=HTMLResponse)
async def admin(request: Request, user: str = Depends(get_current_user)):
    return templates.TemplateResponse("admin.html", {"request": request})


@app.get("/questions", response_class=HTMLResponse)
async def view_questions(
    request: Request,
    user: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    questions = (
        db.query(Question).order_by(Question.timestamp.desc()).all()
    )  # This will sort the answer from latest to earliest.
    return templates.TemplateResponse(
        "questions.html", {"request": request, "questions": questions}
    )


@app.get("/questions/{question_id}", response_class=HTMLResponse)
async def share_question(
    request: Request,
    question_id: str,
    user: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    question = db.query(Question).filter(Question.id == question_id).first()
    if question:
        return templates.TemplateResponse(
            "share.html", {"request": request, "question": question}
        )
    return RedirectResponse(url="/questions")


@app.post("/save_image")
async def save_image(request: Request):
    data = await request.json()
    img_data = data.get("image")
    if not img_data:
        raise HTTPException(status_code=400, detail="No image data found")

    img_data = base64.b64decode(img_data.split(",")[1])
    img = Image.open(BytesIO(img_data))
    img.save("static/question.png")

    return {"url": "/static/question.png"}


@app.post("/answer_question/{question_id}", response_class=HTMLResponse)
async def answer_question(
    request: Request,
    question_id: str,
    answer: str = Form(...),
    db: Session = Depends(get_db),
    user: str = Depends(get_current_user),
):
    question = db.query(Question).filter(Question.id == question_id).first()
    if question:
        question.answer = answer  # Save the answer to the database
        db.commit()
    return RedirectResponse(url="/questions", status_code=303)


@app.get("/answered_questions", response_class=HTMLResponse)
async def answered_questions(
    request: Request, page: int = 1, page_size: int = 10, db: Session = Depends(get_db)
):
    all_questions = db.query(Question).filter(Question.answer != None).all()

    # Sort with timezone-aware datetimes
    all_questions.sort(
        key=lambda q: malaysia_tz.localize(
            datetime.strptime(q.timestamp, "%d-%m-%Y %H:%M:%S")
        ),
        reverse=True,
    )

    # Add human-readable timestamp
    now = datetime.now(malaysia_tz)
    for q in all_questions:
        dt = malaysia_tz.localize(datetime.strptime(q.timestamp, "%d-%m-%Y %H:%M:%S"))
        q.human_timestamp = humanize.naturaltime(now - dt)

    # Paginate
    total = len(all_questions)
    start = (page - 1) * page_size
    end = start + page_size
    paginated = all_questions[start:end]

    return templates.TemplateResponse(
        "answered_questions.html",
        {
            "request": request,
            "questions": paginated,
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": (total + page_size - 1) // page_size,
        },
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
