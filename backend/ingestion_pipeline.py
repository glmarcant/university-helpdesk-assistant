from datapizza.clients.openai import OpenAIClient
from datapizza.core.vectorstore import VectorConfig
from datapizza.embedders import ChunkEmbedder
from datapizza.embedders.openai import OpenAIEmbedder
from datapizza.modules.captioners import LLMCaptioner
from datapizza.modules.parsers.docling import DoclingParser
from datapizza.modules.splitters import NodeSplitter
from datapizza.pipeline import IngestionPipeline
from datapizza.vectorstores.qdrant import QdrantVectorstore

from pathlib import Path

from config import (
    OPENAI_API_KEY,
    QDRANT_HOST,
    QDRANT_PORT,
    QDRANT_API_KEY,
    COLLECTION_NAME,
)

vectorstore = QdrantVectorstore(
    host=QDRANT_HOST,
    port=QDRANT_PORT,
    api_key=QDRANT_API_KEY,
    https=True,   
)

vectorstore.create_collection(
    COLLECTION_NAME,
    vector_config=[VectorConfig(name="embedding", dimensions=1536)],
)

embedder_client = OpenAIEmbedder(
    api_key=OPENAI_API_KEY,
    model_name="text-embedding-3-small",
)

ingestion_pipeline = IngestionPipeline(
    modules=[
        DoclingParser(), # choose between Docling, Azure or TextParser to parse plain text

        #LLMCaptioner(
        #    client=OpenAIClient(api_key="YOUR_API_KEY"),
        #), # This is optional, add it if you want to caption the media

        NodeSplitter(max_char=1000),             # Split Nodes into Chunks
        ChunkEmbedder(client=embedder_client),   # Add embeddings to Chunks
    ],
    vector_store=vectorstore,
    collection_name="my_documents"
)


folder = Path("data")

for pdf in folder.rglob("*.pdf"):
    print("Ingestion:", pdf)
    ingestion_pipeline.run(str(pdf), metadata={"source": str(pdf)})



res = vectorstore.search(
    query_vector = [0.0] * 1536,
    collection_name="my_documents",
    k=2,
)
print(res)