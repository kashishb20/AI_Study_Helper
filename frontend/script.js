// async function generateContent() {
//   const topic = document.getElementById("topicInput").value.trim();

//   if (topic === "") {
//     alert("Please enter a topic");
//     return;
//   }

//   document.getElementById("notes").innerHTML = "<h3>📌 Short Notes</h3><p>Loading...</p>";
//   document.getElementById("explanation").innerHTML = "<h3>📖 Explanation</h3><p>Loading...</p>";
//   document.getElementById("exam").innerHTML = "<h3>📝 Exam Points</h3><p>Loading...</p>";

//   try {
//     const response = await fetch("http://127.0.0.1:5000/generate", {
//       method: "POST",
//       headers: {
//         "Content-Type": "application/json"
//       },
//       body: JSON.stringify({ topic })
//     });

//     if (!response.ok) {
//       throw new Error("Server error");
//     }

//     const data = await response.json();

//     document.getElementById("notes").innerHTML =
//       `<h3>📌 Short Notes</h3><ul>${data.notes.map(n => `<li>${n}</li>`).join("")}</ul>`;

//     document.getElementById("explanation").innerHTML =
//       `<h3>📖 Explanation</h3><p>${data.explanation}</p>`;

//     document.getElementById("exam").innerHTML =
//       `<h3>📝 Exam Points</h3><ul>${data.exam.map(e => `<li>${e}</li>`).join("")}</ul>`;

//   } catch (error) {
//     alert("Backend not running or error occurred");
//     console.error(error);
//   }
// }
// const btn = document.querySelector(".generate-btn");
// btn.disabled = true;
// btn.innerText = "Generating...";
// btn.disabled = false;
// btn.innerText = "Generate";
async function generateContent() {
  const topicInput = document.getElementById("topicInput");
  const topic = topicInput.value.trim();

  if (!topic) {
    alert("Please enter a topic");
    return;
  }

  const btn = document.querySelector(".generate-btn");

  // 🔹 Disable button while loading
  btn.disabled = true;
  btn.innerText = "Generating...";

  // 🔹 Show loading state
  document.getElementById("notes").innerHTML =
    "<h3>📌 Short Notes</h3><p class='loading'>⏳ Generating...</p>";

  document.getElementById("explanation").innerHTML =
    "<h3>📖 Explanation</h3><p class='loading'>⏳ Generating...</p>";

  document.getElementById("exam").innerHTML =
    "<h3>📝 Exam Points</h3><p class='loading'>⏳ Generating...</p>";

  document.getElementById("quiz").innerHTML =
    "<h3>🧠 Quick Quiz</h3><p class='loading'>⏳ Generating...</p>";

  try {
    const response = await fetch("http://127.0.0.1:5000/generate", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ topic })
    });

    if (!response.ok) {
      throw new Error("Server error");
    }

    const data = await response.json();

    // 🔹 Render Short Notes
    document.getElementById("notes").innerHTML =
      `<h3>📌 Short Notes</h3>
       <ul>${data.notes.map(note => `<li>${note}</li>`).join("")}</ul>`;

    // 🔹 Render Explanation
    document.getElementById("explanation").innerHTML =
      `<h3>📖 Explanation</h3>
       <p>${data.explanation}</p>`;

    // 🔹 Render Exam Points
    document.getElementById("exam").innerHTML =
      `<h3>📝 Exam Points</h3>
       <ul>${data.exam.map(point => `<li>${point}</li>`).join("")}</ul>`;

    // ⭐ Standout Feature: Quick Quiz
    document.getElementById("quiz").innerHTML =
      `<h3>🧠 Quick Quiz</h3>
       <ul>${data.quiz.map(q => `<li>${q}</li>`).join("")}</ul>`;

  } catch (error) {
    alert("Something went wrong. Please try again.");
    console.error(error);
  } finally {
    // 🔹 Re-enable button
    btn.disabled = false;
    btn.innerText = "Generate";
  }
}
