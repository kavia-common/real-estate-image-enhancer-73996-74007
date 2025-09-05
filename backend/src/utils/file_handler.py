from fastapi import UploadFile, HTTPException, status
from pathlib import Path
import uuid
from datetime import datetime
from src.utils.config import get_settings

settings = get_settings()

async def save_upload_file(upload_file: UploadFile, user_id: int) -> str:
    """
    Save an uploaded file with validation and proper naming
    Returns the saved file path
    """
    # Validate file size
    content = await upload_file.read()
    if len(content) > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds maximum limit of {settings.MAX_UPLOAD_SIZE // 1024 // 1024}MB"
        )
    
    # Create upload directory if it doesn't exist
    upload_dir = Path(settings.UPLOAD_DIR) / str(user_id)
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate unique filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    original_extension = Path(upload_file.filename).suffix
    safe_filename = f"{timestamp}_{unique_id}{original_extension}"
    
    # Save file
    file_path = upload_dir / safe_filename
    with open(file_path, "wb") as f:
        f.write(content)
    
    return str(file_path)

async def delete_file(file_path: str) -> bool:
    """
    Delete a file if it exists
    Returns True if file was deleted, False if it didn't exist
    """
    try:
        path = Path(file_path)
        if path.exists() and path.is_file():
            path.unlink()
            return True
        return False
    except Exception:
        return False
