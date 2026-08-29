import os
import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.config import settings
from app.models.candidate import Candidate
from app.schemas.candidate import CandidateResponse
from app.services.parser import extract_text_from_file
from app.services.extractor import extract_candidate_info

router = APIRouter()

ALLOWED_EXTENSIONS = {"pdf", "docx", "txt", "md"}

@router.post("/upload", response_model=List[CandidateResponse], status_code=status.HTTP_201_CREATED)
async def upload_resumes(files: List[UploadFile] = File(...), db: Session = Depends(get_db)):
    """
    Upload one or multiple candidate resumes (PDF, DOCX, TXT).
    Parses document text, extracts skills & contact info, and saves candidate records.
    """
    candidates_created = []

    for file in files:
        filename = file.filename or "resume.pdf"
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file format '{ext}' for file '{filename}'. Supported: PDF, DOCX, TXT."
            )
            
        # Save file to disk
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        file_path = os.path.join(settings.UPLOAD_DIR, unique_filename)
        
        try:
            content = await file.read()
            with open(file_path, "wb") as f:
                f.write(content)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error saving file '{filename}': {str(e)}"
            )

        # Parse text content
        try:
            raw_text, file_type = extract_text_from_file(file_path, filename)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Failed to parse content from '{filename}': {str(e)}"
            )

        if not raw_text or len(raw_text.strip()) == 0:
            raw_text = f"Empty or unreadable file content for {filename}"

        # Extract information
        extracted = extract_candidate_info(raw_text, filename)

        candidate = Candidate(
            name=extracted["name"],
            email=extracted["email"],
            phone=extracted["phone"],
            filename=filename,
            file_type=file_type,
            file_path=file_path,
            raw_text=raw_text,
            extracted_skills=extracted["skills"],
            extracted_education=extracted["education"],
            experience_years=extracted["experience_years"]
        )

        db.add(candidate)
        candidates_created.append(candidate)

    db.commit()
    for cand in candidates_created:
        db.refresh(cand)

    return candidates_created

@router.get("/", response_model=List[CandidateResponse])
def list_candidates(db: Session = Depends(get_db)):
    """List all stored candidates."""
    return db.query(Candidate).order_by(Candidate.created_at.desc()).all()

@router.get("/{candidate_id}", response_model=CandidateResponse)
def get_candidate(candidate_id: int, db: Session = Depends(get_db)):
    """Get candidate details by ID."""
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found")
    return candidate

@router.delete("/{candidate_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_candidate(candidate_id: int, db: Session = Depends(get_db)):
    """Delete a candidate record."""
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found")
    
    # Remove file from disk if present
    if candidate.file_path and os.path.exists(candidate.file_path):
        try:
            os.remove(candidate.file_path)
        except Exception:
            pass

    db.delete(candidate)
    db.commit()
    return None
