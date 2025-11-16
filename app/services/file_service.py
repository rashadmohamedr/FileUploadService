import uuid
import shutil
from fastapi import UploadFile, status
from sqlalchemy.orm import Session
from app.models.file import File
from app.core.config import settings
import os

UPLOAD_DIR = settings.UPLOAD_DIR

def save_upload(db: Session, upload_file: UploadFile, owner_id: int):
    """
    Save uploaded file to disk and persist its metadata in the database.
    Returns the created File ORM instance.
    """

    # ensure filename is a str (UploadFile.filename can be None)
    filename = upload_file.filename or "unnamed"
    _, ext = os.path.splitext(filename)
    ext = ext.lstrip('.')  # remove leading dot if present
    saved_name = f"{uuid.uuid4()}.{ext}" if ext else str(uuid.uuid4())
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    file_path = os.path.join(UPLOAD_DIR, saved_name)

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(upload_file.file, buffer)

        db_file = File(
            name=filename,
            ownerID=owner_id,
            content_type=upload_file.content_type,
            path=file_path
        )
        db.add(db_file)
        db.commit()
        db.refresh(db_file)
        return db_file
    except Exception:
        db.rollback()
        # attempt to remove partially written file
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception:
            pass
        raise