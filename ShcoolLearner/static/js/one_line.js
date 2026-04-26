document.addEventListener("DOMContentLoaded", () => {
  const root = document.getElementById("one-line-container");
  if (!root) return;

  const subject = root.dataset.subject;
  const counterEl = document.getElementById("one-line-counter");
  const questionEl = document.getElementById("one-line-question");
  const answerEl = document.getElementById("one-line-answer");
  const feedbackEl = document.getElementById("one-line-feedback");
  const checkBtn = document.getElementById("check-answer-btn");
  const nextBtn = document.getElementById("next-one-line-btn");

  let questions = [];
  let currentIndex = 0;

  initialize();

  async function initialize() {
    try {
      const response = await fetch(`/api/one-line-questions/${encodeURIComponent(subject)}?count=10&mode=random`);
      const payload = await response.json().catch(() => []);
      if (!response.ok || !Array.isArray(payload) || !payload.length) {
        showMessage("No one-line questions are available for this subject yet.");
        return;
      }

      questions = payload;
      renderQuestion();
    } catch (error) {
      showMessage("Could not load one-line questions. Please try again.");
    }
  }

  checkBtn.addEventListener("click", () => {
    const current = questions[currentIndex];
    if (!current) return;

    const studentAnswer = normalize(answerEl.value);
    const correctAnswer = normalize(current.answer);
    if (!studentAnswer) {
      showFeedback("Please type your answer first.", "wrong");
      return;
    }

    if (studentAnswer === correctAnswer) {
      showFeedback(`Correct. ${current.explanation || ""}`, "correct");
    } else {
      showFeedback(`Right answer: ${current.answer}. ${current.explanation || ""}`, "wrong");
    }
  });

  nextBtn.addEventListener("click", () => {
    if (!questions.length) return;
    currentIndex = (currentIndex + 1) % questions.length;
    renderQuestion();
  });

  answerEl.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      checkBtn.click();
    }
  });

  function renderQuestion() {
    const current = questions[currentIndex];
    counterEl.textContent = `Question ${currentIndex + 1} of ${questions.length}`;
    questionEl.textContent = current.question;
    answerEl.value = "";
    feedbackEl.hidden = true;
    feedbackEl.textContent = "";
    answerEl.focus();
  }

  function showFeedback(message, type) {
    feedbackEl.hidden = false;
    feedbackEl.className = `one-line-feedback ${type}`;
    feedbackEl.textContent = message;
  }

  function showMessage(message) {
    questionEl.textContent = message;
    answerEl.disabled = true;
    checkBtn.disabled = true;
    nextBtn.disabled = true;
  }

  function normalize(value) {
    return String(value || "")
      .trim()
      .toLowerCase()
      .replace(/\s+/g, " ");
  }
});
