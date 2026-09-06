from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from pathlib import Path
import requests
import os
import json


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)


# ============================================================
# FASTAPI APP
# ============================================================

app = FastAPI(
    title="AI Study Helper API",
    description="Backend API for AI-powered study assistance",
    version="1.0.0"
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# ENVIRONMENT VARIABLES
# ============================================================

HF_TOKEN = os.getenv("HUGGINGFACE_API_KEY")

# Current Hugging Face OpenAI-compatible router
API_URL = "https://router.huggingface.co/v1/chat/completions"

# Model available through Hugging Face Inference Providers
MODEL_NAME = "deepseek-ai/DeepSeek-V3-0324"


# ============================================================
# REQUEST MODEL
# ============================================================

class GenerateRequest(BaseModel):
    topic: str
    subject: str = "General"


# ============================================================
# ROOT ROUTE
# ============================================================

@app.get("/")
def home():
    return {
        "message": "AI Study Helper Backend Running",
        "status": "online"
    }


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "api_key_configured": bool(HF_TOKEN)
    }


# ============================================================
# AI QUERY FUNCTION
# ============================================================

def query_ai(topic: str, subject: str):

    if not HF_TOKEN:
        raise HTTPException(
            status_code=500,
            detail="HUGGINGFACE_API_KEY is not configured."
        )

    headers = {
        "Authorization": f"Bearer {HF_TOKEN}",
        "Content-Type": "application/json"
    }

    prompt = f"""
You are an expert AI study assistant for college students.

Subject: {subject}
Topic: {topic}

Create useful exam-oriented study material for this topic.

Return ONLY valid JSON in exactly this format:

{{
    "notes": "Short and concise exam notes about the topic.",
    "explanation": "A clear and beginner-friendly explanation of the topic.",
    "exam_points": [
        "Important exam point 1",
        "Important exam point 2",
        "Important exam point 3"
    ],
    "quiz": [
        {{
            "question": "Quiz question 1",
            "answer": "Correct answer 1"
        }},
        {{
            "question": "Quiz question 2",
            "answer": "Correct answer 2"
        }}
    ]
}}

Rules:

1. Keep the notes concise.
2. Explain the concept clearly.
3. Give exactly 3 important exam points.
4. Give exactly 2 quiz questions.
5. Make the quiz relevant to the topic.
6. Do not use markdown outside the JSON.
7. Do not add any text before or after the JSON.
"""

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a reliable college-level AI study assistant. "
                    "Always follow the requested JSON format."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.4,
        "max_tokens": 1200
    }

    try:

        response = requests.post(
            API_URL,
            headers=headers,
            json=payload,
            timeout=60
        )

    except requests.exceptions.Timeout:

        raise HTTPException(
            status_code=504,
            detail="AI request timed out. Please try again."
        )

    except requests.exceptions.RequestException as e:

        raise HTTPException(
            status_code=502,
            detail=f"Could not connect to Hugging Face: {str(e)}"
        )


    # ========================================================
    # HANDLE HTTP ERRORS
    # ========================================================

    if response.status_code != 200:

        try:
            error_data = response.json()
        except Exception:
            error_data = response.text

        print("Hugging Face error:", error_data)

        raise HTTPException(
            status_code=response.status_code,
            detail=f"Hugging Face API error: {error_data}"
        )


    # ========================================================
    # PARSE RESPONSE
    # ========================================================

    try:

        result = response.json()

        content = result["choices"][0]["message"]["content"]

    except (KeyError, IndexError, TypeError, ValueError):

        print("Unexpected AI response:", response.text)

        raise HTTPException(
            status_code=500,
            detail="Unexpected response received from AI model."
        )


    # ========================================================
    # PARSE AI JSON
    # ========================================================

    try:

        # Remove possible markdown code fences
        content = content.strip()

        if content.startswith("```json"):
            content = content[7:]

        elif content.startswith("```"):
            content = content[3:]

        if content.endswith("```"):
            content = content[:-3]

        content = content.strip()

        data = json.loads(content)

    except json.JSONDecodeError:

        print("AI returned invalid JSON:")
        print(content)

        raise HTTPException(
            status_code=500,
            detail="AI returned an invalid response format. Please try again."
        )


    # ========================================================
    # VALIDATE RESPONSE
    # ========================================================

    required_fields = [
        "notes",
        "explanation",
        "exam_points",
        "quiz"
    ]

    for field in required_fields:

        if field not in data:

            raise HTTPException(
                status_code=500,
                detail=f"AI response is missing '{field}'."
            )


    return data


# ============================================================
# MAIN GENERATE ROUTE
# ============================================================

@app.post("/generate")
def generate(data: GenerateRequest):

    # Clean user input
    topic = data.topic.strip()
    subject = data.subject.strip()

    if not topic:

        raise HTTPException(
            status_code=400,
            detail="Topic cannot be empty."
        )

    if not subject:

        subject = "General"


    print(
        f"Generating study material | "
        f"Subject: {subject} | "
        f"Topic: {topic}"
    )


    result = query_ai(
        topic=topic,
        subject=subject
    )


    return result


# ============================================================
# RUN LOCALLY
# ============================================================

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        "app:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )
