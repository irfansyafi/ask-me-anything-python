from fastapi import FastAPI, Request, Form, HTTPException, Depends
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy import create_engine, Column, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import uuid
from dotenv import load_dotenv
import os
from PIL import Image
import base64
from io import BytesIO

load_dotenv()

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

security = HTTPBasic()

# Admin credentials
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Question(Base):
    __tablename__ = "questions"
    id = Column(String, primary_key=True, index=True)
    content = Column(String, index=True)

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(credentials: HTTPBasicCredentials = Depends(security)):
    if credentials.username == ADMIN_USERNAME and credentials.password == ADMIN_PASSWORD:
        return credentials.username
    raise HTTPException(status_code=401, detail="Unauthorized")

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/ask", response_class=HTMLResponse)
async def ask(request: Request):
    return templates.TemplateResponse("ask.html", {"request": request})

@app.post("/ask", response_class=HTMLResponse)
async def submit_question(request: Request, question: str = Form(...), db: SessionLocal = Depends(get_db)):
    question_id = str(uuid.uuid4())
    db_question = Question(id=question_id, content=question)
    db.add(db_question)
    db.commit()
    db.refresh(db_question)
    return templates.TemplateResponse("ask.html", {"request": request, "submitted": True})

@app.get("/admin", response_class=HTMLResponse)
async def admin(request: Request, user: str = Depends(get_current_user)):
    return templates.TemplateResponse("admin.html", {"request": request})

@app.get("/questions", response_class=HTMLResponse)
async def view_questions(request: Request, user: str = Depends(get_current_user), db: SessionLocal = Depends(get_db)):
    questions = db.query(Question).all()
    return templates.TemplateResponse("questions.html", {"request": request, "questions": questions})

@app.get("/questions/{question_id}", response_class=HTMLResponse)
async def share_question(request: Request, question_id: str, user: str = Depends(get_current_user), db: SessionLocal = Depends(get_db)):
    question = db.query(Question).filter(Question.id == question_id).first()
    if question:
        return templates.TemplateResponse("share.html", {"request": request, "question": question})
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
