document.addEventListener("DOMContentLoaded", function () {
    const chatForm = document.getElementById("chatForm");
    const userInput = document.getElementById("userInput");
    const chatWindow = document.getElementById("chatWindow");
    const plusBtn = document.getElementById("plusBtn");
    const quickPanel = document.getElementById("quickPanel");
    const quickChips = document.getElementById("quickChips");
    const clearBtn = document.getElementById("clearBtn");

    // Check whether the chat elements exist
    if (!chatForm || !userInput || !chatWindow) {
        console.error("Chat elements not found!");
        return;
    }

    // ---------- Chat messages ----------

    const THUMB_ICON =
        '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">' +
        '<path d="M1 21h4V9H1v12zm22-11c0-1.1-.9-2-2-2h-6.31l.95-4.57.03-.32c0-.41-.17-.79-.44-1.06L14.17 1 7.59 7.59C7.22 7.95 7 8.45 7 9v10c0 1.1.9 2 2 2h9c.83 0 1.54-.5 1.84-1.22l3.02-7.05c.09-.23.14-.47.14-.73v-2z"/>' +
        '</svg>';

    // Display a message in the chat window.
    // For a real bot reply, pass feedbackFor = the user's message to show 👍 👎.
    function addMessage(message, sender, feedbackFor) {
        const messageDiv = document.createElement("div");
        messageDiv.classList.add("message", sender);

        const bubble = document.createElement("div");
        bubble.classList.add("bubble");
        bubble.textContent = message;

        if (feedbackFor) {
            const column = document.createElement("div");
            column.classList.add("msg-col");
            column.appendChild(bubble);
            column.appendChild(createFeedback(feedbackFor, message));
            messageDiv.appendChild(column);
        } else {
            messageDiv.appendChild(bubble);
        }

        chatWindow.appendChild(messageDiv);
        chatWindow.scrollTop = chatWindow.scrollHeight;
    }

    // Build the like / dislike buttons for one bot reply
    function createFeedback(userMessage, botReply) {
        const box = document.createElement("div");
        box.classList.add("feedback");
        box.setAttribute("role", "group");
        box.setAttribute("aria-label", "Rate this reply");

        const likeBtn = makeFeedbackButton("like", "This reply was helpful");
        const dislikeBtn = makeFeedbackButton("dislike", "This reply was not helpful");
        const note = document.createElement("span");
        note.classList.add("fb-note");
        note.setAttribute("aria-live", "polite");

        async function send(rating, clickedBtn) {
            likeBtn.disabled = true;
            dislikeBtn.disabled = true;
            try {
                const response = await fetch("/feedback", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        rating: rating,
                        user_message: userMessage,
                        bot_reply: botReply
                    })
                });
                if (response.status === 401) {
                    window.location.href = "/login";
                    return;
                }
                if (!response.ok) {
                    throw new Error("Server error: " + response.status);
                }
                clickedBtn.classList.add("active");
                note.textContent = "Thanks for your feedback";
            } catch (error) {
                console.error("Feedback error:", error);
                likeBtn.disabled = false;
                dislikeBtn.disabled = false;
                note.textContent = "Could not save. Try again.";
            }
        }

        likeBtn.addEventListener("click", function () { send("like", likeBtn); });
        dislikeBtn.addEventListener("click", function () { send("dislike", dislikeBtn); });

        box.appendChild(likeBtn);
        box.appendChild(dislikeBtn);
        box.appendChild(note);
        return box;
    }

    function makeFeedbackButton(kind, label) {
        const button = document.createElement("button");
        button.type = "button";
        button.classList.add("fb-btn", kind);
        button.setAttribute("aria-label", label);
        button.title = label;
        button.innerHTML = THUMB_ICON;
        return button;
    }

    // Display a typing indicator
    function showTyping() {
        const typingDiv = document.createElement("div");
        typingDiv.id = "typingIndicator";
        typingDiv.classList.add("message", "bot");

        const bubble = document.createElement("div");
        bubble.classList.add("bubble");
        bubble.textContent = "Thinking...";

        typingDiv.appendChild(bubble);
        chatWindow.appendChild(typingDiv);
        chatWindow.scrollTop = chatWindow.scrollHeight;
    }

    // Remove the typing indicator
    function removeTyping() {
        const indicator = document.getElementById("typingIndicator");

        if (indicator) {
            indicator.remove();
        }
    }

    // Send the message to the Flask backend.
    // Returns { text, ok } so that errors do not get 👍 👎 buttons.
    async function getBotResponse(message) {
        try {
            const response = await fetch("/chat", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ message: message })
            });

            if (response.status === 401) {
                window.location.href = "/login";
                return { text: "Please log in again.", ok: false };
            }

            if (!response.ok) {
                throw new Error("Server error: " + response.status);
            }

            const data = await response.json();

            return {
                text: data.reply || "Sorry, I couldn't generate a response.",
                ok: Boolean(data.reply)
            };

        } catch (error) {
            console.error("Chat error:", error);

            return {
                text: "Unable to connect. Please check that the server is running.",
                ok: false
            };
        }
    }

    // ---------- Quick symptoms (+ button) ----------

    const QUICK_SYMPTOMS = [
        "fever", "cough", "headache", "sore throat", "runny nose", "sneezing",
        "body ache", "fatigue", "nausea", "vomiting", "diarrhea", "stomach pain",
        "heartburn", "dizziness", "itchy eyes", "skin rash",
        "burning urination", "difficulty sleeping"
    ];

    let selected = [];
    let lastAutoText = "";

    function buildSentence() {
        if (selected.length === 0) {
            return "";
        }
        if (selected.length === 1) {
            return "I have " + selected[0];
        }
        return "I have " + selected.slice(0, -1).join(", ") + " and " +
               selected[selected.length - 1];
    }

    function toggleSymptom(symptom, chip) {
        const index = selected.indexOf(symptom);
        const wasSelected = index !== -1;
        const current = userInput.value.trim();
        const typedByUser = current !== "" && current !== lastAutoText;

        if (wasSelected) {
            selected.splice(index, 1);
        } else {
            selected.push(symptom);
        }
        chip.setAttribute("aria-pressed", String(!wasSelected));

        if (!typedByUser) {
            // the box is empty or still holds our own sentence: rebuild it
            lastAutoText = buildSentence();
            userInput.value = lastAutoText;
        } else if (!wasSelected) {
            // the user typed their own text: just add the symptom to it
            userInput.value = current + ", " + symptom;
        }
        userInput.focus();
    }

    function resetQuickSymptoms() {
        selected = [];
        lastAutoText = "";
        if (quickChips) {
            quickChips.querySelectorAll(".chip").forEach(function (chip) {
                chip.setAttribute("aria-pressed", "false");
            });
        }
    }

    function setPanelOpen(open) {
        quickPanel.hidden = !open;
        plusBtn.setAttribute("aria-expanded", String(open));
    }

    if (plusBtn && quickPanel && quickChips) {
        QUICK_SYMPTOMS.forEach(function (symptom) {
            const chip = document.createElement("button");
            chip.type = "button";
            chip.classList.add("chip");
            chip.textContent = symptom;
            chip.setAttribute("aria-pressed", "false");
            chip.addEventListener("click", function () {
                toggleSymptom(symptom, chip);
            });
            quickChips.appendChild(chip);
        });

        plusBtn.addEventListener("click", function () {
            setPanelOpen(quickPanel.hidden);
        });

        // Esc closes the panel
        document.addEventListener("keydown", function (event) {
            if (event.key === "Escape" && !quickPanel.hidden) {
                setPanelOpen(false);
                plusBtn.focus();
            }
        });
    }

    // ---------- Saved chat history ----------

    // Load the user's old messages (saved in the database) when the page opens
    async function loadHistory() {
        try {
            const response = await fetch("/history");

            if (response.status === 401) {
                window.location.href = "/login";
                return;
            }
            if (!response.ok) {
                return;
            }

            const data = await response.json();
            (data.messages || []).forEach(function (item) {
                addMessage(item.text, item.sender);
            });
        } catch (error) {
            console.error("History error:", error);
        }
    }

    // Keep only the first greeting message
    function resetChatWindow() {
        while (chatWindow.children.length > 1) {
            chatWindow.removeChild(chatWindow.lastChild);
        }
    }

    if (clearBtn) {
        clearBtn.addEventListener("click", async function () {
            if (!window.confirm("Delete your saved chat history?")) {
                return;
            }
            try {
                const response = await fetch("/history/clear", { method: "POST" });

                if (response.status === 401) {
                    window.location.href = "/login";
                    return;
                }
                if (!response.ok) {
                    throw new Error("Server error: " + response.status);
                }
                resetChatWindow();
                resetQuickSymptoms();
                userInput.value = "";
            } catch (error) {
                console.error("Clear history error:", error);
                window.alert("Could not clear the chat. Please try again.");
            }
        });
    }

    loadHistory();

    // ---------- Handle the chat form submission ----------

    chatForm.addEventListener("submit", async function (event) {
        event.preventDefault();

        const message = userInput.value.trim();

        if (!message) {
            return;
        }

        addMessage(message, "user");

        userInput.value = "";
        userInput.disabled = true;
        resetQuickSymptoms();
        if (quickPanel) {
            setPanelOpen(false);
        }

        showTyping();

        const result = await getBotResponse(message);

        removeTyping();
        addMessage(result.text, "bot", result.ok ? message : null);

        userInput.disabled = false;
        userInput.focus();
    });
});