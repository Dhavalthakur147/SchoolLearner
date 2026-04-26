document.addEventListener("DOMContentLoaded", () => {
  const widget = document.querySelector(".chatbot-widget");
  if (!widget) return;

  const toggle = widget.querySelector(".chatbot-toggle");
  const panel = widget.querySelector(".chatbot-panel");
  const close = widget.querySelector(".chatbot-close");
  const form = widget.querySelector("#chatbotForm");
  const input = widget.querySelector("#chatbotInput");
  const messages = widget.querySelector("#chatbotMessages");

  function setOpen(isOpen) {
    panel.hidden = !isOpen;
    toggle.setAttribute("aria-expanded", String(isOpen));
    if (isOpen) input.focus();
  }

  function addMessage(text, type) {
    const bubble = document.createElement("div");
    bubble.className = `chat-message ${type}`;
    bubble.textContent = text;
    messages.appendChild(bubble);
    messages.scrollTop = messages.scrollHeight;
    return bubble;
  }

  toggle.addEventListener("click", () => {
    setOpen(panel.hidden);
  });

  close.addEventListener("click", () => {
    setOpen(false);
  });

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const text = input.value.trim();
    if (!text) return;

    addMessage(text, "user");
    input.value = "";
    input.disabled = true;
    const thinking = addMessage("Thinking...", "bot");

    try {
      const response = await fetch("/api/chatbot", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ message: text }),
      });
      const data = await response.json();
      thinking.textContent = data.reply || data.error || "I could not answer that right now.";
    } catch (error) {
      thinking.textContent = "Network problem. Please try again.";
    } finally {
      input.disabled = false;
      input.focus();
      messages.scrollTop = messages.scrollHeight;
    }
  });
});
