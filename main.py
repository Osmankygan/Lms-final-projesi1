from fastapi import FastAPI, Depends, HTTPException, status, Header
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional

import models
from database import engine, get_db, init_db, hash_password, verify_password
import ai_service

app = FastAPI(
    title="AI-Supported LMS API",
    description="Backend API for User Management, Course & Content Management, and AI Services.",
    version="1.0.0"
)

# Enable CORS for frontend flexibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database on startup
@app.on_event("startup")
def startup_event():
    init_db()

# ==========================================
# Authentication & User Management
# ==========================================

@app.post("/register", response_model=models.UserResponse, status_code=status.HTTP_201_CREATED)
def register(user: models.UserCreate, db: Session = Depends(get_db)):
    # Check if username exists
    existing_user = db.query(models.User).filter(models.User.username == user.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bu kullanıcı adı zaten alınmış."
        )
    
    hashed_pwd = hash_password(user.password)
    db_user = models.User(
        username=user.username,
        password_hash=hashed_pwd,
        role=user.role
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.post("/login", response_model=models.UserResponse)
def login(credentials: models.UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.username == credentials.username).first()
    if not db_user or not verify_password(credentials.password, db_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Geçersiz kullanıcı adı veya şifre."
        )
    return db_user

@app.get("/users/{user_id}", response_model=models.UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı.")
    return db_user


# ==========================================
# Course Management
# ==========================================

@app.get("/courses", response_model=List[models.CourseResponse])
def get_courses(student_id: Optional[int] = None, teacher_id: Optional[int] = None, db: Session = Depends(get_db)):
    query = db.query(models.Course)
    
    if teacher_id:
        query = query.filter(models.Course.teacher_id == teacher_id)
    elif student_id:
        # Filter courses where the student is enrolled
        query = query.join(models.Enrollment).filter(models.Enrollment.student_id == student_id)
        
    return query.all()

@app.get("/courses/all", response_model=List[models.CourseResponse])
def get_all_courses(db: Session = Depends(get_db)):
    return db.query(models.Course).all()

@app.post("/courses", response_model=models.CourseResponse, status_code=status.HTTP_201_CREATED)
def create_course(course: models.CourseCreate, teacher_id: int, db: Session = Depends(get_db)):
    # Verify teacher exists and has proper role
    db_user = db.query(models.User).filter(models.User.id == teacher_id).first()
    if not db_user or db_user.role != "teacher":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sadece eğitmenler kurs oluşturabilir."
        )
    
    db_course = models.Course(
        title=course.title,
        description=course.description,
        teacher_id=teacher_id
    )
    db.add(db_course)
    db.commit()
    db.refresh(db_course)
    return db_course

@app.post("/courses/{course_id}/enroll", response_model=models.EnrollmentResponse, status_code=status.HTTP_201_CREATED)
def enroll_course(course_id: int, student_id: int, db: Session = Depends(get_db)):
    # Check if course exists
    db_course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not db_course:
        raise HTTPException(status_code=404, detail="Kurs bulunamadı.")
    
    # Verify student exists and has student role
    db_user = db.query(models.User).filter(models.User.id == student_id).first()
    if not db_user or db_user.role != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sadece öğrenciler kursa kaydolabilir."
        )
    
    # Check if already enrolled
    existing_enrollment = db.query(models.Enrollment).filter(
        models.Enrollment.student_id == student_id,
        models.Enrollment.course_id == course_id
    ).first()
    if existing_enrollment:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bu kursa zaten kayıtlısınız."
        )
        
    db_enrollment = models.Enrollment(
        student_id=student_id,
        course_id=course_id
    )
    db.add(db_enrollment)
    db.commit()
    db.refresh(db_enrollment)
    return db_enrollment


# ==========================================
# Course Materials
# ==========================================

@app.get("/courses/{course_id}/materials", response_model=List[models.MaterialResponse])
def get_course_materials(course_id: int, db: Session = Depends(get_db)):
    # Verify course exists
    db_course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not db_course:
        raise HTTPException(status_code=404, detail="Kurs bulunamadı.")
        
    return db.query(models.Material).filter(models.Material.course_id == course_id).all()

@app.post("/courses/{course_id}/materials", response_model=models.MaterialResponse, status_code=status.HTTP_201_CREATED)
def create_course_material(course_id: int, material: models.MaterialCreate, teacher_id: int, db: Session = Depends(get_db)):
    # Verify course exists
    db_course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not db_course:
        raise HTTPException(status_code=404, detail="Kurs bulunamadı.")
        
    # Verify teacher is the owner of the course
    if db_course.teacher_id != teacher_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sadece bu kursun eğitmeni materyal ekleyebilir."
        )
        
    db_material = models.Material(
        course_id=course_id,
        title=material.title,
        content=material.content
    )
    db.add(db_material)
    db.commit()
    db.refresh(db_material)
    return db_material


# ==========================================
# Student Submissions & AI Services
# ==========================================

@app.get("/courses/{course_id}/submissions", response_model=List[models.SubmissionResponse])
def get_submissions(course_id: int, student_id: Optional[int] = None, db: Session = Depends(get_db)):
    query = db.query(models.Submission).filter(models.Submission.course_id == course_id)
    if student_id:
        query = query.filter(models.Submission.student_id == student_id)
    return query.all()

@app.post("/courses/{course_id}/submissions", response_model=models.SubmissionResponse, status_code=status.HTTP_201_CREATED)
def create_submission(
    course_id: int, 
    submission: models.SubmissionCreate, 
    student_id: int, 
    provider: Optional[str] = "gemini",
    api_key: Optional[str] = None,
    db: Session = Depends(get_db)
):
    # Verify course exists
    db_course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not db_course:
        raise HTTPException(status_code=404, detail="Kurs bulunamadı.")
        
    # Verify student is enrolled in the course
    enrollment = db.query(models.Enrollment).filter(
        models.Enrollment.student_id == student_id,
        models.Enrollment.course_id == course_id
    ).first()
    if not enrollment:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu kursa kayıtlı olmadığınız için ödev gönderemezsiniz."
        )
        
    # Automatically analyze the submission using the AI service
    analysis = ai_service.analyze_submission(
        text_content=submission.text_content,
        course_title=db_course.title,
        provider=provider,
        api_key=api_key
    )
    
    db_submission = models.Submission(
        student_id=student_id,
        course_id=course_id,
        text_content=submission.text_content,
        ai_feedback=analysis.get("feedback"),
        grade=analysis.get("grade")
    )
    
    db.add(db_submission)
    db.commit()
    db.refresh(db_submission)
    return db_submission

@app.post("/submissions/{submission_id}/reanalyze", response_model=models.SubmissionResponse)
def reanalyze_submission(
    submission_id: int, 
    request: models.AIAnalyzeRequest, 
    db: Session = Depends(get_db)
):
    # Get submission
    db_submission = db.query(models.Submission).filter(models.Submission.id == submission_id).first()
    if not db_submission:
        raise HTTPException(status_code=404, detail="Ödev gönderisi bulunamadı.")
        
    # Re-run AI analysis
    analysis = ai_service.analyze_submission(
        text_content=request.text_content,
        course_title=request.course_title,
        provider=request.provider,
        api_key=request.api_key
    )
    
    db_submission.text_content = request.text_content
    db_submission.ai_feedback = analysis.get("feedback")
    db_submission.grade = analysis.get("grade")
    
    db.commit()
    db.refresh(db_submission)
    return db_submission


# ==========================================
# Standalone AI Utilities
# ==========================================

@app.post("/ai/summarize", response_model=models.AISummarizeResponse)
def api_summarize_text(request: models.AISummarizeRequest):
    summary = ai_service.summarize_text(
        text=request.content,
        provider=request.provider,
        api_key=request.api_key
    )
    return models.AISummarizeResponse(summary=summary)

@app.post("/ai/analyze", response_model=models.AIAnalyzeResponse)
def api_analyze_submission(request: models.AIAnalyzeRequest):
    analysis = ai_service.analyze_submission(
        text_content=request.text_content,
        course_title=request.course_title,
        provider=request.provider,
        api_key=request.api_key
    )
    return models.AIAnalyzeResponse(
        feedback=analysis.get("feedback"),
        grade=analysis.get("grade")
    )
