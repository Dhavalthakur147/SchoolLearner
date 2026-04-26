document.addEventListener("DOMContentLoaded", () => {
  const quizRoot = document.getElementById("quiz-container");
  if (!quizRoot) {
    return;
  }

  const subject = quizRoot.dataset.subject || getSubjectFromPath();
  const subjectTitle = quizRoot.dataset.subjectTitle || "Quiz";
  const questionCounterEl = document.getElementById("question-counter");
  const timerEl = document.getElementById("timer");
  const progressBarEl = document.getElementById("progress-bar");
  const questionEl = document.getElementById("question");
  const optionsEl = document.getElementById("options");
  const nextBtn = document.getElementById("next-btn");
  const randomModeEl = document.getElementById("random-mode");
  const quizContentEl = document.getElementById("quiz-content");
  const resultEl = document.getElementById("result");

  let questions = [];
  let currentIndex = 0;
  let score = 0;
  let selectedAnswer = null;
  let userAnswers = [];
  let timeLeft = 10 * 60;
  let timerId = null;
  let isRandomMode = true;

  if (!subject || !questionEl || !optionsEl || !nextBtn) {
    showError("Quiz setup is incomplete. Please refresh the page.");
    return;
  }

  initializeQuiz();

  async function initializeQuiz() {
    setLoadingState(true);
    isRandomMode = randomModeEl ? !!randomModeEl.checked : true;
    try {
      const response = await fetch(
        `/api/questions/${encodeURIComponent(subject)}?count=10&mode=${isRandomMode ? "random" : "sequential"}`
      );
      const payload = await response.json().catch(() => ({}));

      if (!response.ok) {
        const errorMessage = payload.error || "Unable to load questions right now.";
        showError(errorMessage);
        return;
      }

      const normalized = Array.isArray(payload)
        ? payload.filter((item) => item && item.question && Array.isArray(item.options))
        : [];

      if (!normalized.length) {
        showError("No questions are available for this subject yet.");
        return;
      }

      questions = normalized;
      bindEvents();
      if (randomModeEl) {
        randomModeEl.disabled = true;
      }
      startTimer();
      renderCurrentQuestion();
    } catch (error) {
      showError("Could not connect to server. Please try again.");
    } finally {
      setLoadingState(false);
    }
  }

  function bindEvents() {
    nextBtn.addEventListener("click", () => {
      if (selectedAnswer === null) {
        alert("Please select an option first.");
        return;
      }

      const current = questions[currentIndex];
      const selectedIndex = Number(selectedAnswer);
      const isCorrect = selectedIndex === Number(current.answer);
      if (isCorrect) {
        score += 1;
      }
      userAnswers.push({
        question: current.question,
        options: current.options,
        selectedIndex,
        correctIndex: Number(current.answer),
        explanation: current.explanation || "",
      });

      currentIndex += 1;
      if (currentIndex >= questions.length) {
        finishQuiz();
        return;
      }

      renderCurrentQuestion();
    });
  }

  function renderCurrentQuestion() {
    const current = questions[currentIndex];
    selectedAnswer = null;

    questionCounterEl.textContent = `Question ${currentIndex + 1} of ${questions.length}`;
    questionEl.textContent = current.question;
    progressBarEl.style.width = `${(currentIndex / questions.length) * 100}%`;
    nextBtn.textContent = currentIndex === questions.length - 1 ? "Submit Quiz" : "Next Question";

    optionsEl.innerHTML = "";
    current.options.forEach((optionText, idx) => {
      const wrapper = document.createElement("label");
      wrapper.className = "option";

      const radio = document.createElement("input");
      radio.type = "radio";
      radio.name = "quiz-option";
      radio.value = String(idx);
      radio.addEventListener("change", () => {
        selectedAnswer = radio.value;
      });

      const text = document.createElement("span");
      text.textContent = optionText;

      wrapper.appendChild(radio);
      wrapper.appendChild(text);
      optionsEl.appendChild(wrapper);
    });
  }

  function finishQuiz() {
    stopTimer();
    progressBarEl.style.width = "100%";

    const total = questions.length;
    const percentage = total ? Math.round((score / total) * 1000) / 10 : 0;
    const reviewHtml = buildReviewHtml(userAnswers);

    quizContentEl.style.display = "none";
    resultEl.style.display = "block";
    resultEl.innerHTML = `
      <div class="quiz-result">
        <h2>${subjectTitle} Quiz Completed</h2>
        <p><strong>Mode:</strong> ${isRandomMode ? "Random" : "Sequential"}</p>
        <p><strong>Score:</strong> ${score} / ${total}</p>
        <p><strong>Percentage:</strong> ${percentage}%</p>
        <div class="actions">
          <a class="btn" href="/quiz/${subject}">Try Again</a>
          <a class="btn btn-outline" href="/">Back to Home</a>
        </div>
        <hr style="margin: 16px 0; border: 0; border-top: 1px solid #dce7e2;">
        <h3>Answer Review</h3>
        ${reviewHtml}
      </div>
    `;

    void saveProgress(score, total);
  }

  async function saveProgress(finalScore, totalQuestions) {
    if (!totalQuestions) return;
    try {
      await fetch("/api/quiz/progress", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          subject,
          score: finalScore,
          total_questions: totalQuestions,
        }),
      });
    } catch (error) {
      // Ignore save errors for guest users or temporary network issues.
    }
  }

  function startTimer() {
    updateTimerUI();
    timerId = window.setInterval(() => {
      timeLeft -= 1;
      if (timeLeft <= 0) {
        timeLeft = 0;
        updateTimerUI();
        finishQuiz();
        return;
      }
      updateTimerUI();
    }, 1000);
  }

  function stopTimer() {
    if (timerId) {
      window.clearInterval(timerId);
      timerId = null;
    }
  }

  function updateTimerUI() {
    if (!timerEl) return;
    const minutes = Math.floor(timeLeft / 60)
      .toString()
      .padStart(2, "0");
    const seconds = (timeLeft % 60).toString().padStart(2, "0");
    timerEl.textContent = `Time Left: ${minutes}:${seconds}`;
  }

  function showError(message) {
    if (quizContentEl) {
      quizContentEl.style.display = "none";
    }
    if (resultEl) {
      resultEl.style.display = "block";
      resultEl.innerHTML = `
        <div class="quiz-result">
          <h2>Unable to Start Quiz</h2>
          <p>${escapeHtml(message)}</p>
          <div class="actions">
            <a class="btn" href="/quiz/${subject}">Retry</a>
            <a class="btn btn-outline" href="/">Back to Home</a>
          </div>
        </div>
      `;
    }
  }

  function setLoadingState(isLoading) {
    if (!nextBtn) return;
    nextBtn.disabled = isLoading;
    nextBtn.textContent = isLoading ? "Loading..." : "Next Question";
  }

  function buildReviewHtml(answerRows) {
    if (!Array.isArray(answerRows) || !answerRows.length) {
      return "<p>No answers to review.</p>";
    }
    const letters = ["A", "B", "C", "D"];
    return answerRows
      .map((row, idx) => {
        const selectedText = row.selectedIndex >= 0 ? `${letters[row.selectedIndex]}. ${escapeHtml(row.options[row.selectedIndex] || "")}` : "Not answered";
        const correctText = `${letters[row.correctIndex]}. ${escapeHtml(row.options[row.correctIndex] || "")}`;
        const correct = row.selectedIndex === row.correctIndex;
        const borderColor = correct ? "#9bdcbe" : "#f2b6b6";
        const bgColor = correct ? "#f1fcf6" : "#fff5f5";
        const explanationHtml = row.explanation
          ? `<p style="margin:6px 0 0 0; color:#35544b;"><strong>Explanation:</strong> ${escapeHtml(row.explanation)}</p>`
          : "";
        return `
          <div style="border:1px solid ${borderColor}; background:${bgColor}; border-radius:10px; padding:10px; margin-bottom:10px;">
            <p style="margin:0 0 6px 0; font-weight:700;">Q${idx + 1}. ${escapeHtml(row.question)}</p>
            <p style="margin:0; color:#2f4f46;"><strong>Your Answer:</strong> ${selectedText}</p>
            <p style="margin:4px 0 0 0; color:#2f4f46;"><strong>Correct Answer:</strong> ${correctText}</p>
            ${explanationHtml}
          </div>
        `;
      })
      .join("");
  }

  function getSubjectFromPath() {
    const parts = window.location.pathname.split("/").filter(Boolean);
    return parts.length >= 2 && parts[0] === "quiz" ? parts[1] : "";
  }

  function escapeHtml(input) {
    return String(input)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;");
  }
});
