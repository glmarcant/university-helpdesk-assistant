# email_utils.py

import json
import re
from datapizza.clients.openai import OpenAIClient

from config import (
    OPENAI_API_KEY,
    HELPDESK_EMAIL,
)

# LLM client dedicated to writing formal emails
email_client = OpenAIClient(
    model="gpt-4o-mini",
    api_key=OPENAI_API_KEY,
    system_prompt=(
        "You are an assistant that writes formal emails in English to the university helpdesk. "
        "You must be polite, clear, and concise. "
        "Always include the student's name, surname, and student ID (matricola)."
    ),
)


def build_helpdesk_email(
    first_name: str,
    last_name: str,
    student_id: str,
    student_email: str,
    user_question: str,
    rag_answer: str,
) -> dict:
    """
    Does NOT send any email: it only generates a ready-to-use email payload.

    Returns a dict:
    {
        "to": ...,
        "cc": ...,
        "subject": ...,
        "body": ...
    }
    which the frontend can show to the user or turn into a `mailto:` link.
    """

    prompt = f"""
    Student data:
    - First name: {first_name}
    - Last name: {last_name}
    - Student ID (matricola): {student_id}
    - Email: {student_email}

    Original student question:
    {user_question}

    Answer given by the chatbot (based on official documents):
    {rag_answer}

    Write a formal email in English to the university helpdesk to ask for clarifications.

    The email must:
    - start with a formal greeting (e.g. "Dear Student Services Office,")
    - briefly explain the context
    - restate the student's doubt / question
    - politely ask for an answer or operational guidance
    - end with a polite closing formula
    - be signed with the student's name, surname, student ID, and email.

    Respond in JSON with EXACTLY these keys:
    - "subject": a short and clear subject line (string)
    - "body": the full email text (string)
    """

    resp = email_client.invoke(prompt)

    raw = resp.text.strip()

    # 1) Se il modello ha messo i ```json ... ``` li togliamo
    if raw.startswith("```"):
        lines = raw.splitlines()
        # rimuovi la prima e l’ultima linea se iniziano/finiscono con ```
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        raw = "\n".join(lines).strip()

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        # Fallback se proprio non ci riesce
        data = {
            "subject": "Information request",
            "body": resp.text,
        }

    # Post-process subject and body to ensure consistent formatting
    subject = data.get("subject", "Information request")
    body_raw = data.get("body", "")

    # Normalize newlines and trim
    body = body_raw.replace("\r\n", "\n").strip()

    # If the model didn't include a formal greeting, add one
    if not re.match(r"(?i)^(dear|hello|hi)\b", body):
        body = "Dear Student Services Office,\n\n" + body

    # Final payload that the frontend can directly use
    email_payload = {
        "to": HELPDESK_EMAIL,
        "cc": student_email,
        "subject": subject.strip(),
        "body": body,
    }

    return email_payload
