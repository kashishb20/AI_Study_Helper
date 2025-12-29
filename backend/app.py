from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route("/")
def home():
    return "AI Study Helper Backend Running!"

@app.route("/generate", methods=["POST"])
def generate():
    data = request.get_json()

    topic = data.get("topic", "").strip()

    if not topic:
        return jsonify({"error": "No topic provided"}), 400

    response = {
    "notes": [
        f"{topic} is a core topic",
        "Frequently asked in exams",
        "Helps build strong fundamentals"
    ],
    "explanation": (
        f"{topic} is explained in a simple and structured manner. "
        "It focuses on understanding the concept clearly with examples."
    ),
    "exam": [
        "Definition-based questions",
        "Short notes questions",
        "Concept clarity is tested"
    ],
    "quiz": [
    f"What is {topic}?",
    f"Why is {topic} important?",
    f"Where is {topic} commonly used?"
]
}

    return jsonify(response)

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)



