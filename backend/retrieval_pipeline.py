from datapizza.clients.openai import OpenAIClient
from datapizza.embedders.openai import OpenAIEmbedder
from datapizza.modules.prompt import ChatPromptTemplate
from datapizza.modules.rewriters import ToolRewriter
from datapizza.pipeline import DagPipeline
from datapizza.vectorstores.qdrant import QdrantVectorstore

from config import (
    OPENAI_API_KEY,
    QDRANT_HOST,
    QDRANT_PORT,
    QDRANT_API_KEY,
    COLLECTION_NAME,   # es. "my_documents"
)

openai_client = OpenAIClient(
    model="gpt-4o-mini",
    api_key=OPENAI_API_KEY
)

query_rewriter = ToolRewriter(
    client=openai_client,
    system_prompt="Rewrite the user’s query to maximize retrieval accuracy while preserving its meaning. Clarify intent, expand important keywords, and avoid adding new assumptions."
)

embedder = OpenAIEmbedder(
    api_key=OPENAI_API_KEY,
    model_name="text-embedding-3-small"
)

# Use the same qdrant of ingestion (prefer host and port instead of location when possible)
retriever = QdrantVectorstore(
    host=QDRANT_HOST,
    port=QDRANT_PORT,
    api_key=QDRANT_API_KEY,
    https=True,   # importante perché l’endpoint è https
)



prompt_template = ChatPromptTemplate(
    user_prompt_template="User question: {{user_prompt}}\n:",
    retrieval_prompt_template="Retrieved content:\n{% for chunk in chunks %}{{ chunk.text }}\n{% endfor %}"
)

dag_pipeline = DagPipeline()
dag_pipeline.add_module("rewriter", query_rewriter)
dag_pipeline.add_module("embedder", embedder)
dag_pipeline.add_module("retriever", retriever)
dag_pipeline.add_module("prompt", prompt_template)
dag_pipeline.add_module("generator", openai_client)

dag_pipeline.connect("rewriter", "embedder", target_key="text")
dag_pipeline.connect("embedder", "retriever", target_key="query_vector")
dag_pipeline.connect("retriever", "prompt", target_key="chunks")
dag_pipeline.connect("prompt", "generator", target_key="memory")

from email_utils import build_helpdesk_email

def clean_response_with_slicing(response_str: str) -> str:
    prefix = "ClientResponse(content=[TextBlock(content="
    suffix = ")], delta=None, stop_reason=completed)"

    # Prova a togliere prefisso e suffisso solo se ci sono davvero
    if response_str.startswith(prefix) and response_str.endswith(suffix):
        # Rimuovi prefisso
        trimmed = response_str[len(prefix):]
        # Rimuovi suffisso
        trimmed = trimmed[:-len(suffix)]

        # Ora trimmed è qualcosa tipo "'risposta test'" oppure "\"risposta test\""
        if trimmed and trimmed[0] in ("'", '"') and trimmed[-1] == trimmed[0]:
            return trimmed[1:-1]  # togli le virgolette esterne

        return trimmed

    # Fallback: se per qualche motivo non matcha, restituisci l’intera stringa
    return response_str



def answer_question(query: str) -> str:
    result = dag_pipeline.run(
        {
            "rewriter": {"user_prompt": query},
            "prompt": {"user_prompt": query},
            "retriever": {
                "collection_name": COLLECTION_NAME,
                "k": 3,
            },
            "generator": {"input": query},
        }
    )
    response_str = str(result["generator"])
    clean_text = clean_response_with_slicing(response_str)
    return clean_text

'''# Test veloce
if __name__ == "__main__":
    # 1) simulate user question
    question = "Tell me how the exchange program works at Bocconi"

    # 2) call the RAG function
    rag_answer = answer_question(question)

    # 3) simulate the student pressing "yes, send an email"
    first_name = "Mario"
    last_name = "Rossi"
    student_id = "123456"
    student_email = "mario.rossi@studenti.unibocconi.it"

    # 4) now call build_helpdesk_email FROM email_utils
    email_payload = build_helpdesk_email(
        first_name=first_name,
        last_name=last_name,
        student_id=student_id,
        student_email=student_email,
        user_question=question,
        rag_answer=rag_answer,   # 👈 here is the connection
    )

    print("\n=== EMAIL READY FOR HELPDESK ===")
    print("To: ", email_payload["to"])
    print("Cc: ", email_payload["cc"])
    print("Subject: ", email_payload["subject"])
    print("Body:\n", email_payload["body"])
'''
