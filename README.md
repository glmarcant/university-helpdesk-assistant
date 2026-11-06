# Bocconi Student Assistant (RAG demo)

Hackathon prototype built with the [DataPizza AI](https://pypi.org/project/datapizza-ai/) framework: a chatbot that answers student questions with retrieval-augmented generation (RAG) over university documents, plus a human-in-the-loop escalation flow that drafts an email to the helpdesk.

The assistant is designed to cover Bocconi student topics in general. This demo is limited to 3 documents about the exchange program.

**Demo video:** [https://1drv.ms/v/c/60e1f9f4de0836c8/IQBv-78-qzjKTYyDZPvICERjAaVt1CEv-ksJbmxnbya3BiI?e=gPCdpy]

## How it works

**1. Ingestion** (`backend/ingestion_pipeline.py`, run once)
PDFs in `data/` are parsed with Docling, split into chunks of at most 1000 characters, embedded with OpenAI `text-embedding-3-small` (1536 dimensions) and stored in a Qdrant collection together with their source filename.

**2. Question answering** (`backend/retrieval_pipeline.py`)
A DataPizza `DagPipeline` chains five steps:
1. `gpt-4o-mini` rewrites the user question to improve retrieval
2. the rewritten question is embedded
3. the 3 most similar chunks are retrieved from Qdrant
4. the chunks and the original question are placed in the prompt
5. `gpt-4o-mini` generates the answer

**3. Helpdesk escalation** (`backend/email_utils.py`)
After each answer, the user can ask to contact the helpdesk. They enter first name, last name and student ID, and `gpt-4o-mini` drafts a formal email (subject and body) that includes the original question and the chatbot's answer. The draft is shown as a preview before anything would be sent.

**API** (`backend/main.py`, FastAPI): `POST /api/chat`, `POST /api/escalate`, `GET /health`.
**Frontend** (`frontend/`): a plain HTML/CSS/JS chat widget.

## Setup

Requirements: Python 3.10+, an OpenAI API key, and a Qdrant instance reachable over HTTPS (for example Qdrant Cloud).

```
python -m venv venv
venv\Scripts\activate          # macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
copy .env.example .env         # macOS/Linux: cp .env.example .env
```

Fill in `.env`, put your own PDFs in `data/` (the original documents are not included in this repository), then from the project root:

```
python backend/ingestion_pipeline.py    # run once: creates the collection and indexes the PDFs
python backend/main.py                  # starts the API on http://127.0.0.1:8000
```

Open `frontend/bocconi.html` in the browser. The first ingestion run may take a while because Docling downloads its models.

## Known limitations

- Tested on 3 documents only. There is no quantitative evaluation of answer quality yet, and retrieval quality with many more documents is untested.
- The prompt does not instruct the model to answer only from the retrieved chunks, so it can also answer from general knowledge.
- The source filename is stored as metadata but answers do not cite sources.
- The "Send Email" button is simulated: the email draft is generated, but no email is sent.
- Student name and ID are sent to OpenAI to generate the draft.
- The frontend calls the backend at a hardcoded `http://127.0.0.1:8000`, and CORS is open to all origins: suitable for local demos only.
- The ingestion script creates the collection, so running it twice fails unless the collection is deleted first.

## Possible improvements

- Ground the prompt in the retrieved context and return source citations
- Build a small question set with known answers to measure answer quality
- Filter retrieval by topic using document metadata
- Send the email for real after user confirmation, and let the user edit the draft
- Make the API URL and CORS settings configurable