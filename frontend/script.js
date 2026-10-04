async function generateContent() {
  const topicInput = document.getElementById("topicInput");
  const subjectInput = document.getElementById("subjectInput");

  const topic = topicInput.value.trim();
  const subject = subjectInput ? subjectInput.value.trim() : "General";

  if (!topic) {
    alert("Please enter a topic");
    return;
  }

  const btn = document.querySelector(".generate-btn");

  // Disable button while loading
  btn.disabled = true;
  btn.innerText = "Generating...";

  // Show loading state
  document.getElementById("notes").innerHTML =
    "<h3>📌 Short Notes</h3><p class='loading'>⏳ Generating...</p>";

  document.getElementById("explanation").innerHTML =
    "<h3>📖 Explanation</h3><p class='loading'>⏳ Generating...</p>";

  document.getElementById("exam").innerHTML =
    "<h3>📝 Exam Points</h3><p class='loading'>⏳ Generating...</p>";

  document.getElementById("quiz").innerHTML =
    "<h3>🧠 Quick Quiz</h3><p class='loading'>⏳ Generating...</p>";

  try {
    const response = await fetch("https://ai-study-helper-api.onrender.com/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        topic: topic,
        subject: subject || "General"
      })
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || "Server error");
    }

    const data = await response.json();

    // Render Short Notes
    document.getElementById("notes").innerHTML =
      `<h3>📌 Short Notes</h3>
       <p>${data.notes}</p>`;

    // Render Explanation
    document.getElementById("explanation").innerHTML =
      `<h3>📖 Explanation</h3>
       <p>${data.explanation}</p>`;

    // Render Exam Points
    document.getElementById("exam").innerHTML =
      `<h3>📝 Exam Points</h3>
       <ul>
         ${data.exam_points.map(point => `<li>${point}</li>`).join("")}
       </ul>`;

    // Render Quick Quiz
    document.getElementById("quiz").innerHTML =
      `<h3>🧠 Quick Quiz</h3>
       ${data.quiz.map((q, index) => `
         <div class="quiz-question">
           <p><strong>Q${index + 1}. ${q.question}</strong></p>
           <p><strong>Answer:</strong> ${q.answer}</p>
         </div>
       `).join("")}`;

  } catch (error) {
    console.error("Error:", error);

    alert(
      error.message || "Something went wrong. Please try again."
    );

    // Show error in the UI
    document.getElementById("notes").innerHTML =
      "<h3>📌 Short Notes</h3><p>❌ Failed to generate content.</p>";

    document.getElementById("explanation").innerHTML =
      "<h3>📖 Explanation</h3><p>❌ Failed to generate content.</p>";

    document.getElementById("exam").innerHTML =
      "<h3>📝 Exam Points</h3><p>❌ Failed to generate content.</p>";

    document.getElementById("quiz").innerHTML =
      "<h3>🧠 Quick Quiz</h3><p>❌ Failed to generate content.</p>";

  } finally {
    // Re-enable button
    btn.disabled = false;
    btn.innerText = "Generate";
  }
}