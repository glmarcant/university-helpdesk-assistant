# FastAPI backend server for DataPizza RAG chatbot
# Connects frontend to the retrieval pipeline for intelligent Q&A

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
import logging

# Import the RAG pipeline
from retrieval_pipeline import answer_question
from email_utils import build_helpdesk_email

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="DataPizza RAG API",
    description="University Q&A chatbot powered by RAG",
    version="1.0.0",
)

# Enable CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response models
class QueryRequest(BaseModel):
    """Chat query request model"""
    query: str


class QueryResponse(BaseModel):
    """Chat query response model"""
    answer: str


@app.get("/", tags=["Health"])
async def root():
    """Root endpoint - health check"""
    return {
        "status": "running",
        "service": "DataPizza RAG API",
        "endpoints": {
            "chat": "POST /api/chat",
            "docs": "/docs",
        },
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "DataPizza RAG API"}


@app.post("/api/chat", response_model=QueryResponse, tags=["Chat"])
async def chat_endpoint(request: QueryRequest):
    """
    Main chat endpoint - accepts user query and returns RAG-powered response

    Args:
        request: QueryRequest containing the user's question

    Returns:
        QueryResponse with the generated answer

    Raises:
        HTTPException: If query processing fails
    """
    if not request.query or not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    try:
        logger.info(f"Processing query: {request.query[:50]}...")

        # Run the blocking RAG pipeline in a thread pool
        answer = await asyncio.to_thread(answer_question, request.query)

        logger.info("Query processed successfully")
        return QueryResponse(answer=answer)

    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing query: {str(e)}",
        )


@app.post("/ask-agent", response_model=QueryResponse, tags=["Chat"])
async def ask_agent_endpoint(request: dict):
    """
    Legacy endpoint for frontend compatibility - accepts question and returns answer

    Args:
        request: Dictionary with 'question' key

    Returns:
        QueryResponse with the generated answer
    """
    # Extract question from request
    question = request.get("question") or request.get("query")

    if not question or not str(question).strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    try:
        logger.info(f"Processing question: {question[:50]}...")

        # Run the blocking RAG pipeline in a thread pool
        answer = await asyncio.to_thread(answer_question, question)

        # Clean the answer - extract text from ClientResponse object
        answer_text = clean_answer(answer)

        logger.info("Question processed successfully")
        return QueryResponse(answer=answer_text)

    except Exception as e:
        logger.error(f"Error processing question: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing question: {str(e)}",
        )


def clean_answer(answer):
    """
    Extract clean text from DataPizza ClientResponse object.
    Handles the pattern: ClientResponse(content=[TextBlock(content='...')])

    Args:
        answer: Response from RAG pipeline (DataPizza ClientResponse)

    Returns:
        Clean string text only
    """
    # If it's already a string, return it
    if isinstance(answer, str):
        return answer.strip()

    # If it's a dict-like object, try to extract content
    if isinstance(answer, dict):
        if "content" in answer:
            return str(answer["content"]).strip()
        if "answer" in answer:
            return str(answer["answer"]).strip()
        if "text" in answer:
            return str(answer["text"]).strip()

    # Try to access as object with attributes (ClientResponse)
    try:
        if hasattr(answer, "content"):
            content = answer.content

            # If content is a list of TextBlock objects
            if isinstance(content, list) and len(content) > 0:
                first_item = content[0]

                # Try to get text from TextBlock
                if hasattr(first_item, "content"):
                    text = first_item.content
                    return str(text).strip()
                elif hasattr(first_item, "text"):
                    text = first_item.text
                    return str(text).strip()
    except Exception as e:
        logger.warning(f"Error accessing as object: {e}")

    # Fallback: parse string representation
    answer_str = str(answer)

    # Extract text between TextBlock(content='...')
    if "TextBlock(content=" in answer_str:
        try:
            start_pattern = "TextBlock(content="
            start_idx = answer_str.find(start_pattern)
            if start_idx != -1:
                start_idx += len(start_pattern)

                # Find the quote that starts the content
                if start_idx < len(answer_str) and answer_str[start_idx] in ("'", '"'):
                    quote_char = answer_str[start_idx]
                    start_idx += 1

                    # Find the closing quote (handling escaped quotes)
                    end_idx = start_idx
                    while end_idx < len(answer_str):
                        if answer_str[end_idx] == quote_char:
                            extracted = answer_str[start_idx:end_idx]
                            return extracted.strip()
                        end_idx += 1
        except Exception as e:
            logger.warning(f"Error parsing TextBlock: {e}")

    logger.warning("Could not extract clean text, returning raw string")
    return answer_str.strip()


@app.post("/api/escalate", tags=["Chat"])
async def escalate_endpoint(request: dict):
    """
    Escalation endpoint - generates email payload for helpdesk when user wants to escalate

    Expected request body:
    {
        "query": "user's original question",
        "name": "student name",
        "surname": "student surname",
        "student_id": "student ID",
        "email": "student email (optional)"
    }
    """
    try:
        # Extract form fields
        query = request.get("query", "")
        name = request.get("name", "")
        surname = request.get("surname", "")
        student_id = request.get("student_id", "")
        student_email = request.get("email", "")

        if not query:
            raise HTTPException(status_code=400, detail="Missing original query")

        logger.info(f"Generating helpdesk email for {name} {surname} ({student_id})")

        # Generate email payload using the LLM (email_utils) - this does NOT send
        email_payload = build_helpdesk_email(
            first_name=name,
            last_name=surname,
            student_id=student_id,
            student_email=student_email,
            user_question=query,
            rag_answer=request.get("rag_answer", ""),
        )

        # Return the generated payload to the frontend for preview
        return email_payload

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating helpdesk email: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error generating email: {str(e)}",
        )


@app.on_event("startup")
async def startup_event():
    """Run on application startup"""
    logger.info("DataPizza RAG API starting...")
    logger.info("Backend ready for frontend connections")


@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown"""
    logger.info("DataPizza RAG API shutting down...")


if __name__ == "__main__":
    import uvicorn

    # Run the server
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=False,
        log_level="info",
    )
