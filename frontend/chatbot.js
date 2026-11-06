// Chatbot popup functionality
const openBtn = document.getElementById("openChat");
const closeBtn = document.getElementById("closeChat");
const chatWindow = document.getElementById("chatWindow");
const sendBtn = document.getElementById("sendBtn");
const userInput = document.getElementById("userInput");
const chatMessages = document.getElementById("chatMessages");

openBtn.addEventListener("click", () => {
    chatWindow.classList.toggle("hidden");
});

closeBtn.addEventListener("click", () => {
    chatWindow.classList.add("hidden");
});

// Send message on Enter key
userInput.addEventListener("keypress", (e) => {
    if (e.key === "Enter") {
        e.preventDefault();
        sendBtn.click();
    }
});

sendBtn.addEventListener("click", () => {
    const question = userInput.value.trim();
    if (!question) return;

    addMessage("You", question);
    userInput.value = "";

    // Mostra "sto pensando..."
    addMessage("Assistant", "🤔 Searching for an answer...");

    // Chiamata al backend RAG
    fetch("http://127.0.0.1:8000/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: question })
    })
        .then((response) => {
            if (!response.ok) {
                throw new Error(`Server error: ${response.status}`);
            }
            return response.json();
        })
        .then((data) => {
            // Rimuovi il messaggio "sto pensando..."
            const lastMsg = chatMessages.lastChild;
            if (lastMsg && lastMsg.textContent.includes("🤔")) {
                lastMsg.remove();
            }

            // Add the real answer
            addMessage("Assistant", data.answer);

            // After each agent answer, ask user if they want to escalate to helpdesk
            showEscalationPrompt(data.answer, question);
        })
        .catch((err) => {
            // Rimuovi il messaggio "sto pensando..."
            const lastMsg = chatMessages.lastChild;
            if (lastMsg && lastMsg.textContent.includes("🤔")) {
                lastMsg.remove();
            }
            addMessage("Assistant", `❌ Error: ${err.message}`);
        });
});

function addMessage(sender, message) {
    const msgDiv = document.createElement("div");
    msgDiv.style.cssText =
        "margin: 8px 0; padding: 10px; border-radius: 6px; word-wrap: break-word; line-height: 1.4;";

    if (sender === "You") {
        msgDiv.style.cssText +=
            "background-color: #004080; color: white; text-align: right; margin-left: 20px;";
    } else {
        msgDiv.style.cssText +=
            "background-color: #f0f0f0; color: #333; margin-right: 20px;";
    }

    // Formatta il messaggio con supporto per markdown-like formatting
    const formattedMessage = formatMessage(message);
    msgDiv.innerHTML = `<strong>${sender}:</strong><br>${formattedMessage}`;

    chatMessages.appendChild(msgDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function formatMessage(message) {
    // Escape HTML per sicurezza
    let formatted = escapeHtml(message);

    // Converti **testo** in <strong>testo</strong> (bold)
    formatted = formatted.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");

    // Converti *testo* in <em>testo</em> (italic)
    formatted = formatted.replace(/\*(.*?)\*/g, "<em>$1</em>");

    // Converti numeri seguiti da punto in liste (1. -> • )
    formatted = formatted.replace(/^\d+\.\s+/gm, "• ");

    // Converti nuove linee in <br>
    formatted = formatted.replace(/\n/g, "<br>");

    return formatted;
}

function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
}

// --- Escalation UI/functions ---

function showEscalationPrompt(answerText, originalQuestion) {
    const promptDiv = document.createElement("div");
    promptDiv.style.cssText =
        "margin: 8px 0; padding: 8px; border-radius:6px; background:#fff7e6; border:1px solid #ffd27a;";

    const msg = document.createElement("div");
    msg.innerHTML =
        "<strong>Assistant:</strong><br>Would you like to send an email to the helpdesk for more information?";
    promptDiv.appendChild(msg);

    const btnContainer = document.createElement("div");
    btnContainer.style.cssText = "margin-top:8px; display:flex; gap:8px;";

    const yesBtn = document.createElement("button");
    yesBtn.textContent = "Yes";
    yesBtn.style.cssText =
        "background:#004080;color:#fff;border:none;padding:6px 10px;border-radius:4px;cursor:pointer;";
    yesBtn.addEventListener("click", () => {
        promptDiv.remove();
        showEscalationForm(originalQuestion, answerText);
    });

    const noBtn = document.createElement("button");
    noBtn.textContent = "No";
    noBtn.style.cssText =
        "background:#e0e0e0;color:#111;border:none;padding:6px 10px;border-radius:4px;cursor:pointer;";
    noBtn.addEventListener("click", () => {
        promptDiv.remove();
        addMessage("Assistant", "Okay — if you need more help, just ask!");
    });

    btnContainer.appendChild(yesBtn);
    btnContainer.appendChild(noBtn);
    promptDiv.appendChild(btnContainer);

    chatMessages.appendChild(promptDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function showEscalationForm(originalQuestion, answerText) {
    const formDiv = document.createElement("div");
    formDiv.style.cssText =
        "margin:8px 0; padding:10px; border-radius:6px; background:#f7f7ff; border:1px solid #d0d0ff;";

    formDiv.innerHTML = `
        <strong>Send to Helpdesk</strong><br>
        <div style="margin-top:8px; display:flex; flex-direction:column; gap:6px;">
            <input id="es_name" placeholder="First name" style="padding:6px; border-radius:4px; border:1px solid #ccc;" />
            <input id="es_surname" placeholder="Last name" style="padding:6px; border-radius:4px; border:1px solid #ccc;" />
            <input id="es_id" placeholder="Student ID" style="padding:6px; border-radius:4px; border:1px solid #ccc;" />
            <input id="es_email" placeholder="Email (optional)" style="padding:6px; border-radius:4px; border:1px solid #ccc;" />
        </div>
        <div style="margin-top:8px; display:flex; gap:8px;">
            <button id="es_submit" style="background:#007b00;color:#fff;border:none;padding:6px 10px;border-radius:4px;cursor:pointer;">Send</button>
            <button id="es_cancel" style="background:#e0e0e0;color:#111;border:none;padding:6px 10px;border-radius:4px;cursor:pointer;">Cancel</button>
        </div>
    `;

    chatMessages.appendChild(formDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;

    const submitBtn = formDiv.querySelector("#es_submit");
    const cancelBtn = formDiv.querySelector("#es_cancel");

    cancelBtn.addEventListener("click", () => {
        formDiv.remove();
        addMessage("Assistant", "No problem — the message was not sent.");
    });

    submitBtn.addEventListener("click", async () => {
        const name = document.getElementById("es_name").value.trim();
        const surname = document.getElementById("es_surname").value.trim();
        const studentId = document.getElementById("es_id").value.trim();
        const email = document.getElementById("es_email").value.trim();

        if (!name || !surname || !studentId) {
            alert("Please provide your first name, last name, and student ID.");
            return;
        }

        // Show a small loading indicator
        submitBtn.disabled = true;
        submitBtn.textContent = "Sending...";

        try {
            const resp = await fetch("http://127.0.0.1:8000/api/escalate", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    query: originalQuestion,
                    name: name,
                    surname: surname,
                    student_id: studentId,
                    email: email,
                    rag_answer: answerText
                })
            });

            if (!resp.ok) {
                throw new Error(`Server error: ${resp.status}`);
            }

            const data = await resp.json();

            // data is expected to be the generated email payload: { to, cc, subject, body }
            formDiv.remove();
            showEmailPreview(data, {
                name,
                surname,
                studentId,
                email: email,
                originalQuestion,
                answerText
            });
        } catch (err) {
            submitBtn.disabled = false;
            submitBtn.textContent = "Send";
            alert("Error sending escalation: " + err.message);
        }
    });
}

function showEmailPreview(emailPayload, studentInfo) {
    const previewDiv = document.createElement("div");
    previewDiv.style.cssText =
        "margin:8px 0; padding:10px; border-radius:6px; background:#fff; border:1px solid #ccc;";

    let subject = emailPayload.subject || "No subject";
    let body = emailPayload.body || "No body";

    // If body is a JSON string, try to parse it
    if (typeof body === "string" && body.trim().startsWith("{")) {
        try {
            const parsed = JSON.parse(body);
            body = parsed.body || body;
        } catch (e) {
            // Not JSON, use as-is
        }
    }

    // Escape and format
    subject = escapeHtml(subject);
    body = escapeHtml(body);

    // Convert \n to actual line breaks for display
    body = body.replace(/\\n/g, "\n");

    previewDiv.innerHTML = `
        <strong>Email preview</strong>
        <div style="margin-top:8px"><strong>To:</strong> ${escapeHtml(emailPayload.to || "")}</div>
        <div style="margin-top:4px"><strong>Cc:</strong> ${escapeHtml(emailPayload.cc || "")}</div>
        <div style="margin-top:8px">
            <strong>Subject:</strong><br>
            <div style="background:#f7f7f7;padding:8px;border-radius:4px;">${subject}</div>
        </div>
        <div style="margin-top:8px">
            <strong>Body:</strong><br>
            <div style="background:#f7f7f7;padding:10px;border-radius:4px; white-space:pre-wrap;">${body}</div>
        </div>
        <div style="margin-top:10px; display:flex; gap:8px;">
            <button id="preview_send" style="background:#007b00;color:#fff;border:none;padding:6px 10px;border-radius:4px;cursor:pointer;">Send Email</button>
            <button id="preview_cancel" style="background:#e0e0e0;color:#111;border:none;padding:6px 10px;border-radius:4px;cursor:pointer;">Cancel</button>
        </div>
    `;

    chatMessages.appendChild(previewDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;

    const sendBtn = previewDiv.querySelector("#preview_send");
    const cancelBtn = previewDiv.querySelector("#preview_cancel");

    cancelBtn.addEventListener("click", () => {
        previewDiv.remove();
        addMessage("Assistant", "Email cancelled. No email was sent.");
    });

    // FULL SIMULATION: do not call backend, just show success
    sendBtn.addEventListener("click", async () => {
        sendBtn.disabled = true;
        sendBtn.textContent = "Sending...";
        setTimeout(() => {
            previewDiv.remove();
            addMessage("Assistant", "✅ Email sent.");
        }, 900);
    });
}
