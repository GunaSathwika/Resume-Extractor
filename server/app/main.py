from fastapi import FastAPI, UploadFile, HTTPException, File, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional
import fitz  # PyMuPDF
import re
import spacy
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
import os
from dotenv import load_dotenv
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

app = FastAPI(title="Resume Skill Extractor API")

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB connection
client = AsyncIOMotorClient(os.getenv("MONGODB_URI", "mongodb://localhost:27017"))
db = client.resume_extractor
resumes = db.resumes

# Load NLP model
nlp = spacy.load("en_core_web_sm")

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
    # Check file size
    if file.size > 10 * 1024 * 1024:  # 10MB limit
        raise HTTPException(
            status_code=413,
            detail="File too large. Maximum file size is 10MB"
        )

    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    try:
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
