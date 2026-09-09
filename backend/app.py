from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from pathlib import Path
import requests
import os
import json
import re


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)

HF_TOKEN = os.getenv("HUGGINGFACE_API_KEY")

API_URL = "https://router.huggingface.co/v1/chat/completions"
MODEL_NAME = "deepseek-ai/DeepSeek-V3-0324"


# ============================================================
# FASTAPI APP
# ============================================================

app = FastAPI(
    title="AI Study Helper API",
    description="Backend API for AI-powered study assistance",
    version="2.0.0"
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
# CLEAN AI RESPONSE
# ============================================================

def clean_json_response(content: str):
    content = content.strip()

    # Remove markdown code fences if the model adds them
    content = re.sub(r"^```json\s*", "", content, flags=re.IGNORECASE)
    content = re.sub(r"^```\s*", "", content)
    content = re.sub(r"\s*```$", "", content)

    content = content.strip()

    # Find JSON object if extra text was returned
    start = content.find("{")
    end = content.rfind("}")

    if start != -1 and end != -1:
        content = content[start:end + 1]

    try:
        return json.loads(content)

    except json.JSONDecodeError:
        raise HTTPException(
            status_code=500,
            detail="AI returned an invalid response format. Please try again."
        )


# ============================================================
# NORMALIZE AI RESPONSE
# ============================================================

def normalize_response(data):
    notes = data.get("notes", [])
    explanation = data.get("explanation", "")
    exam_points = data.get("exam_points", data.get("exam", []))
    quiz = data.get("quiz", [])

    # Ensure notes is always a list
    if isinstance(notes, str):
        notes = [notes]

    # Ensure exam points is always a list
    if isinstance(exam_points, str):
        exam_points = [exam_points]

    # Ensure quiz is always a list
    if isinstance(quiz, dict):
        quiz = [quiz]

    cleaned_quiz = []

    for question in quiz:
        if isinstance(question, dict):
            cleaned_quiz.append({
                "question": str(question.get("question", "")),
                "answer": str(question.get("answer", ""))
            })
        else:
            cleaned_quiz.append({
                "question": str(question),
                "answer": ""
            })

    return {
        "notes": [str(note) for note in notes],
        "explanation": str(explanation),
        "exam": [str(point) for point in exam_points],
        "quiz": cleaned_quiz
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
You are an expert AI study assistant for college engineering students.

Subject: {subject}
Topic: {topic}

Create useful, accurate and exam-oriented study material.

Return ONLY valid JSON using exactly this structure:

{{
    "notes": [
        "Short note 1",
        "Short note 2",
        "Short note 3",
        "Short note 4"
    ],
    "explanation": "A clear and beginner-friendly explanation of the topic.",
    "exam": [
        "Important exam point 1",
        "Important exam point 2",
        "Important exam point 3",
        "Important exam point 4",
        "Important exam point 5"
    ],
    "quiz": [
        {{
            "question": "Question 1",
            "answer": "Correct answer 1"
        }},
        {{
            "question": "Question 2",
            "answer": "Correct answer 2"
        }},
        {{
            "question": "Question 3",
            "answer": "Correct answer 3"
        }}
    ]
}}

Rules:

1. Keep the notes concise and useful for revision.
2. Explain the topic in simple but technically correct language.
3. Include important definitions, concepts and formulas where relevant.
4. Give exactly 5 exam points.
5. Give exactly 3 quiz questions.
6. Quiz questions must test understanding, not just memorization.
7. Keep every answer directly relevant to the given topic.
8. Do not invent facts.
9. Do not use markdown outside the JSON.
10. Do not add any text before or after the JSON.
"""

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a reliable college-level AI study assistant. "
                    "Return only valid JSON and follow the requested structure exactly."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.4,
        "max_tokens": 1600
    }

    try:
        response = requests.post(
            API_URL,
            headers=headers,
            json=payload,
            timeout=90
        )

    except requests.exceptions.Timeout:
        raise HTTPException(
            status_code=504,
            detail="AI request timed out. Please try again."
        )

    except requests.exceptions.RequestException:
        raise HTTPException(
            status_code=502,
            detail="Could not connect to the AI service."
        )

    # ========================================================
    # HANDLE API ERRORS
    # ========================================================

    if response.status_code != 200:

        try:
            error_data = response.json()
        except Exception:
            error_data = response.text

        print("Hugging Face error:", error_data)

        raise HTTPException(
            status_code=502,
            detail="AI service returned an error. Please try again."
        )

    # ========================================================
    # EXTRACT AI RESPONSE
    # ========================================================

    try:
        result = response.json()

        content = result["choices"][0]["message"]["content"]

    except (KeyError, IndexError, TypeError, ValueError):

        print("Unexpected AI response:", response.text)

        raise HTTPException(
            status_code=500,
            detail="Unexpected response received from AI service."
        )

    # ========================================================
    # PARSE JSON
    # ========================================================

    data = clean_json_response(content)

    # ========================================================
    # VALIDATE REQUIRED FIELDS
    # ========================================================

    required_fields = [
        "notes",
        "explanation",
        "exam",
        "quiz"
    ]

    for field in required_fields:

        if field not in data:
            raise HTTPException(
                status_code=500,
                detail=f"AI response is missing '{field}'."
            )

    # ========================================================
    # RETURN NORMALIZED RESPONSE
    # ========================================================

    return normalize_response(data)


# ============================================================
# GENERATE STUDY MATERIAL
# ============================================================

@app.post("/generate")
def generate(data: GenerateRequest):

    topic = data.topic.strip()
    subject = data.subject.strip()

    if not topic:
        raise HTTPException(
            status_code=400,
            detail="Topic cannot be empty."
        )

    if len(topic) > 300:
        raise HTTPException(
            status_code=400,
            detail="Topic is too long. Please enter a shorter topic."
        )

    if not subject:
        subject = "General"

    if len(subject) > 100:
        raise HTTPException(
            status_code=400,
            detail="Subject is too long."
        )

    print(
        f"Generating study material | "
        f"Subject: {subject} | "
        f"Topic: {topic}"
    )

    return query_ai(
        topic=topic,
        subject=subject
    )


# ============================================================
# RUN LOCALLY
# ============================================================

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        "app:app",
        host="127.0.0.1",
        port=5000,
        reload=True
    )
    
