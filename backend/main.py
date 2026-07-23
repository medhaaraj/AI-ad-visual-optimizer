from certifi import contents
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from analyzer import analyze_image
from generator import generate_image
import io
import base64
from datetime import datetime

app = FastAPI(title="AI Ad Visual Optimizer API")

# Setup CORS for the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "AI Ad Visual Optimizer API is running."}

@app.post("/analyze")
async def analyze_endpoint(
    file: UploadFile = File(...),
    audience: str = Form(""),
    campaign_info: str = Form("")
):
    if file.content_type not in ["image/jpeg", "image/png", "image/webp"]:
        raise HTTPException(status_code=400, detail="Invalid file type")
    
    contents = await file.read()
    results = analyze_image(contents, audience, campaign_info)
    return results

@app.post("/generate")
async def generate_endpoint(
    file: UploadFile = File(...),
    prompt: str = Form(...)
):
    if file.content_type not in ["image/jpeg", "image/png", "image/webp"]:
        raise HTTPException(status_code=400, detail="Invalid file type")
    
    contents = await file.read()
    analysis = analyze_image(contents, audience="", campaign_info="")
    result_image_base64 = generate_image(contents, prompt, analysis)
    return {"generated_image": result_image_base64}

@app.post("/download")
async def download_endpoint(data: dict):
    """Download generated image as file"""
    try:
        image_data = data.get("image_base64")
        
        if not image_data:
            raise HTTPException(status_code=400, detail="No image data provided")
        
        # Remove data URL prefix if present
        if image_data.startswith("data:image"):
            image_data = image_data.split(",")[1]
        
        # Decode base64 to bytes
        image_bytes = base64.b64decode(image_data)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"ad-optimization-{timestamp}.jpg"
        
        # Return as file download
        return StreamingResponse(
            io.BytesIO(image_bytes),
            media_type="image/jpeg",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")
