from fastapi import FastAPI, UploadFile, HTTPException, File, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.security import HTTPBearer
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from pydantic import BaseModel, ValidationError
from typing import List, Optional, Dict, Any
import fitz  # PyMuPDF
import re
import spacy
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
import os
from dotenv import load_dotenv
import logging
from ratelimit import limits, RateLimitException
from functools import wraps
from time import time
import traceback
import uuid
import filetype
from prometheus_client import Counter, Histogram
from prometheus_client import make_asgi_app
from prometheus_fastapi_instrumentator import Instrumentator

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log')
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Resume Skill Extractor API",
    description="API for extracting skills and information from resumes",
    version="1.0.0",
    docs_url=None,  # Disable default docs
    redoc_url=None   # Disable default redoc
)

# Add Prometheus middleware
app.add_route("/metrics", make_asgi_app())

# Initialize Prometheus metrics
download_counter = Counter(
    'resume_downloads',
    'Number of resume downloads',
    ['status_code', 'method', 'path']
)

request_latency = Histogram(
    'request_latency_seconds',
    'Request latency in seconds',
    ['method', 'path', 'status_code']
)

# Add security middleware
app.add_middleware(
    HTTPSRedirectMiddleware,  # Redirect HTTP to HTTPS
    trusted_hosts=[os.getenv("ALLOWED_HOSTS", "localhost")]
)

# Add session middleware
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SECRET_KEY", "your-secret-key"),
    max_age=3600  # 1 hour
)

# Initialize FastAPI app with security
security = HTTPBearer()

# Log server startup
@app.on_event("startup")
async def startup_event():
    logger.info("Server starting up...")
    try:
        # Test MongoDB connection
        client = AsyncIOMotorClient(os.getenv("MONGODB_URI"))
        await client.server_info()
        logger.info("MongoDB connection successful")
    except Exception as e:
        logger.error(f"MongoDB connection failed: {str(e)}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Server shutting down...")

# Configure CORS with security
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(',')
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],  # Only allow specific methods
    allow_headers=["Authorization", "Content-Type"],  # Only allow specific headers
    expose_headers=["X-RateLimit-Limit", "X-RateLimit-Remaining", "X-RateLimit-Reset"]
)

# Add security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response

# Add rate limiting middleware
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    if request.method in ["GET", "POST"]:
        try:
            rate_limit = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
            window = int(os.getenv("RATE_LIMIT_WINDOW", "60"))
            
            @limits(calls=rate_limit, period=window)
            async def limited():
                return await call_next(request)
            
            return await limited()
        except RateLimitException:
            raise HTTPException(
                status_code=429,
                detail="Too many requests. Please try again later."
            )
    return await call_next(request)

# Add request logging middleware with metrics
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time()
    
    try:
        response = await call_next(request)
        process_time = time() - start_time
        
        # Update Prometheus metrics
        download_counter.labels(
            status_code=str(response.status_code),
            method=request.method,
            path=str(request.url.path)
        ).inc()
        
        request_latency.labels(
            method=request.method,
            path=str(request.url.path),
            status_code=str(response.status_code)
        ).observe(process_time)
        
        logger.info(
            f"{request.method} {request.url.path} - {response.status_code} - {process_time:.2f}s"
        )
        return response
    except Exception as e:
        process_time = time() - start_time
        logger.error(
            f"{request.method} {request.url.path} - ERROR - {process_time:.2f}s - {str(e)}"
        )
        raise

# Add GZip middleware for better performance
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Add rate limiting decorator
FIVE_MINUTES = 300

def rate_limited(limit: int):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except RateLimitException:
                raise HTTPException(
                    status_code=429,
                    detail="Too many requests. Please try again later."
                )
        return wrapper
    return decorator

# Error handling middleware
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.error(f"HTTP Exception: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "request": {
                "method": request.method,
                "url": str(request.url),
                "headers": dict(request.headers)
            }
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    error_id = str(uuid.uuid4())
    logger.error(f"Unexpected error ({error_id}): {str(exc)}\n{traceback.format_exc()}")
    
    # Log detailed error information
    error_details = {
        "error_id": error_id,
        "timestamp": datetime.now().isoformat(),
        "request": {
            "method": request.method,
            "url": str(request.url),
            "headers": dict(request.headers),
            "client": request.client.host if request.client else "unknown"
        },
        "exception": {
            "type": type(exc).__name__,
            "message": str(exc),
            "traceback": traceback.format_exc()
        }
    }
    
    # Log to file with detailed information
    with open("error.log", "a") as f:
        f.write(json.dumps(error_details, indent=2) + "\n")
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "An unexpected error occurred. Please try again later.",
            "error_id": error_id,
            "request": {
                "method": request.method,
                "url": str(request.url),
                "headers": dict(request.headers)
            }
        }
    )

# Add startup event handler
@app.on_event("startup")
async def startup_event():
    logger.info("Server starting up...")
    try:
        # Initialize MongoDB connection
        client = AsyncIOMotorClient(os.getenv("MONGODB_URI"))
        await client.server_info()
        logger.info("MongoDB connection successful")
        
        # Initialize NLTK data
        try:
            import nltk
            nltk.download("punkt")
            logger.info("NLTK data initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing NLTK data: {str(e)}")
            raise
        
    except Exception as e:
        logger.error(f"Startup error: {str(e)}")
        raise

# Add shutdown event handler
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Server shutting down...")
    try:
        # Close MongoDB connection
        if "client" in globals():
            client.close()
            logger.info("MongoDB connection closed")
        
    except Exception as e:
        logger.error(f"Shutdown error: {str(e)}")
        raise

# Add request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        
        # Log request details
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "method": request.method,
            "url": str(request.url),
            "status_code": response.status_code,
            "processing_time": process_time,
            "client": request.client.host if request.client else "unknown",
            "user_agent": request.headers.get("user-agent", "unknown")
        }
        
        # Log to file
        with open("access.log", "a") as f:
            f.write(json.dumps(log_data, indent=2) + "\n")
        
        logger.info(f"{request.method} {request.url} - {response.status_code} - {process_time:.2f}s")
        return response
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"{request.method} {request.url} - ERROR - {process_time:.2f}s - {str(e)}")
        raise

# Add static files serving
import os
from pathlib import Path

# Get the build directory from environment variable
BUILD_DIR = os.getenv("CLIENT_BUILD_DIR", Path(__file__).parent.parent.parent / "client" / "build")

# Create build directory if it doesn't exist
if not BUILD_DIR.exists():
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"Created build directory: {BUILD_DIR}")

# Mount static files
try:
    app.mount("/static", StaticFiles(directory=str(BUILD_DIR)), name="static")
    logger.info(f"Static files mounted from: {BUILD_DIR}")
except Exception as e:
    logger.error(f"Error mounting static files: {str(e)}")
    raise

# Custom error handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"Validation Error: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "body": exc.body}
    )

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

# OpenAPI documentation
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=app.title + " - API Documentation",
        swagger_favicon_url="/static/favicon.ico"
    )

# Root endpoint
@app.get("/")
async def root():
    return {"message": "Welcome to Resume Skill Extractor API"}

# Database connection
async def get_db():
    try:
        client = AsyncIOMotorClient(os.getenv("MONGODB_URI"))
        db = client.resume_extractor
        yield db
    finally:
        client.close()

# MongoDB connection
client = AsyncIOMotorClient(os.getenv("MONGODB_URI", "mongodb://localhost:27017"))
db = client.resume_extractor
resumes = db.resumes

# Load NLP model
try:
    # Try to load the model
    nlp = spacy.load("en_core_web_sm")
    logger.info("Spacy model loaded successfully")
except Exception as e:
    logger.error(f"Error loading Spacy model: {str(e)}")
    # Try to download and load again
    try:
        import spacy.cli
        spacy.cli.download("en_core_web_sm")
        nlp = spacy.load("en_core_web_sm")
        logger.info("Spacy model downloaded and loaded successfully")
    except Exception as e2:
        logger.error(f"Failed to download and load Spacy model: {str(e2)}")
        raise

# Predefined skill list
SKILLS = [
    "Python", "JavaScript", "Java", "C++", "C#", "React", "Node.js",
    "Angular", "Vue.js", "Django", "Flask", "SQL", "MongoDB",
    "PostgreSQL", "AWS", "Docker", "Kubernetes", "Git", "CI/CD"
]

class Resume(BaseModel):
    _id: str
    name: str
    email: str
    phone: str
    skills: List[str]
    experience: List[dict]
    uploaded_at: str
    tags: Optional[List[str]] = []

    @property
    def id(self):
        return str(self._id)

    class Config:
        json_encoders = {
            ObjectId: str
        }

@app.delete("/resumes/{resume_id}")
async def delete_resume(resume_id: str):
    """Delete a resume by ID"""
    try:
        # Convert string ID to ObjectId
        object_id = ObjectId(resume_id)
        
        # Delete the resume
        result = await resumes.delete_one({"_id": object_id})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Resume not found")
            
        return {"message": "Resume deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting resume: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/upload")
async def upload_resume(
    file: UploadFile = File(..., description="PDF file to upload")
):
    try:
        # Validate file type using filetype
        file_type = filetype.guess(await file.read(1024))
        if not file_type or file_type.mime != 'application/pdf':
            logger.error(f"Invalid file type: {file_type.mime if file_type else 'None'}")
            raise HTTPException(
                status_code=400,
                detail="Only PDF files are allowed"
            )
            
        # Reset file pointer
        await file.seek(0)
        
        # Check file size
        if file.size > 10 * 1024 * 1024:  # 10MB limit
            logger.error(f"File too large: {file.size/1024/1024:.2f}MB")
            raise HTTPException(
                status_code=413,
                detail="File too large. Maximum file size is 10MB"
            )
            
        logger.info(f"Processing file: {file.filename}")
        
        # Read and process PDF
        content = await file.read()
        
        # Extract text from PDF
        try:
            text = await extract_text_from_pdf(content)
            if not text:
                logger.error("Failed to extract text from PDF")
                raise HTTPException(status_code=400, detail="Failed to extract text from PDF")
        except Exception as e:
            logger.error(f"Error extracting text: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to extract text: {str(e)}")
            
        # Extract resume data
        try:
            data = await extract_resume_data(text)
            data["uploaded_at"] = datetime.now().isoformat()
        except Exception as e:
            logger.error(f"Error extracting resume data: {str(e)}")
            raise HTTPException(status_code=400, detail=f"Failed to extract resume data: {str(e)}")
        
        # Save to database
        try:
            result = await save_resume(data)
            logger.info(f"Resume saved successfully with ID: {result.inserted_id}")
            return {"id": str(result.inserted_id)}
        except Exception as e:
            logger.error(f"Error saving to database: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to save resume: {str(e)}")
            
    except Exception as e:
        logger.error(f"Unexpected error processing resume: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

async def extract_text_from_pdf(pdf_content: bytes) -> str:
    """Extract text from PDF content"""
    try:
        # Create a temporary file to process with PyMuPDF
        with open("temp.pdf", "wb") as f:
            f.write(pdf_content)
        
        # Open and extract text
        pdf_document = fitz.open("temp.pdf")
        text = ""
        for page in pdf_document:
            text += page.get_text()
        
        # Clean up
        pdf_document.close()
        os.remove("temp.pdf")
        
        return text.strip()
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))



@app.get("/resumes")
async def get_resumes():
    try:
        cursor = resumes.find({})
        resumes_list = []
        async for resume in cursor:
            resume['_id'] = str(resume['_id'])  # Convert ObjectId to string
            resumes_list.append(resume)
        return resumes_list
    except Exception as e:
        logger.error(f"Error fetching resumes: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch resumes")


@app.get("/resumes/{resume_id}")
async def get_resume(resume_id: str):
    resume = await resumes.find_one({"_id": resume_id})
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    return Resume(**resume).dict()

async def extract_resume_data(text: str):
    """Extract resume data from text"""
    if not text:
        raise ValueError("No text content provided")

    # Extract name
    name = ""
    name_patterns = [
        r'([A-Z][a-z]+\s+[A-Z][a-z]+)',  # First Last
        r'([A-Z][a-z]+\s+[A-Z][a-z]+\s+[A-Z][a-z]+)',  # First Middle Last
    ]
    for pattern in name_patterns:
        match = re.search(pattern, text)
        if match:
            name = match.group(0)
            break

    # Extract email
    email = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
    email = email.group(0) if email else ""

    # Extract phone
    phone_patterns = [
        r'\+?[0-9]{10,15}',  # 10-15 digit numbers
        r'\+?[0-9\s()-]+',  # With spaces and special characters
    ]
    phone = ""
    for pattern in phone_patterns:
        match = re.search(pattern, text)
        if match:
            phone = match.group(0)
            break

    # Extract skills
    skills = set()  # Use set to prevent duplicates
    
    # First check exact matches
    for skill in SKILLS:
        if skill.lower() in text.lower():
            skills.add(skill)
    
    # Then check partial matches, but only add if not already matched
    for skill in SKILLS:
        if skill not in skills:  # Only check partial if not already matched
            if any(skill.lower() in word.lower() for word in text.split()):
                skills.add(skill)
    
    # Convert set back to list
    skills = list(skills)

    # Extract experience using spaCy
    experience = []
    doc = nlp(text)
    
    # Find companies
    companies = []
    for ent in doc.ents:
        if ent.label_ in ['ORG', 'ORGANIZATION']:
            companies.append(ent.text)

    # Find roles
    roles = []
    role_patterns = [
        r'\b(software|senior|junior|lead|principal|chief|chief\s+technology\s+officer|cto|director|manager|engineer|developer|analyst|architect|consultant)\b',
    ]
    for pattern in role_patterns:
        matches = re.finditer(pattern, text.lower())
        for match in matches:
            role = text[match.start():match.end()].strip()
            if len(role) > 3:
                roles.append(role)

    # Find dates
    durations = []
    date_patterns = [
        r'\b(\d{4}|january|february|march|april|may|june|july|august|september|october|november|december)\b',
    ]
    for pattern in date_patterns:
        matches = re.finditer(pattern, text.lower())
        for match in matches:
            duration = text[match.start():match.end()].strip()
            if len(duration) > 3:
                durations.append(duration)

    # Create experience entries
    experiences = []
    for i in range(min(len(companies), len(roles), len(durations))):
        experiences.append({
            "company": companies[i],
            "role": roles[i],
            "duration": durations[i],
            "description": " ".join(text.split()[:50])  # First 50 words as description
        })

    # Validate required fields
    if not name or not email:
        raise ValueError("Missing required fields: name and email are required")
    
    return {
        "name": name,
        "email": email,
        "phone": phone,
        "skills": skills,
        "experience": experiences,
        "uploaded_at": datetime.now().isoformat()
    }
    
    print("\n=== Extracted Data ===")
    print(f"Name: {name}")
    print(f"Email: {email}")
    print(f"Phone: {phone}")
    print(f"Skills: {skills}")
    print(f"Experience: {experiences}")
    print("=== End of Extracted Data ===")
    
    return {
        "name": name,
        "email": email,
        "phone": phone,
        "skills": list(skills),  # Convert set to list
        "experience": experiences,
        "uploaded_at": datetime.now().isoformat()
    }

async def save_resume(data: dict):
    try:
        # Validate required fields
        if not all(key in data for key in ['name', 'email', 'phone', 'skills', 'uploaded_at']):
            raise ValueError("Missing required fields in resume data")
            
        # Validate experience data structure
        if 'experience' in data:
            for exp in data['experience']:
                if not all(key in exp for key in ['company', 'role', 'duration', 'description']):
                    raise ValueError("Invalid experience data structure")
                    
        # Save to MongoDB
        result = await resumes.insert_one(data)
        logger.info(f"Resume saved with ID: {result.inserted_id}")
        return result  # Return the entire result object
    except Exception as e:
        logger.error(f"Error saving resume: {str(e)}")
        raise ValueError(f"Failed to save resume: {str(e)}")
