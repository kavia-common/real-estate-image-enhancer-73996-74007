from pathlib import Path
from typing import BinaryIO

from src.core.config import get_settings

settings = get_settings()


class StorageService:
    """Abstraction over storage backends (local or S3 stub)."""

    def __init__(self):
        self.backend = settings.STORAGE_BACKEND
        if self.backend == "local":
            Path(settings.LOCAL_STORAGE_PATH).mkdir(parents=True, exist_ok=True)

    # PUBLIC_INTERFACE
    def save(self, fileobj: BinaryIO, filename: str, subdir: str = "") -> str:
        """Save a file and return a URL/path to access it."""
        if self.backend == "local":
            directory = Path(settings.LOCAL_STORAGE_PATH) / subdir if subdir else Path(settings.LOCAL_STORAGE_PATH)
            directory.mkdir(parents=True, exist_ok=True)
            dest = directory / filename
            with open(dest, "wb") as out:
                out.write(fileobj.read())
            # For local, return a pseudo-URL path that frontend can proxy or backend can serve
            return f"/static/uploads/{subdir}/{filename}" if subdir else f"/static/uploads/{filename}"
        elif self.backend == "s3":
            # Stub: In a real implementation, use boto3 to upload and return a signed/public URL
            # For now, just simulate a URL
            return f"https://s3.{settings.S3_REGION}.amazonaws.com/{settings.S3_BUCKET_NAME}/{subdir}/{filename}"
        else:
            raise ValueError("Unsupported storage backend")

    # PUBLIC_INTERFACE
    def delete(self, key_or_path: str) -> None:
        """Delete a stored object (best-effort)."""
        if self.backend == "local":
            try:
                path = key_or_path.replace("/static/uploads/", "").lstrip("/")
                real_path = Path(settings.LOCAL_STORAGE_PATH) / path
                if real_path.exists():
                    real_path.unlink()
            except Exception:
                pass
        elif self.backend == "s3":
            # Stub
            pass
