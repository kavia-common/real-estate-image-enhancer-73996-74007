import os
import httpx
from src.models import SessionLocal
from src.models.image import Image
from dotenv import load_dotenv

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_API_ENDPOINT = os.getenv("GOOGLE_API_ENDPOINT")

async def process_image(image_id: int, file_path: str, edit_request: str):
    db = SessionLocal()
    try:
        # Get image record
        image = db.query(Image).filter(Image.id == image_id).first()
        if not image:
            return
        
        image.status = "processing"
        db.commit()

        # Prepare image data
        with open(file_path, "rb") as f:
            image_data = f.read()

        # Call Google Nano Banana API
        async with httpx.AsyncClient() as client:
            response = await client.post(
                GOOGLE_API_ENDPOINT,
                headers={
                    "Authorization": f"Bearer {GOOGLE_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "image": image_data.decode('utf-8'),  # Base64 encoded image
                    "edit_request": edit_request
                }
            )

            if response.status_code == 200:
                result = response.json()
                
                # Save enhanced image
                enhanced_path = f"{os.path.dirname(file_path)}/enhanced_{os.path.basename(file_path)}"
                with open(enhanced_path, "wb") as f:
                    f.write(result["enhanced_image"].encode('utf-8'))  # Decode base64 image
                
                # Update image record
                image.enhanced_url = enhanced_path
                image.status = "completed"
                image.google_task_id = result.get("task_id")
            else:
                image.status = "failed"
            
            db.commit()

    except Exception:
        if image:
            image.status = "failed"
            db.commit()
    finally:
        db.close()
