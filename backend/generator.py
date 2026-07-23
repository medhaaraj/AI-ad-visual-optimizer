import io
import base64
import numpy as np
import cv2
import requests
import os
from PIL import Image, ImageEnhance
from dotenv import load_dotenv

load_dotenv()

API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"

def generate_image(image_bytes: bytes, prompt: str, analysis: dict = None) -> str:
    try:
        scores = analysis.get("scores", {}) if analysis else {}
        suggestions = analysis.get("suggestions", []) if analysis else []

        # Build a proper image generation prompt
        smart_prompt = (
            "A professional, modern, high-converting advertisement. "
            "Clean layout, strong visual hierarchy, clear call-to-action, "
            "vibrant but balanced colors, excellent typography. "
        )
        if suggestions:
            smart_prompt += " ".join(suggestions)

        negative_prompt = (
            "blurry, low quality, cluttered, messy, watermark, "
            "text errors, distorted, ugly, amateur"
        )

        hf_token = os.environ.get("HF_TOKEN")
        headers = {"Authorization": f"Bearer {hf_token}"}

        payload = {
            "inputs": smart_prompt,
            "parameters": {
                "negative_prompt": negative_prompt,
                "num_inference_steps": 30,
                "guidance_scale": 7.5,
                "width": 768,
                "height": 768,
            }
        }

        print("Calling HuggingFace SDXL...")
        response = requests.post(API_URL, headers=headers, json=payload, timeout=120)

        if response.status_code == 200:
            print("HuggingFace succeeded, blending images...")
            return blend_images(image_bytes, response.content, scores)
        else:
            print(f"HuggingFace failed ({response.status_code}): {response.text}")
            return cv_enhance(image_bytes, scores)

    except Exception as e:
        print(f"Generation error: {e}")
        return cv_enhance(image_bytes, analysis.get("scores", {}) if analysis else {})


def blend_images(original_bytes: bytes, generated_bytes: bytes, scores: dict) -> str:
    orig = Image.open(io.BytesIO(original_bytes)).convert("RGB").resize((768, 768))
    gen = Image.open(io.BytesIO(generated_bytes)).convert("RGB").resize((768, 768))

    orig_np = np.array(orig)
    gen_np = np.array(gen)

    # Blend: keep more of the original (70%) so it still looks like the same ad
    blended = cv2.addWeighted(orig_np, 0.7, gen_np, 0.3, 0)

    # Sharpen the blend
    kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
    blended = cv2.filter2D(blended, -1, kernel)

    img = Image.fromarray(blended)
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=95)
    return "data:image/jpeg;base64," + base64.b64encode(buffer.getvalue()).decode()


def cv_enhance(image_bytes: bytes, scores: dict) -> str:
    """Fallback: apply targeted CV enhancements based on analysis scores."""
    try:
        img = cv2.imdecode(np.frombuffer(image_bytes, np.uint8), cv2.IMREAD_COLOR)

        contrast_score = scores.get("contrast", 50)
        readability_score = scores.get("readability", 50)
        aesthetic_score = scores.get("aesthetic", 50)

        # Contrast enhancement
        if contrast_score < 60:
            lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            clip = 3.0 if contrast_score < 40 else 2.0
            clahe = cv2.createCLAHE(clipLimit=clip, tileGridSize=(8, 8))
            l = clahe.apply(l)
            img = cv2.cvtColor(cv2.merge((l, a, b)), cv2.COLOR_LAB2BGR)

        # Brightness/saturation boost
        if aesthetic_score < 60:
            pil_img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
            pil_img = ImageEnhance.Color(pil_img).enhance(1.2)
            pil_img = ImageEnhance.Brightness(pil_img).enhance(1.05)
            img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

        # Sharpen
        if readability_score < 70:
            kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
            img = cv2.filter2D(img, -1, kernel)

        # Denoise
        img = cv2.fastNlMeansDenoisingColored(img, None, 3, 3, 7, 21)

        _, buffer = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 95])
        return "data:image/jpeg;base64," + base64.b64encode(buffer).decode()

    except Exception as e:
        print(f"CV enhance error: {e}")
        return "data:image/jpeg;base64," + base64.b64encode(image_bytes).decode()