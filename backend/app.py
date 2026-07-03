from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import os
from dotenv import load_dotenv

# Load environment variables
from pathlib import Path

env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)

app = FastAPI()

# ✅ CORS (IMPORTANT for frontend connection)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request schema
class GenerateRequest(BaseModel):
    topic: str
    subject: str

# Hugging Face API setup
API_URL = "https://api-inference.huggingface.co/models/google/flan-t5-large"

HEADERS = {
    "Authorization": f"Bearer {os.getenv('HUGGINGFACE_API_KEY')}"
}

# Query function
def query(payload):
    try:
        response = requests.post(
            API_URL,
            headers=HEADERS,
            json=payload,
            timeout=30
        )

        print("🔥 STATUS CODE:", response.status_code)
        print("🔥 RAW RESPONSE:", response.text)

        return response.json()

    except Exception as e:
        print("❌ REQUEST ERROR:", str(e))
        return {"error": str(e)}

# Root route
@app.get("/")
def home():
    return {"message": "AI Study Helper Backend Running 🚀"}

# Main AI route
@app.post("/generate")
def generate(data: GenerateRequest):
    print("📥 Incoming request:", data)

    prompt = f"""
    Topic: {data.topic}
    Subject: {data.subject}

    Give:
    1. Short exam notes
    2. Explanation
    3. 3 exam points
    4. 2 quiz questions
    """

    try:
        print("🔑 API KEY:", os.getenv("HUGGINGFACE_API_KEY"))

        result = query({"inputs": prompt})

        print("🔥 FULL HF RESPONSE:", result)

        # ✅ Handle Hugging Face response safely
        if isinstance(result, list) and "generated_text" in result[0]:
            output = result[0]["generated_text"]
        else:
            raise HTTPException(status_code=500, detail=str(result))

        return {
            "notes": output,
            "explanation": output,
            "exam_points": ["Point 1", "Point 2", "Point 3"],
            "quiz": ["Question 1", "Question 2"]
        }

    except Exception as e:
        print("❌ ERROR:", str(e))
        raise HTTPException(status_code=500, detail=str(e))