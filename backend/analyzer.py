import base64
import io
import os
import cv2
import numpy as np
from PIL import Image
import pytesseract
import json
import re
from dotenv import load_dotenv
import ollama

load_dotenv()

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def extract_json(text: str):
    """Robust JSON extractor"""
    try:
        # find first valid JSON object
        start = text.find('{')
        end = text.rfind('}') + 1

        if start != -1 and end != -1:
            json_str = text[start:end]
            return json.loads(json_str)
        else:
            print("No JSON found:", text)
            return None

    except Exception as e:
        print("JSON parse error:", e)
        print("Raw output:", text)  
        return None

def get_ollama_analysis(image_bytes: bytes, extracted_text: str, audience: str, campaign: str) -> dict:
    try:
        prompt = f"""
You are an expert AI Marketing and Design Consultant. Analyze this advertisement image and return a JSON object with these fields:

- "aesthetic" (0-100)
- "readability" (0-100)
- "layout" (0-100)
- "suggestions": exactly 3 actionable suggestions

Context:
- Target Audience: {audience or "General"}
- Campaign Goal: {campaign or "General Objective"}
- OCR Extracted Text: {extracted_text}

Respond ONLY with valid JSON.
"""
        image_b64 = base64.b64encode(image_bytes).decode("utf-8")
        response = ollama.chat(
            model="llava:7b",
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                    "images": [image_b64],  # ✅ no temp file
                }
            ]
        )

        raw = response["message"]["content"].strip()
        raw = raw.replace("```json", "").replace("```", "").strip()

        return extract_json(raw)

    except Exception as e:
        print(f"Ollama error: {e}")
        return None


def analyze_image(image_bytes: bytes, audience: str, campaign_info: str) -> dict:
    nparr = np.frombuffer(image_bytes, np.uint8)
    img_cv = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    # Contrast score
    try:
        gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
        contrast = float(gray.std())
        contrast_score = min(100, int((contrast / 128) * 100))
    except:
        contrast_score = 50

    # OCR
    try:
        pil_img = Image.open(io.BytesIO(image_bytes))
        extracted_text = pytesseract.image_to_string(pil_img).strip()

        words = extracted_text.split()
        avg_len = sum(len(w) for w in words) / len(words) if words else 0

        if avg_len < 3 or len(words) < 2:
            extracted_text = "No prominent text found."

        if not extracted_text:
            extracted_text = "No prominent text found."

    except:
        extracted_text = "No prominent text found."

    # 🔁 Ollama analysis
    ai_result = get_ollama_analysis(image_bytes, extracted_text, audience, campaign_info)

    if ai_result:
        return {
            "scores": {
                "aesthetic": ai_result.get("aesthetic", 50),
                "readability": ai_result.get("readability", 50),
                "contrast": contrast_score,
                "layout": ai_result.get("layout", 50),
            },
            "extracted_text": extracted_text,
            "suggestions": ai_result.get(
                "suggestions",
                ["Improve layout.", "Increase contrast.", "Add a clear CTA."]
            ),
            "ai_powered": True
        }
    else:
        return {
            "scores": {
                "aesthetic": 50,
                "readability": 50,
                "contrast": contrast_score,
                "layout": 50,
            },
            "extracted_text": extracted_text,
            "suggestions": [
                "Improve layout balance.",
                "Use higher contrast colors.",
                "Add a clear CTA."
            ],
            "ai_powered": False
        }